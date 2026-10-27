"""Live Blender regression; load inspection helper/fingerprint and diagnostics first."""
import uuid


def run_diagnostics_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Require Object-mode window; do not force user's mode")
    token = uuid.uuid4().hex
    window = bpy.context.window
    original_scene, original_layer = bpy.context.scene, bpy.context.view_layer
    before = source_fingerprint(original_scene)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                   bpy.data.actions, bpy.data.shape_keys)
    names_before = [[id.name for id in c] for c in collections]
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

    fixture = own(bpy.data.scenes.new("GAI_Diagnostics_" + token), bpy.data.scenes)
    material = own(bpy.data.materials.new("GAI_Material_" + token), bpy.data.materials)
    material.use_nodes = True

    def mesh_object(label, vertices, faces, edges=()):
        mesh = own(bpy.data.meshes.new(label + token), bpy.data.meshes)
        mesh.from_pydata(vertices, edges, faces)
        obj = own(bpy.data.objects.new(label + token, mesh), bpy.data.objects)
        fixture.collection.objects.link(obj)
        mesh.materials.append(material)
        return obj

    def diagnose(obj, **options):
        report = diagnose_mesh(obj.name, scene_name=fixture.name, **options)
        check("execution_" + obj.name.split(token)[0] + str(len(checks)), report["status"] == "ok")
        return report

    def codes(report):
        return {item["code"] for item in report["findings"]}

    try:
        cube = mesh_object("ClosedCube", [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                           (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],
                           [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
        cube.data.uv_layers.new(name="TestUV")
        plane = mesh_object("OpenPlane", [(0,0,0),(1,0,0),(1,1,0),(0,1,0)], [(0,1,2,3)])
        window.scene = fixture
        report = diagnose(cube)
        check("closed_cube_counts", report["metrics"]["triangles"] == 12
              and report["metrics"]["boundary_edges"] == 0)
        check("no_default_profile_limits", report["supplied_constraints"] == {}
              and "max_triangles" in report["unrequested_constraints"])
        check("healthy_cube_no_findings", report["verdict"] == "no_findings")
        check("budget_violation", "triangle_budget_exceeded" in codes(diagnose(cube, constraints={"max_triangles":10})))
        check("budget_equal_valid", "triangle_budget_exceeded" not in codes(diagnose(cube, constraints={"max_triangles":12})))
        check("zero_budget_valid_rule", "triangle_budget_exceeded" in codes(diagnose(cube, constraints={"max_triangles":0})))
        report = diagnose(plane)
        check("open_surface_is_review_not_issue", report["metrics"]["boundary_edges"] == 4
              and report["verdict"] == "needs_review")
        check("closure_only_when_required", "required_closed_surface_failed" in codes(diagnose(plane, constraints={"closed_surface":True})))
        check("uv_only_when_required", "required_uv_missing" in codes(diagnose(plane, constraints={"require_uv":True})))
        check("false_uv_rule_not_requirement", "required_uv_missing" not in codes(diagnose(plane, constraints={"require_uv":False})))
        check("material_budget", "material_budget_exceeded" in codes(diagnose(cube, constraints={"max_materials":0})))
        for value in ({"max_triangles":True}, {"max_triangles":-1}, {"max_triangles":2.5},
                      {"max_triangles":float("nan")}, {"require_uv":"yes"}, {"unknown":3}, []):
            check("invalid_constraints_" + str(len(checks)),
                  diagnose_mesh(cube.name, constraints=value)["status"] == "error")
        check("missing_target", diagnose_mesh("__missing_" + token)["status"] == "error")
        check("no_implicit_target", diagnose_mesh(None)["status"] == "error")
        check("missing_scene", diagnose_mesh(cube.name, scene_name="__missing_" + token)["status"] == "error")
        empty = mesh_object("Empty", [], [])
        check("empty_surface", "empty_surface" in codes(diagnose(empty)))
        loose = mesh_object("LooseWire", [(0,0,0),(1,0,0),(0,1,0),(2,0,0),(5,0,0)],
                            [(0,1,2)], [(1,3)])
        report = diagnose(loose)
        check("loose_wire_metrics", report["metrics"]["loose_vertices"] == 1
              and report["metrics"]["wire_edges"] == 1)
        degenerate = mesh_object("Degenerate", [(0,0,0),(1,0,0),(2,0,0)], [(0,1,2)])
        check("degenerate_polygon", "zero_area_polygons" in codes(diagnose(degenerate)))
        winding = mesh_object("Winding", [(0,0,0),(1,0,0),(0,1,0),(0,-1,0)], [(0,1,2),(0,1,3)])
        check("winding_incidence", diagnose(winding)["metrics"]["inconsistent_winding_edges"] == 1)
        branch = mesh_object("Branch", [(0,0,0),(1,0,0),(0,1,0),(0,-1,0),(0,0,1)],
                             [(0,1,2),(1,0,3),(0,1,4)])
        check("overconnected_incidence", diagnose(branch)["metrics"]["overconnected_edges"] == 1)
        coincident = mesh_object("Coincident", [(0,0,0),(1,0,0),(0,1,0),(0,0,0)], [(0,1,2)])
        check("coincident_not_auto_error", diagnose(coincident)["metrics"]["coincident_vertex_coordinates"] == 1
              and diagnose(coincident)["verdict"] == "needs_review")
        cube.scale.x = -1
        fixture.view_layers[0].update()
        check("mirrored_transform", "mirrored_world_transform" in codes(diagnose(cube)))
        cube.scale.x = 0
        fixture.view_layers[0].update()
        check("singular_transform", "noninvertible_transform" in codes(diagnose(cube)))
        cube.scale.x = 1
        fixture.view_layers[0].update()
        types = {i.identifier for i in bpy.types.ObjectModifiers.bl_rna.functions["new"].parameters["type"].enum_items}
        check("subsurf_enum", "SUBSURF" in types)
        modifier = cube.modifiers.new("TestSubdivision", "SUBSURF")
        modifier.levels = 1
        fixture.view_layers[0].update()
        check("base_vs_evaluated_counts", diagnose(cube)["metrics"]["triangles"] == 12
              and diagnose(cube, evaluate=True)["metrics"]["triangles"] == 48)
        fixture_fingerprint = source_fingerprint(fixture)
        meshes_before_evaluation = [m.name for m in bpy.data.meshes]
        diagnose(cube, evaluate=True)
        check("evaluated_mesh_released", meshes_before_evaluation == [m.name for m in bpy.data.meshes])
        check("evaluation_preserves_source", fixture_fingerprint == source_fingerprint(fixture))
        globals_ = diagnose_mesh.__globals__
        original_metrics = globals_["_diagnostic_metrics"]
        def fail_metrics(mesh):
            raise RuntimeError("simulated metrics failure after evaluation")
        try:
            globals_["_diagnostic_metrics"] = fail_metrics
            report = diagnose_mesh(cube.name, evaluate=True)
            check("evaluation_failure_not_green", report["status"] == "error" and report["verdict"] == "unverified")
        finally:
            globals_["_diagnostic_metrics"] = original_metrics
        check("failure_preserves_source", fixture_fingerprint == source_fingerprint(fixture))
        check("failure_no_datablock_leak", meshes_before_evaluation == [m.name for m in bpy.data.meshes])
        cube.shape_key_add(name="Basis")
        cube.shape_key_add(name="Preserve")
        check("shape_keys_sensitive", diagnose(cube)["preservation_sensitive"])
        cube.keyframe_insert(data_path="location", frame=1)
        cube.location.x = 0.5
        cube.keyframe_insert(data_path="location", frame=10)
        own(cube.animation_data.action, bpy.data.actions)
        check("animation_sensitive", diagnose(cube)["preservation_sensitive"])
        fixture_fingerprint = source_fingerprint(fixture)
        diagnose(cube)
        blocked = diagnose_mesh(cube.name, evaluate=True)
        check("animated_evaluation_guard", blocked["status"] == "error"
              and "blocked" in blocked["errors"][0])
        check("unrelated_animated_dependency_guard", diagnose_mesh(plane.name, evaluate=True)["status"] == "error")
        check("animation_shape_key_preservation", fixture_fingerprint == source_fingerprint(fixture))
        plane.data.vertices[0].co.x = float("nan")
        report = diagnose(plane)
        check("nonfinite_coordinates_withheld", "nonfinite_coordinates" in codes(report)
              and report["metrics"]["triangles"] is None)
        check("nonfinite_report_serializable", bool(json.dumps(report, allow_nan=False)))
        plane.data.vertices[0].co.x = 0
        fixture.view_layers[0].objects.active = plane
        plane.select_set(True)
        modes = {i.identifier for i in bpy.ops.object.mode_set.get_rna_type().properties["mode"].enum_items}
        check("mode_enum", {"EDIT","OBJECT"}.issubset(modes))
        bpy.ops.object.mode_set(mode="EDIT")
        check("edit_mode_uncertainty", diagnose_mesh(plane.name)["status"] == "error")
        check("validator_does_not_change_mode", bpy.context.mode == "EDIT_MESH")
        bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        if window.scene == fixture and bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        window.scene, window.view_layer = original_scene, original_layer
        for id, collection in owned:
            if collection.get(id.name) != id or id.get("gameassetai_test_owner") != token:
                raise RuntimeError("Ownership changed; cleanup aborted")
        for id, collection in owned:
            if collection == bpy.data.objects:
                if any(c != fixture.collection for c in id.users_collection):
                    raise RuntimeError("External fixture links; cleanup aborted")
        for id, collection in owned:
            if collection == bpy.data.objects:
                collection.remove(id, do_unlink=True)
        for collection in (bpy.data.meshes, bpy.data.actions, bpy.data.materials):
            for id, owner_collection in owned:
                if owner_collection == collection:
                    if id.users != 0:
                        raise RuntimeError("Unexpected datablock users; cleanup aborted")
                    collection.remove(id)
        bpy.data.scenes.remove(fixture)
    check("original_scene_preserved", source_fingerprint(original_scene) == before)
    check("all_names_restored", names_before == [[id.name for id in c] for c in collections])
    return {"status":"passed", "check_count":len(checks), "checks":checks,
            "fixture_cleanup":"complete", "source_fingerprint":before,
            "blender_version":bpy.app.version_string}
