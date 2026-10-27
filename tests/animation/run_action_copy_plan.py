"""Run inside Blender after animation inventory and copy-plan helpers."""
import json
import uuid


def run_action_copy_plan_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action copy plan fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.actions.keys()), original_scene.frame_current,
              original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_ActionPlan_" + token)
    rig_data = bpy.data.armatures.new("GAI_ActionPlanData_" + token)
    rig = bpy.data.objects.new("GAI_ActionPlanRig_" + token, rig_data)
    for item in (scene, rig_data, rig): item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = None
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
        track = rig.animation_data.nla_tracks.new(); track.name = "GAI_PlanTrack_" + token
        strip = track.strips.new("GAI_PlanStrip_" + token, 20, action)
        inventory = inspect_animation(scene.name, rig.name)
        target = "GAI_CopiedAction_" + token
        request = {"schema": "gameassetai.action-copy-request.v1", "scene_name": scene.name,
                   "source_action": action.name, "target_action": target,
                   "preserve_source": True, "bind_copy": False,
                   "set_fake_user": True}
        frozen = json.dumps(inventory, ensure_ascii=False, sort_keys=True)
        plan = plan_action_copy(inventory, request)
        check("candidate", plan["status"] == "candidate_for_review" and
              plan["authorization"] is False and plan["candidate"]["target_action"] == target)
        check("references", plan["candidate"]["current_action_references"] ==
              [{"owner": rig.name, "owner_type": "Object"}] and
              plan["candidate"]["nla_references"] ==
              [{"owner": rig.name, "track": track.name, "strip": strip.name}])
        collision = dict(request); collision["target_action"] = action.name
        check("collision_refused", plan_action_copy(inventory, collision)["status"] == "error")
        missing = dict(request); missing["source_action"] = "Missing"
        check("missing_source_refused", plan_action_copy(inventory, missing)["status"] == "error")
        long_name = dict(request); long_name["target_action"] = "가" * 86
        check("utf8_limit_refused", plan_action_copy(inventory, long_name)["status"] == "error")
        unsafe = dict(request); unsafe["preserve_source"] = False
        check("nonpreserving_refused", plan_action_copy(inventory, unsafe)["status"] == "error")
        check("invalid_inventory_refused", plan_action_copy({}, request)["status"] == "error")
        check("read_only", frozen == json.dumps(inventory, ensure_ascii=False, sort_keys=True) and
              bpy.data.actions.get(target) is None and scene.frame_current == 1)
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for item in (rig, rig_data, scene):
            if item.get("gameassetai_test_owner") != token:
                raise RuntimeError("Action plan fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Action plan fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        if rig_data.users: raise RuntimeError("Action plan Armature users changed")
        bpy.data.armatures.remove(rig_data); bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.actions.keys()), bpy.context.scene.frame_current,
             bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
