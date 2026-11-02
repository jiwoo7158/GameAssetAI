import copy
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_static_asset_assembly_request import (  # noqa: E402
    validate_request,
    validate_revision_request,
)


def profile(points, depth=0.24):
    return {"kind": "PROFILE_EXTRUSION", "profile_points": points, "depth": depth}


def beveled(outer, core, depth=0.24):
    return {
        "kind": "PROFILE_BEVELED_EXTRUSION",
        "outer_profile_points": outer,
        "core_profile_points": core,
        "depth": depth,
    }


class StaticAssetV3RequestTests(unittest.TestCase):
    def setUp(self):
        self.request = {
            "schema": "gameassetai.static-asset-assembly-request.v3",
            "scene_name": "Scene",
            "asset_name": "Stylized Axe",
            "collection_name": "GAA Stylized Axe",
            "style": {
                "family": "STYLIZED_LOW_POLY",
                "shape_language": "BOLD_ANGULAR",
                "silhouette_strategy": "EXPLICIT_PART_GEOMETRY",
                "shading": "FLAT",
                "material_strategy": "DECLARED_LIMITED",
                "max_materials": 2,
                "triangle_budget": 128,
            },
            "materials": [
                {"name": "Wood", "base_color": [0.2, 0.07, 0.02, 1], "metallic": 0, "roughness": 0.8},
                {"name": "Iron", "base_color": [0.22, 0.28, 0.35, 1], "metallic": 0.7, "roughness": 0.3},
            ],
            "parts": [
                {
                    "name": "Handle", "semantic_role": "handle",
                    "geometry": {"kind": "PRIMITIVE", "primitive": "CYLINDER", "dimensions": [0.2, 0.2, 3], "segments": 8},
                    "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "Wood",
                },
                {
                    "name": "Blade", "semantic_role": "blade",
                    "geometry": profile([[-0.1, -0.5], [1.0, -0.4], [1.3, 0.1], [0.8, 0.8], [-0.1, 0.5]]),
                    "location": [0, 0, 1.1], "rotation_degrees": [0, 0, 0], "material": "Iron",
                },
            ],
            "policy": {
                "existing_names": "REFUSE",
                "source_scene": "PRESERVE",
                "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
                "failure": "ROLL_BACK_OWNED_DATA",
            },
        }

    def test_v3_profile_and_style_validate(self):
        result = validate_request(copy.deepcopy(self.request))
        self.assertEqual("ready", result["status"])
        self.assertEqual("PROFILE_EXTRUSION", result["request"]["parts"][1]["geometry"]["kind"])

    def test_self_intersection_and_budget_are_rejected(self):
        crossing = copy.deepcopy(self.request)
        crossing["parts"][1]["geometry"]["profile_points"] = [[0, 0], [1, 1], [0, 1], [1, 0]]
        with self.assertRaisesRegex(ValueError, "counter-clockwise|self-intersect"):
            validate_request(crossing)
        over = copy.deepcopy(self.request)
        over["style"]["triangle_budget"] = 20
        with self.assertRaisesRegex(ValueError, "estimated triangles"):
            validate_request(over)

    def test_repeated_touching_and_overlapping_profile_edges_are_rejected(self):
        invalid_profiles = [
            [[0, 0], [2, 0], [2, 2], [0, 2], [2, 0]],
            [[0, 0], [3, 0], [3, 2], [1.5, 0], [0, 2]],
            [[0, 0], [3, 0], [2, 0], [2, 2], [0, 2]],
        ]
        for points in invalid_profiles:
            with self.subTest(points=points):
                request = copy.deepcopy(self.request)
                request["parts"][1]["geometry"]["profile_points"] = points
                with self.assertRaisesRegex(ValueError, "reuse|self-intersect|self-touch|overlap"):
                    validate_request(request)

    def test_valid_concave_profile_is_accepted(self):
        request = copy.deepcopy(self.request)
        request["parts"][1]["geometry"]["profile_points"] = [
            [0, 0], [2, 0], [2, 2], [1, 1], [0, 2],
        ]
        self.assertEqual("ready", validate_request(request)["status"])

    def test_style_material_limit_is_enforced(self):
        request = copy.deepcopy(self.request)
        request["style"]["max_materials"] = 1
        with self.assertRaisesRegex(ValueError, "max_materials"):
            validate_request(request)

    def test_geometry_revision_v2_requires_a_real_change(self):
        request = {
            "schema": "gameassetai.static-asset-revision-request.v2",
            "scene_name": "Scene",
            "source_collection_name": "GAA Stylized Axe",
            "asset_name": "Sharper Axe",
            "collection_name": "GAA Sharper Axe",
            "revisions": [{
                "semantic_role": "blade",
                "geometry": profile([[-0.1, -0.6], [1.2, -0.5], [1.6, 0], [1.1, 0.9], [-0.1, 0.5]], 0.28),
                "location": None,
                "rotation_degrees": None,
            }],
            "policy": {
                "existing_names": "REFUSE",
                "source": "PRESERVE",
                "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
                "failure": "ROLL_BACK_OWNED_DATA",
            },
        }
        self.assertEqual("ready", validate_revision_request(copy.deepcopy(request))["status"])
        request["revisions"][0]["geometry"] = None
        with self.assertRaisesRegex(ValueError, "must change"):
            validate_revision_request(request)

    def test_v4_beveled_profile_and_revision_v3_validate(self):
        request = copy.deepcopy(self.request)
        request["schema"] = "gameassetai.static-asset-assembly-request.v4"
        request["parts"][1]["geometry"] = beveled(
            [[0, 0], [2, 0], [2.4, 1], [2, 2], [0, 2]],
            [[0.2, 0.2], [1.7, 0.2], [2.0, 1], [1.7, 1.8], [0.2, 1.8]],
            0.4,
        )
        self.assertEqual("ready", validate_request(copy.deepcopy(request))["status"])

        revision = {
            "schema": "gameassetai.static-asset-revision-request.v3",
            "scene_name": "Scene",
            "source_collection_name": request["collection_name"],
            "asset_name": "Sharper Axe",
            "collection_name": "GAA Sharper Axe",
            "revisions": [{
                "semantic_role": "blade",
                "geometry": beveled(
                    [[0, 0], [2.2, 0], [2.7, 1], [2.2, 2], [0, 2]],
                    [[0.25, 0.3], [1.5, 0.3], [1.8, 1], [1.5, 1.7], [0.25, 1.7]],
                    0.32,
                ),
                "location": None,
                "rotation_degrees": None,
            }],
            "policy": {
                "existing_names": "REFUSE", "source": "PRESERVE",
                "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
                "failure": "ROLL_BACK_OWNED_DATA",
            },
        }
        self.assertEqual("ready", validate_revision_request(revision)["status"])

    def test_v3_rejects_beveled_and_v4_rejects_invalid_core(self):
        geometry = beveled(
            [[0, 0], [2, 0], [2, 2], [0, 2]],
            [[0.2, 0.2], [1.8, 0.2], [1.8, 1.8], [0.2, 1.8]],
        )
        legacy = copy.deepcopy(self.request)
        legacy["parts"][1]["geometry"] = geometry
        with self.assertRaisesRegex(ValueError, "kind must be"):
            validate_request(legacy)

        invalid = copy.deepcopy(self.request)
        invalid["schema"] = "gameassetai.static-asset-assembly-request.v4"
        invalid["parts"][1]["geometry"] = copy.deepcopy(geometry)
        invalid["parts"][1]["geometry"]["core_profile_points"][2] = [2.5, 2.5]
        with self.assertRaisesRegex(ValueError, "inside or on"):
            validate_request(invalid)

        mismatch = copy.deepcopy(invalid)
        mismatch["parts"][1]["geometry"] = copy.deepcopy(geometry)
        mismatch["parts"][1]["geometry"]["core_profile_points"].pop()
        with self.assertRaisesRegex(ValueError, "same point count"):
            validate_request(mismatch)


if __name__ == "__main__":
    unittest.main()
