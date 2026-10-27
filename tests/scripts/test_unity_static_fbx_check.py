"""Offline request and no-overwrite generation tests for Unity static FBX checks."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from prepare_unity_static_fbx_check import SCHEMA, prepare, read_request, validate_request


class UnityStaticFbxCheckTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-unity-check-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.asset = self.root / "Assets" / "Blender" / "fixture.fbx"
        self.asset.parent.mkdir(parents=True)
        self.asset.write_bytes(b"fixture-fbx")
        self.request = {
            "schema": SCHEMA, "project_root": str(self.root),
            "asset_path": "Assets/Blender/fixture.fbx",
            "expected_sha256": hashlib.sha256(self.asset.read_bytes()).hexdigest(),
            "allow_import_refresh": True,
            "expected": {"mesh_count": 1, "total_vertices": 4,
                         "total_triangles": 2, "total_uv_coordinates": 4,
                         "total_submeshes": 1, "material_slot_count": 1,
                         "animation_clip_count": 0, "root_location": [0, 0, 0],
                         "root_rotation": [0, 0, 0], "root_scale": [1, 1, 1],
                         "world_bounds_size": [2, 0, 1], "tolerance": 1e-5}}

    def test_prepare_binds_request_and_never_overwrites(self):
        output = self.root / "check.cs"
        before = json.loads(json.dumps(self.request))
        result = prepare(self.request, output)
        self.assertEqual("prepared", result["status"])
        self.assertEqual(before, self.request)
        code = output.read_text(encoding="utf-8")
        self.assertIn(self.request["asset_path"], code)
        self.assertIn(self.request["expected_sha256"], code)
        self.assertIn(r"TrimEnd('\\', '/')", code)
        self.assertEqual(result["code_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
        with self.assertRaises(FileExistsError):
            prepare(self.request, output)

    def test_changed_asset_hash_refused(self):
        self.asset.write_bytes(b"changed")
        errors, _ = validate_request(self.request)
        self.assertIn("asset file SHA-256 mismatch", errors)

    def test_path_scope_and_schema_refused(self):
        for changes in ({"asset_path": "../fixture.fbx"},
                        {"asset_path": "Packages/fixture.fbx"},
                        {"asset_path": "Assets\\fixture.fbx"},
                        {"schema": "unknown"}, {"allow_import_refresh": None}):
            with self.subTest(changes=changes):
                request = {**self.request, **changes}
                self.assertTrue(validate_request(request)[0])

    def test_expected_contract_is_exact_and_finite(self):
        cases = []
        missing = dict(self.request["expected"])
        del missing["mesh_count"]
        cases.append(missing)
        unknown = dict(self.request["expected"], game_default=True)
        cases.append(unknown)
        cases.append(dict(self.request["expected"], total_vertices=-1))
        cases.append(dict(self.request["expected"], mesh_count=0))
        cases.append(dict(self.request["expected"], root_scale=[1, 1]))
        cases.append(dict(self.request["expected"], tolerance=float("nan")))
        for expected in cases:
            with self.subTest(expected=expected):
                request = {**self.request, "expected": expected}
                self.assertTrue(validate_request(request)[0])

    def test_missing_asset_and_relative_output_refused(self):
        request = {**self.request, "asset_path": "Assets/Blender/missing.fbx"}
        self.assertTrue(validate_request(request)[0])
        with self.assertRaises(ValueError):
            prepare(self.request, Path("relative.cs"))

    def test_duplicate_and_nonstandard_json_refused(self):
        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"schema":"a","schema":"b"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            read_request(duplicate)
        nonstandard = self.root / "nan.json"
        nonstandard.write_text('{"value":NaN}', encoding="utf-8")
        with self.assertRaises(ValueError):
            read_request(nonstandard)


if __name__ == "__main__":
    unittest.main()
