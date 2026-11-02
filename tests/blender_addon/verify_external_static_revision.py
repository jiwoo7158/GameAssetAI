import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


def snapshot(collection):
    return {obj.get("gameassetai_semantic_role"): {
        "vertices": tuple(tuple(round(float(value), 8) for value in vertex.co) for vertex in obj.data.vertices),
        "edges": tuple(tuple(edge.vertices) for edge in obj.data.edges),
        "polygons": tuple(tuple(polygon.vertices) for polygon in obj.data.polygons),
        "materials": tuple(material.name for material in obj.data.materials),
        "uv": tuple((layer.name, len(layer.data)) for layer in obj.data.uv_layers),
    } for obj in collection.objects if obj.type == "MESH"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--glb", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    args = parser.parse_args(values)
    assert hashlib.sha256(args.glb.read_bytes()).hexdigest() == args.sha256
    bpy.ops.wm.open_mainfile(filepath=str(args.blend.resolve(strict=True)))
    source = bpy.data.collections["GAA External Field Cannon Source"]
    result = bpy.data.collections["GAA Extended Trail Field Cannon"]
    source_state, result_state = snapshot(source), snapshot(result)
    assert set(source_state) == set(result_state) and len(source_state) == 13
    for role in source_state:
        assert source_state[role]["edges"] == result_state[role]["edges"]
        assert source_state[role]["polygons"] == result_state[role]["polygons"]
        assert source_state[role]["materials"] == result_state[role]["materials"]
        assert source_state[role]["uv"] == result_state[role]["uv"]
        if role in {"trail_left", "trail_right"}:
            assert source_state[role]["vertices"] != result_state[role]["vertices"]
        else:
            assert source_state[role]["vertices"] == result_state[role]["vertices"]
    print(json.dumps({"status": "pass", "roles": len(source_state),
                      "modified": ["trail_left", "trail_right"]}))


if __name__ == "__main__":
    main()
