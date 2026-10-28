"""Export the real M3.4 prepared Walking Action through the installed/source M4 Skill."""
import argparse
import json
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path, required=True)
    parser.add_argument("--skills-root", type=Path)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def load_api(repo, skills_root=None):
    skills = skills_root or (repo / "skills")
    namespace = {"__name__": "gameassetai_animated_fbx_export_test"}
    files = (skills / "blender-inspect-animation" / "scripts" / "inspect_animation.py",
             skills / "blender-copy-action" / "scripts" / "action_copy.py",
             skills / "blender-export-static-fbx" / "scripts" / "promote_export_artifact.py",
             skills / "blender-export-animated-fbx" / "scripts" /
             "validate_animated_fbx_request.py",
             skills / "blender-export-animated-fbx" / "scripts" / "export_animated_fbx.py")
    for path in files:
        exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace, namespace)
    return namespace


def request_for(api, run, target_name="compact-walking-01-24.fbx"):
    action = bpy.data.actions["GAA M3 Walking Clip 01-24"]
    return {
        "schema": api["ANIMATED_FBX_SCHEMA"], "scene_name": bpy.context.scene.name,
        "mesh_object_name": "GAA M2 Compact Mesh Object",
        "armature_object_name": "GAA M2 Compact Rig", "action_name": action.name,
        "action_slot_identifier": action.slots[0].identifier,
        "clip": {"frame_start": 1, "frame_end": 24, "fps": 30},
        "target": {"engine": "UNITY", "target_file": str(run / target_name)},
        "transform": {"axis_forward": "-Z", "axis_up": "Y", "global_scale": 1.0,
                      "apply_unit_scale": True, "apply_scale_options": "FBX_SCALE_UNITS",
                      "use_space_transform": True, "bake_space_transform": False},
        "geometry": {"use_mesh_modifiers": True},
        "materials": {"mode": "BLENDER_MATERIALS_NO_TEXTURE_COPY", "path_mode": "STRIP"},
        "rig": {"add_leaf_bones": False, "deform_bones_only": True,
                "armature_nodetype": "NULL",
                "validation_bones": ["pelvis", "head", "hand.L", "hand.R", "foot.L", "foot.R"]},
        "animation": {"bake_step": 1.0, "simplify_factor": 0.0,
                      "loop": False, "root_motion": "IN_PLACE"},
        "policy": {"preserve_source": True, "overwrite": False,
                   "failure": "ROLL_BACK_TEMPORARY_DATA"},
    }


def main():
    options = args()
    run = options.run_directory
    manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("run_id") != run.name:
        raise ValueError("artifact run identity mismatch")
    api = load_api(options.repo_root, options.skills_root)
    request = request_for(api, run)
    rig = bpy.data.objects[request["armature_object_name"]]
    source_action = bpy.data.actions[request["action_name"]]
    source_state = api["_source_fingerprint"](bpy.data.objects[request["mesh_object_name"]],
                                                rig, source_action)
    binding = (rig.animation_data.action.name,
               rig.animation_data.action_slot.identifier)
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    plan = api["preview_animated_fbx_export"](request)
    check("candidate", plan["status"] == "candidate_for_review"
          and plan["candidate"]["selected_action_bound_on_source"] is False)
    check("authorization_required", api["export_animated_fbx_staged"](plan)["status"] == "error")
    bad = json.loads(json.dumps(request)); bad["action_name"] = "Missing Action"
    check("bad_action_refused", api["preview_animated_fbx_export"](bad)["status"] == "error")
    collision = run / "collision.fbx"
    collision.write_bytes(b"owned collision")
    collision_request = request_for(api, run, collision.name)
    check("collision_refused",
          not api["validate_animated_fbx_request"](collision_request)["ready_for_blender_inspection"])
    collision.unlink()
    failure_request = request_for(api, run, "induced-publication-failure.fbx")
    failure_plan = api["preview_animated_fbx_export"](failure_request)
    original_promote = api["promote_export_artifact"]
    api["promote_export_artifact"] = lambda *_: (_ for _ in ()).throw(RuntimeError("induced publish failure"))
    failed = api["export_animated_fbx_staged"](failure_plan, True)
    api["promote_export_artifact"] = original_promote
    check("failed_stage_rolled_back", failed["status"] == "error" and failed["stage_cleaned"]
          and not Path(failure_request["target"]["target_file"]).exists()
          and not list(run.glob(".*.stage.fbx")))
    receipt = api["export_animated_fbx_staged"](
        api["preview_animated_fbx_export"](request), True)
    if receipt.get("status") != "created":
        print("GAMEASSETAI_ANIMATED_FBX_EXPORT_FAILURE " + json.dumps(receipt, sort_keys=True))
    check("created", receipt["status"] == "created" and Path(receipt["target_file"]).is_file())
    check("selected_action", receipt["action"] == "GAA M3 Walking Clip 01-24"
          and receipt["frame_start"] == 1 and receipt["frame_end"] == 24
          and receipt["fps"] == 30 and receipt["loop"] is False)
    check("source_preserved",
          api["_source_fingerprint"](bpy.data.objects[request["mesh_object_name"]], rig,
                                      source_action) == source_state
          and (rig.animation_data.action.name, rig.animation_data.action_slot.identifier) == binding)
    receipt["focused_checks"] = checks
    path = run / "export-receipt.json"
    path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print("GAMEASSETAI_ANIMATED_FBX_EXPORT " + json.dumps(
        {"status": "pass", "fbx": receipt["target_file"], "receipt": str(path),
         "sha256": receipt["sha256"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
