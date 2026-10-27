"""Run guarded aligned Action-path retarget tests on owned Blender data."""
import json
import uuid


def run_aligned_retarget_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Aligned retarget fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_AlignedRetarget_" + token)
    scene["gameassetai_test_owner"] = token
    owned = []
    checks = []
    action = created = None

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def make_rig(label, prefix):
        data = bpy.data.armatures.new("GAI_" + label + "Data_" + token)
        rig = bpy.data.objects.new("GAI_" + label + "Rig_" + token, data)
        for item in (data, rig):
            item["gameassetai_test_owner"] = token
        scene.collection.objects.link(rig)
        owned.append((rig, data))
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bones = {}
        for index, role in enumerate(REQUIRED_ROLES):
            bone = data.edit_bones.new(prefix + role)
            bone.head = (0, 0, index * 0.2)
            bone.tail = (0, 0, index * 0.2 + 0.1)
            bones[role] = bone
            parent = PARENTS.get(role)
            if parent:
                bone.parent = bones[parent]
        bpy.ops.object.mode_set(mode="OBJECT")
        rig.select_set(False)
        return rig, {role: prefix + role for role in REQUIRED_ROLES}

    try:
        source, source_map = make_rig("Source", "S_")
        target, target_map = make_rig("Target", "T_")
        scene.view_layers[0].objects.active = source
        source.select_set(True)
        source.pose.bones[source_map["hips"]].location = (0, 0, 0)
        source.pose.bones[source_map["hips"]].keyframe_insert(data_path="location", frame=1)
        source.pose.bones[source_map["hips"]].location = (1, 2, 3)
        source.pose.bones[source_map["hips"]].keyframe_insert(data_path="location", frame=10)
        source.pose.bones[source_map["upper_arm_l"]].rotation_mode = "QUATERNION"
        target.pose.bones[target_map["upper_arm_l"]].rotation_mode = "QUATERNION"
        source.pose.bones[source_map["upper_arm_l"]].rotation_quaternion = (1, 0, 0, 0)
        source.pose.bones[source_map["upper_arm_l"]].keyframe_insert(
            data_path="rotation_quaternion", frame=1)
        source.pose.bones[source_map["upper_arm_l"]].rotation_quaternion = (0.9238795, 0, 0.3826834, 0)
        source.pose.bones[source_map["upper_arm_l"]].keyframe_insert(
            data_path="rotation_quaternion", frame=10)
        action = source.animation_data.action
        action["gameassetai_test_owner"] = token
        slot = action.slots[0].identifier if len(action.slots) else None
        target_name = "GAI_AlignedResult_" + token
        request = {
            "schema": ALIGNED_RETARGET_SCHEMA,
            "scene_name": scene.name,
            "source_armature": source.name,
            "target_armature": target.name,
            "source_action": action.name,
            "target_action": target_name,
            "source_mapping": source_map,
            "target_mapping": target_map,
            "source_slot_identifier": slot,
            "rest_tolerance": 1e-5,
            "preserve_source": True,
            "bind_result": False,
            "set_fake_user": True,
        }
        source_frozen = action_content_snapshot(action)
        target_frozen = _aligned_pose_snapshot(target, target_map)
        preview = preview_aligned_retarget(request)
        check("preview", preview["status"] == "candidate_for_review" and
              preview["candidate"]["object_transform_max_delta"] == 0.0)
        check("authorization_refused", apply_aligned_retarget(preview)["status"] == "error"
              and bpy.data.actions.get(target_name) is None)
        first_curve = _curves(action)[0]
        old_mute = first_curve.mute
        first_curve.mute = not old_mute
        check("stale_refused", apply_aligned_retarget(preview, True)["status"] == "error"
              and bpy.data.actions.get(target_name) is None)
        first_curve.mute = old_mute
        target.location.x = 0.25
        check("misaligned_object_refused",
              preview_aligned_retarget(request)["status"] == "error")
        target.location.x = 0.0
        target.pose.bones[target_map["upper_arm_l"]].rotation_mode = "XYZ"
        check("rotation_mode_refused",
              preview_aligned_retarget(request)["status"] == "error")
        target.pose.bones[target_map["upper_arm_l"]].rotation_mode = "QUATERNION"
        constraint = target.pose.bones[target_map["hips"]].constraints.new("COPY_ROTATION")
        constraint.target = source
        check("constraint_refused", preview_aligned_retarget(request)["status"] == "error")
        target.pose.bones[target_map["hips"]].constraints.remove(constraint)
        source.select_set(False)
        target.select_set(True)
        scene.view_layers[0].objects.active = target
        bpy.ops.object.mode_set(mode="EDIT")
        changed_bone = target.data.edit_bones[target_map["head"]]
        changed_bone.head.x += 0.1
        changed_bone.tail.x += 0.1
        bpy.ops.object.mode_set(mode="OBJECT")
        check("rest_mismatch_refused", preview_aligned_retarget(request)["status"] == "error")
        bpy.ops.object.mode_set(mode="EDIT")
        changed_bone = target.data.edit_bones[target_map["head"]]
        changed_bone.head.x -= 0.1
        changed_bone.tail.x -= 0.1
        bpy.ops.object.mode_set(mode="OBJECT")
        target.select_set(False)
        source.select_set(True)
        scene.view_layers[0].objects.active = source
        collision = bpy.data.actions.new(target_name)
        check("collision_refused", preview_aligned_retarget(request)["status"] == "error")
        bpy.data.actions.remove(collision)
        preview = preview_aligned_retarget(request)
        check("restored_preview", preview["status"] == "candidate_for_review")
        target_frozen = _aligned_pose_snapshot(target, target_map)
        applied = apply_aligned_retarget(preview, True)
        created = bpy.data.actions.get(target_name)
        if applied["status"] != "created":
            raise AssertionError("created: " + repr(applied))
        paths = sorted(curve.data_path for curve in _curves(created))
        check("created_unbound", created is not None and created != action and
              created.use_fake_user and _action_references(created) == ([], []))
        check("paths_remapped", all('pose.bones["T_' in path for path in paths) and
              not any('pose.bones["S_' in path for path in paths))
        check("values_preserved", applied["remapped_curve_count"] == len(_curves(action)) and
              action_content_snapshot(action) == source_frozen)
        check("target_preserved", _aligned_pose_snapshot(target, target_map) == target_frozen and
              target.animation_data is None)
        check("slot_retargeted", len(created.slots) == 1 and
              created.slots[0].name_display == target.name)
        check("groups_remapped", all(not group.name.startswith("S_")
                                     for group in getattr(created, "groups", ())))
        bpy.data.actions.remove(created)
        created = None
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for rig, data in owned:
            if rig.get("gameassetai_test_owner") != token or data.get("gameassetai_test_owner") != token:
                raise RuntimeError("Aligned retarget fixture ownership changed")
            bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Aligned retarget source Action ownership/users changed")
            bpy.data.actions.remove(action)
        for rig, data in owned:
            if data.users:
                raise RuntimeError("Aligned retarget Armature users changed")
            bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner") != token:
            raise RuntimeError("Aligned retarget Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
