"""Run rotation-only local-basis retarget bake on owned differing-rest rigs."""
import uuid


def run_rotation_retarget_bake_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Rotation bake fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_RotationBakeFixture_" + token)
    scene["gameassetai_test_owner"] = token
    owned = []; checks = []; action = created = None

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def make_rig(label, prefix, horizontal):
        data = bpy.data.armatures.new("GAI_" + label + "Data_" + token)
        rig = bpy.data.objects.new("GAI_" + label + "Rig_" + token, data)
        for item in (data, rig): item["gameassetai_test_owner"] = token
        scene.collection.objects.link(rig); owned.append((rig, data))
        window.scene = scene; scene.view_layers[0].objects.active = rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT"); bones = {}
        for index, role in enumerate(REQUIRED_ROLES):
            bone = data.edit_bones.new(prefix + role)
            if horizontal:
                bone.head = (index * 0.2, 0, 0); bone.tail = (index * 0.2, 0.1, 0)
            else:
                bone.head = (0, 0, index * 0.2); bone.tail = (0, 0, index * 0.2 + 0.1)
            bones[role] = bone
            parent = PARENTS.get(role)
            if parent: bone.parent = bones[parent]
        bpy.ops.object.mode_set(mode="OBJECT"); rig.select_set(False)
        return rig, {role: prefix + role for role in REQUIRED_ROLES}

    try:
        source, source_map = make_rig("Source", "S_", False)
        target, target_map = make_rig("Target", "T_", True)
        scene.view_layers[0].objects.active = source; source.select_set(True)
        pose = source.pose.bones[source_map["upper_arm_l"]]
        pose.rotation_mode = "XYZ"
        pose.rotation_euler = (0, 0, 0)
        pose.keyframe_insert(data_path="rotation_euler", frame=1)
        pose.rotation_euler = (0.2, -0.3, 0.4)
        pose.keyframe_insert(data_path="rotation_euler", frame=3)
        action = source.animation_data.action
        action["gameassetai_test_owner"] = token
        slot = action.slots[0].identifier if len(action.slots) else None
        target_name = "GAI_RotationBaked_" + token
        request = {
            "schema": ROTATION_BAKE_SCHEMA, "scene_name": scene.name,
            "source_armature": source.name, "target_armature": target.name,
            "source_action": action.name, "target_action": target_name,
            "source_mapping": source_map, "target_mapping": target_map,
            "source_slot_identifier": slot, "frame_start": 1, "frame_end": 3,
            "frame_step": 1, "preserve_source": True, "bind_result": False,
            "set_fake_user": True, "rotation_only": True,
        }
        source_snapshot = action_content_snapshot(action)
        preview = preview_rotation_retarget_bake(request)
        check("differing_rest_candidate", preview["status"] == "candidate_for_review" and
              preview["candidate"]["frame_count"] == 3)
        check("authorization_refused", apply_rotation_retarget_bake(preview)["status"] == "error")
        curve = _curves(action)[0]; old_mute = curve.mute; curve.mute = not old_mute
        check("stale_refused", apply_rotation_retarget_bake(preview, True)["status"] == "error")
        curve.mute = old_mute
        source.location.x = 0.1
        check("object_transform_refused", preview_rotation_retarget_bake(request)["status"] == "error")
        source.location.x = 0.0
        constraint = target.pose.bones[target_map["upper_arm_l"]].constraints.new("COPY_ROTATION")
        constraint.target = source
        check("constraint_refused", preview_rotation_retarget_bake(request)["status"] == "error")
        target.pose.bones[target_map["upper_arm_l"]].constraints.remove(constraint)
        bad_step = dict(request); bad_step["frame_step"] = 2
        check("step_refused", preview_rotation_retarget_bake(bad_step)["status"] == "error")
        preview = preview_rotation_retarget_bake(request)
        result = apply_rotation_retarget_bake(preview, True)
        created = bpy.data.actions.get(target_name)
        if result["status"] != "created":
            raise AssertionError("created: " + repr(result))
        check("created_unbound", created is not None and created.use_fake_user and
              _action_references(created) == ([], []))
        check("baked_shape", result["frame_count"] == 3 and result["curve_count"] == 4 and
              result["mapped_roles"] == ["upper_arm_l"])
        check("target_paths", all(target_map["upper_arm_l"] in curve.data_path
                                  for curve in _curves(created)))
        check("integer_linear_keys", all(
            [float(point.co.x) for point in curve.keyframe_points] == [1.0, 2.0, 3.0]
            and all(point.interpolation == "LINEAR" for point in curve.keyframe_points)
            for curve in _curves(created)))
        check("source_target_preserved", action_content_snapshot(action) == source_snapshot and
              target.animation_data is None)
        bpy.data.actions.remove(created); created = None
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for rig, data in owned:
            if rig.get("gameassetai_test_owner") != token or data.get("gameassetai_test_owner") != token:
                raise RuntimeError("Rotation bake fixture ownership changed")
            bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Rotation bake source Action ownership/users changed")
            bpy.data.actions.remove(action)
        for rig, data in owned:
            if data.users: raise RuntimeError("Rotation bake Armature users changed")
            bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner") != token:
            raise RuntimeError("Rotation bake Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}

