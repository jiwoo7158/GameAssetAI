"""Offline tests for the static impostor bundle result manifest."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from quantize_rgba import encode_png_rgba8  # noqa: E402
from validate_2d_depth_pass_request import SCHEMA as DEPTH_SCHEMA  # noqa: E402
from validate_2d_impostor_bundle_request import (  # noqa: E402
    SCHEMA as REQUEST_SCHEMA, validate_2d_impostor_bundle_request)
from validate_2d_impostor_result_manifest import (  # noqa: E402
    PREVIEW_SCHEMA, SCHEMA, validate_2d_impostor_result_manifest)
from validate_2d_normal_pass_request import SCHEMA as NORMAL_SCHEMA  # noqa: E402


def _hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def fixture(root):
    view = {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
            "up": [0, 0, 1], "framing_margin": 0.1}
    style = {"resolution": [1, 1], "anti_aliasing": "DISABLED", "nearest_neighbor": True}
    output = lambda name: {"target_file": str(root / name), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}
    normal = {"schema": NORMAL_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
              "view": copy.deepcopy(view),
              "normal": {"space": "CAMERA_BASIS", "source": "SHADING_NORMAL",
                         "encoding": "SIGNED_XYZ_TO_UNORM_RGB",
                         "background_rgba": [0.0, 0.0, 0.0, 0.0]},
              "style": copy.deepcopy(style), "output": output("normal.png")}
    depth = {"schema": DEPTH_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
             "view": copy.deepcopy(view),
             "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                       "normalization": "OBJECT_VERTEX_BOUNDS",
                       "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                       "background_rgba": [0.0, 0.0, 0.0, 0.0]},
             "style": copy.deepcopy(style), "output": output("depth.png")}
    request = {"schema": REQUEST_SCHEMA,
               "items": [{"id": "front-normal", "view_id": "front",
                           "pass_kind": "NORMAL", "request": normal},
                          {"id": "front-depth", "view_id": "front",
                           "pass_kind": "DEPTH", "request": depth}],
               "manifest": {"target_file": str(root / "result.json"), "overwrite": False},
               "policy": {"execution_order": "LIST_ORDER", "publication": "ALL_OR_NOTHING",
                          "on_failure": "ROLL_BACK_BUNDLE_OUTPUTS",
                          "framing_mismatch": "REJECT"}}
    preflight = validate_2d_impostor_bundle_request(request)
    plan_hash, source_hash = "a" * 64, "b" * 64
    view_result = {"view_id": "front", "plan": {"projection": "ORTHOGRAPHIC"},
                   "plan_fingerprint": plan_hash, "children": []}
    preview = {"schema": PREVIEW_SCHEMA, "status": "planned", "errors": [], "blockers": [],
               "camera_created": False, "render_authorized": False,
               "request_sha256": preflight["request_sha256"],
               "source_fingerprint": source_hash, "views": [view_result],
               "view_count": 1, "child_count": 2, "children": []}
    preview["preview_fingerprint"] = _hash_json(
        {"request_sha256": preflight["request_sha256"],
         "source_fingerprint": source_hash, "views": preview["views"]})
    png = encode_png_rgba8([[(255, 255, 255, 255)]])
    for target in preflight["outputs"]:
        Path(target).write_bytes(png)
    artifacts = []
    for item in preflight["items"]:
        path = Path(item["target_file"])
        artifacts.append({"position": item["position"], "item_id": item["id"],
                          "view_id": item["view_id"], "pass_kind": item["pass_kind"],
                          "target_file": item["target_file"],
                          "request_sha256": item["request_sha256"],
                          "plan_fingerprint": plan_hash,
                          "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                          "receipt_sha256": str(item["position"] + 1) * 64,
                          "bytes": path.stat().st_size})
    manifest = {"schema": SCHEMA, "request_sha256": preflight["request_sha256"],
                "source_fingerprint": source_hash,
                "preview_fingerprint": preview["preview_fingerprint"],
                "policy": copy.deepcopy(preflight["policy"]),
                "views": [{"position": 0, "view_id": "front",
                           "plan_fingerprint": plan_hash}], "artifacts": artifacts}
    return preflight, preview, manifest


class ImpostorResultManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gai-result-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.preflight, self.preview, self.manifest = fixture(self.root)

    def validate(self, manifest=None, preflight=None, preview=None):
        return validate_2d_impostor_result_manifest(
            manifest or self.manifest, preflight or self.preflight, preview or self.preview)

    def test_complete_result_is_stable_and_read_only(self):
        before = sorted(path.name for path in self.root.iterdir())
        first, second = self.validate(), self.validate()
        self.assertEqual("ready", first["status"])
        self.assertEqual(first, second)
        self.assertEqual(2, first["artifact_count"])
        self.assertFalse((self.root / "result.json").exists())
        self.assertEqual(before, sorted(path.name for path in self.root.iterdir()))

    def test_order_and_binding_changes_refuse(self):
        changed = copy.deepcopy(self.manifest)
        changed["artifacts"].reverse()
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.manifest)
        changed["views"][0]["plan_fingerprint"] = "c" * 64
        self.assertEqual("error", self.validate(changed)["status"])

    def test_file_hash_size_signature_and_missing_refuse(self):
        changed = copy.deepcopy(self.manifest); changed["artifacts"][0]["bytes"] += 1
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.manifest); changed["artifacts"][0]["png_sha256"] = "d" * 64
        self.assertEqual("error", self.validate(changed)["status"])
        Path(self.preflight["outputs"][0]).write_bytes(b"not-png")
        self.assertEqual("error", self.validate()["status"])

    def test_stale_preview_request_and_policy_refuse(self):
        changed = copy.deepcopy(self.preview); changed["source_fingerprint"] = "e" * 64
        self.assertEqual("error", self.validate(preview=changed)["status"])
        changed = copy.deepcopy(self.manifest); changed["request_sha256"] = "f" * 64
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.manifest); changed["policy"]["publication"] = "PARTIAL"
        self.assertEqual("error", self.validate(changed)["status"])

    def test_unknown_fields_and_manifest_collision_refuse(self):
        changed = copy.deepcopy(self.manifest); changed["extra"] = True
        self.assertEqual("error", self.validate(changed)["status"])
        (self.root / "result.json").write_text("occupied", encoding="utf-8")
        self.assertEqual("error", self.validate()["status"])
        (self.root / "result.json").unlink()
        (self.root / "result.json.meta").write_text("occupied", encoding="utf-8")
        self.assertEqual("error", self.validate()["status"])


if __name__ == "__main__":
    unittest.main()
