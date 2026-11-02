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
    from create_static_asset_assembly import create_asset, remove_created_asset
    before = (set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.materials), set(bpy.data.collections))
    request = {
        "schema": "gameassetai.static-asset-assembly-request.v4", "scene_name": bpy.context.scene.name,
        "asset_name": "Installed B2 Smoke", "collection_name": "GAA Installed B2 Smoke",
        "style": {"family": "CUSTOM", "shape_language": "ANGULAR",
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": 1, "triangle_budget": 64},
        "materials": [{"name": "GAA Installed B2 Material", "base_color": [.2, .4, .7, 1],
                       "metallic": .1, "roughness": .7}],
        "parts": [{"name": "GAA Installed B2 Part", "semantic_role": "beveled_part",
            "geometry": {"kind": "PROFILE_BEVELED_EXTRUSION",
                "outer_profile_points": [[-1, -.5], [1, -.5], [1, .5], [-1, .5]],
                "core_profile_points": [[-.8, -.3], [.8, -.3], [.8, .3], [-.8, .3]], "depth": .4},
            "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "GAA Installed B2 Material"}],
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS", "failure": "ROLL_BACK_OWNED_DATA"}}
    receipt = create_asset(request, authorized=True)
    assert receipt["parts"][0]["geometry_kind"] == "PROFILE_BEVELED_EXTRUSION"
    assert receipt["parts"][0]["mesh_quality"]["closed_manifold"]
    remove_created_asset(receipt)
    after = (set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.materials), set(bpy.data.collections))
    assert before == after
    print(f"Installed static v4 execution passed from {skill_root}")


if __name__ == "__main__":
    main()
