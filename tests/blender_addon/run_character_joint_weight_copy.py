import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


def parse_args():
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True)
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(args)


def _geometry_hash(obj):
    value = {"vertices": [[float(x) for x in vertex.co] for vertex in obj.data.vertices],
             "polygons": [list(polygon.vertices) for polygon in obj.data.polygons]}
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                        separators=(",", ":")).encode()).hexdigest()


def _weight_hash(obj):
    value = {group.name: [[v.index, next((x.weight for x in v.groups if x.group == group.index), 0.0)]
                          for v in obj.data.vertices]
             for group in obj.vertex_groups}
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                        separators=(",", ":")).encode()).hexdigest()


def main():
    repo = Path(parse_args().repo_root).resolve()
    sys.path.insert(0, str(repo / "skills" / "blender-adjust-character-joint-weights-copy" / "scripts"))
    sys.path.insert(0, str(repo / "scripts"))
    sys.path.insert(0, str(repo / "tests" / "blender_addon"))
    from apply_character_joint_weight_copy import apply_character_joint_weight_copy
    from create_character_base import create_character, remove_created_character
    from preview_character_joint_weight_copy import preview_character_joint_weight_copy
    from rig_character_base import create_rig, remove_created_rig
    from run_character_base import request as base_request

    before = {"objects": sorted(item.name for item in bpy.data.objects),
              "meshes": sorted(item.name for item in bpy.data.meshes),
              "armatures": sorted(item.name for item in bpy.data.armatures),
              "materials": sorted(item.name for item in bpy.data.materials)}
    scene = bpy.context.scene
    character_request = base_request(scene.name)
    character_request.update({"schema": "gameassetai.character-base-request.v2",
                              "character_name": "GAA Weight Test",
                              "collection_name": "GAA Weight Test Character",
                              "object_name": "GAA Weight Test Base",
                              "mesh_name": "GAA Weight Test Base Mesh",
                              "topology_mode": "VOLUME_ISLANDS"})
    character = create_character(character_request, authorized=True)
    rig_request = {"schema": "gameassetai.character-rig-request.v2", "scene_name": scene.name,
                   "mesh_object_name": character["object_name"],
                   "armature_object_name": "GAA Weight Test Rig",
                   "armature_data_name": "GAA Weight Test Skeleton", "rig_name": "GAA Weight Test",
                   "policy": {"target": "OWNED_CHARACTER_BASE_ONLY", "existing_rig": "REFUSE",
                              "weights": "LINEAR_JOINT_BLEND_V2", "source_mesh": "PRESERVE_GEOMETRY",
                              "failure": "ROLL_BACK_RIG_CHANGES"}}
    rig = create_rig(rig_request, authorized=True)
    request = {
        "schema": "gameassetai.character-joint-weight-copy-request.v1",
        "scene_name": scene.name, "source_object_name": character["object_name"],
        "armature_object_name": rig["armature_object_name"],
        "output_object_name": "GAA Weight Test Refined", "output_mesh_name": "GAA Weight Test Refined Mesh",
        "adjustment": {"joint": "SHOULDER", "side": "BOTH", "transition_width_ratio": 0.035},
        "policy": {"target": "OWNED_CHARACTER_RIG_ONLY", "source_mutation": "PRESERVE",
                   "output": "NEW_OBJECT_AND_MESH", "geometry": "PRESERVE_EXACT",
                   "armature": "SHARE_EXISTING", "other_weights": "PRESERVE",
                   "normalization": "TARGET_PAIR_TO_EXISTING_SUM",
                   "authorization": "PREVIEW_THEN_EXPLICIT_APPLY"}}
    checks = []
    try:
        preview = preview_character_joint_weight_copy(request)
        assert preview["status"] == "candidate_for_review" and not preview["blockers"]
        assert preview["adjustment_preview"]["affected_vertex_count"] > 0; checks.append("preview_ready")
        expected = {"expected_request_sha256": preview["request_sha256"],
                    "expected_source_fingerprint": preview["source_fingerprint"],
                    "expected_setup_fingerprint": preview["setup_fingerprint"],
                    "expected_preview_fingerprint": preview["preview_fingerprint"]}
        refused = apply_character_joint_weight_copy(request, authorized=False, **expected)
        assert refused["status"] == "error" and bpy.data.objects.get(request["output_object_name"]) is None
        checks.append("authorization_required")
        source = bpy.data.objects[character["object_name"]]
        geometry_before, weights_before = _geometry_hash(source), _weight_hash(source)
        result = apply_character_joint_weight_copy(request, authorized=True, **expected)
        assert result["status"] == "created" and result["published"]; checks.append("copy_created")
        output = bpy.data.objects[request["output_object_name"]]
        assert output.data is not source.data and output.modifiers[0].object == bpy.data.objects[rig["armature_object_name"]]
        checks.append("independent_mesh_shared_armature")
        assert _geometry_hash(output) == geometry_before == _geometry_hash(source); checks.append("geometry_preserved")
        assert _weight_hash(source) == weights_before and _weight_hash(output) != weights_before
        checks.append("source_weights_preserved")
        assert result["metrics"]["affected_vertex_count"] > 0 and result["receipt_fingerprint"]
        checks.append("metrics_and_receipt")
        mesh = output.data; bpy.data.objects.remove(output, do_unlink=True); bpy.data.meshes.remove(mesh)
    finally:
        remove_created_rig(rig); remove_created_character(character)
    after = {"objects": sorted(item.name for item in bpy.data.objects),
             "meshes": sorted(item.name for item in bpy.data.meshes),
             "armatures": sorted(item.name for item in bpy.data.armatures),
             "materials": sorted(item.name for item in bpy.data.materials)}
    assert before == after; checks.append("exact_cleanup")
    print("GameAssetAI joint weight copy: %d checks passed" % len(checks))


if __name__ == "__main__":
    main()
