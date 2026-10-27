import argparse
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


def main():
    root = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(root / "blender_addon"))
    import gameassetai
    from gameassetai.constants import ADDON_OWNER_KEY, MATERIAL_OWNER_VALUE, MATERIAL_STATE_KEY

    gameassetai.register()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = "GAA Material Test"
    original_names = []
    for index, color in enumerate(((0.8, 0.2, 0.1, 1.0), (0.1, 0.3, 0.8, 1.0))):
        material = bpy.data.materials.new(f"GAA Original {index}")
        material.diffuse_color = color
        obj.data.materials.append(material)
        original_names.append(material.name)
    obj.data.polygons[0].material_index = 1
    original_indices = [polygon.material_index for polygon in obj.data.polygons]
    settings = scene.gameassetai
    settings.material_target = obj
    settings.material_preset = "CEL_BANDED"
    settings.shadow_bands = 3

    assert bpy.ops.gameassetai.apply_material_preset() == {"FINISHED"}
    assert MATERIAL_STATE_KEY in obj
    owned = [slot.material for slot in obj.material_slots]
    owned_names = [material.name for material in owned]
    assert all(material.get(ADDON_OWNER_KEY) == MATERIAL_OWNER_VALUE for material in owned)
    assert all(material.get("gaa_shadow_bands") == 3 for material in owned)
    assert [polygon.material_index for polygon in obj.data.polygons] == original_indices
    assert bpy.ops.gameassetai.apply_material_preset.poll() is False

    assert bpy.ops.gameassetai.remove_material_preset() == {"FINISHED"}
    assert MATERIAL_STATE_KEY not in obj
    assert [slot.material.name for slot in obj.material_slots] == original_names
    assert [polygon.material_index for polygon in obj.data.polygons] == original_indices
    assert all(bpy.data.materials.get(name) is None for name in owned_names)
    gameassetai.unregister()
    print("GameAssetAI material presets: 9 checks passed")


if __name__ == "__main__":
    main()
