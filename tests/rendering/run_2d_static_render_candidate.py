"""Synthetic Blender regression for read-only static 2D candidate inspection."""
from __future__ import annotations

from pathlib import Path
import uuid


def run_2d_static_render_candidate_tests(artifact_root):
    token = uuid.uuid4().hex
    root = Path(artifact_root).resolve(strict=True)
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selection = sorted(obj.name for obj in bpy.context.selected_objects)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    before_names = [[item.name for item in collection] for collection in collections]
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.data.scenes.new("GAI_2DCandidate_" + token)
    mesh = bpy.data.meshes.new("GAI_2DMesh_" + token)
    mesh.from_pydata([(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)],
                     [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("GAI_2DObject_" + token, mesh)
    scene.collection.objects.link(obj)
    material = bpy.data.materials.new("GAI_2DMaterial_" + token)
    mesh.materials.append(material)
    request = {
        "schema": SCHEMA, "scene_name": scene.name, "object_name": obj.name,
        "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
        "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                 "up": [0, 0, 1], "framing_margin": 0.1},
        "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
        "style": {"mode": "PIXEL", "resolution": [64, 64],
                  "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                  "palette_mode": "NONE", "palette": [], "max_colors": None,
                  "outline_mode": "NONE", "outline_color": None,
                  "outline_width": 0, "shading_mode": "NONE",
                  "value_steps": None},
        "output": {"target_file": str(root / ("candidate-" + token + ".png")),
                   "color_mode": "RGBA", "color_depth": 8, "overwrite": False},
    }
    try:
        preflight = validate_2d_static_render_request(request)
        check("offline_preflight", preflight["ready_for_blender_inspection"])
        candidate = inspect_2d_static_render_candidate(request, preflight)
        check("candidate_ready", candidate["status"] == "candidate_for_review"
              and candidate["blockers"] == [] and not candidate["render_authorized"])
        check("three_fingerprints", all(len(candidate[key]) == 64 for key in
              ("source_fingerprint", "setup_fingerprint", "output_fingerprint")))
        check("bounds_and_counts", candidate["world_bounds"]["dimensions"] == [2.0, 0.0, 2.0]
              and candidate["mesh"]["vertices"] == 4 and candidate["mesh"]["polygons"] == 1)
        framing = preview_2d_orthographic_framing(request, candidate)
        check("framing_planned", framing["status"] == "planned"
              and not framing["camera_created"] and not framing["render_authorized"])
        check("square_framing", abs(framing["plan"]["orthographic_scale"] - 2.4) < 1e-6
              and framing["plan"]["basis_columns"]["right_x"] == [1.0, 0.0, 0.0])
        portrait = {**request, "style": {**request["style"], "resolution": [32, 64]}}
        portrait_preflight = validate_2d_static_render_request(portrait)
        portrait_candidate = inspect_2d_static_render_candidate(portrait, portrait_preflight)
        portrait_framing = preview_2d_orthographic_framing(portrait, portrait_candidate)
        check("portrait_aspect_framing", abs(
              portrait_framing["plan"]["orthographic_scale"] - 4.8) < 1e-6)
        landscape = {**request, "style": {**request["style"], "resolution": [64, 48]}}
        landscape_preflight = validate_2d_static_render_request(landscape)
        landscape_candidate = inspect_2d_static_render_candidate(landscape, landscape_preflight)
        landscape_framing = preview_2d_orthographic_framing(landscape, landscape_candidate)
        landscape_ok = (landscape_framing["status"] == "planned"
                        and abs(landscape_framing["plan"]["orthographic_scale"] - 3.2) < 1e-6
                        and abs(landscape_framing["plan"]["camera_frame"][0] - 3.2) < 1e-6
                        and abs(landscape_framing["plan"]["camera_frame"][1] - 2.4) < 1e-6)
        if not landscape_ok:
            raise AssertionError("landscape_aspect_framing: " + repr(landscape_framing))
        checks.append("landscape_aspect_framing")
        mesh.vertices[0].co.x -= 0.25
        changed = inspect_2d_static_render_candidate(request, preflight)
        check("source_change_detected", changed["source_fingerprint"] != candidate["source_fingerprint"]
              and changed["setup_fingerprint"] == candidate["setup_fingerprint"])
        check("stale_framing_refused", preview_2d_orthographic_framing(request, candidate)
              ["status"] == "error")
        mesh.vertices[0].co.x += 0.25
        check("source_restored", inspect_2d_static_render_candidate(request, preflight)
              ["source_fingerprint"] == candidate["source_fingerprint"])
        tampered = {**request, "style": {**request["style"], "resolution": [32, 32]}}
        check("stale_preflight_refused", inspect_2d_static_render_candidate(tampered, preflight)
              ["status"] == "error")
        modifier = obj.modifiers.new("Unsupported", "SUBSURF")
        blocked = inspect_2d_static_render_candidate(request, preflight)
        check("dependency_blocked", blocked["status"] == "blocked"
              and "modifiers_unsupported" in blocked["blockers"])
        obj.modifiers.remove(modifier)
        unsupported = {**request, "style": {**request["style"], "mode": "CEL"}}
        unsupported_preflight = validate_2d_static_render_request(unsupported)
        check("future_mode_blocked", inspect_2d_static_render_candidate(
              unsupported, unsupported_preflight)["status"] == "blocked")
        fixed = {**request, "style": {**request["style"], "palette_mode": "FIXED",
                                      "palette": [[0, 0, 0, 1], [1, 1, 1, 1]]}}
        fixed_preflight = validate_2d_static_render_request(fixed)
        check("opaque_fixed_palette_supported", inspect_2d_static_render_candidate(
              fixed, fixed_preflight)["status"] == "candidate_for_review")
        automatic = {**request, "style": {**request["style"],
                                            "palette_mode": "AUTO",
                                            "palette": [], "max_colors": 4}}
        automatic_preflight = validate_2d_static_render_request(automatic)
        check("explicit_auto_palette_supported", inspect_2d_static_render_candidate(
              automatic, automatic_preflight)["status"] == "candidate_for_review")
        translucent = {**fixed, "style": {**fixed["style"],
                                           "palette": [[0, 0, 0, 0.5]]}}
        translucent_preflight = validate_2d_static_render_request(translucent)
        check("translucent_fixed_palette_blocked", inspect_2d_static_render_candidate(
              translucent, translucent_preflight)["status"] == "blocked")
        outlined = {**request, "style": {**request["style"],
                                           "outline_mode": "OUTER",
                                           "outline_color": [0, 0, 0, 1],
                                           "outline_width": 1}}
        outlined_preflight = validate_2d_static_render_request(outlined)
        check("one_pixel_outer_outline_supported", inspect_2d_static_render_candidate(
              outlined, outlined_preflight)["status"] == "candidate_for_review")
        shaded = {**request, "style": {**request["style"],
                                        "shading_mode": "VALUE_STEPS",
                                        "value_steps": 4}}
        shaded_preflight = validate_2d_static_render_request(shaded)
        check("explicit_value_steps_supported", inspect_2d_static_render_candidate(
              shaded, shaded_preflight)["status"] == "candidate_for_review")
        check("no_output_created", not Path(request["output"]["target_file"]).exists())
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("context_preserved", bpy.context.scene == original_scene
          and bpy.context.view_layer.objects.active == original_active
          and sorted(obj.name for obj in bpy.context.selected_objects) == original_selection)
    check("exact_id_teardown", before_names == [[item.name for item in c] for c in collections])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "blender_version": bpy.app.version_string}
