"""Run stored Action endpoint inspection against one owned Blender fixture."""
import json
import uuid


def run_action_loop_inspection_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Action loop fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.actions.keys()), original_scene.frame_current,
              original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_Loop_" + token)
    obj = bpy.data.objects.new("GAI_LoopObject_" + token, None)
    for item in (scene, obj): item["gameassetai_test_owner"] = token
    scene.collection.objects.link(obj)
    action = None
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    try:
        window.scene = scene; scene.view_layers[0].objects.active = obj; obj.select_set(True)
        obj.location = (0, 0, 0); obj.keyframe_insert(data_path="location", frame=1)
        obj.location = (0, 1, 0); obj.keyframe_insert(data_path="location", frame=10)
        action = obj.animation_data.action; action["gameassetai_test_owner"] = token
        x_curve = next(curve for curve in _curves(action)
                       if curve.data_path == "location" and curve.array_index == 0)
        x_curve.modifiers.new("CYCLES")
        frozen = json.dumps(inspect_animation(scene.name), ensure_ascii=False, sort_keys=True)
        report = inspect_action_loop(scene.name, action.name, 1, 10, 1e-6)
        channels = {(item["data_path"], item["array_index"]): item
                    for item in report["channels"]}
        check("matching_component", channels[("location", 0)]["component_match"] and
              channels[("location", 0)]["cyclic_modifier"])
        check("mismatch_detected", not channels[("location", 1)]["component_match"] and
              not report["all_components_match"] and not report["endpoint_candidate"])
        check("boundary_keys", report["all_channels_keyed_at_boundaries"])
        relaxed = inspect_action_loop(scene.name, action.name, 1, 10, 2.0)
        check("explicit_tolerance", relaxed["all_components_match"] and relaxed["endpoint_candidate"])
        interior = inspect_action_loop(scene.name, action.name, 2, 9, 2.0)
        check("missing_boundary_review", not interior["all_channels_keyed_at_boundaries"] and
              not interior["endpoint_candidate"])
        check("invalid_inputs_refused",
              inspect_action_loop(scene.name, action.name, 10, 1, 1e-6)["status"] == "error" and
              inspect_action_loop(scene.name, action.name, 1, 10, -1)["status"] == "error")
        check("missing_targets_refused",
              inspect_action_loop("Missing", action.name, 1, 10, 1e-6)["status"] == "error" and
              inspect_action_loop(scene.name, "Missing", 1, 10, 1e-6)["status"] == "error")
        check("read_only", scene.frame_current == 1 and
              frozen == json.dumps(inspect_animation(scene.name), ensure_ascii=False, sort_keys=True))
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        window.scene, window.view_layer = original_scene, original_layer
        for item in (obj, scene):
            if item.get("gameassetai_test_owner") != token:
                raise RuntimeError("Action loop fixture ownership changed")
        bpy.data.objects.remove(obj, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Action loop fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.actions.keys()), bpy.context.scene.frame_current,
             bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
