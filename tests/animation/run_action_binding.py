"""Exercise guarded empty-target Action binding and receipt rollback on owned data."""
import uuid


def run_action_binding_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action binding fixture requires Object mode")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_BindingFixture_" + token)
    armature = bpy.data.armatures.new("GAI_BindingData_" + token)
    rig = bpy.data.objects.new("GAI_BindingRig_" + token, armature)
    for item in (scene, armature, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = None
    checks = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)

    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bone = armature.edit_bones.new("Root")
        bone.head = (0, 0, 0)
        bone.tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="OBJECT")
        pose = rig.pose.bones["Root"]
        pose.rotation_mode = "QUATERNION"
        for frame, value in ((1, 0.0), (2, 0.2), (3, 0.4)):
            pose.rotation_quaternion = (1, 0, value, 0)
            pose.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        action = rig.animation_data.action
        action.name = "GAI_BindingAction_" + token
        action.use_fake_user = True
        action["gameassetai_test_owner"] = token
        rig.animation_data.action = None
        rig.animation_data_clear()
        source_sha = action_content_fingerprint(action)
        slot_id = action.slots[0].identifier
        request = {"schema": ACTION_BINDING_SCHEMA, "scene_name": scene.name,
                   "armature_name": rig.name, "action_name": action.name,
                   "action_slot_identifier": slot_id, "binding_policy": "EMPTY_ONLY",
                   "preserve_action": True, "set_fake_user": True}
        plan = preview_action_binding(request)
        check("candidate", plan["status"] == "candidate_for_review"
              and plan["candidate"]["animation_data_existed_before"] is False)
        check("authorization_refused", apply_action_binding(plan)["status"] == "error")
        _curves(action)[0].mute = True
        check("stale_refused", apply_action_binding(plan, True)["status"] == "error")
        _curves(action)[0].mute = False
        rig.animation_data_create().action = action
        check("occupied_target_refused", preview_action_binding(request)["status"] == "error")
        rig.animation_data.action = None
        rig.animation_data_clear()
        result = apply_action_binding(preview_action_binding(request), True)
        receipt = result.get("receipt")
        check("bound", result["status"] == "bound" and rig.animation_data.action == action)
        check("exact_reference", _action_references(action) == ([rig.name], []))
        check("content_preserved", action_content_fingerprint(action) == source_sha)
        check("rollback_authorization_refused",
              rollback_action_binding(receipt)["status"] == "error")
        tampered = dict(receipt)
        tampered["action_name"] = "Wrong"
        check("tampered_receipt_refused",
              rollback_action_binding(tampered, True)["status"] == "error")
        rolled = rollback_action_binding(receipt, True)
        check("rolled_back", rolled["status"] == "rolled_back"
              and rig.animation_data is None and _action_references(action) == ([], []))
        check("protected_action_retained", action.use_fake_user
              and action_content_fingerprint(action) == source_sha)
        rig.animation_data_create()
        retained_plan = preview_action_binding(request)
        check("existing_empty_animation_data_detected",
              retained_plan["candidate"]["animation_data_existed_before"] is True)
        retained_result = apply_action_binding(retained_plan, True)
        retained_rollback = rollback_action_binding(retained_result["receipt"], True)
        check("existing_empty_animation_data_restored",
              retained_rollback["status"] == "rolled_back"
              and rig.animation_data is not None and rig.animation_data.action is None)
        rig.animation_data_clear()
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        if rig.animation_data is not None:
            rig.animation_data_clear()
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            action.use_fake_user = False
            if action.users:
                raise RuntimeError("Fixture Action still referenced")
            bpy.data.actions.remove(action)
        if armature.users:
            raise RuntimeError("Fixture Armature still referenced")
        bpy.data.armatures.remove(armature)
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
