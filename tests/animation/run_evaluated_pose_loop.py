"""Run evaluated pose-loop endpoint inspection on an owned Blender fixture."""
import math
import uuid


def run_evaluated_pose_loop_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Evaluated pose-loop fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_EvaluatedPoseLoopFixture_" + token)
    data = bpy.data.armatures.new("GAI_EvaluatedPoseLoopData_" + token)
    rig = bpy.data.objects.new("GAI_EvaluatedPoseLoopRig_" + token, data)
    for item in (scene, data, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = None
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        root = data.edit_bones.new("Root")
        root.head = (0, 0, 0); root.tail = (0, 0, 1)
        child = data.edit_bones.new("Child")
        child.head = (0, 0, 1); child.tail = (0, 0, 2); child.parent = root
        bpy.ops.object.mode_set(mode="POSE")
        root_pose = rig.pose.bones["Root"]
        child_pose = rig.pose.bones["Child"]
        child_pose.rotation_mode = "QUATERNION"
        root_pose.location = (0, 0, 0); root_pose.keyframe_insert(data_path="location", frame=1)
        root_pose.location = (1, 0, 0); root_pose.keyframe_insert(data_path="location", frame=2)
        root_pose.location = (-1, 0, 0); root_pose.keyframe_insert(data_path="location", frame=3)
        root_pose.location = (0, 0, 0); root_pose.keyframe_insert(data_path="location", frame=4)
        child_pose.rotation_quaternion = (1, 0, 0, 0)
        child_pose.keyframe_insert(data_path="rotation_quaternion", frame=1)
        child_pose.rotation_quaternion = (math.cos(0.25), 0, 0, math.sin(0.25))
        child_pose.keyframe_insert(data_path="rotation_quaternion", frame=2)
        child_pose.rotation_quaternion = (math.cos(0.25), 0, 0, math.sin(0.25))
        child_pose.keyframe_insert(data_path="rotation_quaternion", frame=3)
        child_pose.rotation_quaternion = (1, 0, 0, 0)
        child_pose.keyframe_insert(data_path="rotation_quaternion", frame=4)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action
        action["gameassetai_test_owner"] = token
        scene.frame_set(scene.frame_current, subframe=scene.frame_subframe)
        slot = action.slots[0].identifier if len(action.slots) else None
        request = {
            "schema": EVALUATED_POSE_LOOP_SCHEMA,
            "scene_name": scene.name, "armature_name": rig.name,
            "action_name": action.name, "bone_names": ["Root", "Child"],
            "slot_identifier": slot, "frame_start": 1, "frame_end": 4,
            "translation_tolerance": 1e-6,
            "rotation_tolerance_radians": 1e-6, "scale_tolerance": 1e-6,
            "velocity_sample_frames": 1, "translation_velocity_tolerance": 1e-6,
            "angular_velocity_tolerance_radians_per_frame": 1e-6,
            "scale_velocity_tolerance_per_frame": 1e-6,
        }
        frozen_action = action_content_snapshot(action)
        frozen_source = _evaluated_root_source_snapshot(rig)
        report = inspect_evaluated_pose_loop(request)
        if report["status"] != "ok":
            raise AssertionError("evaluated_ok: " + repr(report))
        checks.append("evaluated_ok")
        check("root_endpoint_matches", report["bones"]["Root"]["endpoint_matches"])
        check("child_endpoint_matches", report["bones"]["Child"]["endpoint_matches"])
        check("aggregate_endpoints_match", report["all_endpoints_match"])
        check("root_tangent_matches", report["bones"]["Root"]["velocity"]["tangent_matches"])
        check("child_angular_tangent_mismatch",
              not report["bones"]["Child"]["velocity"]["rotation_matches"] and
              report["bones"]["Child"]["velocity"]["angular_delta_radians_per_frame"] > 0.9)
        check("aggregate_tangent_mismatch", not report["all_tangents_match"])
        check("animated_flags", all(item["animated"] for item in report["bones"].values()))

        missing = dict(request); missing["bone_names"] = ["Root", "Missing"]
        check("missing_bone_refused", inspect_evaluated_pose_loop(missing)["status"] == "error")
        omitted = dict(request); omitted["bone_names"] = ["Root"]
        check("omitted_animated_bone_refused", inspect_evaluated_pose_loop(omitted)["status"] == "error")
        bad_slot = dict(request); bad_slot["slot_identifier"] = "Missing"
        check("slot_refused", inspect_evaluated_pose_loop(bad_slot)["status"] == "error")
        bad_sample = dict(request); bad_sample["velocity_sample_frames"] = 2
        check("crossing_velocity_sample_refused",
              inspect_evaluated_pose_loop(bad_sample)["status"] == "error")
        constraint = child_pose.constraints.new("COPY_ROTATION"); constraint.target = rig
        check("constraint_refused", inspect_evaluated_pose_loop(request)["status"] == "error")
        child_pose.constraints.remove(constraint)
        rig.location = (1, 0, 0); rig.keyframe_insert(data_path="location", frame=1)
        check("object_motion_refused", inspect_evaluated_pose_loop(request)["status"] == "error")
        for curve in [curve for curve in _curves(action) if curve.data_path == "location"]:
            action.layers[0].strips[0].channelbags[0].fcurves.remove(curve)
        rig.location = (0, 0, 0)
        check("source_preserved", action_content_snapshot(action) == frozen_action and
              _evaluated_root_source_snapshot(rig) == frozen_source)
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        if rig.get("gameassetai_test_owner") != token or data.get("gameassetai_test_owner") != token:
            raise RuntimeError("Evaluated pose-loop fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Evaluated pose-loop Action ownership/users changed")
            bpy.data.actions.remove(action)
        if data.users:
            raise RuntimeError("Evaluated pose-loop Armature users changed")
        bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner") != token:
            raise RuntimeError("Evaluated pose-loop Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
