"""Fresh-process verification for the saved B5 representative result."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", required=True)
    parser.add_argument("--validation", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def by_role(collection):
    return {obj.get("gameassetai_semantic_role"): obj for obj in collection.objects}


def main():
    args = parse_args()
    blend = Path(args.blend).resolve(strict=True)
    validation_path = Path(args.validation).resolve(strict=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    report = json.loads(validation_path.read_text(encoding="utf-8"))
    expected = {
        "shield": ("GAA B5 Shield", "GAA B5 Shield Revised", 4),
        "lantern": ("GAA B5 Lantern", "GAA B5 Lantern Revised", 8),
        "doorway": ("GAA B5 Doorway", "GAA B5 Doorway Revised", 6),
    }
    facts = {}
    for family, (source_name, revised_name, count) in expected.items():
        source, revised = bpy.data.collections.get(source_name), bpy.data.collections.get(revised_name)
        if source is None or revised is None:
            raise AssertionError(f"saved {family} pair is missing")
        source_roles, revised_roles = by_role(source), by_role(revised)
        if set(source_roles) != set(revised_roles) or len(source_roles) != count:
            raise AssertionError(f"saved {family} semantic roles changed")
        for role in source_roles:
            left, right = source_roles[role], revised_roles[role]
            if left.data.as_pointer() == right.data.as_pointer():
                raise AssertionError(f"{family}:{role} shares mutable mesh data")
            if [item.as_pointer() for item in left.data.materials] != [item.as_pointer() for item in right.data.materials]:
                raise AssertionError(f"{family}:{role} did not preserve read-only materials")
            if len(left.data.uv_layers) != 1 or len(right.data.uv_layers) != 1:
                raise AssertionError(f"{family}:{role} UV layer is missing")
            for obj in (left, right):
                values = [tuple(float(value) for value in loop.uv)
                          for loop in obj.data.uv_layers[0].data]
                if not values or not all(-1e-6 <= value <= 1.000001
                                         for pair in values for value in pair):
                    raise AssertionError(f"{family}:{role} UV coordinates are invalid")
        facts[family] = {"roles": sorted(source_roles),
                         "source_triangles": report["receipts"][family]["triangle_count"],
                         "revision_triangles": report["revision_receipts"][family]["triangle_count"]}

    shield_textures = report["receipts"]["shield"]["textures"]
    if len(shield_textures) != 2:
        raise AssertionError("saved shield texture inventory changed")
    for item in shield_textures:
        path = Path(item["path"]).resolve(strict=True)
        if sha256(path) != item["sha256"]:
            raise AssertionError(f"external texture changed: {path}")
        image = bpy.data.images.get(item["image_name"])
        if image is None or image.packed_file is None:
            raise AssertionError(f"packed texture missing: {item['image_name']}")

    print(json.dumps({"status": "pass", "blend": str(blend),
                      "families": facts,
                      "texture_sha256": {Path(item["path"]).name: item["sha256"]
                                         for item in shield_textures}}))


if __name__ == "__main__":
    main()
