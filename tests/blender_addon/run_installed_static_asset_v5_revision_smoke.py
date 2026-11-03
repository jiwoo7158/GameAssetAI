"""Direct installed-Skill smoke for creation v5 and revision v4."""
import argparse
from pathlib import Path
import sys

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    skill_root = Path(parser.parse_args(values).skill_root).resolve()
    sys.path.insert(0, str(skill_root / "scripts"))
    from create_static_asset_assembly import create_asset, revise_asset_copy, remove_created_asset

    scene = bpy.context.scene
    before = (set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.materials),
              set(bpy.data.images), set(bpy.data.collections))
    request = {
        "schema": "gameassetai.static-asset-assembly-request.v5",
        "scene_name": scene.name, "asset_name": "Installed B5 Smoke",
        "collection_name": "GAA Installed B5 Smoke",
        "style": {"family": "CUSTOM", "shape_language": "ANGULAR",
                  "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
                  "material_strategy": "DECLARED_LIMITED", "max_materials": 1,
                  "triangle_budget": 32},
        "art_direction": {"provenance": {"source": "USER_REQUEST",
                                           "source_ref": "installed B5 smoke",
                                           "profile_sha256": None},
                          "surface_style": "ANGULAR_LOW_POLY", "silhouette": "beveled panel",
                          "proportion": "wide and shallow", "geometry_detail": "single bounded solid",
                          "palette": [[.2, .4, .7, 1], [.08, .12, .18, 1]], "unsupported": []},
        "appearance": {"uv_policy": "LOCAL_BOX_PROJECT",
                       "texture_policy": "OPTIONAL_GENERATED_PNG",
                       "texture_output_directory": str(skill_root),
                       "max_texture_resolution": 32, "max_texture_bytes": 65536,
                       "pack_images": True},
        "materials": [{"name": "Installed B5 Material", "material_role": "panel",
                       "base_color": [.2, .4, .7, 1], "metallic": .1,
                       "roughness": .7, "texture": None}],
        "parts": [{"name": "Installed B5 Panel", "semantic_role": "panel",
                   "geometry": {"kind": "PROFILE_BEVELED_EXTRUSION",
                                "outer_profile_points": [[-1, -.5], [1, -.5], [1, .5], [-1, .5]],
                                "core_profile_points": [[-.8, -.3], [.8, -.3], [.8, .3], [-.8, .3]],
                                "depth": .4},
                   "location": [0, 0, 0], "rotation_degrees": [0, 0, 0],
                   "material": "Installed B5 Material",
                   "uv_mapping": {"rotation_degrees": 90, "mirror_u": False, "mirror_v": False}}],
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS_IMAGES",
                   "external_files": "NO_OVERWRITE_OWNED_PNG",
                   "failure": "ROLL_BACK_OWNED_DATA_AND_FILES"},
    }
    source = create_asset(request, authorized=True)
    revision = {"schema": "gameassetai.static-asset-revision-request.v4",
                "scene_name": scene.name, "source_collection_name": request["collection_name"],
                "asset_name": "Installed B5 Smoke Revised",
                "collection_name": "GAA Installed B5 Smoke Revised",
                "revisions": [{"semantic_role": "panel",
                               "geometry": {"kind": "PROFILE_BEVELED_EXTRUSION",
                                            "outer_profile_points": [[-1.2, -.5], [1.2, -.5], [1.2, .5], [-1.2, .5]],
                                            "core_profile_points": [[-1, -.3], [1, -.3], [1, .3], [-1, .3]],
                                            "depth": .4},
                               "location": None, "rotation_degrees": None}],
                "policy": {"existing_names": "REFUSE", "source": "PRESERVE",
                           "revision": "NEW_COLLECTION_OBJECTS_MESHES_REGENERATED_UV_SHARED_MATERIALS_IMAGES",
                           "failure": "ROLL_BACK_OWNED_DATA"}}
    revised = revise_asset_copy(revision, authorized=True)
    assert source["parts"][0]["uv_mapping"]["rotation_degrees"] == 90
    assert revised["replaced_geometry_uv_regenerated"]
    remove_created_asset(revised)
    remove_created_asset(source)
    after = (set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.materials),
             set(bpy.data.images), set(bpy.data.collections))
    assert before == after
    print(f"Installed static v5/revision-v4 execution passed from {skill_root}")


if __name__ == "__main__":
    main()
