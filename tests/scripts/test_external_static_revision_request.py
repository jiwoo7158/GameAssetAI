import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_static_asset_assembly_request import validate_external_revision_request  # noqa: E402


def request():
    return {
        "schema": "gameassetai.external-static-revision-request.v1",
        "scene_name": "Scene", "asset_name": "Revised Cannon",
        "source_collection_name": "External Cannon Source", "collection_name": "Revised Cannon",
        "source_file": "D:/external/cannon.glb", "source_sha256": "1" * 64,
        "part_roles": [
            {"object_name": "Barrel", "semantic_role": "barrel"},
            {"object_name": "Body", "semantic_role": "body"},
        ],
        "revisions": [{"semantic_role": "barrel", "operation": "LOCAL_AXIS_END_OFFSET",
                       "axis": "X", "side": "MAX", "threshold": 1.0, "delta": 0.25}],
        "provenance": {"producer": "Example", "version": "1", "source_ref": "asset-1", "license": "CC0"},
        "policy": {"existing_names": "REFUSE", "source_file": "READ_ONLY",
                   "import": "NEW_COLLECTION_OWNED_SOURCE",
                   "revision": "NEW_COLLECTION_INDEPENDENT_MESHES_SHARED_MATERIALS",
                   "failure": "ROLL_BACK_OPERATION_DELTA"},
    }


class ExternalStaticRevisionRequestTests(unittest.TestCase):
    def test_valid_request_normalizes_numeric_values(self):
        result = validate_external_revision_request(request())
        self.assertEqual("ready", result["status"])
        self.assertEqual(0.25, result["request"]["revisions"][0]["delta"])

    def test_mapping_and_revision_roles_are_explicit_unique_and_complete(self):
        duplicate = request()
        duplicate["part_roles"][1]["semantic_role"] = "BARREL"
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_external_revision_request(duplicate)
        missing = request()
        missing["revisions"][0]["semantic_role"] = "wheel"
        with self.assertRaisesRegex(ValueError, "not mapped"):
            validate_external_revision_request(missing)

    def test_only_bounded_region_operation_is_supported(self):
        invalid = request()
        invalid["revisions"][0]["operation"] = "ARBITRARY_DEFORM"
        with self.assertRaisesRegex(ValueError, "LOCAL_AXIS_END_OFFSET"):
            validate_external_revision_request(invalid)
        zero = request()
        zero["revisions"][0]["delta"] = 0
        with self.assertRaisesRegex(ValueError, "non-zero"):
            validate_external_revision_request(zero)

    def test_source_and_result_collections_must_differ(self):
        invalid = copy.deepcopy(request())
        invalid["collection_name"] = invalid["source_collection_name"]
        with self.assertRaisesRegex(ValueError, "must differ"):
            validate_external_revision_request(invalid)


if __name__ == "__main__":
    unittest.main()
