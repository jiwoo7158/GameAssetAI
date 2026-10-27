"""Run evaluated root-motion inspection on an owned Blender fixture."""
import math
import uuid


def run_evaluated_root_motion_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Evaluated root-motion fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_EvaluatedRootFixture_" + token)
    data = bpy.data.armatures.new("GAI_EvaluatedRootData_" + token)
    rig = bpy.data.objects.new("GAI_EvaluatedRootRig_" + token, data)
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
        bpy.ops.object.mode_set(mode="POSE")
        pose = rig.pose.bones["Root"]
        pose.location = (0, 0, 0); pose.keyframe_insert(data_path="location", frame=1)
        pose.location = (2, 0, 0); pose.keyframe_insert(data_path="location", frame=2)
        pose.location = (0, 0, 0); pose.keyframe_insert(data_path="location", frame=3)
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.rotation_euler.z = math.pi / 2
        rig.scale = (2, 2, 2)
        action = rig.animation_data.action
        action["gameassetai_test_owner"] = token
        slot = action.slots[0].identifier if len(action.slots) else None
        request = {
            "schema": EVALUATED_ROOT_MOTION_SCHEMA,
            "scene_name": scene.name,
            "armature_name": rig.name,
            "action_name": action.name,
            "bone_name": "Root",
            "slot_identifier": slot,
            "frame_start": 1,
            "frame_end": 3,
            "frame_step": 1,
            "tolerance": 1e-6,
        }
        frozen_action = action_content_snapshot(action)
        frozen_source = _evaluated_root_source_snapshot(rig)
        report = inspect_evaluated_root_motion(request)
        check("evaluated_ok", report["status"] == "ok" and report["sample_count"] == 3)
        check("loop_net_zero", not report["net_translation_evidence"] and
              report["spaces"]["WORLD"]["net_distance"] <= 1e-6)
        check("intermediate_path_detected", report["path_translation_evidence"] and
              report["spaces"]["LOCAL_BASIS"]["path_length"] > 0.0)
        local_path = report["spaces"]["LOCAL_BASIS"]["path_length"]
        world_path = report["spaces"]["WORLD"]["path_length"]
        check("world_scale_applied", abs(world_path - local_path * 2.0) <= 1e-5)
        check("three_spaces", set(report["spaces"]) == {"LOCAL_BASIS", "ARMATURE", "WORLD"})

        constraint = rig.pose.bones["Root"].constraints.new("COPY_LOCATION")
        constraint.target = rig
        check("constraint_refused", inspect_evaluated_root_motion(request)["status"] == "error")
        rig.pose.bones["Root"].constraints.remove(constraint)
        bad_step = dict(request); bad_step["frame_step"] = 2
        check("step_refused", inspect_evaluated_root_motion(bad_step)["status"] == "error")
        bad_slot = dict(request); bad_slot["slot_identifier"] = "Missing"
        check("slot_refused", inspect_evaluated_root_motion(bad_slot)["status"] == "error")
        rig.location = (1, 0, 0)
        rig.keyframe_insert(data_path="location", frame=1)
        check("object_motion_refused", inspect_evaluated_root_motion(request)["status"] == "error")
        object_curve = next(curve for curve in _curves(action) if curve.data_path == "location")
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
            raise RuntimeError("Evaluated root-motion fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Evaluated root-motion Action ownership/users changed")
            bpy.data.actions.remove(action)
        if data.users:
            raise RuntimeError("Evaluated root-motion Armature users changed")
        bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner") != token:
            raise RuntimeError("Evaluated root-motion Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
