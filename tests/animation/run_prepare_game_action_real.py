"""Apply Action preparation to the accepted real Mixamo Walking checkpoint."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def load_api(repo):
    namespace = {"__name__": "gameassetai_prepare_game_action_real"}
    for path in (repo / "skills" / "blender-inspect-animation" / "scripts" /
                 "inspect_animation.py",
                 repo / "skills" / "blender-copy-action" / "scripts" / "action_copy.py",
                 repo / "skills" / "blender-prepare-game-action" / "scripts" /
                 "prepare_game_action.py"):
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace, namespace)
    return namespace


def evaluated_vertices(mesh):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    temporary = evaluated.to_mesh()
    try:
        return [vertex.co.copy() for vertex in temporary.vertices]
    finally:
        evaluated.to_mesh_clear()


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main():
    options = args()
    api = load_api(options.repo_root)
    run = options.run_directory
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("run_id") != run.name:
        raise ValueError("artifact run identity mismatch")
    scene = bpy.context.scene
    rig = scene.objects["GAA M2 Compact Rig"]
    mesh = scene.objects["GAA M2 Compact Mesh Object"]
    source = bpy.data.actions["GAA M3 Mixamo Walking"]
    original_action = rig.animation_data.action
    original_slot = rig.animation_data.action_slot.identifier
    original_source = api["action_content_snapshot"](source)
    original_refs = api["_action_references"](source)
    request = {
        "schema": api["SCHEMA"], "scene_name": scene.name, "armature_name": rig.name,
        "source_action": source.name, "source_slot_identifier": source.slots[0].identifier,
        "target_action": "GAA M3 Walking Clip 01-24", "root_bone_name": "pelvis",
        "frame": {"source_start": 1, "source_end": 24, "source_fps": 30,
                  "target_fps": 30, "output_start": 1},
        "sampling": {"mode": "EVALUATED_POSE", "key_cleanup": "EXACT_REDUNDANT"},
        "tolerances": {"translation": 1e-6, "rotation_radians": 1e-3, "scale": 1e-6},
        "policy": {"preserve_source": True, "bind_result": False,
                   "set_fake_user": True, "failure": "ROLL_BACK_NEW_DATA"},
    }
    receipt = api["apply_game_action_preparation"](
        api["preview_game_action_preparation"](request), True)
    if receipt["status"] != "created":
        raise RuntimeError(repr(receipt))
    prepared = bpy.data.actions[receipt["target_action"]]
    source_samples, prepared_samples = {}, {}
    for frame in (1, 12, 24):
        scene.frame_set(frame); bpy.context.view_layer.update()
        source_samples[frame] = evaluated_vertices(mesh)
    rig.animation_data.action = prepared
    rig.animation_data.action_slot = prepared.slots[0]
    for frame in (1, 12, 24):
        scene.frame_set(frame); bpy.context.view_layer.update()
        prepared_samples[frame] = evaluated_vertices(mesh)
    pose_mesh_error = max((left - right).length
                          for frame in source_samples
                          for left, right in zip(source_samples[frame], prepared_samples[frame]))
    movement = max((left - right).length for left, right in
                   zip(prepared_samples[1], prepared_samples[24]))
    rig.animation_data.action = original_action
    rig.animation_data.action_slot = next(slot for slot in original_action.slots
                                           if slot.identifier == original_slot)
    if pose_mesh_error > 1e-5 or movement < 0.01:
        raise AssertionError(f"prepared Mesh validation failed: {pose_mesh_error}, {movement}")
    if (api["action_content_snapshot"](source) != original_source
            or api["_action_references"](source) != original_refs):
        raise AssertionError("source Action changed")
    sys.path.insert(0, str(options.repo_root / "tests" / "blender_addon"))
    from run_humanoid_animation_import import render_frames
    rig.animation_data.action = prepared
    rig.animation_data.action_slot = prepared.slots[0]
    previews = render_frames(run / "previews", mesh, 1.58, frames=(1, 12, 24), views=("front", "side"))
    rig.animation_data.action = original_action
    rig.animation_data.action_slot = next(slot for slot in original_action.slots
                                           if slot.identifier == original_slot)
    blend = run / "m3.4-prepared-walking.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    report = {"schema": "gameassetai.game-action-preparation-validation.v1",
              "status": "pass", "source_kind": "accepted_real_adobe_mixamo_retarget",
              "request": request, "receipt": receipt,
              "source_action_preserved": True, "source_binding_preserved": True,
              "mesh_pose_max_error": pose_mesh_error,
              "prepared_mesh_movement_1_24": movement,
              "loop_claim": "inspection_only_not_approved",
              "root_motion_policy": "PRESERVE_INSPECT_ONLY",
              "previews": previews, "blend": str(blend),
              "blender_version": bpy.app.version_string}
    report_path = run / "validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("GAMEASSETAI_PREPARE_ACTION_REAL " + json.dumps(
        {"status": "pass", "blend": str(blend), "validation": str(report_path),
         "pose_mesh_error": pose_mesh_error, "movement": movement,
         "blend_sha256": digest(blend)}, sort_keys=True))


if __name__ == "__main__":
    main()
