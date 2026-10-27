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
    sys.path.insert(0, str(repo_root / "tests" / "blender_addon"))
    from create_character_base import create_character, remove_created_character
    from rig_character_base import create_rig, remove_created_rig
    from run_character_base import request as character_request

    scene = bpy.context.scene
    char_receipt = create_character(character_request(scene.name), authorized=True)
    request = {
        "schema": "gameassetai.character-rig-request.v1",
        "scene_name": scene.name,
        "mesh_object_name": char_receipt["object_name"],
        "armature_object_name": "GAA Scout Rig",
        "armature_data_name": "GAA Scout Armature",
        "rig_name": "GAA Scout",
        "policy": {
            "target": "OWNED_CHARACTER_BASE_ONLY",
            "existing_rig": "REFUSE",
            "weights": "REGION_ASSIGNMENT_V1",
            "source_mesh": "PRESERVE_GEOMETRY",
            "failure": "ROLL_BACK_RIG_CHANGES",
        },
    }
    before_geometry = (len(bpy.data.objects[char_receipt["object_name"]].data.vertices), len(bpy.data.objects[char_receipt["object_name"]].data.polygons))
    try:
        create_rig(request, authorized=False)
        raise AssertionError("unauthorized rig creation must fail")
    except ValueError as exc:
        assert "authorized=true" in str(exc)
    receipt = create_rig(request, authorized=True)
    obj = bpy.data.objects[char_receipt["object_name"]]
    arm = bpy.data.objects[receipt["armature_object_name"]]
    assert receipt["status"] == "created" and len(receipt["bone_names"]) == 18
    assert arm.type == "ARMATURE" and len(obj.modifiers) == 1
    assert len(obj.vertex_groups) == 17 and receipt["weighted_vertex_count"] == len(obj.data.vertices)
    assert all(len(group.name) > 0 for group in obj.vertex_groups)
    assert (len(obj.data.vertices), len(obj.data.polygons)) == before_geometry
    assert len(receipt["receipt_sha256"]) == 64
    remove_created_rig(receipt)
    assert len(obj.modifiers) == 0 and len(obj.vertex_groups) == 0
    remove_created_character(char_receipt)
    connected_request = character_request(scene.name)
    connected_request.update({
        "schema": "gameassetai.character-base-request.v2",
        "character_name": "GAA Connected Rig Scout",
        "collection_name": "GAA Connected Rig Character",
        "object_name": "GAA Connected Rig Base",
        "mesh_name": "GAA Connected Rig Base Mesh",
        "topology_mode": "VOLUME_ISLANDS",
    })
    connected_character = create_character(connected_request, authorized=True)
    blended_request = {
        "schema": "gameassetai.character-rig-request.v2",
        "scene_name": scene.name,
        "mesh_object_name": connected_character["object_name"],
        "armature_object_name": "GAA Connected Rig",
        "armature_data_name": "GAA Connected Armature",
        "rig_name": "GAA Connected",
        "policy": {
            "target": "OWNED_CHARACTER_BASE_ONLY",
            "existing_rig": "REFUSE",
            "weights": "LINEAR_JOINT_BLEND_V2",
            "source_mesh": "PRESERVE_GEOMETRY",
            "failure": "ROLL_BACK_RIG_CHANGES",
        },
    }
    blended_receipt = create_rig(blended_request, authorized=True)
    connected_obj = bpy.data.objects[connected_character["object_name"]]
    multi_weighted = sum(1 for vertex in connected_obj.data.vertices if len(vertex.groups) > 1)
    assert blended_receipt["weight_mode"] == "LINEAR_JOINT_BLEND_V2"
    assert blended_receipt["blended_vertex_count"] == multi_weighted and multi_weighted > 0
    assert all(abs(sum(group.weight for group in vertex.groups) - 1.0) < 1e-5
               for vertex in connected_obj.data.vertices)
    remove_created_rig(blended_receipt)
    remove_created_character(connected_character)
    assert bpy.data.objects.get("GAA Scout Base") is None and bpy.data.objects.get("GAA Scout Rig") is None
    assert bpy.data.objects.get("GAA Connected Rig Base") is None and bpy.data.objects.get("GAA Connected Rig") is None
    print("GameAssetAI character rig: 13 checks passed (v1 regions and v2 joint blends)")


if __name__ == "__main__":
    main()
