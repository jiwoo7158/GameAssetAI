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
    settings = bpy.context.scene.gameassetai
    output = Path(tempfile.gettempdir()) / "gaa-addon-preset-roundtrip.json"
    if output.exists():
        output.unlink()
    settings.preset_file = str(output)
    settings.resolution_x = 96
    settings.view_preset = "QUARTER"
    settings.material_preset = "CEL_BANDED"
    settings.shadow_bands = 4
    assert bpy.ops.gameassetai.save_preset() == {"FINISHED"}
    assert output.is_file() and "gameassetai.blender-addon-preset.v1" in output.read_text(encoding="utf-8")
    settings.resolution_x = 32
    settings.view_preset = "FRONT"
    settings.material_preset = "FLAT_LIT"
    settings.shadow_bands = 2
    assert bpy.ops.gameassetai.load_preset() == {"FINISHED"}
    assert (settings.resolution_x, settings.view_preset, settings.material_preset, settings.shadow_bands) == (96, "QUARTER", "CEL_BANDED", 4)
    assert not list(output.parent.glob(f".{output.stem}.*.stage.json"))
    output.unlink()
    gameassetai.unregister()
    print("GameAssetAI preset roundtrip: 5 checks passed")


if __name__ == "__main__":
    main()
