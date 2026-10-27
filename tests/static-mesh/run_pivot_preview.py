"""Native explicit-pivot preview/apply regression, synthetic exact-owned IDs only."""
import uuid
import bpy
from mathutils import Matrix, Euler, Vector


def run_pivot_preview_tests():
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Object mode required; do not force mode")
    original = bpy.context.scene
    fingerprint = source_fingerprint(original)
    tracked = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    names = [[i.name for i in c] for c in tracked]
    token = uuid.uuid4().hex
    scene = bpy.data.scenes.new("GAI_Pivot_" + token)
    mesh = bpy.data.meshes.new("GAI_PivotMesh_" + token)
    obj = bpy.data.objects.new("GAI_PivotObject_" + token, mesh)
    for item in (scene, obj, mesh):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(obj)
    shared = bpy.data.objects.new("GAI_PivotShared_" + token, mesh)
    shared["gameassetai_test_owner"] = token
    scene.collection.objects.link(shared)
    mesh.from_pydata([(2, 0, 0), (4, 0, 0), (4, 2, 1), (2, 2, 1)], [],
                     [(0, 1, 2), (0, 2, 3)])
    layer = mesh.uv_layers.new(name="PivotUV")
    for item, uv in zip(layer.data, ((0, 0), (1, 0), (1, 1), (0, 0), (1, 1), (0, 1))):
        item.uv = uv
    second_layer = mesh.uv_layers.new(name="PivotUV2")
    for item, uv in zip(second_layer.data, ((.1, .2), (.9, .2), (.9, .8), (.1, .2), (.9, .8), (.1, .8))):
        item.uv = uv
    mesh.uv_layers.active = layer
    layer.active_render = True
    second_layer.active_render = False
    mats = [bpy.data.materials.new("GAI_PivotMat_" + token + "_" + str(i)) for i in range(2)]
    for mat in mats:
        mat["gameassetai_test_owner"] = token
        mesh.materials.append(mat)
    mesh.polygons[1].material_index = 1
    obj.matrix_world = Matrix.LocRotScale(Vector((7, -2, 3)), Euler((.2, .4, .1)).to_quaternion(), Vector((2, 3, .5)))
    checks = []
    outputs = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    def preview(point, tolerance=1e-5):
        return preview_pivot_copy(obj.name, local_pivot=point, geometry_tolerance=tolerance, scene_name=scene.name)
    try:
        before = source_fingerprint(scene)
        ids = [[i.name for i in c] for c in tracked]
        shared_vertices = [tuple(v.co) for v in shared.data.vertices]
        result = preview([3, 1, .5])
        source_transform = inspect_static_transform(obj.name, scene_name=scene.name)
        check("explicit_preview", result["status"] == "preview" and result["mutation_authorized"] is False)
        check("world_preserved_prediction", result["maximum_position_error"] <= 1e-5)
        check("origin_prediction", (Vector(result["predicted_world_origin"]) - obj.matrix_world @ Vector((3, 1, .5))).length <= 1e-5)
        check("mesh_shift_not_object_translation", result["predicted_vertices"][0] == [-1, -1, -.5])
        check("scale_not_applied", result["scale_preserved"] == list(obj.scale))
        args = dict(local_pivot=[3, 1, .5], geometry_tolerance=1e-5, scene_name=scene.name)
        check("verify_fresh", verify_pivot_preview(obj.name, expected_source_sha256=result["source_sha256"], **args)["status"] == "preview")
        check("verify_missing", verify_pivot_preview(obj.name, expected_source_sha256=None, **args)["status"] == "error")
        check("candidate_bound", preview([3, 1, 0])["source_sha256"] != result["source_sha256"])
        check("tolerance_bound", preview([3, 1, .5], 1e-4)["source_sha256"] != result["source_sha256"])
        mesh.vertices[0].co.x += 1
        check("stale_geometry", verify_pivot_preview(obj.name, expected_source_sha256=result["source_sha256"], **args)["status"] == "error")
        mesh.vertices[0].co.x -= 1
        check("zero_candidate_no_change", preview([0, 0, 0])["status"] == "no_change")
        check("explicit_object_required", preview_pivot_copy("", **args)["status"] == "error")
        check("scene_scope_required", preview_pivot_copy(obj.name, local_pivot=[3, 1, .5], geometry_tolerance=1e-5, scene_name=original.name)["status"] == "error")
        for tolerance in (0, -1, True, float("nan"), float("inf")):
            check("invalid_tolerance_" + str(len(checks)), preview([3, 1, .5], tolerance)["status"] == "error")
        obj.delta_location.x = 1
        check("delta_refused", preview([3, 1, .5])["status"] == "error")
        obj.delta_location.x = 0
        saved_scale = obj.scale.copy()
        obj.scale.x = -obj.scale.x
        check("reflection_refused", preview([3, 1, .5])["status"] == "error")
        obj.scale = saved_scale
        for point in (None, [], [1, 2], [1, 2, 3, 4], [True, 0, 0], [float("nan"), 0, 0], [float("inf"), 0, 0], [1e39, 0, 0]):
            check("invalid_point_" + str(len(checks)), preview(point)["status"] == "error")
        check("snapshot_preserved", source_fingerprint(scene) == before and ids == [[i.name for i in c] for c in tracked])
        saved = obj.matrix_world.copy()
        obj.matrix_world = Matrix.Identity(4)
        check("stale_world", verify_pivot_preview(obj.name, expected_source_sha256=result["source_sha256"], **args)["status"] == "error")
        obj.matrix_world = saved
        result = preview([3, 1, .5])
        def apply(**overrides):
            params = dict(local_pivot=[3, 1, .5], geometry_tolerance=1e-5,
                          expected_source_sha256=result["source_sha256"], result_name="GAI_PivotCopy_" + token,
                          authorized=True, scene_name=scene.name)
            params.update(overrides)
            response = apply_pivot_copy(obj.name, **params)
            if response["status"] == "created":
                new_obj = bpy.data.objects[response["object"]]
                new_mesh = bpy.data.meshes[response["mesh"]]
                assert new_obj.get("gameassetai_copy_owner") == new_mesh.get("gameassetai_copy_owner") == response["owner_token"]
                new_obj["gameassetai_test_owner"] = new_mesh["gameassetai_test_owner"] = token
                outputs.append((new_obj, new_mesh))
            return response
        check("apply_auth_refused", apply(authorized=False)["status"] == "error")
        check("apply_stale_refused", apply(expected_source_sha256=None)["status"] == "error")
        applied = apply()
        check("apply_created", applied["status"] == "created")
        copy_obj, copy_mesh = outputs[-1]
        check("apply_independent", copy_obj != obj and copy_mesh != mesh and copy_obj.data == copy_mesh)
        check("shared_source_mesh_retained", obj.data == shared.data == mesh
              and copy_obj.data != shared.data and mesh.users == 2)
        check("shared_coordinates_retained", shared_vertices == [tuple(v.co) for v in shared.data.vertices])
        check("apply_source_preserved", inspect_static_transform(obj.name, scene_name=scene.name) == source_transform
              and verify_pivot_preview(obj.name, expected_source_sha256=result["source_sha256"], **args)["status"] == "preview")
        check("apply_uv_topology", _pivot_surface(copy_obj) == _pivot_surface(obj))
        check("two_faces_materials", len(copy_mesh.polygons) == 2
              and [face.material_index for face in copy_mesh.polygons] == [0, 1]
              and [slot.material for slot in copy_obj.material_slots] == mats)
        check("two_uv_layers_state", len(copy_mesh.uv_layers) == 2
              and copy_mesh.uv_layers.active_index == mesh.uv_layers.active_index
              and [layer.active_render for layer in copy_mesh.uv_layers] == [True, False])
        check("apply_world_positions", all((copy_obj.matrix_world @ a.co - obj.matrix_world @ b.co).length <= 1e-5 for a, b in zip(copy_mesh.vertices, mesh.vertices)))
        check("apply_origin", (copy_obj.matrix_world.translation - obj.matrix_world @ Vector((3, 1, .5))).length <= 1e-5)
        check("apply_scale_rotation_preserved", tuple(copy_obj.scale) == tuple(obj.scale) and tuple(copy_obj.rotation_euler) == tuple(obj.rotation_euler))
        check("apply_collision_refused", apply()["status"] == "error")
        current_ids = [[i.name for i in c] for c in tracked]
        for kind in ("write", "linked_uv", "linked_scale", "linked_mesh", "linked_vertex", "link"):
            namespace = apply_pivot_copy.__globals__
            target = "_pivot_write" if kind == "write" else "_pivot_link"
            original_function = namespace[target]
            def injected(*a):
                if kind == "write":
                    raise RuntimeError("Injected pivot write failure")
                original_function(*a)
                if kind == "linked_uv":
                    a[1].data.uv_layers[0].data[0].uv.x = 25
                elif kind == "linked_scale":
                    a[1].scale = (1, 1, 1)
                elif kind == "linked_mesh":
                    a[1].data = mesh
                elif kind == "linked_vertex":
                    import bmesh
                    bm = bmesh.new()
                    try:
                        bm.from_mesh(a[1].data)
                        bm.verts.new((25, 25, 25))
                        bm.to_mesh(a[1].data)
                    finally:
                        bm.free()
                else:
                    raise RuntimeError("Injected pivot link failure")
            try:
                namespace[target] = injected
                failed = apply(result_name="GAI_PivotFailure_" + token)
            finally:
                namespace[target] = original_function
            check("apply_rollback_" + kind, failed["status"] == "error" and failed["failure_cleanup"] == "complete" and current_ids == [[i.name for i in c] for c in tracked])
        zero = preview([0, 0, 0])
        check("apply_no_change", apply(local_pivot=[0, 0, 0], expected_source_sha256=zero["source_sha256"], result_name="GAI_PivotZero_" + token)["status"] == "no_change")
        # Temporary blockers are added only to owned synthetic IDs and removed exactly.
        blocker_ids = [[i.name for i in c] for c in tracked]
        obj.animation_data_create()
        check("source_animation_preview_refused", preview([3, 1, .5])["status"] == "error")
        check("source_animation_apply_refused", apply(result_name="GAI_AnimBlocked_" + token)["status"] == "error")
        obj.animation_data_clear()
        blocker = obj.constraints.new("COPY_LOCATION")
        check("constraint_preview_refused", preview([3, 1, .5])["status"] == "error")
        check("constraint_apply_refused", apply(result_name="GAI_ConstraintBlocked_" + token)["status"] == "error")
        obj.constraints.remove(blocker)
        modifier = obj.modifiers.new("GAI_PivotBlocker", "BEVEL")
        check("modifier_preview_refused", preview([3, 1, .5])["status"] == "error")
        check("modifier_apply_refused", apply(result_name="GAI_ModifierBlocked_" + token)["status"] == "error")
        obj.modifiers.remove(modifier)
        group = obj.vertex_groups.new(name="GAI_PivotGroup")
        check("weights_preview_refused", preview([3, 1, .5])["status"] == "error")
        obj.vertex_groups.remove(group)
        scene.animation_data_create()
        check("filewide_animation_apply_refused", apply(result_name="GAI_FileAnimBlocked_" + token)["status"] == "error")
        scene.animation_data_clear()
        check("source_recovered_after_blockers", verify_pivot_preview(obj.name, expected_source_sha256=result["source_sha256"], **args)["status"] == "preview")
        check("blocker_ids_restored", blocker_ids == [[i.name for i in c] for c in tracked])
    finally:
        for output_obj, output_mesh in outputs:
            assert output_obj.get("gameassetai_test_owner") == output_mesh.get("gameassetai_test_owner") == token
            assert list(output_obj.users_collection) == [scene.collection] and output_obj.users == 1
            bpy.data.objects.remove(output_obj, do_unlink=True)
            assert output_mesh.users == 0
            bpy.data.meshes.remove(output_mesh)
        assert shared.get("gameassetai_test_owner") == token
        assert shared.data == mesh and list(shared.users_collection) == [scene.collection]
        bpy.data.objects.remove(shared, do_unlink=True)
        assert all(i.get("gameassetai_test_owner") == token for i in (scene, obj, mesh))
        assert obj.data == mesh and list(obj.users_collection) == [scene.collection] and obj.users == 1
        bpy.data.objects.remove(obj, do_unlink=True)
        assert mesh.users == 0
        bpy.data.meshes.remove(mesh)
        for mat in mats:
            assert mat.get("gameassetai_test_owner") == token and mat.users == 0
            bpy.data.materials.remove(mat)
        bpy.data.scenes.remove(scene)
    check("original_preserved", source_fingerprint(original) == fingerprint)
    check("ids_restored", names == [[i.name for i in c] for c in tracked])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "source_fingerprint": fingerprint}
