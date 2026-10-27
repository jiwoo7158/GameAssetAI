"""Native read-only transform-preflight regression on exact owned synthetic IDs."""
import uuid
from mathutils import Matrix, Euler, Vector


def run_transform_preflight_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Object-mode window required; do not force mode")
    original = bpy.context.scene
    fingerprint = source_fingerprint(original)
    tracked = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials,
               bpy.data.actions, bpy.data.shape_keys)
    names = [[item.name for item in items] for items in tracked]
    token = uuid.uuid4().hex
    fixture = bpy.data.scenes.new("GAI_Transform_" + token)
    fixture["gameassetai_test_owner"] = token
    owned = []
    checks = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    def own(item, collection):
        item["gameassetai_test_owner"] = token
        owned.append((item, collection))
        return item
    def inspect(obj):
        before = source_fingerprint(fixture)
        before_names = [[item.name for item in items] for items in tracked]
        result = inspect_static_transform(obj.name, scene_name=fixture.name)
        check("readonly_" + str(len(checks)), before == source_fingerprint(fixture)
              and before_names == [[item.name for item in items] for items in tracked])
        return result
    try:
        mesh = own(bpy.data.meshes.new("GAI_TransformMesh_" + token), bpy.data.meshes)
        mesh.from_pydata([(2, 0, 0), (4, 0, 0), (2, 2, 0)], [], [(0, 1, 2)])
        obj = own(bpy.data.objects.new("GAI_TransformObject_" + token, mesh), bpy.data.objects)
        fixture.collection.objects.link(obj)
        obj.matrix_world = Matrix.Identity(4)
        report = inspect(obj)
        check("identity_snapshot", report["status"] == "ok" and report["review_items"] == [])
        check("offset_bounds_not_pivot_target", report["local_base_bounds"]["center"] == [3, 1, 0]
              and report["local_origin"] == [0, 0, 0])
        check("no_export_or_mutation_claim", report["export_ready"] is None
              and report["mutation_authorized"] is False and report["freshness"] == "snapshot_only")
        obj.matrix_world = Matrix.Diagonal((-2, 3, 1, 1))
        report = inspect(obj)
        check("mirrored_nonuniform", {"nonunit_local_scale", "nonuniform_local_scale",
              "reported_world_reflection"}.issubset(report["review_items"]))
        obj.matrix_world = Matrix.Diagonal((0, 1, 1, 1))
        report = inspect(obj)
        check("singular", "reported_world_singular" in report["review_items"])
        obj.matrix_world = Matrix.Identity(4)
        parent = own(bpy.data.objects.new("GAI_TransformParent_" + token, None), bpy.data.objects)
        fixture.collection.objects.link(parent)
        obj.parent = parent
        report = inspect(obj)
        check("parent_dependency", report["parent"] == parent.name
              and "parent_dependency" in report["review_items"])
        obj.parent = None
        constraint = obj.constraints.new("COPY_LOCATION")
        report = inspect(obj)
        check("constraint_not_evaluated", "constraints_or_modifiers_not_evaluated" in report["review_items"])
        obj.constraints.remove(constraint)
        obj.vertex_groups.new(name="Preserve")
        report = inspect(obj)
        check("bindings", "preservation_sensitive_bindings" in report["review_items"])
        obj.vertex_groups.clear()
        # Capability experiment ONLY: explicit synthetic source, no workflow/apply API.
        material = own(bpy.data.materials.new("GAI_TransformMaterial_" + token), bpy.data.materials)
        mesh.materials.append(material)
        uv = mesh.uv_layers.new(name="ScaleUV")
        for item, value in zip(uv.data, [(0, 0), (1, 0), (0, 1)]):
            item.uv = value
        obj.matrix_world = Matrix.Diagonal((-2, 3, 0.5, 1))
        original_positions = [tuple(v.co) for v in mesh.vertices]
        original_scale = tuple(obj.scale)
        original_basis = obj.matrix_basis.copy()
        original_uv = [tuple(item.uv) for item in uv.data]
        original_face = [tuple(p.vertices) for p in mesh.polygons]
        before_positions = [original_basis @ v.co for v in mesh.vertices]
        copied_mesh = own(mesh.copy(), bpy.data.meshes)
        copied = own(obj.copy(), bpy.data.objects)
        copied.data = copied_mesh
        fixture.collection.objects.link(copied)
        copied_mesh.transform(Matrix.Diagonal((*original_scale, 1)))
        copied.scale = (1, 1, 1)
        after_positions = [copied.matrix_basis @ v.co for v in copied_mesh.vertices]
        check("scale_copy_independent", copied != obj and copied_mesh != mesh)
        check("scale_copy_unit_channels", tuple(copied.scale) == (1, 1, 1))
        check("scale_copy_local_basis_positions", all((a-b).length <= 1e-6
              for a, b in zip(before_positions, after_positions)))
        check("scale_copy_uv_material_topology", [tuple(item.uv) for item in copied_mesh.uv_layers[0].data] == original_uv
              and copied_mesh.materials[0] == material
              and [tuple(p.vertices) for p in copied_mesh.polygons] == original_face)
        check("scale_source_preserved", [tuple(v.co) for v in mesh.vertices] == original_positions
              and tuple(obj.scale) == original_scale and obj.matrix_basis == original_basis
              and [tuple(item.uv) for item in uv.data] == original_uv)
        # Edit the copied mesh to directly verify independence, not merely distinct names.
        copied_mesh.vertices[0].co.z += 1
        check("scale_copy_edit_independent", [tuple(v.co) for v in mesh.vertices] == original_positions)
        # Restore synthetic source before the unrelated refusal tests; copied data stays owned.
        obj.matrix_world = Matrix.Identity(4)
        coordinate = tuple(mesh.vertices[0].co)
        # Analytic preview/freshness guard, still no reusable apply or new output IDs.
        obj.location = (3, 4, 5)
        second_uv = mesh.uv_layers.new(name="SecondScaleUV")
        for item, value in zip(second_uv.data, [(2, 0), (3, 0), (2, 1)]):
            item.uv = value
        obj.rotation_euler = (0.1, 0.2, 0.3)
        obj.scale = (2, 3, 0.5)
        snapshot = source_fingerprint(fixture)
        snapshot_ids = [[item.name for item in items] for items in tracked]
        preview = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)
        check("scale_preview", preview["status"] == "preview")
        check("scale_preview_readonly", source_fingerprint(fixture) == snapshot
              and snapshot_ids == [[item.name for item in items] for items in tracked])
        check("scale_preview_not_permission", preview["mutation_authorized"] is False
              and preview["export_ready"] is None)
        check("scale_preview_prediction", preview["predicted_vertices"][0] == [4, 0, 0]
              and preview["predicted_scale"] == [1, 1, 1])
        def verify(digest, tolerance=1e-5):
            return verify_scale_preview(obj.name, scene_name=fixture.name,
                         expected_source_sha256=digest, geometry_tolerance=tolerance)
        digest = preview["source_sha256"]
        old_active = mesh.uv_layers.active_index
        mesh.uv_layers.active_index = 1 - old_active
        check("scale_preview_active_uv_bound", verify(digest)["status"] == "error")
        mesh.uv_layers.active_index = old_active
        check("scale_preview_current", verify(digest)["freshness"] == "matches_current_supported_snapshot")
        check("scale_preview_missing_hash", verify(None)["status"] == "error")
        mesh.vertices[0].co.z += 1
        check("scale_preview_stale_geometry", verify(digest)["status"] == "error")
        mesh.vertices[0].co = coordinate
        obj.location.x += 1
        check("scale_preview_stale_transform", verify(digest)["status"] == "error")
        obj.location.x = 3
        uv.data[0].uv.x = 0.25
        check("scale_preview_stale_uv", verify(digest)["status"] == "error")
        uv.data[0].uv = (0, 0)
        mesh.edges[0].use_seam = True
        check("scale_preview_stale_edge_flags", verify(digest)["status"] == "error")
        mesh.edges[0].use_seam = False
        uv.data[0].uv.x = float("nan")
        check("scale_preview_nonfinite_uv", verify(digest)["status"] == "error")
        uv.data[0].uv = (0, 0)
        check("scale_preview_parameter_bound", verify(digest, 2e-5)["status"] == "error")
        old_name = fixture.name
        fixture.name = old_name + "_renamed"
        check("scale_preview_scene_bound", verify(digest)["status"] == "error")
        fixture.name = old_name
        check("scale_preview_exact_restoration", verify(digest)["status"] == "preview")
        for tolerance in (True, 0, -1, float("nan"), None):
            check("scale_preview_bad_tolerance_" + str(len(checks)),
                  preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=tolerance)["status"] == "error")
        obj.scale.x = -2
        check("scale_preview_reflection_refused", preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "error")
        obj.scale.x = 0
        check("scale_preview_zero_refused", preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "error")
        obj.scale = (1, 1, 1)
        check("scale_preview_no_change", preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "no_change")
        obj.delta_scale = (2, 1, 1)
        check("scale_preview_delta_refused", preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "error")
        obj.delta_scale = (1, 1, 1)
        obj.parent = parent
        check("scale_preview_parent_refused", preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "error")
        obj.parent = None
        check("scale_preview_no_new_ids", snapshot_ids == [[item.name for item in items] for items in tracked])
        # Actual apply scope: deterministic directly reported world/basis from explicit matrix.
        obj.matrix_world = Matrix.Diagonal((2, 3, 0.5, 1))
        fresh_preview = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)
        apply_digest = fresh_preview["source_sha256"]
        def apply(**options):
            args = dict(result_name="GAI_ScaleApply_" + token, expected_source_sha256=apply_digest,
                        geometry_tolerance=1e-5, authorized=True, scene_name=fixture.name)
            args.update(options)
            return apply_scale_copy(obj.name, **args)
        pre_apply = source_fingerprint(fixture)
        check("scale_apply_no_authorization", apply(authorized=False)["status"] == "error")
        check("scale_apply_invalid_authorization", apply(authorized="yes")["status"] == "error")
        check("scale_apply_missing_hash", apply(expected_source_sha256=None)["status"] == "error")
        check("scale_apply_stale_hash", apply(expected_source_sha256="stale")["status"] == "error")
        for invalid in ("", "\x00", "x" * 64):
            check("scale_apply_invalid_name_" + str(len(checks)), apply(result_name=invalid)["status"] == "error")
        parent.animation_data_create()
        check("scale_apply_empty_animation_guard", apply()["status"] == "error")
        parent.animation_data_clear()
        check("scale_apply_initial_refusals_no_changes", source_fingerprint(fixture) == pre_apply
              and snapshot_ids == [[item.name for item in items] for items in tracked])
        source_coordinates = [tuple(v.co) for v in mesh.vertices]
        report = apply()
        if report["status"] != "created":
            raise AssertionError("scale apply failed: " + str(report))
        check("scale_apply_created", True)
        output = own(bpy.data.objects[report["object"]], bpy.data.objects)
        output_mesh = own(output.data, bpy.data.meshes)
        check("scale_apply_independent", output_mesh != mesh and tuple(output.scale) == (1, 1, 1))
        check("scale_apply_source_preserved", source_coordinates == [tuple(v.co) for v in mesh.vertices]
              and tuple(obj.scale) == (2, 3, 0.5))
        check("scale_apply_uv_material_retained", _scale_surface(output) == _scale_surface(obj))
        check("scale_apply_world_positions", all((output.matrix_world @ a.co - obj.matrix_world @ b.co).length <= 1e-5
              for a, b in zip(output_mesh.vertices, mesh.vertices)))
        check("scale_apply_collision", apply()["status"] == "error")
        obj.matrix_world = Matrix.LocRotScale(Vector((3, 4, 5)), Euler((0.1, 0.2, 0.3)).to_quaternion(), Vector((2, 3, 0.5)))
        apply_digest = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["source_sha256"]
        rotated_report = apply(result_name="GAI_RotatedScale_" + token)
        if rotated_report["status"] != "created":
            raise AssertionError("rotated scale apply failed: " + str(rotated_report))
        rotated_output = own(bpy.data.objects[rotated_report["object"]], bpy.data.objects)
        own(rotated_output.data, bpy.data.meshes)
        check("scale_apply_rotated_translated_world", all((rotated_output.matrix_world @ a.co - obj.matrix_world @ b.co).length <= 1e-5
              for a, b in zip(rotated_output.data.vertices, mesh.vertices)))
        check("scale_apply_rotated_pivot_channels", tuple(rotated_output.location) == tuple(obj.location)
              and tuple(rotated_output.rotation_euler) == tuple(obj.rotation_euler)
              and (rotated_output.matrix_world.translation - obj.matrix_world.translation).length <= 1e-5)
        # Representative shading-direction test on tilted synthetic triangle only.
        mesh.vertices[2].co.z = 1
        mesh.update()
        apply_digest = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["source_sha256"]
        shading_report = apply(result_name="GAI_ShadingScale_" + token)
        if shading_report["status"] != "created":
            raise AssertionError("tilted scale apply failed: " + str(shading_report))
        shading_output = own(bpy.data.objects[shading_report["object"]], bpy.data.objects)
        shading_mesh = own(shading_output.data, bpy.data.meshes)
        source_normal = (obj.matrix_world.to_3x3().inverted().transposed() @ mesh.polygons[0].normal).normalized()
        copy_normal = (shading_output.matrix_world.to_3x3().inverted().transposed() @ shading_mesh.polygons[0].normal).normalized()
        check("scale_tilted_world_normal", (source_normal - copy_normal).length <= 1e-5)
        mesh.calc_tangents(uvmap="ScaleUV")
        shading_mesh.calc_tangents(uvmap="ScaleUV")
        check("scale_tilted_world_tangents", all(((obj.matrix_world.to_3x3() @ a.tangent).normalized()
              - (shading_output.matrix_world.to_3x3() @ b.tangent).normalized()).length <= 1e-5
              for a, b in zip(mesh.loops, shading_mesh.loops)))
        check("scale_tilted_bitangent_signs", [loop.bitangent_sign for loop in mesh.loops]
              == [loop.bitangent_sign for loop in shading_mesh.loops])
        mesh.free_tangents()
        shading_mesh.free_tangents()
        mesh.vertices[2].co.z = 0
        mesh.update()
        apply_digest = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["source_sha256"]
        failure_ids = [[item.name for item in items] for items in tracked]
        namespace = apply_scale_copy.__globals__
        for kind in ("write", "corrupt", "nan", "link", "linked_uv", "linked_scale", "linked_mesh"):
            target = "_scale_link" if kind.startswith("link") else "_scale_write"
            original_function = namespace[target]
            def injected(*args, **kwargs):
                if kind == "write":
                    raise RuntimeError("injected scale write failure")
                original_function(*args, **kwargs)
                if kind == "corrupt":
                    args[0].vertices[0].co.z += 5
                elif kind == "nan":
                    args[0].vertices[0].co.z = float("nan")
                elif kind == "linked_uv":
                    args[1].data.uv_layers[0].data[0].uv.x = 25
                elif kind == "linked_scale":
                    args[1].scale = (2, 2, 2)
                elif kind == "linked_mesh":
                    args[1].data = mesh
                else:
                    raise RuntimeError("injected post-link failure")
            try:
                namespace[target] = injected
                failed = apply(result_name="GAI_ScaleFailure_" + token)
            finally:
                namespace[target] = original_function
            if failed.get("status") == "created":
                unexpected_object = bpy.data.objects[failed["object"]]
                unexpected_mesh = bpy.data.meshes[failed["mesh"]]
                assert unexpected_object.get("gameassetai_copy_owner") == failed["owner_token"]
                assert unexpected_mesh.get("gameassetai_copy_owner") == failed["owner_token"]
                own(unexpected_object, bpy.data.objects)
                own(unexpected_mesh, bpy.data.meshes)
            check("scale_apply_rollback_" + kind, failed["status"] == "error"
                  and failed["failure_cleanup"] == "complete"
                  and failure_ids == [[item.name for item in items] for items in tracked])
        output_mesh.vertices[0].co.z += 1
        check("scale_apply_edit_independent", source_coordinates == [tuple(v.co) for v in mesh.vertices])
        unrelated = parent.constraints.new("COPY_LOCATION")
        check("scale_apply_unrelated_constraint_guard", apply(result_name="GAI_Blocked_" + token)["status"] == "error")
        parent.constraints.remove(unrelated)
        obj.matrix_world = Matrix.Identity(4)
        no_change_hash = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)["source_sha256"]
        check("scale_apply_no_change", apply(result_name="GAI_NoScale_" + token,
              expected_source_sha256=no_change_hash)["status"] == "no_change")
        check("scale_apply_no_change_stale_refused", apply(result_name="GAI_NoScale_" + token)["status"] == "error")
        obj.matrix_world = Matrix.Identity(4)
        numeric_ids = [[item.name for item in items] for items in tracked]
        numeric_raw = inspect_static_transform(obj.name, scene_name=fixture.name)["raw_transform"]
        obj.scale = (1e38, 1, 1)
        overflow_preview = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)
        check("scale_preview_coordinate_overflow", overflow_preview["status"] == "error")
        for key, value in numeric_raw.items():
            setattr(obj, key, value)
        obj.scale = (1e-30, 1, 1)
        tiny_preview = preview_scale_copy(obj.name, scene_name=fixture.name, geometry_tolerance=1e-5)
        # Observation only: do not treat absolute residual tolerance as a conditioning test.
        numeric_probes = {"overflow": {"status": overflow_preview["status"], "errors": overflow_preview["errors"]},
                          "tiny_positive": {"status": tiny_preview["status"],
                              "normal_conditioning_certified": False, "apply_attempted": False}}
        check("scale_numeric_probes_no_ids", numeric_ids == [[item.name for item in items] for items in tracked])
        for key, value in numeric_raw.items():
            setattr(obj, key, value)
        obj.matrix_world = Matrix.Identity(4)
        mesh.vertices[0].co.x = float("nan")
        report = inspect_static_transform(obj.name, scene_name=fixture.name)
        check("nonfinite_withheld", report["status"] == "error" and "reported_matrices" not in report)
        mesh.vertices[0].co = coordinate
        euler = tuple(obj.rotation_euler)
        obj.rotation_euler.x = float("nan")
        report = inspect_static_transform(obj.name, scene_name=fixture.name)
        check("unflushed_raw_rotation_withheld", report["status"] == "error"
              and "reported_matrices" not in report)
        obj.rotation_euler = euler
        check("missing_target", inspect_static_transform("GAI_Missing_" + token, scene_name=fixture.name)["status"] == "error")
        check("missing_scene", inspect_static_transform(obj.name, scene_name="GAI_Missing_" + token)["status"] == "error")
        check("explicit_target", inspect_static_transform(None)["status"] == "error")
        window = bpy.context.window
        layer = bpy.context.view_layer
        try:
            window.scene = fixture
            fixture.view_layers[0].objects.active = obj
            obj.select_set(True)
            bpy.ops.object.mode_set(mode="EDIT")
            report = inspect_static_transform(obj.name, scene_name=fixture.name)
            check("edit_mode_refused", report["status"] == "error")
            check("edit_mode_retained", bpy.context.mode == "EDIT_MESH")
            check("scale_preview_edit_mode_refused", preview_scale_copy(obj.name,
                  scene_name=fixture.name, geometry_tolerance=1e-5)["status"] == "error")
        finally:
            if window.scene == fixture and bpy.context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            window.scene = original
            window.view_layer = layer
        check("original_context_retained", bpy.context.scene == original and bpy.context.mode == "OBJECT")
    finally:
        for item, collection in owned:
            if collection.get(item.name) != item or item.get("gameassetai_test_owner") != token:
                raise RuntimeError("Fixture ownership changed; cleanup stopped")
            if collection == bpy.data.objects and any(c != fixture.collection for c in item.users_collection):
                raise RuntimeError("External fixture links; cleanup stopped")
        for item, collection in owned:
            if collection == bpy.data.objects:
                collection.remove(item, do_unlink=True)
        # Dependency order matters: shared material can still have copied Mesh users.
        for target_collection in (bpy.data.meshes, bpy.data.materials):
            for item, collection in owned:
                if collection == target_collection:
                    if item.users:
                        raise RuntimeError("Unexpected fixture users; cleanup stopped")
                    collection.remove(item)
        if fixture.get("gameassetai_test_owner") != token:
            raise RuntimeError("Scene ownership changed; cleanup stopped")
        bpy.data.scenes.remove(fixture)
    check("original_preserved", source_fingerprint(original) == fingerprint)
    check("ids_restored", names == [[item.name for item in items] for items in tracked])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "source_fingerprint": fingerprint,
            "numeric_probes": numeric_probes}
