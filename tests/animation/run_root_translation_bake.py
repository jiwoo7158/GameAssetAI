"""Run guarded root-translation bake tests on owned Blender data."""
import uuid


def run_root_translation_bake_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Root translation fixture requires an Object-mode window")
    token = uuid.uuid4().hex; window = bpy.context.window
    original_scene, original_layer = window.scene, window.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.armatures.keys()), sorted(bpy.data.actions.keys()),
              original_scene.frame_current, original_scene.frame_subframe)
    scene = bpy.data.scenes.new("GAI_RootTranslationFixture_" + token); scene["gameassetai_test_owner"] = token
    owned = []; source_action = transfer = in_place = None; checks = []
    def check(name, value):
        if not value: raise AssertionError(name)
        checks.append(name)
    def rig(label, horizontal):
        data = bpy.data.armatures.new("GAI_" + label + "Data_" + token)
        obj = bpy.data.objects.new("GAI_" + label + "Rig_" + token, data)
        for item in (data, obj): item["gameassetai_test_owner"] = token
        scene.collection.objects.link(obj); owned.append((obj, data)); window.scene = scene
        scene.view_layers[0].objects.active = obj; obj.select_set(True); bpy.ops.object.mode_set(mode="EDIT")
        bone = data.edit_bones.new(label + "Root")
        bone.head = (0,0,0); bone.tail = ((1,0,0) if horizontal else (0,0,1))
        bone_name = bone.name
        bpy.ops.object.mode_set(mode="OBJECT"); obj.select_set(False)
        return obj, bone_name
    try:
        source, source_root = rig("Source", False); target, target_root = rig("Target", True)
        pose = source.pose.bones[source_root]
        pose.location=(0,0,0); pose.keyframe_insert(data_path="location",frame=1)
        pose.location=(1,2,3); pose.keyframe_insert(data_path="location",frame=3)
        source_action=source.animation_data.action; source_action["gameassetai_test_owner"] = token
        slot=source_action.slots[0].identifier if len(source_action.slots) else None
        def request(name, policy="TRANSFER", mask=(True,False,True), scale=2.0):
            return {"schema":ROOT_TRANSLATION_BAKE_SCHEMA,"scene_name":scene.name,
                    "source_armature":source.name,"target_armature":target.name,
                    "source_action":source_action.name,"target_action":name,
                    "source_root_bone":source_root,"target_root_bone":target_root,
                    "source_slot_identifier":slot,"frame_start":1,"frame_end":3,"frame_step":1,
                    "motion_policy":policy,"translation_scale":scale,"axis_mask":list(mask),
                    "preserve_source":True,"bind_result":False,"set_fake_user":True}
        source_snapshot=action_content_snapshot(source_action)
        transfer_name="GAI_RootTransfer_"+token; plan=preview_root_translation_bake(request(transfer_name))
        check("transfer_candidate",plan["status"]=="candidate_for_review")
        check("authorization_refused",apply_root_translation_bake(plan)["status"]=="error")
        curve=_curves(source_action)[0]; curve.mute=True
        check("stale_refused",apply_root_translation_bake(plan,True)["status"]=="error"); curve.mute=False
        check("bad_mask_refused",preview_root_translation_bake(request("Bad",mask=(False,False,False)))["status"]=="error")
        check("bad_scale_refused",preview_root_translation_bake(request("Bad",scale=0))["status"]=="error")
        constraint=target.pose.bones[target_root].constraints.new("COPY_LOCATION"); constraint.target=source
        check("constraint_refused",preview_root_translation_bake(request("Bad"))["status"]=="error")
        target.pose.bones[target_root].constraints.remove(constraint)
        plan=preview_root_translation_bake(request(transfer_name)); result=apply_root_translation_bake(plan,True)
        transfer=bpy.data.actions.get(transfer_name)
        check("transfer_created",result["status"]=="created" and transfer and transfer.use_fake_user and _action_references(transfer)==([],[]))
        check("translation_only",len(_curves(transfer))==3 and all(c.data_path.endswith(".location") for c in _curves(transfer)))
        check("linear_integer_keys",all([p.co.x for p in c.keyframe_points]==[1,2,3] and all(p.interpolation=="LINEAR" for p in c.keyframe_points) for c in _curves(transfer)))
        in_name="GAI_RootInPlace_"+token
        in_request=request(in_name,"IN_PLACE",(False,False,False),1.0)
        in_result=apply_root_translation_bake(preview_root_translation_bake(in_request),True)
        in_place=bpy.data.actions.get(in_name)
        check("in_place_created",in_result["status"]=="created" and all(abs(p.co.y)<=1e-6 for c in _curves(in_place) for p in c.keyframe_points))
        check("source_target_preserved",action_content_snapshot(source_action)==source_snapshot and target.animation_data is None)
        bpy.data.actions.remove(transfer); transfer=None; bpy.data.actions.remove(in_place); in_place=None
        window.scene,window.view_layer=original_scene,original_layer
    finally:
        for action in (transfer,in_place):
            if action is not None and bpy.data.actions.get(action.name)==action: bpy.data.actions.remove(action)
        if window.scene==scene and bpy.context.mode!="OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene,window.view_layer=original_scene,original_layer
        for obj,data in owned: bpy.data.objects.remove(obj,do_unlink=True)
        if source_action is not None:
            if source_action.users!=0: raise RuntimeError("Source Action still referenced")
            bpy.data.actions.remove(source_action)
        for obj,data in owned:
            if data.users: raise RuntimeError("Armature still referenced")
            bpy.data.armatures.remove(data)
        bpy.data.scenes.remove(scene)
    after=(sorted(bpy.data.scenes.keys()),sorted(bpy.data.objects.keys()),
           sorted(bpy.data.armatures.keys()),sorted(bpy.data.actions.keys()),
           bpy.context.scene.frame_current,bpy.context.scene.frame_subframe)
    check("original_state_restored",before==after)
    return {"status":"passed","check_count":len(checks),"checks":checks,
            "fixture_cleanup":"complete","blender_version":bpy.app.version_string}
