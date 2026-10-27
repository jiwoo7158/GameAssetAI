"""Run explicit root-motion translation inspection on one owned Blender fixture."""
import json
import uuid


def run_root_motion_inspection_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Root-motion fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_RootMotion_" + token)
    data = bpy.data.armatures.new("GAI_RootMotionData_" + token)
    rig = bpy.data.objects.new("GAI_RootMotionRig_" + token, data)
    for item in (scene, data, rig): item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig)
    action = None
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    try:
        window.scene = scene; scene.view_layers[0].objects.active = rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        root = data.edit_bones.new("Root"); root.head=(0,0,0); root.tail=(0,0,1)
        child = data.edit_bones.new("Child"); child.head=(0,0,1); child.tail=(0,0,2); child.parent=root
        bpy.ops.object.mode_set(mode="POSE")
        rig.pose.bones["Root"].location=(0,0,0)
        rig.pose.bones["Root"].keyframe_insert(data_path="location", frame=1)
        rig.pose.bones["Root"].location=(2,0,0)
        rig.pose.bones["Root"].keyframe_insert(data_path="location", frame=10)
        rig.pose.bones["Root"].rotation_mode="XYZ"
        rig.pose.bones["Root"].rotation_euler=(0,0,0.5)
        rig.pose.bones["Root"].keyframe_insert(data_path="rotation_euler", frame=10)
        rig.pose.bones["Child"].location=(0,3,0)
        rig.pose.bones["Child"].keyframe_insert(data_path="location", frame=10)
        bpy.ops.object.mode_set(mode="OBJECT")
        action=rig.animation_data.action; action["gameassetai_test_owner"]=token
        slot = action.slots[0].identifier if len(action.slots) else None
        frozen=json.dumps(inspect_animation(scene.name),ensure_ascii=False,sort_keys=True)
        report=inspect_root_motion(scene.name,rig.name,action.name,1,10,1e-6,"Root",slot)
        check("explicit_root_translation", report["status"]=="ok" and
              report["target_kind"]=="BONE" and report["translation_evidence"] and
              report["net_translation"]==[2.0,0.0,0.0])
        check("axis_evidence", next(c for c in report["translation_channels"] if c["axis"]=="X")["keyed_span"]==2.0)
        check("nonroot_excluded", all("Child" not in c["data_path"] for c in report["translation_channels"]))
        check("rotation_reviewed", bool(report["other_root_transform_channels"]) and
              any("not interpreted" in item for item in report["reviews"]))
        object_report=inspect_root_motion(scene.name,rig.name,action.name,1,10,1e-6,None,slot)
        check("object_and_bone_distinct", not object_report["translation_channels"] and
              not object_report["translation_evidence"])
        check("bad_mapping_refused", inspect_root_motion(scene.name,rig.name,action.name,1,10,1e-6,"Missing",slot)["status"]=="error")
        check("bad_range_refused", inspect_root_motion(scene.name,rig.name,action.name,10,1,1e-6,"Root",slot)["status"]=="error")
        check("bad_slot_refused", inspect_root_motion(scene.name,rig.name,action.name,1,10,1e-6,"Root","Missing")["status"]=="error")
        check("read_only", scene.frame_current==1 and frozen==json.dumps(
              inspect_animation(scene.name),ensure_ascii=False,sort_keys=True))
        window.scene,window.view_layer=original_scene,original_layer
    finally:
        if window.scene==scene and bpy.context.mode!="OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene,window.view_layer=original_scene,original_layer
        for item in (rig,data,scene):
            if item.get("gameassetai_test_owner")!=token: raise RuntimeError("Root-motion fixture ownership changed")
        bpy.data.objects.remove(rig,do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner")!=token or action.users!=0:
                raise RuntimeError("Root-motion fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        if data.users: raise RuntimeError("Root-motion Armature users changed")
        bpy.data.armatures.remove(data); bpy.data.scenes.remove(scene)
    after=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),
           sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),
           bpy.context.scene.frame_current,bpy.context.scene.frame_subframe)
    check("original_state_restored",before==after)
    return {"status":"passed","check_count":len(checks),"checks":checks,
            "fixture_cleanup":"complete","blender_version":bpy.app.version_string}
