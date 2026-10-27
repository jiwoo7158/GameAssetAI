"""Run inside Blender after loading inspect_asset.py. Own only exact synthetic IDs."""
import hashlib
import uuid


def fingerprint_action_curves(action):
    curves = list(getattr(action, "fcurves", ()))
    for layer in getattr(action, "layers", ()):
        for strip in layer.strips:
            for bag in getattr(strip, "channelbags", ()):
                curves.extend(bag.fcurves)
    return curves


def source_fingerprint(scene):
    facts = inspect_scene(scene_name=scene.name)
    geometry = {}
    for obj in scene.objects:
        if obj.type == "MESH" and not obj.data.is_editmode:
            geometry[obj.name] = {
                "vertices": [list(v.co) for v in obj.data.vertices],
                "edges": [list(e.vertices) for e in obj.data.edges],
                "polygons": [list(p.vertices) for p in obj.data.polygons],
                "uvs": [[list(item.uv) for item in layer.data] for layer in obj.data.uv_layers],
                "weights": [[(g.group, g.weight) for g in v.groups] for v in obj.data.vertices],
                "keys": [[list(v.co) for v in key.data] for key in obj.data.shape_keys.key_blocks]
                        if obj.data.shape_keys else [],
            }
        elif obj.type == "ARMATURE":
            geometry[obj.name] = {
                "rest_matrices": [[list(row) for row in bone.matrix_local] for bone in obj.data.bones],
                "pose_basis": [[list(row) for row in bone.matrix_basis] for bone in obj.pose.bones],
            }
    actions = []
    for action in bpy.data.actions:
        curves = fingerprint_action_curves(action)
        actions.append({"name": action.name, "curves": [
            {"path": curve.data_path, "index": curve.array_index,
             "points": [{"co": list(point.co), "left": list(point.handle_left),
                         "right": list(point.handle_right), "interpolation": point.interpolation}
                        for point in curve.keyframe_points]} for curve in curves]})
    context = {"scene": bpy.context.scene.name, "mode": bpy.context.mode,
               "active": bpy.context.view_layer.objects.active.name
                         if bpy.context.view_layer.objects.active else None,
               "selected": sorted(o.name for o in bpy.context.selected_objects),
               "frame": scene.frame_current, "subframe": scene.frame_subframe}
    payload = json.dumps([facts, geometry, context, actions], sort_keys=True, allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def run_inspection_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Synthetic fixture tests require an Object-mode window; do not force user mode")
    token = uuid.uuid4().hex
    original_scene = bpy.context.scene
    original_layer = bpy.context.view_layer
    window = bpy.context.window
    before = source_fingerprint(original_scene)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.armatures,
                   bpy.data.materials, bpy.data.actions, bpy.data.shape_keys)
    id_names_before = [[id.name for id in collection] for collection in collections]
    owned = []
    checks = []

    def own(id, collection):
        id["gameassetai_test_owner"] = token
        owned.append((id, collection))
        return id

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    fixture = own(bpy.data.scenes.new("GAI_Inspection_" + token), bpy.data.scenes)
    try:
        report = inspect_scene(scene_name=fixture.name)
        check("empty_scene", report["status"] == "ok" and report["object_count"] == 0)
        check("missing_scene", inspect_scene(scene_name="__missing_" + token)["status"] == "error")
        check("invalid_scene_name", inspect_scene(scene_name=[])["status"] == "error")
        check("invalid_scope", inspect_scene(scope="all")["status"] == "error")
        mesh = own(bpy.data.meshes.new("GAI_Mesh_" + token), bpy.data.meshes)
        mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
        obj = own(bpy.data.objects.new("GAI_Animated_" + token, mesh), bpy.data.objects)
        fixture.collection.objects.link(obj)
        shared = own(bpy.data.objects.new("GAI_Shared_" + token, mesh), bpy.data.objects)
        fixture.collection.objects.link(shared)
        material = own(bpy.data.materials.new("GAI_Material_" + token), bpy.data.materials)
        material.use_nodes = True
        mesh.materials.append(material)
        obj.shape_key_add(name="Basis")
        obj.shape_key_add(name="TestShape")
        rig_data = own(bpy.data.armatures.new("GAI_RigData_" + token), bpy.data.armatures)
        rig = own(bpy.data.objects.new("GAI_Rig_" + token, rig_data), bpy.data.objects)
        fixture.collection.objects.link(rig)

        # Operators affect only this owned scene. Read enum values before use.
        window.scene = fixture
        fixture.view_layers[0].objects.active = rig
        rig.select_set(True)
        modes = {item.identifier for item in bpy.ops.object.mode_set.get_rna_type().properties["mode"].enum_items}
        check("mode_enum_available", {"EDIT", "OBJECT"}.issubset(modes))
        bpy.ops.object.mode_set(mode="EDIT")
        root = rig_data.edit_bones.new("Root")
        root.head = (0, 0, 0)
        root.tail = (0, 0, 1)
        root.use_deform = False
        child = rig_data.edit_bones.new("Child")
        child.head = (0, 0, 1)
        child.tail = (0, 0, 2)
        child.parent = root
        editing = inspect_scene(object_names=[rig.name])
        check("armature_edit_mode_uncertainty", editing["objects"][0]["armature"]["status"] == "unverified")
        check("armature_edit_mode_preserved", bpy.context.mode == "EDIT_ARMATURE")
        bpy.ops.object.mode_set(mode="OBJECT")
        types = {item.identifier for item in bpy.types.ObjectModifiers.bl_rna.functions["new"].parameters["type"].enum_items}
        check("modifier_enum_available", "ARMATURE" in types)
        mod = obj.modifiers.new("ExistingRig", "ARMATURE")
        mod.object = rig
        obj.keyframe_insert(data_path="location", frame=1)
        obj.location.x = 1
        obj.keyframe_insert(data_path="location", frame=10)
        action = own(obj.animation_data.action, bpy.data.actions)
        obj.animation_data.nla_tracks.new().strips.new("ExistingAnimation", 20, action)
        fixture.frame_set(1)

        report = inspect_scene(scene_name=fixture.name)
        check("fixture_status", report["status"] == "ok")
        objects = {o["name"]: o for o in report["objects"]}
        inspected_mesh = objects[obj.name]["base_mesh"]
        check("base_mesh_counts", (inspected_mesh["vertices"], inspected_mesh["polygons"],
                                  inspected_mesh["triangles"]) == (4, 1, 2))
        check("shared_mesh_preserved", inspected_mesh["users"] == 2 and shared.data == obj.data)
        check("shape_key_inventory", inspected_mesh["shape_keys"] == ["Basis", "TestShape"])
        check("material_inventory", report["materials"][0]["name"] == material.name)
        bones = objects[rig.name]["armature"]["bones"]
        check("bone_parent_and_deform", len(bones) == 2 and bones[0]["use_deform"] is False
              and bones[1]["parent"] == "Root")
        check("armature_modifier_target", objects[obj.name]["modifiers"][0]["object"] == rig.name)
        animation = objects[obj.name]["object_animation"]
        check("action_binding", animation["action"] == action.name)
        check("nla_action_binding", animation["nla_tracks"][0]["strips"][0]["action"] == action.name)
        check("file_action_inventory", any(a["name"] == action.name for a in report["file_actions"]))
        fixture_before = source_fingerprint(fixture)
        curves = fingerprint_action_curves(action)
        check("action_curve_fingerprint_available", bool(curves and curves[0].keyframe_points))
        point = curves[0].keyframe_points[0]
        original_value = point.co.y
        point.co.y += 0.125
        check("fingerprint_detects_keyframe_change", source_fingerprint(fixture) != fixture_before)
        point.co.y = original_value
        check("keyframe_fixture_restored", source_fingerprint(fixture) == fixture_before)
        check("named_scope", inspect_scene(object_names=[obj.name, obj.name])["targets"] == [obj.name])
        check("missing_named_target", inspect_scene(object_names=["__missing_" + token])["status"] == "error")
        check("empty_name_list", inspect_scene(object_names=[])["status"] == "error")
        check("read_only_fixture", source_fingerprint(fixture) == fixture_before)
        shared.location.x = float("nan")
        partial = inspect_scene(object_names=[shared.name])
        check("nonfinite_partial", partial["status"] == "partial" and partial["objects"][0]["location"][0] is None)
        check("nonfinite_json", bool(json.dumps(partial, allow_nan=False)))
        shared.location.x = 0
        globals_ = inspect_scene.__globals__
        original_object = globals_["_object"]
        def fail_object(obj):
            raise RuntimeError("simulated object inspection failure")
        try:
            globals_["_object"] = fail_object
            check("individual_failure_partial", inspect_scene(object_names=[shared.name])["status"] == "partial")
        finally:
            globals_["_object"] = original_object
        rig.select_set(False)
        shared.select_set(True)
        check("selected_scope", inspect_scene(scope="selected")["targets"] == [shared.name])
        shared.select_set(False)
        check("empty_selection_error", inspect_scene(scope="selected")["status"] == "error")

        fixture.view_layers[0].objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        report = inspect_scene(object_names=[obj.name])
        check("edit_mode_uncertainty", report["objects"][0]["base_mesh"]["status"] == "unverified")
        check("edit_mode_not_changed", bpy.context.mode == "EDIT_MESH")
        bpy.ops.object.mode_set(mode="OBJECT")
        obj.select_set(False)
        obj.location.x += 0.25
        check("harmless_fixture_transform", abs(obj.location.x - 0.25) < 1e-6)
        obj.location.x -= 0.25
        check("fixture_transform_restored", abs(obj.location.x) < 1e-6)
        window.scene = original_scene
        window.view_layer = original_layer
    finally:
        if window.scene == fixture and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene = original_scene
        window.view_layer = original_layer
        # Inspect all IDs before removing anything; never delete by prefix/name wildcard.
        owned_objects = [id for id, collection in owned if collection == bpy.data.objects]
        for id, collection in owned:
            if collection.get(id.name) != id or id.get("gameassetai_test_owner") != token:
                raise RuntimeError("Fixture ownership changed; cleanup aborted")
        for obj in owned_objects:
            if any(collection != fixture.collection for collection in obj.users_collection):
                raise RuntimeError("Fixture object gained external links; cleanup aborted")
        for obj in owned_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        for collection in (bpy.data.meshes, bpy.data.armatures, bpy.data.actions, bpy.data.materials):
            for id, owner_collection in owned:
                if owner_collection == collection:
                    if id.users != 0:
                        raise RuntimeError("Fixture datablock has unexpected users; cleanup aborted")
                    collection.remove(id)
        bpy.data.scenes.remove(fixture)
    check("original_scene_fingerprint_preserved", source_fingerprint(original_scene) == before)
    check("all_datablock_names_restored", id_names_before == [[id.name for id in c] for c in collections])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "source_fingerprint": before, "fixture_cleanup": "complete",
            "blender_version": bpy.app.version_string}
