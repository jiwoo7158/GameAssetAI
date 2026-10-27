"""Probe fractional-frame pose evaluation on an owned Blender fixture."""
import uuid


def run_subframe_pose_probe():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Subframe pose probe requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_SubframePoseFixture_" + token)
    data = bpy.data.armatures.new("GAI_SubframePoseData_" + token)
    rig = bpy.data.objects.new("GAI_SubframePoseRig_" + token, data)
    for item in (scene, data, rig):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = None
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def evaluated_x(frame, subframe):
        scene.frame_set(frame, subframe=subframe)
        evaluated = rig.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return float(evaluated.pose.bones["Root"].matrix_basis.translation.x)

    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        root = data.edit_bones.new("Root")
        root.head = (0, 0, 0); root.tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="POSE")
        pose = rig.pose.bones["Root"]
        pose.location = (0, 0, 0); pose.keyframe_insert(data_path="location", frame=1)
        pose.location = (1, 0, 0); pose.keyframe_insert(data_path="location", frame=2)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action
        action["gameassetai_test_owner"] = token
        curves = list(action.layers[0].strips[0].channelbags[0].fcurves)
        for curve in curves:
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"
        frozen_keys = [(curve.data_path, curve.array_index,
                        [(float(key.co.x), float(key.co.y), key.interpolation)
                         for key in curve.keyframe_points]) for curve in curves]

        check("integer_start", abs(evaluated_x(1, 0.0)) <= 1e-6)
        check("quarter_frame", abs(evaluated_x(1, 0.25) - 0.25) <= 1e-6)
        check("three_quarter_frame", abs(evaluated_x(1, 0.75) - 0.75) <= 1e-6)
        check("integer_end", abs(evaluated_x(2, 0.0) - 1.0) <= 1e-6)
        check("subframe_recorded", scene.frame_current == 2 and
              abs(scene.frame_subframe) <= 1e-9)
        current_keys = [(curve.data_path, curve.array_index,
                         [(float(key.co.x), float(key.co.y), key.interpolation)
                          for key in curve.keyframe_points]) for curve in curves]
        check("action_unchanged", current_keys == frozen_keys)
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        original_scene.frame_set(before[-2], subframe=before[-1])
        if rig.get("gameassetai_test_owner") != token or data.get("gameassetai_test_owner") != token:
            raise RuntimeError("Subframe pose fixture ownership changed")
        bpy.data.objects.remove(rig, do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner") != token or action.users != 0:
                raise RuntimeError("Subframe pose Action ownership/users changed")
            bpy.data.actions.remove(action)
        if data.users:
            raise RuntimeError("Subframe pose Armature users changed")
        bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner") != token:
            raise RuntimeError("Subframe pose Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
             bpy.context.scene.frame_current, bpy.context.scene.frame_subframe)
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
