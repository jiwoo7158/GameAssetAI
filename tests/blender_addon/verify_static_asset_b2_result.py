import argparse
import json
from pathlib import Path
import sys

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(values)
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    expected = {"GAA B2 Fantasy Axe", "GAA B2 Wide Bevel Axe", "GAA B2 Reinforced Crate", "GAA B2 Revised Crate"}
    assert expected.issubset(bpy.data.collections.keys())
    beveled = []
    for name in expected:
        for obj in bpy.data.collections[name].objects:
            geometry = json.loads(obj.data["gameassetai_geometry_spec"])
            if geometry["kind"] == "PROFILE_BEVELED_EXTRUSION":
                quality = json.loads(obj.data["gameassetai_profile_mesh_quality"])
                assert quality["closed_manifold"] and quality["normals_outward"] and quality["signed_volume"] > 0
                beveled.append(obj.name)
    assert len(beveled) == 6
    print(json.dumps({"status": "pass", "beveled_objects": beveled}))


if __name__ == "__main__":
    main()
