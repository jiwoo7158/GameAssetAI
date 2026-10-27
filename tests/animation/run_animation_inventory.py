"""Run inside Blender after inspect_animation.py; owns one synthetic animated rig."""
import json
import uuid


def run_animation_inventory_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Animation fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_Animation_" + token)
    data = bpy.data.armatures.new("GAI_AnimationData_" + token)
    rig = bpy.data.objects.new("GAI_AnimationRig_" + token, data)
    for item in (scene, data, rig): item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    action = None
    unused_action = None
    try:
        window.scene = scene; scene.view_layers[0].objects.active = rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        root = data.edit_bones.new("Root"); root.head = (0, 0, 0); root.tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="POSE")
        rig.pose.bones["Root"].location = (0, 0, 0)
        rig.pose.bones["Root"].keyframe_insert(data_path="location", frame=1)
        rig.pose.bones["Root"].location.x = 1
        rig.pose.bones["Root"].keyframe_insert(data_path="location", frame=10)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action; action["gameassetai_test_owner"] = token
        unused_action = bpy.data.actions.new("GAI_UnusedAction_" + token)
        unused_action["gameassetai_test_owner"] = token
        track = rig.animation_data.nla_tracks.new(); track.name = "GAI_Track_" + token
        strip = track.strips.new("GAI_Strip_" + token, 20, action)
        driver = rig.driver_add("scale", 0)
        driver.driver.expression = "1.0"
        report = inspect_animation(scene.name, rig.name, ["Root"])
        check("action_inventory", report["status"] == "ok" and len(report["actions"]) >= 1)
        current = next(item for item in report["actions"] if item["name"] == action.name)
        check("curve_and_key_inventory", current["curve_count"] >= 1 and current["keyframe_count"] >= 2)
        check("binding_inventory", any(item["action"] == action.name for item in report["bindings"]))
        binding = next(item for item in report["bindings"] if item["owner"] == rig.name)
        check("nla_strip_inventory", binding["nla_tracks"] == [{
            "name": track.name, "mute": False,
            "strips": [{"name": strip.name, "action": action.name,
                        "frame_start": float(strip.frame_start),
                        "frame_end": float(strip.frame_end),
                        "scale": 1.0, "repeat": 1.0}],
        }])
        check("driver_inventory", binding["drivers"] == 1)
        unused = next(item for item in report["actions"] if item["name"] == unused_action.name)
        check("unused_action_inventory", unused["users"] == 0 and
              unused["curve_count"] == 0 and unused["keyframe_count"] == 0)
        check("explicit_root_motion", report["root_motion_channels"] and all(item["bone"] == "Root" for item in report["root_motion_channels"]))
        unknown = inspect_animation(scene.name, rig.name)
        check("no_root_guess", not unknown["root_motion_channels"] and any("not inferred" in item for item in unknown["reviews"]))
        check("invalid_roots_refused", inspect_animation(scene.name, rig.name, ["Root", "Root"])["status"] == "error")
        check("json_and_frame_preserved", bool(json.dumps(report, allow_nan=False)) and scene.frame_current == 1)
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for item in (rig, data, scene):
            if item.get("gameassetai_test_owner") != token: raise RuntimeError("Animation fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        for owned_action in (action, unused_action):
            if owned_action is not None:
                if (owned_action.get("gameassetai_test_owner") != token or
                        owned_action.users != 0):
                    raise RuntimeError("Animation fixture Action ownership/users changed")
                bpy.data.actions.remove(owned_action)
        if data.users: raise RuntimeError("Animation Armature users changed")
        bpy.data.armatures.remove(data); bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
