import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "object_id", ROOT / "scripts" / "validate_2d_object_id_request.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ObjectIdRequestTests(unittest.TestCase):
    def request(self, root):
        return {"schema": MODULE.SCHEMA, "scene_name": "Scene",
                "objects": [
                    {"object_name": "Hero", "id_rgba": [1, 0, 0, 1]},
                    {"object_name": "Wall", "id_rgba": [0, 1, 0, 1]},
                    {"object_name": "Prop", "id_rgba": [0, 0, 1, 1]}],
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                          "nearest_neighbor": True},
                "output": {"target_file": str(root / "object-id.png"), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}}

    def test_exact_explicit_request_is_stable(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            first = MODULE.validate_2d_object_id_request(request)
            second = MODULE.validate_2d_object_id_request(request)
            self.assertTrue(first["ready_for_blender_inspection"])
            self.assertEqual(first["request_sha256"], second["request_sha256"])

    def test_names_and_encoded_colors_must_be_unique(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["objects"][1]["object_name"] = "Hero"
            request["objects"][2]["id_rgba"] = [1.0, 0.001, 0.001, 1.0]
            result = MODULE.validate_2d_object_id_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertGreaterEqual(len(result["errors"]), 2)

    def test_object_count_is_bounded_and_no_inference_field_exists(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.request(root)
            request["objects"] = request["objects"][:1]
            self.assertFalse(MODULE.validate_2d_object_id_request(request)["ready_for_blender_inspection"])
            request = self.request(root)
            request["include_scene_objects"] = True
            self.assertFalse(MODULE.validate_2d_object_id_request(request)["ready_for_blender_inspection"])

    def test_sampling_rgba8_and_new_file_policy_are_fixed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.request(root)
            request["style"]["nearest_neighbor"] = False
            request["output"]["color_depth"] = 16
            request["output"]["overwrite"] = True
            (root / "object-id.png").write_bytes(b"occupied")
            result = MODULE.validate_2d_object_id_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertGreaterEqual(len(result["errors"]), 3)


if __name__ == "__main__":
    unittest.main()
