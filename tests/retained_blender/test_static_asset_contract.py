import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "gameassetai" / "blender"))
from validate_static_asset_assembly_request import validate_request, validate_revision_request  # noqa: E402


def request():
    return {
        "schema": "gameassetai.static-asset-assembly-request.v5",
        "scene_name": "Scene", "asset_name": "Painted Crate",
        "collection_name": "GAA Painted Crate",
        "style": {
            "family": "CUSTOM", "shape_language": "SOFT_CHUNKY",
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": 2,
            "triangle_budget": 160,
        },
        "art_direction": {
            "provenance": {"source": "USER_REQUEST", "source_ref": "B4 representative request",
                           "profile_sha256": None},
            "surface_style": "PAINTED_LOOK_STYLIZED", "silhouette": "tall rounded crate",
            "proportion": "narrow body with broad front panel", "geometry_detail": "profile frame and crest",
            "palette": [[0.38, 0.12, 0.03, 1], [0.72, 0.34, 0.08, 1], [0.12, 0.22, 0.28, 1]],
            "unsupported": ["hand-painted illustration quality"],
        },
        "appearance": {
            "uv_policy": "LOCAL_BOX_PROJECT", "texture_policy": "OPTIONAL_GENERATED_PNG",
            "texture_output_directory": "D:/output/textures", "max_texture_resolution": 128,
            "max_texture_bytes": 262144, "pack_images": True,
        },
        "materials": [
            {"name": "Painted Wood", "material_role": "wood", "base_color": [0.5, 0.2, 0.04, 1],
             "metallic": 0, "roughness": 0.78,
             "texture": {"kind": "WOOD_GRAIN", "image_name": "Painted Wood Image",
                         "file_name": "painted-wood.png", "resolution": 128,
                         "palette": [[0.25, 0.06, 0.015, 1], [0.72, 0.3, 0.06, 1], [0.95, 0.58, 0.16, 1]],
                         "scale": 7, "seed": 11}},
            {"name": "Painted Metal", "material_role": "metal", "base_color": [0.1, 0.2, 0.27, 1],
             "metallic": 0.45, "roughness": 0.5, "texture": None},
        ],
        "parts": [
            {"name": "Painted Body", "semantic_role": "body",
             "geometry": {"kind": "PROFILE_BEVELED_EXTRUSION",
                          "outer_profile_points": [[-1, -0.7], [1, -0.7], [1.2, -0.45], [1.2, 0.45], [1, 0.7], [-1, 0.7], [-1.2, 0.45], [-1.2, -0.45]],
                          "core_profile_points": [[-0.85, -0.55], [0.85, -0.55], [1, -0.36], [1, 0.36], [0.85, 0.55], [-0.85, 0.55], [-1, 0.36], [-1, -0.36]],
                          "depth": 1.4},
             "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "Painted Wood"},
        ],
        "policy": {
            "existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS_IMAGES",
            "external_files": "NO_OVERWRITE_OWNED_PNG",
            "failure": "ROLL_BACK_OWNED_DATA_AND_FILES",
        },
    }


class StaticAssetV5RequestTests(unittest.TestCase):
    def test_valid_painted_request(self):
        result = validate_request(request())
        self.assertEqual("ready", result["status"])
        self.assertEqual("LOCAL_BOX_PROJECT", result["request"]["appearance"]["uv_policy"])
        self.assertEqual(
            {"rotation_degrees": 0, "mirror_u": False, "mirror_v": False},
            result["request"]["parts"][0]["uv_mapping"],
        )

    def test_explicit_uv_mapping_is_bounded(self):
        payload = request()
        payload["parts"][0]["uv_mapping"] = {
            "rotation_degrees": 90, "mirror_u": True, "mirror_v": False,
        }
        self.assertEqual(90, validate_request(payload)["request"]["parts"][0]["uv_mapping"]["rotation_degrees"])
        payload = request()
        payload["parts"][0]["uv_mapping"] = {
            "rotation_degrees": 45, "mirror_u": False, "mirror_v": False,
        }
        with self.assertRaisesRegex(ValueError, "rotation_degrees"):
            validate_request(payload)

    def test_revision_v4_accepts_v5_geometry_policy(self):
        payload = request()
        revision = {
            "schema": "gameassetai.static-asset-revision-request.v4",
            "scene_name": "Scene", "source_collection_name": payload["collection_name"],
            "asset_name": "Wider Painted Crate", "collection_name": "GAA Wider Painted Crate",
            "revisions": [{
                "semantic_role": "body", "geometry": copy.deepcopy(payload["parts"][0]["geometry"]),
                "location": None, "rotation_degrees": None,
            }],
            "policy": {
                "existing_names": "REFUSE", "source": "PRESERVE",
                "revision": "NEW_COLLECTION_OBJECTS_MESHES_REGENERATED_UV_SHARED_MATERIALS_IMAGES",
                "failure": "ROLL_BACK_OWNED_DATA",
            },
        }
        self.assertEqual("ready", validate_revision_request(revision)["status"])
        revision["policy"]["revision"] = "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS"
        with self.assertRaisesRegex(ValueError, "policy"):
            validate_revision_request(revision)

    def test_painted_style_requires_texture(self):
        payload = request()
        payload["materials"][0]["texture"] = None
        with self.assertRaisesRegex(ValueError, "requires at least one"):
            validate_request(payload)

    def test_texture_budget_and_names_are_guarded(self):
        payload = request()
        payload["materials"][0]["texture"]["resolution"] = 256
        with self.assertRaisesRegex(ValueError, "resolution"):
            validate_request(payload)
        payload = request()
        payload["materials"][1]["texture"] = copy.deepcopy(payload["materials"][0]["texture"])
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_request(payload)

    def test_workspace_profile_provenance_requires_hash(self):
        payload = request()
        payload["art_direction"]["provenance"] = {
            "source": "WORKSPACE_PROFILE", "source_ref": "profiles/game.md", "profile_sha256": None,
        }
        with self.assertRaisesRegex(ValueError, "profile_sha256"):
            validate_request(payload)
        payload["art_direction"]["provenance"]["profile_sha256"] = "a" * 64
        self.assertEqual("ready", validate_request(payload)["status"])

    def test_legacy_policy_is_not_accepted_for_v5(self):
        payload = request()
        payload["policy"] = {
            "existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        }
        with self.assertRaisesRegex(ValueError, "policy"):
            validate_request(payload)


if __name__ == "__main__":
    unittest.main()
# Retained focused contract regression after the product restructure.
