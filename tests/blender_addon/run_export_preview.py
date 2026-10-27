import argparse
from pathlib import Path
import sys
import tempfile

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

    gameassetai.register()
    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.object
    bpy.ops.object.camera_add(location=(0.0, -5.0, 0.0), rotation=(1.5707963268, 0.0, 0.0))
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.5
    scene.camera = camera
    before = (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.film_transparent)
    output = Path(tempfile.gettempdir()) / "gaa-addon-export-preview-test.png"
    if output.exists():
        output.unlink()
    settings = scene.gameassetai
    settings.resolution_x = 32
    settings.resolution_y = 32
    settings.export_file = str(output)
    assert bpy.ops.gameassetai.export_preview_png() == {"FINISHED"}
    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage, scene.render.film_transparent) == before
    try:
        bpy.ops.gameassetai.export_preview_png()
        raise AssertionError("existing output must be refused")
    except RuntimeError as exc:
        assert "already exists" in str(exc)
    assert not list(output.parent.glob(f".{output.stem}.*.stage.png"))
    output.unlink()
    gameassetai.unregister()
    print("GameAssetAI single PNG export: 5 checks passed")


if __name__ == "__main__":
    main()
