import argparse
import json
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True)
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def main():
    blend = Path(parse_args().blend).resolve()
    assert Path(bpy.data.filepath).resolve() == blend
    expected = {
        "GAA Stylized Fantasy Axe",
        "GAA Wide Sharp Fantasy Axe",
        "GAA Stylized Profile Shield",
    }
    assert expected <= set(bpy.data.collections.keys())
    original = bpy.data.collections["GAA Stylized Fantasy Axe"]
    revised = bpy.data.collections["GAA Wide Sharp Fantasy Axe"]
    original_by_role = {obj.get("gameassetai_semantic_role"): obj for obj in original.objects}
    revised_by_role = {obj.get("gameassetai_semantic_role"): obj for obj in revised.objects}
    assert set(original_by_role) == set(revised_by_role)
    assert [tuple(vertex.co) for vertex in original_by_role["blade"].data.vertices] != [
        tuple(vertex.co) for vertex in revised_by_role["blade"].data.vertices
    ]
    assert tuple(original_by_role["blade"].scale) == tuple(revised_by_role["blade"].scale) == (1.0, 1.0, 1.0)
    assert all(obj.data.get("gameassetai_geometry_spec") for collection in expected for obj in bpy.data.collections[collection].objects)
    result = {
        "status": "pass",
        "blend": str(blend),
        "collections": sorted(expected),
        "original_parts": len(original.objects),
        "revised_parts": len(revised.objects),
        "saved_geometry_revision_persisted": True,
    }
    output = blend.with_name("reopen-validation.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
