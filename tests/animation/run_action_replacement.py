"""Exercise exact current-Action replacement and receipt rollback on owned data."""
import uuid


def run_action_replacement_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action replacement fixture requires Object mode")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_ReplaceFixture_" + token)
    armature = bpy.data.armatures.new("GAI_ReplaceData_" + token)
    rig = bpy.data.objects.new("GAI_ReplaceRig_" + token, armature)
    for item in (scene, armature, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    previous = replacement = None
    checks = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)

    def create_action(name, values):
        rig.animation_data_clear()
        pose = rig.pose.bones["Root"]
        for frame, value in enumerate(values, 1):
            pose.rotation_quaternion = (1, 0, value, 0)
            pose.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        action = rig.animation_data.action
        action.name = name
        action.use_fake_user = True
        action["gameassetai_test_owner"] = token
        rig.animation_data.action = None
        return action

    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bone = armature.edit_bones.new("Root")
        bone.head = (0, 0, 0)
        bone.tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.pose.bones["Root"].rotation_mode = "QUATERNION"
        previous = create_action("GAI_Previous_" + token, (0.0, 0.1, 0.2))
        replacement = create_action("GAI_Replacement_" + token, (0.3, 0.4, 0.5))
        rig.animation_data.action = previous
        rig.animation_data.action_slot = previous.slots[0]
        previous_sha = action_content_fingerprint(previous)
        replacement_sha = action_content_fingerprint(replacement)
        request = {"schema": ACTION_REPLACEMENT_SCHEMA, "scene_name": scene.name,
                   "armature_name": rig.name, "current_action": previous.name,
                   "current_slot_identifier": previous.slots[0].identifier,
                   "replacement_action": replacement.name,
                   "replacement_slot_identifier": replacement.slots[0].identifier,
                   "replacement_policy": "CURRENT_ONLY", "preserve_both_actions": True,
                   "set_fake_users": True}
        plan = preview_action_replacement(request)
        check("candidate", plan["status"] == "candidate_for_review")
        check("authorization_refused", apply_action_replacement(plan)["status"] == "error")
        track = rig.animation_data.nla_tracks.new()
        track.name = "GAI_Refusal"
        track.strips.new("GAI_Refusal", 1, previous)
        check("nla_refused", preview_action_replacement(request)["status"] == "error")
        rig.animation_data.nla_tracks.remove(track)
        rig.driver_add("location", 0)
        check("driver_refused", preview_action_replacement(request)["status"] == "error")
        rig.driver_remove("location", 0)
        _curves(replacement)[0].mute = True
        check("stale_refused", apply_action_replacement(plan, True)["status"] == "error")
        _curves(replacement)[0].mute = False
        rig.animation_data.action = replacement
        rig.animation_data.action_slot = replacement.slots[0]
        check("wrong_current_refused", preview_action_replacement(request)["status"] == "error")
        rig.animation_data.action = previous
        rig.animation_data.action_slot = previous.slots[0]
        result = apply_action_replacement(preview_action_replacement(request), True)
        receipt = result.get("receipt")
        check("replaced", result["status"] == "replaced"
              and rig.animation_data.action == replacement)
        check("references_swapped", _action_references(previous) == ([], [])
              and _action_references(replacement) == ([rig.name], []))
        check("contents_preserved", action_content_fingerprint(previous) == previous_sha
              and action_content_fingerprint(replacement) == replacement_sha)
        check("rollback_authorization_refused",
              rollback_action_replacement(receipt)["status"] == "error")
        tampered = dict(receipt)
        tampered["previous_action"] = "Wrong"
        check("tampered_receipt_refused",
              rollback_action_replacement(tampered, True)["status"] == "error")
        _curves(previous)[0].mute = True
        check("changed_previous_refused",
              rollback_action_replacement(receipt, True)["status"] == "error")
        _curves(previous)[0].mute = False
        rolled = rollback_action_replacement(receipt, True)
        check("rolled_back", rolled["status"] == "rolled_back"
              and rig.animation_data.action == previous)
        check("references_restored", _action_references(previous) == ([rig.name], [])
              and _action_references(replacement) == ([], []))
        check("protected_actions_retained", previous.use_fake_user and replacement.use_fake_user
              and action_content_fingerprint(previous) == previous_sha
              and action_content_fingerprint(replacement) == replacement_sha)
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        if rig.animation_data is not None:
            rig.animation_data_clear()
        bpy.data.objects.remove(rig, do_unlink=True)
        for action in (previous, replacement):
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
