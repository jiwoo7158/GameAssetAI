import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("object_mask", ROOT / "scripts" / "validate_2d_object_mask_request.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ObjectMaskRequestTests(unittest.TestCase):
    def request(self, root):
        return {"schema": MODULE.SCHEMA, "scene_name": "Scene", "target_object_name": "Hero",
                "occluder_object_names": ["Wall", "Prop"],
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "mask": {"visible_rgba": [1, 1, 1, 1]},
                "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                          "nearest_neighbor": True},
                "output": {"target_file": str(root / "object-mask.png"), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}}

    def test_exact_request_is_stable_and_all_objects_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            first = MODULE.validate_2d_object_mask_request(request)
            second = MODULE.validate_2d_object_mask_request(request)
            self.assertTrue(first["ready_for_blender_inspection"])
            self.assertEqual(first["request_sha256"], second["request_sha256"])

    def test_target_and_occluders_must_be_unique_and_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["occluder_object_names"] = ["Hero", "Wall", "Wall"]
            self.assertFalse(MODULE.validate_2d_object_mask_request(request)["ready_for_blender_inspection"])
            request["occluder_object_names"] = [f"Object{i}" for i in range(64)]
            self.assertFalse(MODULE.validate_2d_object_mask_request(request)["ready_for_blender_inspection"])

    def test_inference_sampling_and_output_changes_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.request(root)
            request["include_scene_objects"] = True
            request["style"]["nearest_neighbor"] = False
            request["output"]["overwrite"] = True
            (root / "object-mask.png").write_bytes(b"occupied")
            result = MODULE.validate_2d_object_mask_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertIsNone(result["request_sha256"])

    def test_empty_occluder_list_is_explicitly_valid(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["occluder_object_names"] = []
            self.assertTrue(MODULE.validate_2d_object_mask_request(request)["ready_for_blender_inspection"])


if __name__ == "__main__":
    unittest.main()
