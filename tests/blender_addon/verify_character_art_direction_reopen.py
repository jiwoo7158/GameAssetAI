import argparse
import json
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    report = json.loads(args.report.read_text(encoding="utf-8"))
    failures = []
    for style, expected in report["candidates"].items():
        collections = [item for item in bpy.data.collections if item.get("gameassetai_character_style_prototype_owner") and item.get("gameassetai_character_style_candidate") == style]
        if len(collections) != 1:
            failures.append(style + " Collection identity is missing or ambiguous")
            continue
        objects = [obj for obj in collections[0].objects if obj.type == "MESH"]
        triangles = sum(sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons) for obj in objects)
        if len(objects) != expected["objects"] or triangles != expected["triangles"]:
            failures.append(style + " saved geometry facts differ")
        roles = {obj.get("gameassetai_character_component_role") for obj in objects}
        if set(expected["semantic_roles"]) != roles:
            failures.append(style + " semantic roles differ")
    result = {"status": "pass" if not failures else "failed", "failures": failures,
              "blend": bpy.data.filepath}
    print("GAMEASSETAI_CHARACTER_ART_REOPEN " + json.dumps(result))
    if failures:
        raise AssertionError("; ".join(failures))


if __name__ == "__main__":
    main()
