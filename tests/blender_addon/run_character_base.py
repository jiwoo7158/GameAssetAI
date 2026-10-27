import argparse
from pathlib import Path
import sys

import bmesh
import bpy


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


def request(scene_name):
    return {
        "schema": "gameassetai.character-base-request.v1",
        "scene_name": scene_name,
        "character_name": "GAA Scout",
        "collection_name": "GAA Scout Character",
        "object_name": "GAA Scout Base",
        "mesh_name": "GAA Scout Base Mesh",
        "pose": "A_POSE",
        "proportions": {
            "height": 1.8,
            "shoulder_width_ratio": 0.29,
            "hip_width_ratio": 0.20,
            "body_depth_ratio": 0.13,
            "limb_thickness_ratio": 0.045,
            "head_height_ratio": 0.16,
        },
        "colors": {
            "skin": [0.58, 0.27, 0.16, 1.0],
            "primary": [0.035, 0.12, 0.19, 1.0],
            "secondary": [0.08, 0.38, 0.34, 1.0],
            "boots": [0.045, 0.025, 0.02, 1.0],
        },
        "policy": {
            "existing_names": "REFUSE",
            "source_scene": "PRESERVE",
            "creation": "NEW_SINGLE_MESH_CHARACTER",
            "failure": "ROLL_BACK_OWNED_DATA",
            "rigging": "NOT_INCLUDED",
        },
    }


def main():
    repo_root = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(repo_root / "scripts"))
    from create_character_base import create_character, remove_created_character

    scene = bpy.context.scene
    before = (sorted(bpy.data.objects.keys()), sorted(bpy.data.meshes.keys()), sorted(bpy.data.materials.keys()), sorted(bpy.data.collections.keys()))
    payload = request(scene.name)
    try:
        create_character(payload, authorized=False)
        raise AssertionError("unauthorized creation must fail")
    except ValueError as exc:
        assert "authorized=true" in str(exc)

    receipt = create_character(payload, authorized=True)
    obj = bpy.data.objects[receipt["object_name"]]
    assert receipt["status"] == "created" and receipt["rigged"] is False
    assert obj.type == "MESH" and len(obj.data.materials) == 4
    assert receipt["vertices"] > 150 and receipt["polygons"] > 150
    bounds = receipt["world_bounds"]
    assert bounds["min"][0] < -0.45 and bounds["max"][0] > 0.45
    assert -0.01 <= bounds["min"][2] <= 0.01 and 1.7 < bounds["max"][2] <= 1.9
    assert len(receipt["request_sha256"]) == 64 and len(receipt["receipt_sha256"]) == 64

    remove_created_character(receipt)
    connected = request(scene.name)
    connected.update({"schema":"gameassetai.character-base-request.v2",
                      "character_name":"GAA Connected Scout",
                      "collection_name":"GAA Connected Character",
                      "object_name":"GAA Connected Base",
                      "mesh_name":"GAA Connected Base Mesh",
                      "topology_mode":"VOXEL_CONNECTED"})
    try:
        create_character(connected, authorized=True)
        raise AssertionError("suspended VOXEL_CONNECTED mode must be refused")
    except ValueError as exc:
        assert "VOXEL_CONNECTED is suspended" in str(exc)

    boolean_connected = request(scene.name)
    boolean_connected.update({
        "schema": "gameassetai.character-base-request.v3",
        "character_name": "GAA Boolean Scout",
        "collection_name": "GAA Boolean Character",
        "object_name": "GAA Boolean Base",
        "mesh_name": "GAA Boolean Base Mesh",
        "topology_mode": "BOOLEAN_CONNECTED",
    })
    boolean_receipt = create_character(boolean_connected, authorized=True)
    assert boolean_receipt["mesh_name"] == boolean_connected["mesh_name"]
    assert boolean_receipt["components_before"] > 1
    assert boolean_receipt["components_after"] == 1
    checks = boolean_receipt["semantic_checks"]
    assert checks["foot_centerline_clearance"] > 0.009
    assert checks["lower_leg_centerline_clearance"] > 0.009
    assert checks["cross_side_edges_below_knee"] == 0
    assert boolean_receipt["non_manifold_edges"] == 0
    assert boolean_receipt["quadriflow_micro_edges_before"] > 0
    assert boolean_receipt["quadriflow_micro_edges_after"] == 0
    boolean_mesh = bpy.data.meshes[boolean_receipt["mesh_name"]]
    assert len(boolean_mesh.materials) == 4
    topology = bmesh.new()
    topology.from_mesh(boolean_mesh)
    assert all(len(edge.link_faces) == 2 for edge in topology.edges)
    topology.free()
    remove_created_character(boolean_receipt)
    after = (sorted(bpy.data.objects.keys()), sorted(bpy.data.meshes.keys()), sorted(bpy.data.materials.keys()), sorted(bpy.data.collections.keys()))
    assert after == before, (before, after)
    print("GameAssetAI character base: 22 checks passed (volume, voxel refusal, semantic Boolean connection, micro-edge cleanup)")


if __name__ == "__main__":
    main()
