"""Run guarded Action-copy apply tests in an owned Blender fixture."""
import uuid


def run_action_copy_apply_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action copy fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.actions.keys()), original_scene.frame_current,
              original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_ActionCopy_" + token)
    rig_data = bpy.data.armatures.new("GAI_ActionCopyData_" + token)
    rig = bpy.data.objects.new("GAI_ActionCopyRig_" + token, rig_data)
    for item in (scene, rig_data, rig): item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = created = None
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    try:
        window.scene = scene; scene.view_layers[0].objects.active = rig; rig.select_set(True)
        rig.keyframe_insert(data_path="location", frame=1, index=0)
        rig.location.x = 1.0
        rig.keyframe_insert(data_path="location", frame=10, index=0)
        action = rig.animation_data.action; action["gameassetai_test_owner"] = token
        curve = _curves(action)[0]
        curve.modifiers.new("CYCLES")
        track = rig.animation_data.nla_tracks.new(); track.name = "GAI_CopyTrack_" + token
        strip = track.strips.new("GAI_CopyStrip_" + token, 20, action)
        target = "GAI_CopiedAction_" + token
        request = {"schema": "gameassetai.action-copy-request.v1", "scene_name": scene.name,
                   "source_action": action.name, "target_action": target,
                   "preserve_source": True, "bind_copy": False, "set_fake_user": True}
        plan = preview_action_copy(request)
        check("preview", plan["status"] == "candidate_for_review" and
              len(plan["candidate"]["source_content_sha256"]) == 64)
        check("authorization_refused", apply_action_copy(plan)["status"] == "error" and
              bpy.data.actions.get(target) is None)
        original_mute = curve.mute
        curve.mute = not original_mute
        check("stale_refused", apply_action_copy(plan, True)["status"] == "error" and
              bpy.data.actions.get(target) is None)
        curve.mute = original_mute
        collision = bpy.data.actions.new(target)
        check("collision_refused", apply_action_copy(plan, True)["status"] == "error")
        bpy.data.actions.remove(collision)
        source_snapshot = action_content_snapshot(action)
        source_refs = _action_references(action)
        applied = apply_action_copy(plan, True)
        created = bpy.data.actions.get(target)
        if applied["status"] != "created":
            raise AssertionError("created: " + repr(applied))
        check("created", applied["status"] == "created" and created is not None and
              created != action and created.use_fake_user)
        check("content_and_references", action_content_snapshot(created) == source_snapshot and
              action_content_snapshot(action) == source_snapshot and
              _action_references(action) == source_refs and _action_references(created) == ([], []))
        check("context_preserved", window.scene == scene and scene.frame_current == 1 and
              rig.animation_data.action == action and strip.action == action)
        bpy.data.actions.remove(created); created = None
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        if window.scene == scene and bpy.context.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for item in (rig, rig_data, scene):
            if item.get("gameassetai_test_owner") != token:
                raise RuntimeError("Action copy fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Action copy fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        if rig_data.users: raise RuntimeError("Action copy Armature users changed")
        bpy.data.armatures.remove(rig_data); bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.actions.keys()), bpy.context.scene.frame_current,
             bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
