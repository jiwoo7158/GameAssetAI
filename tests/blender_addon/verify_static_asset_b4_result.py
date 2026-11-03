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
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uv_facts(collection):
    result = {}
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        if len(obj.data.uv_layers) != 1:
            raise AssertionError(f"{obj.name} does not retain exactly one UV layer")
        values = [tuple(float(component) for component in item.uv)
                  for item in obj.data.uv_layers[0].data]
        if not values or not all(-1e-6 <= component <= 1.000001
                                 for pair in values for component in pair):
            raise AssertionError(f"{obj.name} has invalid UV coordinates")
        if len({(round(u, 5), round(v, 5)) for u, v in values}) < 3:
            raise AssertionError(f"{obj.name} has collapsed UV coordinates")
        result[obj.get("gameassetai_semantic_role")] = len(values)
    return result


def main():
    args = parse_args()
    blend = Path(args.blend).resolve(strict=True)
    validation_path = Path(args.validation).resolve(strict=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    angular = bpy.data.collections.get("GAA B4 Angular Crate")
    painted = bpy.data.collections.get("GAA B4 Painted Crate")
    if angular is None or painted is None:
        raise AssertionError("saved style collections are missing")

    angular_uv = uv_facts(angular)
    painted_uv = uv_facts(painted)
    if len(angular_uv) != 4 or len(painted_uv) != 5:
        raise AssertionError("saved semantic part count changed")

    texture_facts = validation["receipts"]["painted"]["textures"]
    if len(texture_facts) != 2:
        raise AssertionError("painted receipt does not retain two textures")
    for item in texture_facts:
        path = Path(item["path"]).resolve(strict=True)
        if sha256(path) != item["sha256"]:
            raise AssertionError(f"external texture hash changed: {path}")
        image = bpy.data.images.get(item["image_name"])
        if image is None or image.packed_file is None:
            raise AssertionError(f"packed image is missing: {item['image_name']}")

    for material_name in ("B4 Painted Wood", "B4 Painted Metal"):
        material = bpy.data.materials.get(material_name)
        if material is None or not material.use_nodes:
            raise AssertionError(f"material is missing: {material_name}")
        image_nodes = [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]
        if len(image_nodes) != 1 or not image_nodes[0].outputs["Color"].is_linked:
            raise AssertionError(f"image texture is not linked: {material_name}")

    angular_receipt = validation["receipts"]["angular"]
    painted_receipt = validation["receipts"]["painted"]
    if angular_receipt["triangle_count"] == painted_receipt["triangle_count"]:
        raise AssertionError("style geometry signatures unexpectedly match")
    if angular_receipt["art_direction"]["surface_style"] != "ANGULAR_LOW_POLY":
        raise AssertionError("angular style provenance was not retained")
    if painted_receipt["art_direction"]["surface_style"] != "PAINTED_LOOK_STYLIZED":
        raise AssertionError("painted style provenance was not retained")

    print(json.dumps({
        "status": "pass",
        "blend": str(blend),
        "uv_parts": {"angular": angular_uv, "painted": painted_uv},
        "texture_sha256": {Path(item["path"]).name: item["sha256"] for item in texture_facts},
        "triangle_counts": {
            "angular": angular_receipt["triangle_count"],
            "painted": painted_receipt["triangle_count"],
        },
    }))


if __name__ == "__main__":
    main()
