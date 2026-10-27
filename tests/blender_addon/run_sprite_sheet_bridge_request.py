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
    from gameassetai.operators.sprite_sheet_bridge import _load_helpers

    gameassetai.register()
    namespace = _load_helpers(root / "skills" / "assemble-png-sprite-sheet" / "scripts")
    assert callable(namespace["validate_2d_sprite_sheet_request"])
    assert callable(namespace["assemble_2d_sprite_sheet"])
    settings = bpy.context.scene.gameassetai
    settings.sprite_sheet_columns = 4
    settings.sprite_sheet_rows = 2
    settings.sprite_sheet_padding = 1
    assert (settings.sprite_sheet_columns, settings.sprite_sheet_rows, settings.sprite_sheet_padding) == (4, 2, 1)
    gameassetai.unregister()
    print("GameAssetAI sprite-sheet bridge request: 4 checks passed")


if __name__ == "__main__":
    main()
