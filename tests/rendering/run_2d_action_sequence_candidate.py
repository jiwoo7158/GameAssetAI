"""Synthetic Blender regression for read-only Action PNG-sequence candidate evaluation."""
from pathlib import Path
import uuid


def run_2d_action_sequence_candidate_tests(artifact_root):
    if bpy.context.window is None or bpy.context.mode != "OBJECT":
        raise RuntimeError("Action sequence candidate fixture requires an Object-mode window")
    root = Path(artifact_root).resolve(strict=True)
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    original_frame = (original_scene.frame_current, original_scene.frame_subframe)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes,
                   bpy.data.armatures, bpy.data.actions)
    before_names = [[item.name for item in collection] for collection in collections]
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.data.scenes.new("GAI_2DSequence_" + token)
    rig_data = bpy.data.armatures.new("GAI_2DSequenceRigData_" + token)
    rig = bpy.data.objects.new("GAI_2DSequenceRig_" + token, rig_data)
    mesh_data = bpy.data.meshes.new("GAI_2DSequenceMesh_" + token)
    mesh_data.from_pydata([(-0.5, 0, 0), (0.5, 0, 0),
                           (0.5, 0, 1), (-0.5, 0, 1)], [], [(0, 1, 2, 3)])
    mesh_obj = bpy.data.objects.new("GAI_2DSequenceObject_" + token, mesh_data)
    scene.collection.objects.link(rig)
    scene.collection.objects.link(mesh_obj)
    action = None
    stage = root / (".gameassetai-2d-sequence-" + token + ".stage.blend")
    job = root / (".gameassetai-2d-sequence-" + token + ".job.json")
    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bone = rig_data.edit_bones.new("Root")
        bone.head, bone.tail = (0, 0, 0), (0, 0, 1)
        bpy.ops.object.mode_set(mode="POSE")
        pose = rig.pose.bones["Root"]
        for frame, x in ((1, -1.0), (2, 0.0), (3, 1.0)):
            pose.location = (x, 0, 0)
            pose.keyframe_insert(data_path="location", frame=frame)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action
        group = mesh_obj.vertex_groups.new(name="Root")
        group.add(range(4), 1.0, "REPLACE")
        modifier = mesh_obj.modifiers.new("Armature", "ARMATURE")
        modifier.object = rig
        slot = action.slots[0].identifier if len(action.slots) else None
        target_dir = str(root)
        request = {
            "schema": SCHEMA,
            "static_template": {
                "schema": STATIC_SCHEMA, "scene_name": scene.name,
                "object_name": mesh_obj.name,
                "profile": {"name": None, "reference_sha256": None,
                            "profile_sha256": None},
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
                "style": {"mode": "PIXEL", "resolution": [32, 32],
                          "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                          "palette_mode": "NONE", "palette": [], "max_colors": None,
                          "outline_mode": "NONE", "outline_color": None,
                          "outline_width": 0, "shading_mode": "NONE",
                          "value_steps": None}},
            "animation": {"armature_name": rig.name, "action_name": action.name,
                          "slot_identifier": slot, "frame_start": 1, "frame_end": 3,
                          "frame_step": 1, "playback_fps": 12},
            "framing": {"bounds_policy": "ACTION_RANGE",
                        "anchor_policy": "OBJECT_ORIGIN"},
            "output": {"target_directory": target_dir,
                       "filename_prefix": "sequence-candidate-" + token + "-",
                       "index_start": 0, "index_padding": 4, "overwrite": False},
        }
        preflight = validate_2d_action_sequence_request(request)
        check("offline_preflight", preflight["ready_for_blender_inspection"]
              and preflight["frame_count"] == 3)
        scene.frame_set(2)
        before_source = (_source_payload(mesh_obj, rig), _action_payload(action))
        report = inspect_2d_action_sequence_candidate(request, preflight)
        check("candidate_ready", report["status"] == "candidate_for_review")
        check("fingerprints_bound", all(len(report[key]) == 64 for key in
              ("request_sha256", "frame_plan_sha256", "source_fingerprint",
               "action_fingerprint", "evaluation_fingerprint")))
        frame_bounds = report["evaluation"]["frames"]
        check("three_evaluated_frames", len(frame_bounds) == 3)
        check("deformation_changes_bounds",
              frame_bounds[0]["bounds"] != frame_bounds[1]["bounds"]
              and frame_bounds[1]["bounds"] != frame_bounds[2]["bounds"])
        union = report["evaluation"]["union_bounds"]
        check("union_bounds_cover_motion", union["minimum"][0] < -1.4
              and union["maximum"][0] > 1.4)
        framing = preview_2d_action_sequence_framing(request, preflight, report)
        check("stable_framing_planned", framing["status"] == "planned"
              and len(framing["plan_fingerprint"]) == 64
              and framing["plan"]["orthographic_scale"] > 0)
        check("object_origin_anchor_recorded",
              len(framing["plan"]["anchor_pixel_from_bottom_left"]) == 2
              and all(__import__("math").isfinite(value)
                      for value in framing["plan"]["anchor_pixel_from_bottom_left"]))
        check("framing_repeatable", preview_2d_action_sequence_framing(
              request, preflight, report)["plan_fingerprint"] == framing["plan_fingerprint"])
        check("source_preserved", before_source ==
              (_source_payload(mesh_obj, rig), _action_payload(action))
              and scene.frame_current == 2)
        group.add([0], 0.5, "REPLACE")
        changed_weight = inspect_2d_action_sequence_candidate(request, preflight)
        check("weight_change_changes_source_fingerprint",
              changed_weight["status"] == "candidate_for_review"
              and changed_weight["source_fingerprint"] != report["source_fingerprint"])
        group.add([0], 1.0, "REPLACE")
        curve = _curves_with_slots(action)[0][0]
        original_interpolation = curve.keyframe_points[0].interpolation
        curve.keyframe_points[0].interpolation = "LINEAR"
        changed_action = inspect_2d_action_sequence_candidate(request, preflight)
        check("interpolation_change_changes_action_fingerprint",
              changed_action["status"] == "candidate_for_review"
              and changed_action["action_fingerprint"] != report["action_fingerprint"])
        curve.keyframe_points[0].interpolation = original_interpolation
        stale = dict(preflight); stale["request_sha256"] = "0" * 64
        check("stale_preflight_refused",
              inspect_2d_action_sequence_candidate(request, stale)["status"] == "error")
        stale_candidate = dict(report); stale_candidate["evaluation_fingerprint"] = "0" * 64
        check("stale_candidate_framing_refused", preview_2d_action_sequence_framing(
              request, preflight, stale_candidate)["status"] == "error")
        bad_slot_request = {**request, "animation": {**request["animation"],
                                                      "slot_identifier": "Missing"}}
        bad_slot_preflight = validate_2d_action_sequence_request(bad_slot_request)
        check("missing_slot_blocked", inspect_2d_action_sequence_candidate(
              bad_slot_request, bad_slot_preflight)["status"] == "blocked")
        mesh_obj.modifiers.remove(modifier)
        check("missing_modifier_blocked", inspect_2d_action_sequence_candidate(
              request, preflight)["status"] == "blocked")
        modifier = mesh_obj.modifiers.new("Armature", "ARMATURE")
        modifier.object = rig
        check("no_output_created", not any(Path(frame["target_file"]).exists()
                                           for frame in preflight["frames"]))
        refused_stage = stage_2d_action_sequence_source(
            request, preflight, report, framing, str(stage), authorize=False)
        check("stage_authorization_required", refused_stage["status"] == "error"
              and not stage.exists())
        staged = stage_2d_action_sequence_source(
            request, preflight, report, framing, str(stage), authorize=True)
        check("independent_stage_created", staged["status"] == "created"
              and stage.is_file() and stage.read_bytes().startswith(b"BLENDER"))
        check("stage_fingerprints_bound", all(staged[key] == report[key] for key in
              ("request_sha256", "frame_plan_sha256", "source_fingerprint",
               "action_fingerprint", "evaluation_fingerprint")))
        check("stage_collision_refused", stage_2d_action_sequence_source(
              request, preflight, report, framing, str(stage), authorize=True)["status"] == "error")
        refused_job = build_2d_action_sequence_job(
            request, preflight, report, framing, staged, str(job), authorize=False)
        check("job_authorization_required", refused_job["status"] == "error"
              and not job.exists())
        prepared = build_2d_action_sequence_job(
            request, preflight, report, framing, staged, str(job), authorize=True)
        check("hash_bound_job_created", prepared["status"] == "created"
              and prepared["frame_count"] == 3 and job.is_file())
        payload = __import__("json").loads(job.read_text(encoding="utf-8"))
        check("job_contains_exact_frame_plan", payload["frames"] == preflight["frames"]
              and payload["source_stage"]["sha256"] == staged["stage_sha256"])
        check("job_collision_refused", build_2d_action_sequence_job(
              request, preflight, report, framing, staged, str(job),
              authorize=True)["status"] == "error")
    finally:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        original_scene.frame_set(original_frame[0], subframe=original_frame[1])
        rig.animation_data_clear()
        bpy.data.objects.remove(mesh_obj, do_unlink=True)
        bpy.data.meshes.remove(mesh_data)
        bpy.data.objects.remove(rig, do_unlink=True)
        bpy.data.armatures.remove(rig_data)
        if action is not None and action.users == 0:
            bpy.data.actions.remove(action)
        bpy.data.scenes.remove(scene)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
    check("context_preserved", window.scene == original_scene
          and original_scene.frame_current == original_frame[0]
          and abs(original_scene.frame_subframe - original_frame[1]) <= 1e-9)
    check("exact_id_teardown", before_names ==
          [[item.name for item in collection] for collection in collections])
    check("exact_file_teardown", not stage.exists() and not job.exists())
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "blender_version": bpy.app.version_string}
