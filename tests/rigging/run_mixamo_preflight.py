"""Run inside Blender after humanoid and Mixamo preflight helpers; exact owned IDs only."""
import uuid


def run_mixamo_preflight_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Mixamo fixture requires an Object-mode window")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
              sorted(bpy.data.meshes.keys()), sorted(bpy.data.armatures.keys()))
    scene = bpy.data.scenes.new("GAI_Mixamo_" + token)
    data = bpy.data.armatures.new("GAI_MixamoData_" + token)
    rig = bpy.data.objects.new("GAI_MixamoRig_" + token, data)
    mesh = bpy.data.meshes.new("GAI_MixamoMesh_" + token)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    body = bpy.data.objects.new("GAI_MixamoBody_" + token, mesh)
    for item in (scene, data, rig, mesh, body):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(rig); scene.collection.objects.link(body)
    checks = []
    def check(name, condition):
        if not condition: raise AssertionError(name)
        checks.append(name)
    prefix = "mixamorig:"
    try:
        window.scene = scene
        scene.view_layers[0].objects.active = rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        edit = {}
        order = list(ROLES)
        for index, role in enumerate(order):
            bone = data.edit_bones.new(prefix + MIXAMO_SUFFIXES[role])
            bone.head = (0, 0, index * 0.1); bone.tail = (0, 0, index * 0.1 + 0.08)
            edit[role] = bone
            parent_role = PARENTS.get(role)
            if parent_role: bone.parent = edit[parent_role]
        bpy.ops.object.mode_set(mode="OBJECT")
        modifier = body.modifiers.new("Armature", "ARMATURE"); modifier.object = rig
        for name in (prefix + suffix for suffix in MIXAMO_SUFFIXES.values()):
            body.vertex_groups.new(name=name)
        result = inspect_mixamo_preflight(rig.name, scene.name)
        check("signature_detected", result["status"] == "ok" and result["candidate_prefixes"] == [prefix])
        check("humanoid_mapping", result["humanoid"]["status"] == "ok")
        check("bound_mesh", len(result["bound_meshes"]) == 1 and not result["bound_meshes"][0]["missing_mapped_vertex_groups"])
        group = body.vertex_groups.get(prefix + "LeftHand"); body.vertex_groups.remove(group)
        check("missing_group_review", any("vertex groups" in x for x in inspect_mixamo_preflight(rig.name, scene.name)["reviews"]))
        body.vertex_groups.new(name=prefix + "LeftHand")
        rig.scale.x = 2
        check("transform_review", any("not identity" in x for x in inspect_mixamo_preflight(rig.name, scene.name)["reviews"]))
        rig.scale.x = 1
        check("wrong_prefix_incomplete", inspect_mixamo_preflight(rig.name, scene.name, "wrong:")["status"] == "incomplete")
        bpy.ops.object.mode_set(mode="EDIT")
        check("edit_mode_refused", inspect_mixamo_preflight(rig.name, scene.name)["status"] == "error")
        bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
    finally:
        if window.scene == scene and bpy.context.mode != "OBJECT": bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for item in (rig, body, data, mesh, scene):
            if item.get("gameassetai_test_owner") != token: raise RuntimeError("Mixamo fixture ownership changed")
        bpy.data.objects.remove(body, do_unlink=True); bpy.data.objects.remove(rig, do_unlink=True)
        if mesh.users or data.users: raise RuntimeError("Mixamo fixture datablock users changed")
        bpy.data.meshes.remove(mesh); bpy.data.armatures.remove(data); bpy.data.scenes.remove(scene)
    after = (sorted(bpy.data.scenes.keys()), sorted(bpy.data.objects.keys()),
             sorted(bpy.data.meshes.keys()), sorted(bpy.data.armatures.keys()))
    check("original_state_restored", before == after)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "blender_version": bpy.app.version_string}
