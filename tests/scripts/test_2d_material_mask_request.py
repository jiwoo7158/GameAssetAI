import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("mask_request", ROOT / "scripts" / "validate_2d_material_mask_request.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MaterialMaskRequestTests(unittest.TestCase):
    def request(self, root):
        return {"schema": MODULE.SCHEMA, "scene_name": "Scene", "object_name": "Prop",
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "mask": {"material_slot_index": 1, "visible_rgba": [1, 1, 1, 1]},
                "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                          "nearest_neighbor": True},
                "output": {"target_file": str(root / "mask.png"), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}}

    def test_accepts_exact_explicit_request_deterministically(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            first = MODULE.validate_2d_material_mask_request(request)
            second = MODULE.validate_2d_material_mask_request(request)
            self.assertTrue(first["ready_for_blender_inspection"])
            self.assertEqual(first["request_sha256"], second["request_sha256"])
            self.assertEqual(first["errors"], [])

    def test_rejects_ambiguous_or_inferred_mask_choices(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["mask"]["material_slot_index"] = "Body"
            request["mask"]["visible_rgba"] = None
            result = MODULE.validate_2d_material_mask_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertGreaterEqual(len(result["errors"]), 2)

    def test_rejects_sampling_format_and_collision_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            request = self.request(root)
            request["style"]["anti_aliasing"] = "ENGINE_DEFAULT"
            request["style"]["nearest_neighbor"] = False
            request["output"]["color_depth"] = 16
            request["output"]["overwrite"] = True
            (root / "mask.png").write_bytes(b"occupied")
            result = MODULE.validate_2d_material_mask_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertGreaterEqual(len(result["errors"]), 5)

    def test_rejects_unknown_fields_and_invalid_view(self):
        with tempfile.TemporaryDirectory() as folder:
            request = self.request(Path(folder))
            request["automatic_material"] = True
            request["view"]["up"] = [0, -1, 0]
            result = MODULE.validate_2d_material_mask_request(request)
            self.assertFalse(result["ready_for_blender_inspection"])
            self.assertIsNone(result["request_sha256"])


if __name__ == "__main__":
    unittest.main()
