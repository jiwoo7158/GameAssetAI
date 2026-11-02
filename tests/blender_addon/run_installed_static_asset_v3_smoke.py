import argparse
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def main():
    skill_root = Path(parse_args().skill_root).resolve()
    sys.path.insert(0, str(skill_root / "scripts"))
    from create_static_asset_assembly import create_asset, remove_created_asset

    before = {
        "objects": sorted(bpy.data.objects.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
        "materials": sorted(bpy.data.materials.keys()),
        "collections": sorted(bpy.data.collections.keys()),
    }
    request = {
        "schema": "gameassetai.static-asset-assembly-request.v3",
        "scene_name": bpy.context.scene.name,
        "asset_name": "Installed Profile Smoke",
        "collection_name": "GAA Installed Profile Smoke",
        "style": {
            "family": "CUSTOM", "shape_language": "ANGULAR",
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": 1,
            "triangle_budget": 32,
        },
        "materials": [{
            "name": "GAA Installed Smoke Material", "base_color": [0.2, 0.4, 0.7, 1],
            "metallic": 0.1, "roughness": 0.7,
        }],
        "parts": [{
            "name": "GAA Installed Profile Part", "semantic_role": "profile_part",
            "geometry": {"kind": "PROFILE_EXTRUSION", "profile_points": [[-0.5, -0.5], [0.7, -0.3], [0.9, 0.2], [0, 0.8], [-0.5, 0.4]], "depth": 0.2},
            "location": [0, 0, 0], "rotation_degrees": [0, 0, 0],
            "material": "GAA Installed Smoke Material",
        }],
        "policy": {
            "existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        },
    }
    receipt = create_asset(request, authorized=True)
    assert receipt["parts"][0]["geometry_kind"] == "PROFILE_EXTRUSION"
    assert receipt["triangle_count"] <= request["style"]["triangle_budget"]
    remove_created_asset(receipt)
    after = {
        "objects": sorted(bpy.data.objects.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
        "materials": sorted(bpy.data.materials.keys()),
        "collections": sorted(bpy.data.collections.keys()),
    }
    assert after == before
    print(f"Installed static v3 execution passed from {skill_root}")


if __name__ == "__main__":
    main()
