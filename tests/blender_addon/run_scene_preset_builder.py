import argparse
import importlib
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


def snapshot(scene):
    return {
        "objects": sorted(bpy.data.objects.keys()),
        "cameras": sorted(bpy.data.cameras.keys()),
        "lights": sorted(bpy.data.lights.keys()),
        "collections": sorted(bpy.data.collections.keys()),
        "camera": scene.camera.name if scene.camera else None,
        "resolution": (
            scene.render.resolution_x,
            scene.render.resolution_y,
            scene.render.resolution_percentage,
        ),
        "transparent": scene.render.film_transparent,
        "node_groups": sorted(bpy.data.node_groups.keys()),
        "use_nodes": scene.use_nodes,
        "compositor": scene.compositing_node_group.name if scene.compositing_node_group else None,
    }


def main():
    repo_root = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(repo_root / "blender_addon"))
    addon = importlib.import_module("gameassetai")
    addon.register()

    scene = bpy.context.scene
    cube = bpy.data.objects.get("Cube")
    assert cube is not None and cube.type == "MESH"
    bpy.context.view_layer.objects.active = cube
    cube.select_set(True)

    before = snapshot(scene)
    settings = scene.gameassetai
    settings.resolution_x = 64
    settings.resolution_y = 48
    settings.view_preset = "QUARTER"
    settings.framing_margin = 0.125

    result = bpy.ops.gameassetai.setup_pixel_scene()
    assert result == {"FINISHED"}
    assert scene.camera is not None and scene.camera.name == "GAA Pixel Camera"
    assert scene.camera.data.type == "ORTHO" and scene.camera.data.ortho_scale > 0.0
    assert scene.render.resolution_x == 64 and scene.render.resolution_y == 48
    assert scene.render.film_transparent is True
    collection = bpy.data.collections.get("GameAssetAI Pixel Preview")
    assert collection is not None and len(collection.objects) == 3
    assert all(obj.get("gameassetai_owner") == "pixel_preview_v1" for obj in collection.objects)

    settings.pixel_scale = 4
    result = bpy.ops.gameassetai.build_pixel_compositor()
    assert result == {"FINISHED"}
    tree = scene.compositing_node_group
    assert tree is not None and tree.name == "GameAssetAI Pixel Compositor"
    assert tree.get("gameassetai_owner") == "pixel_preview_v1"
    assert {node.bl_idname for node in tree.nodes} == {
        "CompositorNodeRLayers",
        "CompositorNodeScale",
        "CompositorNodePixelate",
        "NodeGroupOutput",
    }
    assert len(tree.nodes) == 5 and len(tree.links) == 4
    downsample = tree.nodes.get("GAA Downsample")
    assert downsample.inputs["Type"].default_value == "Relative"
    assert downsample.inputs["Interpolation"].default_value == "Nearest"
    assert downsample.inputs["X"].default_value == 0.25
    assert downsample.inputs["Y"].default_value == 0.25

    result = bpy.ops.gameassetai.remove_pixel_compositor()
    assert result == {"FINISHED"}

    result = bpy.ops.gameassetai.remove_pixel_scene()
    assert result == {"FINISHED"}
    after = snapshot(scene)
    assert after == before, (before, after)
    assert not any(key.startswith("gaa_previous_") for key in scene.keys())

    addon.unregister()
    print("GameAssetAI Scene/Compositor Builders: 17 checks passed")


if __name__ == "__main__":
    main()
