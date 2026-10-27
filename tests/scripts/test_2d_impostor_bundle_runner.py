"""Offline job, success and rollback tests for the static impostor coordinator."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from build_2d_impostor_bundle_job import build_2d_impostor_bundle_job  # noqa: E402
from quantize_rgba import encode_png_rgba8  # noqa: E402
from run_2d_impostor_bundle import run_2d_impostor_bundle_job  # noqa: E402
from validate_2d_depth_pass_request import SCHEMA as DEPTH_SCHEMA  # noqa: E402
from validate_2d_impostor_bundle_request import (  # noqa: E402
    SCHEMA as REQUEST_SCHEMA, validate_2d_impostor_bundle_request)
from validate_2d_normal_pass_request import SCHEMA as NORMAL_SCHEMA  # noqa: E402


def hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def make_fixture(root):
    view = {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
            "up": [0, 0, 1], "framing_margin": 0.1}
    style = {"resolution": [2, 2], "anti_aliasing": "DISABLED", "nearest_neighbor": True}
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
    plan = {"projection": "ORTHOGRAPHIC", "center": [0.0, 0.0, 0.0],
            "position": [0.0, -4.0, 0.0],
            "basis_columns": {"right_x": [1.0, 0.0, 0.0],
                              "up_y": [0.0, 0.0, 1.0],
                              "back_z": [0.0, -1.0, 0.0]},
            "orthographic_scale": 2.4, "clip_start": 1.5, "clip_end": 6.5,
            "resolution": [2, 2], "aspect": 1.0,
            "framing_margin_per_side": 0.1,
            "projected_half_extents": [1.0, 1.0, 1.0]}
    plan_hash, source_hash = hash_json(plan), "a" * 64
    child_reports = []
    for item in preflight["items"]:
        token = str(item["position"] + 1)
        child_reports.append({"position": item["position"], "id": item["id"],
                              "view_id": item["view_id"],
                              "pass_kind": item["pass_kind"],
                              "request_sha256": item["request_sha256"],
                              "candidate_schema": "candidate-" + token,
                              "candidate_status": "candidate_for_review",
                              "source_fingerprint": token * 64,
                              "setup_fingerprint": str(item["position"] + 3) * 64,
                              "output_fingerprint": str(item["position"] + 5) * 64})
    view_children = [{**child, "shared_plan_fingerprint": plan_hash}
                     for child in child_reports]
    views = [{"view_id": "front", "plan": plan,
              "plan_fingerprint": plan_hash, "children": view_children}]
    preview = {"schema": "gameassetai.2d-impostor-shared-framing-preview.v1",
               "status": "planned", "errors": [], "blockers": [],
               "camera_created": False, "render_authorized": False,
               "request_sha256": preflight["request_sha256"],
               "source_fingerprint": source_hash, "views": views,
               "view_count": 1, "child_count": 2, "children": child_reports}
    preview["preview_fingerprint"] = hash_json(
        {"request_sha256": preflight["request_sha256"],
         "source_fingerprint": source_hash, "views": views})
    descriptors = []
    for index, (item, child) in enumerate(zip(request["items"], child_reports)):
        stage = root / f"child-{index}.stage.blend"
        stage.write_bytes(f"stage-{index}".encode())
        stage_sha = hashlib.sha256(stage.read_bytes()).hexdigest()
        candidate = {"status": "candidate_for_review",
                     "request_sha256": child["request_sha256"],
                     "source_fingerprint": child["source_fingerprint"],
                     "setup_fingerprint": child["setup_fingerprint"],
                     "output_fingerprint": child["output_fingerprint"]}
        framing = {"status": "planned", "request_sha256": child["request_sha256"],
                   "source_fingerprint": child["source_fingerprint"],
                   "setup_fingerprint": child["setup_fingerprint"],
                   "output_fingerprint": child["output_fingerprint"],
                   "plan": plan, "plan_fingerprint": plan_hash}
        child_job = root / f"child-{index}.job.json"
        payload = {"schema": ("gameassetai.2d-normal-pass-job.v1" if index == 0
                              else "gameassetai.2d-depth-pass-job.v1"),
                   "request": item["request"], "candidate": candidate,
                   "framing": framing,
                   "source_stage": {"path": str(stage), "size": stage.stat().st_size,
                                    "sha256": stage_sha}}
        child_job.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")),
                             encoding="utf-8")
        descriptors.append({"id": item["id"], "pass_kind": item["pass_kind"],
                            "stage_file": str(stage), "stage_sha256": stage_sha,
                            "job_file": str(child_job),
                            "job_sha256": hashlib.sha256(child_job.read_bytes()).hexdigest(),
                            "helper_root": str(ROOT / "scripts")})
    return request, preflight, preview, descriptors


class ImpostorBundleRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gai-coordinator-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, self.preflight, self.preview, self.children = make_fixture(self.root)
        self.job = self.root / ".gameassetai-impostor-bundle-test.job.json"

    def build(self, preview=None, children=None, authorize=True):
        return build_2d_impostor_bundle_job(
            self.request, preview or self.preview, children or self.children,
            str(self.job), authorize=authorize)

    def prepare(self):
        built = self.build()
        self.assertEqual("created", built["status"], built["errors"])
        return built["job_sha256"]

    @staticmethod
    def write_artifact(path, token):
        pixels = [[(ord(token[0]) % 256, 0, 0, 255)] * 2 for _ in range(2)]
        data = encode_png_rgba8(pixels)
        Path(path).write_bytes(data)
        return {"path": path, "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}

    def success_runner(self, _blender, child):
        artifact = self.write_artifact(child["target_file"], child["id"])
        return {"status": "created", "png_published": True,
                "artifact": artifact, "receipt_sha256": child["request_sha256"]}

    def execute(self, job_sha, runner):
        return run_2d_impostor_bundle_job(
            self.job, job_sha, sys.executable, child_runner=runner)

    def test_job_binds_shared_plan_stages_jobs_and_helpers(self):
        built = self.build()
        self.assertEqual("created", built["status"], built["errors"])
        payload = json.loads(self.job.read_text(encoding="utf-8"))
        self.assertEqual(self.preview["preview_fingerprint"], payload["preview_fingerprint"])
        self.assertEqual(self.preview["views"][0]["plan_fingerprint"],
                         payload["children"][0]["plan_fingerprint"])
        self.assertIn("render_2d_normal_pass.py",
                      payload["children"][0]["helper_sha256"])

    def test_job_refuses_authorization_stale_plan_and_collision(self):
        self.assertEqual("error", self.build(authorize=False)["status"])
        stale = copy.deepcopy(self.preview)
        stale["views"][0]["plan"]["orthographic_scale"] = 9.0
        self.assertEqual("error", self.build(preview=stale)["status"])
        Path(self.preflight["outputs"][0]).write_bytes(b"collision")
        self.assertEqual("error", self.build()["status"])

    def test_success_publishes_pngs_then_validated_manifest(self):
        result = self.execute(self.prepare(), self.success_runner)
        self.assertEqual("created", result["status"], result["errors"])
        self.assertEqual(2, result["published_count"])
        self.assertTrue(result["manifest_published"])
        manifest = json.loads(Path(result["manifest_file"]).read_text(encoding="utf-8"))
        self.assertEqual(["NORMAL", "DEPTH"],
                         [item["pass_kind"] for item in manifest["artifacts"]])
        self.assertEqual(result["manifest_sha256"],
                         hashlib.sha256(Path(result["manifest_file"]).read_bytes()).hexdigest())

    def test_later_child_failure_rolls_back_prior_png_and_no_manifest(self):
        job_sha, calls = self.prepare(), []
        def runner(blender, child):
            calls.append(child["id"])
            if len(calls) == 2:
                return {"status": "error", "png_published": False, "errors": ["synthetic"]}
            return self.success_runner(blender, child)
        result = self.execute(job_sha, runner)
        self.assertEqual("error", result["status"])
        self.assertEqual(0, result["published_count"])
        self.assertFalse(Path(self.preflight["outputs"][0]).exists())
        self.assertFalse(Path(self.preflight["manifest"]).exists())

    def test_changed_prior_png_is_preserved_on_later_failure(self):
        job_sha, calls = self.prepare(), []
        def runner(blender, child):
            calls.append(child["id"])
            if len(calls) == 2:
                Path(self.preflight["outputs"][0]).write_bytes(b"user-change")
                raise RuntimeError("synthetic")
            return self.success_runner(blender, child)
        result = self.execute(job_sha, runner)
        self.assertEqual("error", result["status"])
        self.assertEqual(b"user-change", Path(self.preflight["outputs"][0]).read_bytes())
        self.assertTrue(any("changed before rollback" in item for item in result["errors"]))

    def test_stage_helper_and_manifest_collision_refuse_before_children(self):
        job_sha = self.prepare()
        Path(self.children[0]["stage_file"]).write_bytes(b"changed")
        self.assertEqual("error", self.execute(job_sha, self.success_runner)["status"])
        self.setUp(); job_sha = self.prepare()
        Path(self.preflight["manifest"]).write_text("occupied", encoding="utf-8")
        self.assertEqual("error", self.execute(job_sha, self.success_runner)["status"])


if __name__ == "__main__":
    unittest.main()
