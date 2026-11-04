import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_character_base_request import validate_request, validate_revision_request  # noqa: E402


def request():
    return {
        "schema": "gameassetai.character-base-request.v5",
        "scene_name": "Scene", "character_name": "GAA SD Hero",
        "collection_name": "GAA SD Hero Collection", "object_name": "GAA SD Hero Object",
        "mesh_name": "GAA SD Hero Mesh", "pose": "A_POSE",
        "topology_mode": "DEFORMATION_TEMPLATE",
        "template": {
            "source_file": "D:/external/human.blend", "source_sha256": "a" * 64,
            "mesh_name": "GEO-body_male_stylized", "source_name": "Blender Studio Human Base Meshes",
            "source_version": "1.4.1", "license": "CC0-1.0", "front_axis": "-Y",
        },
        "proportions": {
            "height": 1.55, "shoulder_width_ratio": 0.36, "hip_width_ratio": 0.25,
            "body_depth_ratio": 0.18, "limb_thickness_ratio": 0.06, "head_height_ratio": 0.21,
        },
        "regions": {
            "head_scale": 1.18, "head_width_scale": 1.05, "head_depth_scale": 1.04,
            "torso_width_scale": 1.04, "arm_length_scale": 0.92,
            "arm_thickness_scale": 1.05, "leg_length_scale": 0.94,
            "hand_scale": 1.12, "foot_scale": 1.15,
        },
        "colors": {
            "skin": [0.73, 0.45, 0.29, 1], "primary": [0.12, 0.24, 0.38, 1],
            "secondary": [0.54, 0.18, 0.10, 1], "boots": [0.06, 0.04, 0.03, 1],
        },
        "art_direction": {
            "style_family": "STYLIZED_LOW_POLY_SD", "silhouette": "large head compact limbs",
            "shape_language": "rounded primary masses with readable broad extremities",
            "palette": [[0.73, 0.45, 0.29, 1], [0.12, 0.24, 0.38, 1],
                        [0.54, 0.18, 0.10, 1], [0.06, 0.04, 0.03, 1]],
            "polygon_budget": 30000,
            "provenance": {"source": "USER_REQUEST", "source_ref": "B6.1 representative request",
                           "profile_sha256": None},
            "unsupported": ["hair", "clothing", "facial rig"],
        },
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_SINGLE_MESH_CHARACTER", "failure": "ROLL_BACK_OWNED_DATA",
                   "rigging": "NOT_INCLUDED"},
    }


class CharacterV5RequestTests(unittest.TestCase):
    def test_valid_creation(self):
        result = validate_request(request())
        self.assertEqual("ready", result["status"])
        self.assertEqual(1.18, result["request"]["regions"]["head_scale"])

    def test_region_and_art_contract_are_bounded(self):
        payload = request()
        payload["regions"]["hand_scale"] = 2.0
        with self.assertRaisesRegex(ValueError, "hand_scale"):
            validate_request(payload)
        payload = request()
        payload["art_direction"]["polygon_budget"] = 1000
        with self.assertRaisesRegex(ValueError, "polygon_budget"):
            validate_request(payload)

    def test_v4_contract_remains_valid(self):
        payload = request()
        payload["schema"] = "gameassetai.character-base-request.v4"
        payload.pop("regions")
        payload.pop("art_direction")
        self.assertEqual("ready", validate_request(payload)["status"])

    def test_copy_revision_contract(self):
        revision = {
            "schema": "gameassetai.character-base-revision-request.v1", "scene_name": "Scene",
            "source_collection_name": "GAA SD Hero Collection", "source_object_name": "GAA SD Hero Object",
            "character_name": "GAA SD Hero Revised", "collection_name": "GAA SD Hero Revised Collection",
            "object_name": "GAA SD Hero Revised Object", "mesh_name": "GAA SD Hero Revised Mesh",
            "regional_adjustments": {"head_scale": 1.08, "arm_length_scale": 0.9,
                                     "hand_scale": 1.1, "foot_scale": 1.08},
            "policy": {"existing_names": "REFUSE", "source": "PRESERVE",
                       "revision": "NEW_COLLECTION_OBJECT_MESH_SHARED_MATERIALS_PRESERVE_UV_TOPOLOGY",
                       "failure": "ROLL_BACK_OWNED_DATA", "rigging": "NOT_INCLUDED"},
        }
        self.assertEqual("ready", validate_revision_request(revision)["status"])
        invalid = copy.deepcopy(revision)
        invalid["regional_adjustments"] = {"head_scale": 1.0}
        with self.assertRaisesRegex(ValueError, "non-identity"):
            validate_revision_request(invalid)


if __name__ == "__main__":
    unittest.main()
