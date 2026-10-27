"""Run strict exact-boundary Action range extraction on owned Blender data."""
import uuid


def run_action_range_extraction_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action range fixture requires Object mode")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_RangeFixture_" + token)
    armature = bpy.data.armatures.new("GAI_RangeData_" + token)
    rig = bpy.data.objects.new("GAI_RangeRig_" + token, armature)
    for item in (scene, armature, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    source = created = None
    checks = []

    def check(name, value):
        if not value:
            raise AssertionError(name)
        checks.append(name)

    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        for frame, value in ((1, 0.0), (2, 1.0), (3, 2.0), (4, 3.0)):
            rig.location.x = value
            rig.keyframe_insert(data_path="location", frame=frame, index=0)
        source = rig.animation_data.action
        source.name = "GAI_RangeSource_" + token
        source.use_fake_user = True
        source["gameassetai_test_owner"] = token
        for point in _curves(source)[0].keyframe_points:
            point.interpolation = "LINEAR"
        for name, frame in (("Before", 1), ("Start", 2), ("End", 3), ("After", 4)):
            source.pose_markers.new(name).frame = frame
        target_name = "GAI_RangeTarget_" + token
        request = {"schema": ACTION_RANGE_SCHEMA, "scene_name": scene.name,
                   "source_action": source.name,
                   "source_slot_identifier": source.slots[0].identifier,
                   "target_action": target_name, "frame_start": 2, "frame_end": 3,
                   "frame_policy": "KEEP_FRAMES", "preserve_source": True,
                   "bind_result": False, "set_fake_user": True}
        source_snapshot = action_content_snapshot(source)
        source_refs = _action_references(source)
        plan = preview_action_range_extraction(request)
        check("candidate", plan["status"] == "candidate_for_review"
              and plan["candidate"]["kept_keyframe_count"] == 2
              and plan["candidate"]["kept_pose_marker_count"] == 2)
        check("authorization_refused",
              apply_action_range_extraction(plan)["status"] == "error")
        missing = dict(request)
        missing["frame_end"] = 5
        check("missing_boundary_refused",
              preview_action_range_extraction(missing)["status"] == "error")
        point = _curves(source)[0].keyframe_points[0]
        point.interpolation = "BEZIER"
        check("nonlinear_refused", preview_action_range_extraction(request)["status"] == "error")
        point.interpolation = "LINEAR"
        modifier = _curves(source)[0].modifiers.new("CYCLES")
        check("modifier_refused", preview_action_range_extraction(request)["status"] == "error")
        _curves(source)[0].modifiers.remove(modifier)
        _curves(source)[0].mute = True
        check("stale_refused", apply_action_range_extraction(plan, True)["status"] == "error")
        _curves(source)[0].mute = False
        collision = bpy.data.actions.new(target_name)
        check("collision_refused", preview_action_range_extraction(request)["status"] == "error")
        bpy.data.actions.remove(collision)
        bad_policy = dict(request)
        bad_policy["frame_policy"] = "INFER"
        check("unknown_policy_refused",
              preview_action_range_extraction(bad_policy)["status"] == "error")
        result = apply_action_range_extraction(preview_action_range_extraction(request), True)
        created = bpy.data.actions.get(target_name)
        if result["status"] != "created":
            raise AssertionError("created: " + repr(result))
        check("created", result["status"] == "created" and created is not None
              and created.use_fake_user and _action_references(created) == ([], []))
        check("range_exact", result["keyframe_count"] == 2
              and _curve_frames(_curves(created)[0]) == [2.0, 3.0])
        check("markers_trimmed", [marker.name for marker in created.pose_markers]
              == ["Start", "End"])
        check("source_preserved", action_content_snapshot(source) == source_snapshot
              and _action_references(source) == source_refs
              and rig.animation_data.action == source)
        bpy.data.actions.remove(created)
        created = None
        zero_request = dict(request)
        zero_request["target_action"] = "GAI_RangeZero_" + token
        zero_request["frame_policy"] = "REBASE_TO_ZERO"
        zero_result = apply_action_range_extraction(
            preview_action_range_extraction(zero_request), True)
        created = bpy.data.actions.get(zero_request["target_action"])
        check("rebased_to_zero", zero_result["status"] == "created"
              and zero_result["frame_offset"] == 2
              and _curve_frames(_curves(created)[0]) == [0.0, 1.0])
        check("zero_markers_rebased",
              [(marker.name, marker.frame) for marker in created.pose_markers]
              == [("Start", 0), ("End", 1)])
        bpy.data.actions.remove(created)
        created = None
        one_request = dict(request)
        one_request["target_action"] = "GAI_RangeOne_" + token
        one_request["frame_policy"] = "REBASE_TO_ONE"
        one_result = apply_action_range_extraction(
            preview_action_range_extraction(one_request), True)
        created = bpy.data.actions.get(one_request["target_action"])
        check("rebased_to_one", one_result["status"] == "created"
              and one_result["frame_offset"] == 1
              and _curve_frames(_curves(created)[0]) == [1.0, 2.0])
        check("rebase_source_preserved", action_content_snapshot(source) == source_snapshot
              and _action_references(source) == source_refs
              and _action_references(created) == ([], []))
        bpy.data.actions.remove(created)
        created = None
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        if rig.animation_data is not None:
            rig.animation_data_clear()
        bpy.data.objects.remove(rig, do_unlink=True)
        if source is not None:
            source.use_fake_user = False
            if source.users:
                raise RuntimeError("Fixture source Action still referenced")
            bpy.data.actions.remove(source)
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
