"""Run read-only retarget-readiness inspection on owned source/target humanoid rigs."""
import json
import uuid


def run_retarget_readiness_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Retarget fixture requires an Object-mode window")
    token=uuid.uuid4().hex; window=bpy.context.window
    original_scene,original_layer=bpy.context.scene,bpy.context.view_layer
    before=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),
            sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),
            original_scene.frame_current,original_scene.frame_subframe)
    scene=bpy.data.scenes.new("GAI_Retarget_"+token); scene["gameassetai_test_owner"]=token
    owned=[]; checks=[]; action=None
    def check(name,condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    def make_rig(label,prefix,length_scale):
        data=bpy.data.armatures.new("GAI_"+label+"Data_"+token)
        rig=bpy.data.objects.new("GAI_"+label+"Rig_"+token,data)
        for item in (data,rig): item["gameassetai_test_owner"]=token
        scene.collection.objects.link(rig); owned.append((rig,data))
        window.scene=scene; scene.view_layers[0].objects.active=rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT"); bones={}
        for index,role in enumerate(REQUIRED_ROLES):
            bone=data.edit_bones.new(prefix+role)
            bone.head=(0,0,index*0.2*length_scale); bone.tail=(0,0,(index*0.2+0.1)*length_scale)
            bones[role]=bone
            parent=PARENTS.get(role)
            if parent: bone.parent=bones[parent]
        extra=data.edit_bones.new(prefix+"extra"); extra.head=(0,0,4); extra.tail=(0,0,4.1); extra.parent=bones["hips"]
        extra_name=extra.name
        bpy.ops.object.mode_set(mode="OBJECT"); rig.select_set(False)
        return rig,{role:prefix+role for role in REQUIRED_ROLES},extra_name
    try:
        source,source_map,extra=make_rig("Source","S_",1.0)
        target,target_map,_=make_rig("Target","T_",1.5); target.scale=(1,2,1)
        scene.view_layers[0].objects.active=source; source.select_set(True)
        source.pose.bones[source_map["hips"]].location=(0,0,0)
        source.pose.bones[source_map["hips"]].keyframe_insert(data_path="location",frame=1)
        source.pose.bones[source_map["hips"]].location=(1,0,0)
        source.pose.bones[source_map["hips"]].keyframe_insert(data_path="location",frame=10)
        source.pose.bones[extra].rotation_mode="XYZ"; source.pose.bones[extra].rotation_euler=(0,0,0.5)
        source.pose.bones[extra].keyframe_insert(data_path="rotation_euler",frame=10)
        action=source.animation_data.action; action["gameassetai_test_owner"]=token
        slot=action.slots[0].identifier if len(action.slots) else None
        frozen=json.dumps(inspect_animation(scene.name),ensure_ascii=False,sort_keys=True)
        report=inspect_retarget_readiness(scene.name,source.name,target.name,source_map,target_map,action.name,REQUIRED_ROLES,slot)
        check("candidate",report["status"]=="ok" and report["retarget_candidate"])
        check("humanoid_pair",report["source_humanoid"]["status"]=="ok" and report["target_humanoid"]["status"]=="ok")
        check("rest_metrics",len(report["role_rest_metrics"])==len(REQUIRED_ROLES) and
              all(abs(item["target_to_source_length_ratio"]-1.5)<1e-5 for item in report["role_rest_metrics"]))
        check("action_coverage",report["mapped_animated_roles"]==["hips"] and extra in report["unmapped_animated_bones"])
        check("preservation_reviews",report["source_action_referenced_by_source"] and
              any("non-identity" in item for item in report["reviews"]))
        check("same_rig_refused",inspect_retarget_readiness(scene.name,source.name,source.name,source_map,source_map,action.name)["status"]=="error")
        incomplete=dict(target_map); incomplete.pop("head")
        check("incomplete_mapping",inspect_retarget_readiness(scene.name,source.name,target.name,source_map,incomplete,action.name)["status"]=="incomplete")
        source.animation_data.action=None
        unbound=inspect_retarget_readiness(scene.name,source.name,target.name,source_map,target_map,action.name,REQUIRED_ROLES,slot)
        check("unbound_not_candidate",unbound["status"]=="ok" and not unbound["retarget_candidate"])
        source.animation_data.action=action
        check("bad_slot_refused",inspect_retarget_readiness(scene.name,source.name,target.name,source_map,target_map,action.name,REQUIRED_ROLES,"Missing")["status"]=="error")
        check("read_only",scene.frame_current==1 and frozen==json.dumps(inspect_animation(scene.name),ensure_ascii=False,sort_keys=True))
        window.scene,window.view_layer=original_scene,original_layer
    finally:
        if window.scene==scene and bpy.context.mode!="OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene,window.view_layer=original_scene,original_layer
        for rig,data in owned:
            if rig.get("gameassetai_test_owner")!=token or data.get("gameassetai_test_owner")!=token:
                raise RuntimeError("Retarget fixture ownership changed")
            bpy.data.objects.remove(rig,do_unlink=True)
        if action is not None:
            if action.get("gameassetai_test_owner")!=token or action.users!=0:
                raise RuntimeError("Retarget fixture Action ownership/users changed")
            bpy.data.actions.remove(action)
        for rig,data in owned:
            if data.users: raise RuntimeError("Retarget Armature users changed")
            bpy.data.armatures.remove(data)
        if scene.get("gameassetai_test_owner")!=token: raise RuntimeError("Retarget Scene ownership changed")
        bpy.data.scenes.remove(scene)
    after=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),
           sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),
           bpy.context.scene.frame_current,bpy.context.scene.frame_subframe)
    check("original_state_restored",before==after)
    return {"status":"passed","check_count":len(checks),"checks":checks,
            "fixture_cleanup":"complete","blender_version":bpy.app.version_string}
