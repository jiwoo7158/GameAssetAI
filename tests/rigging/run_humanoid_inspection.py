"""Run inside Blender after inspect_humanoid.py; owns only an exact synthetic Scene/Armature."""
import json
import uuid


def run_humanoid_inspection_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Humanoid fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = {"scene": original_scene.name, "mode": bpy.context.mode,
              "objects": sorted(bpy.data.objects.keys()),
              "armatures": sorted(bpy.data.armatures.keys()),
              "actions": sorted(bpy.data.actions.keys())}
    scene = bpy.data.scenes.new("GAI_Humanoid_" + token)
    data = bpy.data.armatures.new("GAI_HumanoidData_" + token)
    rig = bpy.data.objects.new("GAI_HumanoidRig_" + token, data)
    for item in (scene, data, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    checks = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)
    mapping = {role: role for role in REQUIRED_ROLES}
    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bones = {}
        parent_for = dict(PARENTS)
        parent_for["neck"] = "spine"
        for index, role in enumerate(REQUIRED_ROLES):
            bone = data.edit_bones.new(role)
            bone.head = (0, 0, index * 0.1)
            bone.tail = (0, 0, index * 0.1 + 0.08)
            bones[role] = bone
            parent = parent_for.get(role)
            if parent:
                bone.parent = bones[parent]
        bpy.ops.object.mode_set(mode="OBJECT")
        result = inspect_humanoid(rig.name, mapping, scene.name)
        check("complete_mapping", result["status"] == "ok" and not result["missing_roles"])
        check("hierarchy_valid", result["hierarchy"] and all(item["ok"] for item in result["hierarchy"]))
        check("read_only", json.dumps(result, allow_nan=False) and bpy.context.mode == "OBJECT")
        unnamed = inspect_humanoid(rig.name, None, scene.name)
        check("no_name_guessing", unnamed["status"] == "incomplete" and unnamed["mapping"] == {})
        missing = dict(mapping); missing["head"] = "absent"
        check("missing_bone", inspect_humanoid(rig.name, missing, scene.name)["status"] == "incomplete")
        duplicate = dict(mapping); duplicate["head"] = duplicate["neck"]
        check("duplicate_refused", inspect_humanoid(rig.name, duplicate, scene.name)["status"] == "error")
        wrong = dict(mapping); wrong["lower_arm_l"] = "upper_leg_l"; wrong["upper_leg_l"] = "lower_arm_l"
        check("hierarchy_detected", inspect_humanoid(rig.name, wrong, scene.name)["status"] == "incomplete")
        data.bones["hand_l"].use_deform = False
        review = inspect_humanoid(rig.name, mapping, scene.name)
        check("nondeform_review", review["status"] == "ok" and any("non-deform" in x for x in review["reviews"]))
        data.bones["hand_l"].use_deform = True
        rig.keyframe_insert(data_path="location", frame=1)
        animated = inspect_humanoid(rig.name, mapping, scene.name)
        check("animation_sensitivity", any("animation" in x.lower() for x in animated["reviews"]))
        action = rig.animation_data.action
        action["gameassetai_test_owner"] = token
        bpy.ops.object.mode_set(mode="EDIT")
        check("edit_mode_refused", inspect_humanoid(rig.name, mapping, scene.name)["status"] == "error")
        bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for item in (rig, data, scene):
            if item.get("gameassetai_test_owner") != token:
                raise RuntimeError("Humanoid fixture ownership changed")
        action = rig.animation_data.action if rig.animation_data else None
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Humanoid fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        if data.users != 0:
            raise RuntimeError("Humanoid Armature users changed")
        bpy.data.armatures.remove(data)
        bpy.data.scenes.remove(scene)
    after = {"scene": bpy.context.scene.name, "mode": bpy.context.mode,
             "objects": sorted(bpy.data.objects.keys()),
             "armatures": sorted(bpy.data.armatures.keys()),
             "actions": sorted(bpy.data.actions.keys())}
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
