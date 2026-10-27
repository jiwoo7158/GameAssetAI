import argparse
import copy
import json
import sys
from pathlib import Path

import bpy


PART_ROLES = [
    ("Mesh_CarriageBody", "carriage_body"),
    ("Mesh_TrailLeft", "trail_left"),
    ("Mesh_TrailRight", "trail_right"),
    ("Mesh_Barrel", "barrel"),
    ("Mesh_MuzzleBand", "muzzle_band"),
    ("Mesh_Bore", "bore"),
    ("Mesh_Breech", "breech"),
    ("Mesh_Axle", "axle"),
    ("Mesh_WheelLeft", "wheel_left"),
    ("Mesh_HubLeft", "hub_left"),
    ("Mesh_WheelRight", "wheel_right"),
    ("Mesh_HubRight", "hub_right"),
    ("Mesh_ElevationBlock", "elevation_block"),
]


def snapshot():
    result = {}
    for name in ("scenes", "objects", "meshes", "materials", "collections", "images"):
        result[name] = sorted((block.name, block.as_pointer()) for block in getattr(bpy.data, name))
    result["active_object"] = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    result["selected"] = sorted(obj.name for obj in bpy.context.selected_objects)
    result["active_collection"] = bpy.context.view_layer.active_layer_collection.name
    result["object_state"] = {
        obj.name: {
            "type": obj.type,
            "location": tuple(float(value) for value in obj.location),
            "rotation": tuple(float(value) for value in obj.rotation_euler),
            "scale": tuple(float(value) for value in obj.scale),
            "collections": sorted(collection.name for collection in obj.users_collection),
        }
        for obj in bpy.data.objects
    }
    result["mesh_state"] = {
        mesh.name: (len(mesh.vertices), len(mesh.edges), len(mesh.polygons), tuple(material.name for material in mesh.materials))
        for mesh in bpy.data.meshes
    }
    result["material_state"] = {
        material.name: (tuple(float(value) for value in material.diffuse_color), bool(material.use_nodes))
        for material in bpy.data.materials
    }
    return result


def expect_failure(callback, fragment):
    try:
        callback()
    except Exception as exc:
        assert fragment in str(exc), str(exc)
        return str(exc)
    raise AssertionError(f"expected failure containing {fragment!r}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--glb", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    scripts = Path(args.repo_root) / "scripts"
    sys.path.insert(0, str(scripts))
    from create_static_asset_assembly import import_kiln_glb, remove_imported_asset

    request = {
        "schema": "gameassetai.kiln-glb-import-request.v1",
        "scene_name": bpy.context.scene.name,
        "asset_name": "Kiln Field Cannon Adapter Check",
        "collection_name": "GAA Kiln Field Cannon Import",
        "source_file": str(Path(args.glb).resolve()),
        "source_sha256": args.sha256,
        "part_roles": [
            {"object_name": object_name, "semantic_role": role}
            for object_name, role in PART_ROLES
        ],
        "provenance": {
            "producer": "Kiln",
            "version": "1.5.0",
            "program_ref": "p_7dde98dc80a9",
        },
        "policy": {
            "existing_names": "REFUSE",
            "source_file": "READ_ONLY",
            "import": "NEW_COLLECTION_OWNED_DATA",
            "failure": "ROLL_BACK_IMPORT_DELTA",
        },
    }

    baseline = snapshot()
    bad_hash = copy.deepcopy(request)
    bad_hash["source_sha256"] = "0" * 64
    hash_error = expect_failure(lambda: import_kiln_glb(bad_hash, authorized=True), "SHA-256 mismatch")
    assert snapshot() == baseline

    duplicate_role = copy.deepcopy(request)
    duplicate_role["part_roles"][1]["semantic_role"] = duplicate_role["part_roles"][0]["semantic_role"]
    duplicate_error = expect_failure(
        lambda: import_kiln_glb(duplicate_role, authorized=True),
        "semantic roles must be case-insensitively unique",
    )
    assert snapshot() == baseline

    occupied_name = copy.deepcopy(request)
    occupied_name["part_roles"][0]["object_name"] = "Cube"
    collision_error = expect_failure(
        lambda: import_kiln_glb(occupied_name, authorized=True),
        "mapped object names are occupied",
    )
    assert snapshot() == baseline

    missing_mapping = copy.deepcopy(request)
    missing_mapping["part_roles"] = missing_mapping["part_roles"][:-1]
    mapping_error = expect_failure(
        lambda: import_kiln_glb(missing_mapping, authorized=True),
        "mapping must cover every imported Mesh",
    )
    assert snapshot() == baseline

    receipt = import_kiln_glb(request, authorized=True)
    assert receipt["status"] == "created"
    assert receipt["operation"] == "kiln_glb_import"
    assert receipt["source_sha256"] == args.sha256
    assert receipt["native_revision_compatibility"] == "NOT_VALIDATED"
    assert len(receipt["parts"]) == len(PART_ROLES)
    assert {part["semantic_role"] for part in receipt["parts"]} == {role for _, role in PART_ROLES}
    assert len(receipt["created"]["materials"]) == 4
    for category in ("scenes",):
        assert snapshot()[category] == baseline[category]
    for name, pointer in baseline["objects"]:
        assert bpy.data.objects.get(name) is not None and bpy.data.objects[name].as_pointer() == pointer
    for name, pointer in baseline["meshes"]:
        assert bpy.data.meshes.get(name) is not None and bpy.data.meshes[name].as_pointer() == pointer
    for name, pointer in baseline["materials"]:
        assert bpy.data.materials.get(name) is not None and bpy.data.materials[name].as_pointer() == pointer
    assert snapshot()["active_object"] == baseline["active_object"]
    assert snapshot()["selected"] == baseline["selected"]
    assert snapshot()["active_collection"] == baseline["active_collection"]

    cleanup_receipt = copy.deepcopy(receipt)
    guarded_mesh = bpy.data.objects[receipt["parts"][0]["name"]].data
    owner_token = guarded_mesh["gameassetai_kiln_import_owner"]
    del guarded_mesh["gameassetai_kiln_import_owner"]
    cleanup_guard_error = expect_failure(
        lambda: remove_imported_asset(cleanup_receipt),
        "Mesh ownership cannot be verified",
    )
    guarded_mesh["gameassetai_kiln_import_owner"] = owner_token
    remove_imported_asset(cleanup_receipt)
    assert snapshot() == baseline

    output = {
        "blender_version": bpy.app.version_string,
        "invalid_hash_error": hash_error,
        "duplicate_role_error": duplicate_error,
        "occupied_name_error": collision_error,
        "incomplete_mapping_error": mapping_error,
        "cleanup_guard_error": cleanup_guard_error,
        "receipt": receipt,
        "cleanup_restored_exact_baseline": True,
    }
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        kept_receipt = import_kiln_glb(request, authorized=True)
        blend_path = output_dir / "kiln-field-cannon-adapter-check.blend"
        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
        output["saved_blend"] = str(blend_path)
        output["kept_receipt"] = kept_receipt
        (output_dir / "kiln-field-cannon-adapter-receipt.json").write_text(
            json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    print("GAMEASSETAI_KILN_ADAPTER_RESULT=" + json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
