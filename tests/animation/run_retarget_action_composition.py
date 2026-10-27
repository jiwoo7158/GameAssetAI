"""Run guarded rotation/root-translation Action composition on owned data."""
import uuid


def run_retarget_action_composition_tests():
    if bpy.context.mode!="OBJECT" or bpy.context.window is None: raise RuntimeError("Composition fixture requires Object mode")
    token=uuid.uuid4().hex; window=bpy.context.window; original_scene,original_layer=window.scene,window.view_layer
    before=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),original_scene.frame_current,original_scene.frame_subframe)
    scene=bpy.data.scenes.new("GAI_ComposeFixture_"+token); data=bpy.data.armatures.new("GAI_ComposeData_"+token); rig=bpy.data.objects.new("GAI_ComposeRig_"+token,data)
    for item in (scene,data,rig): item["gameassetai_test_owner"]=token
    scene.collection.objects.link(rig); rotation=translation=created=None; checks=[]
    def check(name,value):
        if not value: raise AssertionError(name)
        checks.append(name)
    try:
        window.scene=scene; scene.view_layers[0].objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode="EDIT")
        root=data.edit_bones.new("Root"); root.head=(0,0,0); root.tail=(0,0,1)
        child=data.edit_bones.new("Child"); child.head=(0,0,1); child.tail=(0,0,2); child.parent=root
        bpy.ops.object.mode_set(mode="OBJECT")
        pose=rig.pose.bones["Child"]; pose.rotation_mode="QUATERNION"
        for frame,value in ((1,0.0),(2,0.2),(3,0.4)):
            pose.rotation_quaternion=(1,0,value,0); pose.keyframe_insert(data_path="rotation_quaternion",frame=frame)
        rotation=rig.animation_data.action; rotation.name="GAI_Rotation_"+token; rotation.use_fake_user=True; rig.animation_data.action=None
        root_pose=rig.pose.bones["Root"]
        for frame,value in ((1,0.0),(2,1.0),(3,2.0)):
            root_pose.location=(value,0,0); root_pose.keyframe_insert(data_path="location",frame=frame)
        translation=rig.animation_data.action; translation.name="GAI_Translation_"+token; translation.use_fake_user=True; rig.animation_data.action=None
        for action in (rotation,translation):
            action["gameassetai_test_owner"]=token
            for curve in _curves(action):
                for point in curve.keyframe_points: point.interpolation="LINEAR"
        target_name="GAI_Composed_"+token
        request={"schema":COMPOSE_RETARGET_SCHEMA,"scene_name":scene.name,"target_armature":rig.name,
                 "rotation_action":rotation.name,"translation_action":translation.name,"target_action":target_name,
                 "target_root_bone":"Root","frame_start":1,"frame_end":3,"frame_step":1,
                 "preserve_sources":True,"bind_result":False,"set_fake_user":True}
        rot_state,trans_state=_compose_curve_map(rotation),_compose_curve_map(translation)
        plan=preview_retarget_action_composition(request)
        check("candidate",plan["status"]=="candidate_for_review" and plan["candidate"]["translation_curve_count"]==3)
        check("authorization_refused",apply_retarget_action_composition(plan)["status"]=="error")
        _curves(translation)[0].mute=True; check("stale_refused",apply_retarget_action_composition(plan,True)["status"]=="error"); _curves(translation)[0].mute=False
        _curves(translation)[0].keyframe_points[0].interpolation="BEZIER"
        check("nonlinear_refused",preview_retarget_action_composition(request)["status"]=="error")
        _curves(translation)[0].keyframe_points[0].interpolation="LINEAR"
        result=apply_retarget_action_composition(preview_retarget_action_composition(request),True); created=bpy.data.actions.get(target_name)
        check("created_unbound",result["status"]=="created" and created and created.use_fake_user and _action_references(created)==([],[]))
        check("curve_counts",result["rotation_curve_count"]==4 and result["translation_curve_count"]==3 and result["curve_count"]==7)
        check("paths_combined",any('Child' in c.data_path and c.data_path.endswith("rotation_quaternion") for c in _curves(created)) and any('Root' in c.data_path and c.data_path.endswith("location") for c in _curves(created)))
        check("sources_preserved",_compose_curve_map(rotation)==rot_state and _compose_curve_map(translation)==trans_state and rig.animation_data.action is None)
        bpy.data.actions.remove(created); created=None; window.scene,window.view_layer=original_scene,original_layer
    finally:
        if created is not None and bpy.data.actions.get(created.name)==created: bpy.data.actions.remove(created)
        if window.scene==scene and bpy.context.mode!="OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene,window.view_layer=original_scene,original_layer; bpy.data.objects.remove(rig,do_unlink=True)
        for action in (rotation,translation):
            if action is not None:
                if action.users!=1: raise RuntimeError("Fixture Action users changed")
                action.use_fake_user=False; bpy.data.actions.remove(action)
        if data.users: raise RuntimeError("Fixture Armature still referenced")
        bpy.data.armatures.remove(data); bpy.data.scenes.remove(scene)
    after=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),bpy.context.scene.frame_current,bpy.context.scene.frame_subframe)
    check("original_state_restored",before==after)
    return {"status":"passed","check_count":len(checks),"checks":checks,"fixture_cleanup":"complete","blender_version":bpy.app.version_string}
