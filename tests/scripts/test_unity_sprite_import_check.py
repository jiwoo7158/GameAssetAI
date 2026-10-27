"""Offline request and no-overwrite generation tests for Unity PNG Sprite checks."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from prepare_unity_sprite_import_check import (  # noqa: E402
    SCHEMA, prepare, read_request, validate_request)


class UnitySpriteImportCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-unity-sprite-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.asset = self.root / "Assets" / "Sprites" / "sheet.png"
        self.asset.parent.mkdir(parents=True); self.asset.write_bytes(b"fixture-png")
        self.request = {"schema": SCHEMA, "project_root": str(self.root),
                        "asset_path": "Assets/Sprites/sheet.png",
                        "expected_sha256": hashlib.sha256(self.asset.read_bytes()).hexdigest(),
                        "allow_import_refresh": False,
                        "expected": {"image_size": [65, 65], "sprite_mode": "MULTIPLE",
                                     "pixels_per_unit": 32, "filter_mode": "POINT",
                                     "compression": "UNCOMPRESSED", "mipmap_enabled": False,
                                     "alpha_is_transparency": True, "srgb_texture": True,
                                     "sprites": [
                                         {"name": "idle_0", "rect": [0, 33, 32, 32],
                                          "pivot": [16, 16], "pixels_per_unit": 32},
                                         {"name": "idle_1", "rect": [33, 33, 32, 32],
                                          "pivot": [16, 16], "pixels_per_unit": 32}],
                                     "tolerance": 1e-5}}

    def test_prepare_is_hash_bound_and_no_overwrite(self):
        output = self.root / "check.cs"; result = prepare(self.request, output)
        self.assertEqual("prepared", result["status"])
        code = output.read_text(encoding="utf-8")
        self.assertIn("TextureImporterType.Sprite", code)
        self.assertIn("SpriteImportMode.Multiple", code)
        self.assertIn("var expectedNames = new string[]", code)
        self.assertNotIn("Newtonsoft", code)
        self.assertIn("TrimEnd('\\\\', '/')", code)
        self.assertIn("active_scene_preserved", code)
        self.assertEqual(result["code_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
        with self.assertRaises(FileExistsError):
            prepare(self.request, output)

    def test_changed_hash_and_scope_refuse(self):
        self.asset.write_bytes(b"changed")
        self.assertIn("PNG SHA-256 mismatch", validate_request(self.request)[0])
        for path in ("../sheet.png", "Packages/sheet.png", "Assets\\sheet.png",
                     "Assets/Sprites/sheet.jpg"):
            self.assertTrue(validate_request({**self.request, "asset_path": path})[0])

    def test_import_policy_is_exact(self):
        for key, value in (("sprite_mode", "PACKED"), ("filter_mode", "BILINEAR"),
                           ("compression", "COMPRESSED"), ("pixels_per_unit", 0),
                           ("tolerance", float("nan"))):
            expected = {**self.request["expected"], key: value}
            self.assertTrue(validate_request({**self.request, "expected": expected})[0])

    def test_sprite_metadata_is_exact_unique_and_finite(self):
        cases = [[],
                 [{**self.request["expected"]["sprites"][0], "rect": [0, 0, 0, 32]},
                  self.request["expected"]["sprites"][1]],
                 [{**self.request["expected"]["sprites"][0], "rect": [48, 0, 32, 32]},
                  self.request["expected"]["sprites"][1]],
                 [{**self.request["expected"]["sprites"][0], "pivot": [33, 16]},
                  self.request["expected"]["sprites"][1]],
                 [self.request["expected"]["sprites"][0],
                  {**self.request["expected"]["sprites"][1], "name": "idle_0"}]]
        for sprites in cases:
            expected = {**self.request["expected"], "sprites": sprites}
            self.assertTrue(validate_request({**self.request, "expected": expected})[0])

    def test_single_requires_one_sprite_and_exact_fields(self):
        expected = {**self.request["expected"], "sprite_mode": "SINGLE"}
        self.assertTrue(validate_request({**self.request, "expected": expected})[0])
        expected = dict(self.request["expected"]); expected["extra"] = True
        self.assertTrue(validate_request({**self.request, "expected": expected})[0])

    def test_duplicate_and_nonstandard_json_refuse(self):
        path = self.root / "bad.json"
        path.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
        with self.assertRaises(ValueError): read_request(path)
        path.write_text('{"value":NaN}', encoding="utf-8")
        with self.assertRaises(ValueError): read_request(path)


if __name__ == "__main__":
    unittest.main()
