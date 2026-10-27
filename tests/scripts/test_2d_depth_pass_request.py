import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("depth_request", ROOT / "scripts" / "validate_2d_depth_pass_request.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DepthPassRequestTests(unittest.TestCase):
    def request(self, root):
        return {"schema": MODULE.SCHEMA, "scene_name": "Scene", "object_name": "Prop",
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                           "normalization": "OBJECT_VERTEX_BOUNDS",
                           "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                           "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                          "nearest_neighbor": True},
                "output": {"target_file": str(root / "depth.png"), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}}

    def test_exact_camera_linear_contract_is_stable(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            first = MODULE.validate_2d_depth_pass_request(request)
            second = MODULE.validate_2d_depth_pass_request(request)
            self.assertTrue(first["ready_for_blender_inspection"])
            self.assertEqual(first["request_sha256"], second["request_sha256"])
            self.assertEqual("camera_back_toward_camera", first["depth_contract"]["axis"])
            self.assertIn("encoded_0", first["depth_contract"]["near"])

    def test_alternate_space_source_and_range_inference_refuse(self):
        with tempfile.TemporaryDirectory() as folder:
            for key, value in (("space", "CAMERA_CLIP"), ("source", "EVALUATED_POSITION"),
                               ("normalization", "SCENE_BOUNDS")):
                request = self.request(Path(folder))
                request["depth"][key] = value
                self.assertFalse(MODULE.validate_2d_depth_pass_request(request)["ready_for_blender_inspection"])

    def test_encoding_background_and_sampling_are_fixed(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["depth"]["encoding"] = "NEAR_WHITE_FAR_BLACK"
            request["depth"]["background_rgba"] = [0.5, 0.5, 1.0, 1.0]
            request["style"]["anti_aliasing"] = "ENGINE_DEFAULT"
            result = MODULE.validate_2d_depth_pass_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertGreaterEqual(len(result["errors"]), 3)

    def test_rgba8_new_file_policy_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.request(root)
            request["output"]["color_depth"] = 16
            request["output"]["overwrite"] = True
            (root / "depth.png").write_bytes(b"occupied")
            result = MODULE.validate_2d_depth_pass_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])


if __name__ == "__main__":
    unittest.main()
