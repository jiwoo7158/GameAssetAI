"""Native export-preflight inventory on owned synthetic data; no export operator call."""
import uuid
import bpy
import hashlib
import json
from pathlib import Path


def run_export_context_tests():
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Object mode required; do not force mode")
    original = bpy.context.scene
    fingerprint = source_fingerprint(original)
    tracked = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    names = [[item.name for item in collection] for collection in tracked]
    token = uuid.uuid4().hex
    scene = bpy.data.scenes.new("GAI_ExportContext_" + token)
    mesh = bpy.data.meshes.new("GAI_ExportMesh_" + token)
    obj = bpy.data.objects.new("GAI_ExportObject_" + token, mesh)
    material = bpy.data.materials.new("GAI_ExportMaterial_" + token)
    for item in (scene, mesh, obj, material):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(obj)
    mesh.from_pydata([(0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    mesh.uv_layers.new(name="ExportUV")
    mesh.materials.append(material)
    checks = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    def inspect(**options):
        return inspect_static_export_context(obj.name, scene_name=scene.name, **options)
    request = {"schema": "gameassetai.static-fbx-request.v1", "scene_name": scene.name,
               "object_name": obj.name,
               "target_file": str(Path(bpy.app.tempdir) / ("GAI_Export_" + token + ".fbx")),
               "axis_forward": "-Z", "axis_up": "Y", "global_scale": 1,
               "apply_unit_scale": False, "apply_scale_options": "FBX_SCALE_NONE",
               "use_space_transform": True, "bake_space_transform": False,
               "use_mesh_modifiers": False,
               "path_mode": "AUTO", "overwrite": False}
    def preflight(values):
        canonical = json.dumps(values, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        return {"schema": values["schema"], "ready_for_blender_inspection": True,
                "errors": [], "request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest()}
    def candidate(values=request):
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            return inspect_static_fbx_candidate(values, preflight(values))
    try:
        before = source_fingerprint(scene)
        ids = [[item.name for item in collection] for collection in tracked]
        result = inspect()
        check("inventory", result["status"] == "inspected" and result["mesh"]["base_triangles"] == 2)
        check("uv_material", result["mesh"]["uv_layers"] == ["ExportUV"]
              and result["mesh"]["material_slots"] == [material.name])
        check("no_policy_inferred", result["requested_format"] is None
              and result["requested_operator_available"] is None
              and "axis_conversion_policy" in result["unresolved_contract"])
        check("not_export_authorized", result["export_authorized"] is False
              and result["export_path"] is None and result["engine_ready"] is None)
        check("inactive_scene_selection_unknown", result["selection_observation"]["selected_in_active_view_layer"] is None)
        check("fbx_available", inspect(requested_format="FBX")["requested_operator_available"] is True)
        check("fbx_parameters_observed", {"filepath", "use_selection", "axis_forward", "axis_up"}.issubset(
              result["exporter_capabilities"]["FBX"]["parameter_names"]))
        observed_fbx = result["exporter_capabilities"]["FBX"]
        check("fbx_axes_observed", all({"-Z", "Y"}.issubset(observed_fbx["axis_identifiers"][key])
                                       for key in ("axis_forward", "axis_up")))
        check("fbx_scale_range_observed", observed_fbx["global_scale_hard_range"][0] <= 1
              <= observed_fbx["global_scale_hard_range"][1])
        check("fbx_scale_options_observed", "FBX_SCALE_UNITS" in
              observed_fbx["apply_scale_options_identifiers"])
        checked = candidate()
        scoped_fingerprint = candidate()["source_fingerprint"]
        if not (checked["status"] == "candidate_for_review"
                and not checked["blockers"] and checked["source_fingerprint"] == scoped_fingerprint):
            raise AssertionError("candidate_readonly_report: " + repr(checked))
        check("candidate_readonly", checked["status"] == "candidate_for_review"
              and not checked["blockers"] and checked["source_fingerprint"] == scoped_fingerprint)
        check("candidate_not_authorized", checked["export_authorized"] is False
              and checked["destination_rechecked"] is False
              and checked["sidecars_verified"] is False
              and checked["fbx_operator_poll"] is True)
        mesh.vertices[0].co.x = 0.25
        check("candidate_fingerprint_tracks_geometry",
              candidate()["source_fingerprint"] != checked["source_fingerprint"])
        mesh.vertices[0].co.x = 0.0
        material.diffuse_color = (0.25, 0.5, 0.75, 1.0)
        check("candidate_fingerprint_tracks_material",
              candidate()["source_fingerprint"] != checked["source_fingerprint"])
        material.diffuse_color = (0.8, 0.8, 0.8, 1.0)
        check("candidate_fingerprint_restored",
              candidate()["source_fingerprint"] == checked["source_fingerprint"])
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
            absent_preflight = inspect_static_fbx_candidate(request, {})
        check("absent_preflight_refused", absent_preflight["status"] == "error")
        changed = dict(request, axis_forward="X")
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
            stale = inspect_static_fbx_candidate(changed, preflight(request))
        check("changed_request_refused", stale["status"] == "error")
        check("invalid_axis_refused", "axis_forward_unavailable" in candidate(
              dict(request, axis_forward="NORTH"))["blockers"])
        check("scale_outside_rna_refused", "scale_outside_current_rna" in candidate(
              dict(request, global_scale=0))["blockers"])
        check("scale_option_refused", "apply_scale_options_unavailable" in candidate(
              dict(request, apply_scale_options="DEFAULT"))["blockers"])
        check("inactive_scene_blocked", "requested_scene_not_active" in
              inspect_static_fbx_candidate(request, preflight(request))["blockers"])
        check("gltf_available", inspect(requested_format="GLTF")["requested_operator_available"] is True)
        check("gltf_parameters_observed", {"filepath", "use_selection", "export_yup"}.issubset(
              result["exporter_capabilities"]["GLTF"]["parameter_names"]))
        check("bad_format_refused", inspect(requested_format="OBJ")["status"] == "error")
        check("missing_object_refused", inspect_static_export_context("GAI_Missing_" + token,
              scene_name=scene.name)["status"] == "error")
        check("wrong_scene_refused", inspect_static_export_context(obj.name,
              scene_name=original.name)["status"] == "error")
        shared = bpy.data.objects.new("GAI_ExportShared_" + token, mesh)
        shared["gameassetai_test_owner"] = token
        scene.collection.objects.link(shared)
        try:
            check("shared_mesh_reported", "shared_mesh" in inspect()["dependencies"])
            check("shared_mesh_candidate_blocked", "shared_mesh" in candidate()["blockers"])
            modifier = obj.modifiers.new("GAI_ExportBevel", "BEVEL")
            try:
                check("modifier_reported", "modifiers" in inspect()["dependencies"])
                check("modifier_candidate_blocked", "modifiers" in candidate()["blockers"])
            finally:
                obj.modifiers.remove(modifier)
        finally:
            assert shared.get("gameassetai_test_owner") == token and shared.data == mesh
            assert list(shared.users_collection) == [scene.collection]
            bpy.data.objects.remove(shared, do_unlink=True)
        check("readonly_fixture", source_fingerprint(scene) == before
              and ids == [[item.name for item in collection] for collection in tracked])
        material.use_nodes = True
        texture_node = material.node_tree.nodes.new("ShaderNodeTexImage")
        try:
            check("texture_node_candidate_blocked", "material_texture_or_group_unresolved"
                  in candidate()["blockers"])
        finally:
            material.node_tree.nodes.remove(texture_node)
    finally:
        assert all(item.get("gameassetai_test_owner") == token for item in (scene, obj, mesh, material))
        assert obj.data == mesh and list(obj.users_collection) == [scene.collection]
        bpy.data.objects.remove(obj, do_unlink=True)
        assert mesh.users == 0
        bpy.data.meshes.remove(mesh)
        assert material.users == 0
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("original_preserved", source_fingerprint(original) == fingerprint)
    check("ids_restored", names == [[item.name for item in collection] for collection in tracked])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "source_fingerprint": fingerprint,
            "observed_fbx_axis_identifiers": observed_fbx["axis_identifiers"],
            "observed_fbx_global_scale_hard_range": observed_fbx["global_scale_hard_range"],
            "observed_operator_parameters": {key: result["exporter_capabilities"][key]["parameter_names"]
                                             for key in ("FBX", "GLTF")}}
