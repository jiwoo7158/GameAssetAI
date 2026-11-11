"""Stage one reviewed Mesh, Armature and Action copy for later sequence rendering."""
from __future__ import annotations

import hashlib
from pathlib import Path
import uuid


def stage_2d_action_sequence_source(request, preflight, candidate, framing, stage_file,
                                    *, authorize=False):
    report = {"schema": "gameassetai.2d-action-sequence-source-stage.v1",
              "status": "error", "errors": [], "source_stage_created": False,
              "png_published": False}
    stage = None
    write_started = False
    temp_scene = temp_mesh = temp_mesh_data = temp_rig = temp_rig_data = temp_action = None
    try:
        if authorize is not True:
            raise ValueError("Explicit Action-sequence staging authorization is required")
        fresh_preflight = validate_2d_action_sequence_request(request)
        if (not fresh_preflight["ready_for_blender_inspection"]
                or fresh_preflight["request_sha256"] != preflight.get("request_sha256")
                or fresh_preflight["frame_plan_sha256"] != preflight.get("frame_plan_sha256")):
            raise ValueError("Action-sequence preflight is stale or invalid")
        fresh_candidate = inspect_2d_action_sequence_candidate(request, fresh_preflight)
        if fresh_candidate["status"] != "candidate_for_review":
            raise ValueError("Current source is not an Action-sequence candidate")
        for key in ("request_sha256", "frame_plan_sha256", "source_fingerprint",
                    "action_fingerprint", "evaluation_fingerprint"):
            if fresh_candidate.get(key) != candidate.get(key):
                raise ValueError("Action-sequence candidate changed before staging")
        fresh_framing = preview_2d_action_sequence_framing(
            request, fresh_preflight, fresh_candidate)
        if (fresh_framing["status"] != "planned"
                or fresh_framing.get("plan_fingerprint") != framing.get("plan_fingerprint")):
            raise ValueError("Action-sequence framing changed before staging")

        directory = Path(request["output"]["target_directory"])
        stage = Path(stage_file)
        if (not stage.is_absolute() or stage.parent != directory
                or not stage.name.startswith(".gameassetai-2d-sequence-")
                or not stage.name.endswith(".stage.blend")):
            raise ValueError("Stage must be a hidden owned .stage.blend in the output directory")
        if stage.exists() or stage.is_symlink():
            raise ValueError("Action-sequence source stage already exists")
        if any(Path(frame["target_file"]).exists()
               or Path(frame["target_file"] + ".meta").exists()
               for frame in fresh_preflight["frames"]):
            raise ValueError("A planned PNG or sibling .meta appeared before staging")

        scene = bpy.data.scenes[fresh_candidate["scene"]]
        source_mesh = scene.objects[fresh_candidate["mesh_object"]]
        source_rig = scene.objects[fresh_candidate["armature"]]
        source_action = bpy.data.actions[fresh_candidate["action"]]
        token = uuid.uuid4().hex
        temp_scene = bpy.data.scenes.new("GAI_2DSequenceStage_" + token)
        temp_rig_data = source_rig.data.copy()
        temp_rig = source_rig.copy()
        temp_rig.data = temp_rig_data
        temp_rig.animation_data_clear()
        temp_mesh_data = source_mesh.data.copy()
        temp_mesh = source_mesh.copy()
        temp_mesh.data = temp_mesh_data
        temp_mesh.animation_data_clear()
        temp_action = source_action.copy()
        temp_scene.collection.objects.link(temp_rig)
        temp_scene.collection.objects.link(temp_mesh)
        if temp_mesh.parent == source_rig:
            temp_mesh.parent = temp_rig
        for modifier in temp_mesh.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = temp_rig
        temp_rig.animation_data_create()
        temp_rig.animation_data.action = temp_action
        effective_slot = fresh_candidate["slot_identifier"]
        if effective_slot is not None:
            temp_rig.animation_data.action_slot = next(
                slot for slot in temp_action.slots if slot.identifier == effective_slot)
        temp_scene.frame_start = request["animation"]["frame_start"]
        temp_scene.frame_end = request["animation"]["frame_end"]
        playback_fps = float(request["animation"]["playback_fps"])
        fps_numerator = max(1, round(playback_fps))
        temp_scene.render.fps = fps_numerator
        temp_scene.render.fps_base = fps_numerator / playback_fps
        write_started = True
        bpy.data.libraries.write(str(stage), {temp_scene}, path_remap="ABSOLUTE",
                                 fake_user=False, compress=False)
        data = stage.read_bytes()
        if not data.startswith(b"BLENDER") or len(data) < 64:
            raise RuntimeError("Action-sequence blend stage failed structural verification")
        report.update(status="created", source_stage_created=True,
                      request_sha256=fresh_candidate["request_sha256"],
                      frame_plan_sha256=fresh_candidate["frame_plan_sha256"],
                      source_fingerprint=fresh_candidate["source_fingerprint"],
                      action_fingerprint=fresh_candidate["action_fingerprint"],
                      evaluation_fingerprint=fresh_candidate["evaluation_fingerprint"],
                      plan_fingerprint=fresh_framing["plan_fingerprint"],
                      stage_file=str(stage), stage_size=len(data),
                      stage_sha256=hashlib.sha256(data).hexdigest())
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
        report["errors"].append(str(exc))
        if write_started and stage is not None and stage.exists():
            try:
                stage.unlink()
            except OSError as cleanup:
                report["errors"].append("Action-sequence stage cleanup failed: " + str(cleanup))
    finally:
        if temp_mesh is not None and bpy.data.objects.get(temp_mesh.name) == temp_mesh:
            bpy.data.objects.remove(temp_mesh, do_unlink=True)
        if temp_mesh_data is not None and temp_mesh_data.users == 0:
            bpy.data.meshes.remove(temp_mesh_data)
        if temp_rig is not None and bpy.data.objects.get(temp_rig.name) == temp_rig:
            temp_rig.animation_data_clear()
            bpy.data.objects.remove(temp_rig, do_unlink=True)
        if temp_rig_data is not None and temp_rig_data.users == 0:
            bpy.data.armatures.remove(temp_rig_data)
        if temp_action is not None and temp_action.users == 0:
            bpy.data.actions.remove(temp_action)
        if temp_scene is not None and bpy.data.scenes.get(temp_scene.name) == temp_scene:
            bpy.data.scenes.remove(temp_scene)
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
