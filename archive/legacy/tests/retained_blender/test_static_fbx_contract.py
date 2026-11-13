"""Read-only, game-neutral static FBX request preflight regressions."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "gameassetai" / "blender"))
from validate_static_fbx_request import (SCHEMA, OBSERVED_MIN_SCALE,
                                         validate_static_fbx_request)


class StaticFbxRequestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-fbx-request-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.request = {"schema": SCHEMA, "scene_name": "OwnedScene",
                        "object_name": "OwnedMesh",
                        "target_file": str(self.root / "new.fbx"),
                        "axis_forward": "-Z", "axis_up": "Y", "global_scale": 1,
                        "apply_unit_scale": False,
                        "apply_scale_options": "FBX_SCALE_NONE",
                        "use_space_transform": True, "bake_space_transform": False,
                        "use_mesh_modifiers": False,
                        "path_mode": "AUTO", "overwrite": False}

    def check_refused(self, **changes):
        request = {**self.request, **changes}
        report = validate_static_fbx_request(request)
        self.assertFalse(report["ready_for_blender_inspection"])
        self.assertTrue(report["errors"])
        self.assertIsNone(report["request_sha256"])
        self.assertFalse((self.root / "new.fbx").exists())

    def test_explicit_request_is_read_only(self):
        before = dict(self.request)
        report = validate_static_fbx_request(self.request)
        self.assertTrue(report["ready_for_blender_inspection"], report["errors"])
        self.assertEqual(64, len(report["request_sha256"]))
        self.assertEqual(before, self.request)
        self.assertEqual([], list(self.root.iterdir()))

    def test_missing_and_unknown_fields_refused(self):
        request = dict(self.request)
        del request["axis_up"]
        request["game_default"] = "Y"
        report = validate_static_fbx_request(request)
        self.assertFalse(report["ready_for_blender_inspection"])
        self.assertTrue(any("missing" in e for e in report["errors"]))
        self.assertTrue(any("unknown" in e for e in report["errors"]))

    def test_axes_and_scale_refused(self):
        for changes in ({"axis_forward": "Y", "axis_up": "-Y"},
                        {"axis_up": "North"}, {"global_scale": 0},
                        {"global_scale": 0.001},
                        {"global_scale": float("nan")},
                        {"global_scale": float("inf")},
                        {"global_scale": 10 ** 400},
                        {"global_scale": True}, {"global_scale": 1001}):
            with self.subTest(changes=changes):
                self.check_refused(**changes)

    def test_missing_policy_and_copy_mode_refused(self):
        for changes in ({"apply_unit_scale": None}, {"apply_scale_options": None},
                        {"apply_scale_options": "DEFAULT"},
                        {"use_space_transform": None}, {"bake_space_transform": 0},
                        {"use_mesh_modifiers": 0},
                        {"path_mode": "COPY"}, {"overwrite": True},
                        {"path_mode": []}, {"axis_up": []},
                        {"object_name": " "}, {"scene_name": " "},
                        {"schema": "unknown"}):
            with self.subTest(changes=changes):
                self.check_refused(**changes)

    def test_target_and_meta_collisions_refused(self):
        self.check_refused(target_file="relative.fbx")
        self.check_refused(target_file=str(self.root / "wrong.obj"))
        self.check_refused(target_file=str(self.root / "CON.fbx"))
        self.check_refused(target_file=str(self.root / "bad?.fbx"))
        self.check_refused(target_file=str(self.root / "missing" / "new.fbx"))
        self.check_refused(target_file=str(self.root / ".." / self.root.name / "new.fbx"))
        self.check_refused(target_file=str(self.root / "bad\x00name.fbx"))
        (self.root / "new.fbx.meta").write_text("sentinel", encoding="utf-8")
        self.check_refused()
        self.assertEqual("sentinel", (self.root / "new.fbx.meta").read_text(encoding="utf-8"))
        (self.root / "new.fbx.meta").unlink()
        (self.root / "new.fbx").write_bytes(b"existing")
        report = validate_static_fbx_request(self.request)
        self.assertFalse(report["ready_for_blender_inspection"])
        self.assertEqual(b"existing", (self.root / "new.fbx").read_bytes())

    def test_non_object_refused(self):
        self.assertFalse(validate_static_fbx_request(None)["ready_for_blender_inspection"])
        self.assertFalse(validate_static_fbx_request({3: "bad"})["ready_for_blender_inspection"])

    def test_observed_minimum_is_accepted(self):
        self.request["global_scale"] = OBSERVED_MIN_SCALE
        self.assertTrue(validate_static_fbx_request(self.request)["ready_for_blender_inspection"])


if __name__ == "__main__":
    unittest.main()
# Retained focused contract regression after the product restructure.
