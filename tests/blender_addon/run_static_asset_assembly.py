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
    repo_root = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(repo_root / "scripts"))
    import create_static_asset_assembly as assembly
    from create_static_asset_assembly import create_asset, remove_created_asset, revise_asset_copy

    scene = bpy.context.scene
    before = {
        "objects": sorted(bpy.data.objects.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
        "materials": sorted(bpy.data.materials.keys()),
        "collections": sorted(bpy.data.collections.keys()),
    }
    request = {
        "schema": "gameassetai.static-asset-assembly-request.v1",
        "scene_name": scene.name,
        "asset_name": "Low Poly Training Sword",
        "collection_name": "GAA Training Sword",
        "materials": [
            {"name": "GAA Steel", "base_color": [0.42, 0.5, 0.62, 1.0], "metallic": 0.65, "roughness": 0.28},
            {"name": "GAA Leather", "base_color": [0.18, 0.055, 0.025, 1.0], "metallic": 0.0, "roughness": 0.8},
            {"name": "GAA Brass", "base_color": [0.55, 0.25, 0.045, 1.0], "metallic": 0.7, "roughness": 0.32},
        ],
        "parts": [
            {"name": "GAA Sword Blade", "primitive": "BOX", "dimensions": [0.22, 0.08, 2.6], "location": [0, 0, 1.55], "rotation_degrees": [0, 0, 0], "material": "GAA Steel", "segments": None},
            {"name": "GAA Sword Tip", "primitive": "WEDGE", "dimensions": [0.22, 0.08, 0.38], "location": [0, 0, 3.04], "rotation_degrees": [0, 0, 0], "material": "GAA Steel", "segments": None},
            {"name": "GAA Sword Guard", "primitive": "BOX", "dimensions": [1.1, 0.16, 0.14], "location": [0, 0, 0.2], "rotation_degrees": [0, 0, 0], "material": "GAA Brass", "segments": None},
            {"name": "GAA Sword Grip", "primitive": "CYLINDER", "dimensions": [0.22, 0.22, 0.78], "location": [0, 0, -0.26], "rotation_degrees": [0, 0, 0], "material": "GAA Leather", "segments": 12},
            {"name": "GAA Sword Pommel", "primitive": "ICOSPHERE", "dimensions": [0.34, 0.34, 0.34], "location": [0, 0, -0.78], "rotation_degrees": [0, 0, 0], "material": "GAA Brass", "segments": 12},
        ],
        "policy": {
            "existing_names": "REFUSE",
            "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        },
    }

    try:
        create_asset(request, authorized=False)
        raise AssertionError("creation without authorization must fail")
    except ValueError as exc:
        assert "authorized=true" in str(exc)

    receipt = create_asset(request, authorized=True)
    assert receipt["status"] == "created" and len(receipt["parts"]) == 5
    assert bpy.data.collections.get("GAA Training Sword") is not None
    assert {item["material"] for item in receipt["parts"]} == {"GAA Steel", "GAA Leather", "GAA Brass"}
    assert all(item["vertices"] >= 5 and item["polygons"] >= 5 for item in receipt["parts"])
    assert len(receipt["request_sha256"]) == 64 and len(receipt["receipt_sha256"]) == 64

    remove_created_asset(receipt)

    lantern = {
        "schema": "gameassetai.static-asset-assembly-request.v2",
        "scene_name": scene.name,
        "asset_name": "Compact Lantern",
        "collection_name": "GAA Compact Lantern",
        "materials": [
            {"name": "GAA Lantern Metal", "base_color": [0.08, 0.12, 0.16, 1.0], "metallic": 0.55, "roughness": 0.38},
            {"name": "GAA Lantern Glow", "base_color": [1.0, 0.48, 0.08, 1.0], "metallic": 0.0, "roughness": 0.3},
        ],
        "parts": [
            {"name": "GAA Lantern Body", "semantic_role": "body", "primitive": "CYLINDER", "dimensions": [1.2, 1.2, 1.4], "location": [0, 0, 0.2], "rotation_degrees": [0, 0, 0], "material": "GAA Lantern Glow", "segments": 12},
            {"name": "GAA Lantern Base", "semantic_role": "base", "primitive": "CYLINDER", "dimensions": [1.5, 1.5, 0.25], "location": [0, 0, -0.62], "rotation_degrees": [0, 0, 0], "material": "GAA Lantern Metal", "segments": 12},
            {"name": "GAA Lantern Cap", "semantic_role": "cap", "primitive": "CYLINDER", "dimensions": [1.35, 1.35, 0.22], "location": [0, 0, 0.97], "rotation_degrees": [0, 0, 0], "material": "GAA Lantern Metal", "segments": 12},
            {"name": "GAA Lantern Handle Left", "semantic_role": "handle_left", "primitive": "BOX", "dimensions": [0.14, 0.14, 1.4], "location": [-0.72, 0, 1.55], "rotation_degrees": [0, 18, 0], "material": "GAA Lantern Metal", "segments": None},
            {"name": "GAA Lantern Handle Right", "semantic_role": "handle_right", "primitive": "BOX", "dimensions": [0.14, 0.14, 1.4], "location": [0.72, 0, 1.55], "rotation_degrees": [0, -18, 0], "material": "GAA Lantern Metal", "segments": None},
            {"name": "GAA Lantern Handle Top", "semantic_role": "handle_top", "primitive": "BOX", "dimensions": [1.08, 0.14, 0.14], "location": [0, 0, 2.2], "rotation_degrees": [0, 0, 0], "material": "GAA Lantern Metal", "segments": None},
        ],
        "policy": request["policy"],
    }
    lantern_receipt = create_asset(lantern, authorized=True)
    source_snapshot = {
        item.name: ([tuple(vertex.co) for vertex in item.data.vertices], tuple(item.location), tuple(item.rotation_euler))
        for item in bpy.data.collections["GAA Compact Lantern"].objects
    }
    revision = {
        "schema": "gameassetai.static-asset-revision-request.v1",
        "scene_name": scene.name,
        "source_collection_name": "GAA Compact Lantern",
        "asset_name": "Wide Handle Lantern",
        "collection_name": "GAA Wide Handle Lantern",
        "revisions": [
            {"semantic_role": "body", "dimensions": [1.45, 1.45, 1.15], "location": [0, 0, 0.08], "rotation_degrees": None},
            {"semantic_role": "handle_left", "dimensions": None, "location": [-0.95, 0, 1.58], "rotation_degrees": [0, 24, 0]},
            {"semantic_role": "handle_right", "dimensions": None, "location": [0.95, 0, 1.58], "rotation_degrees": [0, -24, 0]},
            {"semantic_role": "handle_top", "dimensions": [1.55, 0.14, 0.14], "location": [0, 0, 2.24], "rotation_degrees": None},
        ],
        "policy": {
            "existing_names": "REFUSE", "source": "PRESERVE",
            "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        },
    }
    revised_receipt = revise_asset_copy(revision, authorized=True)
    assert revised_receipt["source_preserved"] and revised_receipt["shared_materials"]
    assert set(revised_receipt["revised_roles"]) == {"body", "handle_left", "handle_right", "handle_top"}
    assert source_snapshot == {
        item.name: ([tuple(vertex.co) for vertex in item.data.vertices], tuple(item.location), tuple(item.rotation_euler))
        for item in bpy.data.collections["GAA Compact Lantern"].objects
    }
    revised_by_role = {item["semantic_role"]: item for item in revised_receipt["parts"]}
    assert all(abs(a - b) < 1e-5 for a, b in zip(revised_by_role["body"]["dimensions"], [1.45, 1.45, 1.15]))

    rollback_request = dict(revision)
    rollback_request["asset_name"] = "Rollback Lantern"
    rollback_request["collection_name"] = "GAA Rollback Lantern"
    original_duplicate = assembly._duplicate_part
    calls = {"count": 0}
    def fail_after_first(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("deliberate rollback probe")
        return original_duplicate(*args, **kwargs)
    assembly._duplicate_part = fail_after_first
    try:
        revise_asset_copy(rollback_request, authorized=True)
        raise AssertionError("deliberate revision failure must propagate")
    except RuntimeError as exc:
        assert "rollback probe" in str(exc)
    finally:
        assembly._duplicate_part = original_duplicate
    assert bpy.data.collections.get("GAA Rollback Lantern") is None
    assert not any(item.name.startswith("Rollback Lantern ") for item in bpy.data.objects)

    remove_created_asset(revised_receipt)
    remove_created_asset(lantern_receipt)
    after = {
        "objects": sorted(bpy.data.objects.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
        "materials": sorted(bpy.data.materials.keys()),
        "collections": sorted(bpy.data.collections.keys()),
    }
    assert after == before, (before, after)
    print("GameAssetAI static asset assembly: v1 regression, v2 semantic revision, source preservation and rollback passed")


if __name__ == "__main__":
    main()
