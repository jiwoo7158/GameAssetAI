"""Offline tests for exact static multi-pass impostor bundle requests."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_2d_depth_pass_request import SCHEMA as DEPTH_SCHEMA  # noqa: E402
from validate_2d_impostor_bundle_request import (  # noqa: E402
    SCHEMA, validate_2d_impostor_bundle_request)
from validate_2d_normal_pass_request import SCHEMA as NORMAL_SCHEMA  # noqa: E402
from validate_2d_static_render_request import SCHEMA as COLOR_SCHEMA  # noqa: E402


def fixture(root):
    view = {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
            "up": [0, 0, 1], "framing_margin": 0.1}
    style = {"resolution": [32, 32], "anti_aliasing": "DISABLED",
             "nearest_neighbor": True}
    output = lambda name: {"target_file": str(root / name), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}
    color = {"schema": COLOR_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
             "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
             "view": copy.deepcopy(view),
             "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
             "style": {"mode": "PIXEL", **style, "palette_mode": "NONE", "palette": [],
                       "max_colors": None, "outline_mode": "NONE", "outline_color": None,
                       "outline_width": 0, "shading_mode": "NONE", "value_steps": None},
             "output": output("front-color.png")}
    normal = {"schema": NORMAL_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
              "view": copy.deepcopy(view),
              "normal": {"space": "CAMERA_BASIS", "source": "SHADING_NORMAL",
                         "encoding": "SIGNED_XYZ_TO_UNORM_RGB",
                         "background_rgba": [0.0, 0.0, 0.0, 0.0]},
              "style": copy.deepcopy(style), "output": output("front-normal.png")}
    depth = {"schema": DEPTH_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
             "view": copy.deepcopy(view),
             "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                       "normalization": "OBJECT_VERTEX_BOUNDS",
                       "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                       "background_rgba": [0.0, 0.0, 0.0, 0.0]},
             "style": copy.deepcopy(style), "output": output("front-depth.png")}
    return {"schema": SCHEMA,
            "items": [
                {"id": "front-color", "view_id": "front", "pass_kind": "COLOR",
                 "request": color},
                {"id": "front-normal", "view_id": "front", "pass_kind": "NORMAL",
                 "request": normal},
                {"id": "front-depth", "view_id": "front", "pass_kind": "DEPTH",
                 "request": depth}],
            "manifest": {"target_file": str(root / "impostor.json"), "overwrite": False},
            "policy": {"execution_order": "LIST_ORDER", "publication": "ALL_OR_NOTHING",
                       "on_failure": "ROLL_BACK_BUNDLE_OUTPUTS",
                       "framing_mismatch": "REJECT"}}


class ImpostorBundleRequestTests(unittest.TestCase):
    def setUp(self):
        # Keep the temporary basename short for Windows security/path compatibility.
        self.temp = tempfile.TemporaryDirectory(prefix="gai-bundle-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request = fixture(self.root)

    def validate(self, request=None):
        return validate_2d_impostor_bundle_request(request or self.request)

    def test_exact_bundle_is_stable_ordered_and_read_only(self):
        before = list(self.root.iterdir())
        first, second = self.validate(), self.validate()
        self.assertEqual("ready", first["status"])
        self.assertEqual(first, second)
        self.assertEqual(1, first["view_count"])
        self.assertEqual(["COLOR", "NORMAL", "DEPTH"], first["pass_kinds"])
        self.assertEqual(before, list(self.root.iterdir()))

    def test_shared_scene_object_view_resolution_are_required(self):
        for path, value in (([1, "request", "object_name"], "Other"),
                            ([1, "request", "view", "framing_margin"], 0.2),
                            ([2, "request", "style", "resolution"], [64, 32])):
            changed = copy.deepcopy(self.request)
            target = changed["items"][path[0]]
            for key in path[1:-1]:
                target = target[key]
            target[path[-1]] = value
            self.assertEqual("error", self.validate(changed)["status"])

    def test_every_view_requires_same_two_or_more_pass_order(self):
        changed = copy.deepcopy(self.request); changed["items"] = changed["items"][:1]
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request)
        duplicate = copy.deepcopy(changed["items"][0])
        duplicate.update(id="side-color", view_id="side")
        duplicate["request"]["output"]["target_file"] = str(self.root / "side-color.png")
        changed["items"].append(duplicate)
        self.assertEqual("error", self.validate(changed)["status"])

    def test_child_output_manifest_collisions_and_directories_refuse(self):
        changed = copy.deepcopy(self.request)
        changed["items"][1]["request"]["output"]["target_file"] = changed["items"][0]["request"]["output"]["target_file"]
        self.assertEqual("error", self.validate(changed)["status"])
        child = self.root / "child"; child.mkdir()
        changed = copy.deepcopy(self.request)
        changed["manifest"]["target_file"] = str(child / "impostor.json")
        self.assertEqual("error", self.validate(changed)["status"])

    def test_policy_sampling_profile_and_unknown_pass_refuse(self):
        changed = copy.deepcopy(self.request); changed["policy"]["framing_mismatch"] = "ADJUST"
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][0]["request"]["profile"]["name"] = "Game"
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][0]["pass_kind"] = "OBJECT_ID"
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["extra"] = True
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][1]["view_id"] = "Front"
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][1]["view_id"] = None
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][0]["request"]["schema"] = "gameassetai.2d-static-render-request.v2"
        changed["items"][0]["request"]["style"].pop("shading_mode")
        changed["items"][0]["request"]["style"].pop("value_steps")
        self.assertEqual("error", self.validate(changed)["status"])


if __name__ == "__main__":
    unittest.main()
