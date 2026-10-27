"""Blender regression for read-only multi-pass shared impostor framing."""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
import uuid

import bpy


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args(tail)
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    sys.path.insert(0, str(repo / "scripts"))
    from preview_2d_impostor_shared_framing import preview_2d_impostor_shared_framing
    from validate_2d_depth_pass_request import SCHEMA as DEPTH_SCHEMA
    from validate_2d_impostor_bundle_request import (
        SCHEMA as BUNDLE_SCHEMA, validate_2d_impostor_bundle_request)
    from validate_2d_normal_pass_request import SCHEMA as NORMAL_SCHEMA
    from validate_2d_static_render_request import SCHEMA as COLOR_SCHEMA

    token = uuid.uuid4().hex
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selection = sorted(item.name for item in bpy.context.selected_objects)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    before_names = [[item.name for item in collection] for collection in collections]
    before_files = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.data.scenes.new("GAI_ImpostorFraming_" + token)
    mesh = bpy.data.meshes.new("GAI_ImpostorMesh_" + token)
    mesh.from_pydata([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                      (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [],
                     [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                      (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)])
    obj = bpy.data.objects.new("GAI_ImpostorObject_" + token, mesh)
    scene.collection.objects.link(obj)
    material = bpy.data.materials.new("GAI_ImpostorMaterial_" + token)
    mesh.materials.append(material)

    def output(name):
        return {"target_file": str(root / (token + "-" + name + ".png")),
                "color_mode": "RGBA", "color_depth": 8, "overwrite": False}

    def children(view_id, direction):
        view = {"projection": "ORTHOGRAPHIC", "direction": direction,
                "up": [0, 0, 1], "framing_margin": 0.1}
        sample = {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                  "nearest_neighbor": True}
        color = {"schema": COLOR_SCHEMA, "scene_name": scene.name, "object_name": obj.name,
                 "profile": {"name": None, "reference_sha256": None,
                             "profile_sha256": None}, "view": copy.deepcopy(view),
                 "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
                 "style": {"mode": "PIXEL", **sample, "palette_mode": "NONE",
                           "palette": [], "max_colors": None, "outline_mode": "NONE",
                           "outline_color": None, "outline_width": 0,
                           "shading_mode": "NONE", "value_steps": None},
                 "output": output(view_id + "-color")}
        normal = {"schema": NORMAL_SCHEMA, "scene_name": scene.name, "object_name": obj.name,
                  "view": copy.deepcopy(view),
                  "normal": {"space": "CAMERA_BASIS", "source": "SHADING_NORMAL",
                             "encoding": "SIGNED_XYZ_TO_UNORM_RGB",
                             "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                  "style": copy.deepcopy(sample), "output": output(view_id + "-normal")}
        depth = {"schema": DEPTH_SCHEMA, "scene_name": scene.name, "object_name": obj.name,
                 "view": copy.deepcopy(view),
                 "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                           "normalization": "OBJECT_VERTEX_BOUNDS",
                           "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                           "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                 "style": copy.deepcopy(sample), "output": output(view_id + "-depth")}
        return [{"id": view_id + "-color", "view_id": view_id,
                 "pass_kind": "COLOR", "request": color},
                {"id": view_id + "-normal", "view_id": view_id,
                 "pass_kind": "NORMAL", "request": normal},
                {"id": view_id + "-depth", "view_id": view_id,
                 "pass_kind": "DEPTH", "request": depth}]

    diagonal = math.sqrt(0.5)
    request = {"schema": BUNDLE_SCHEMA,
               "items": children("front", [0, -1, 0])
                        + children("diagonal", [diagonal, -diagonal, 0]),
               "manifest": {"target_file": str(root / (token + "-impostor.json")),
                            "overwrite": False},
               "policy": {"execution_order": "LIST_ORDER",
                          "publication": "ALL_OR_NOTHING",
                          "on_failure": "ROLL_BACK_BUNDLE_OUTPUTS",
                          "framing_mismatch": "REJECT"}}
    try:
        preflight = validate_2d_impostor_bundle_request(request)
        check("bundle_request_ready", preflight["status"] == "ready")
        preview = preview_2d_impostor_shared_framing(request, preflight)
        check("shared_preview_planned", preview["status"] == "planned"
              and not preview["camera_created"] and not preview["render_authorized"])
        check("all_children_bound", preview["view_count"] == 2
              and preview["child_count"] == 6
              and all(len(view["children"]) == 3 for view in preview["views"])
              and all(child["shared_plan_fingerprint"] == view["plan_fingerprint"]
                      for view in preview["views"] for child in view["children"]))
        check("front_exact_scale",
              abs(preview["views"][0]["plan"]["orthographic_scale"] - 2.4) < 1e-6)
        check("diagonal_exact_scale", abs(
              preview["views"][1]["plan"]["orthographic_scale"]
              - 2.0 * math.sqrt(2.0) * 1.2) < 1e-6)
        stale = copy.deepcopy(request)
        stale["items"][0]["request"]["style"]["resolution"] = [64, 64]
        check("stale_preflight_refused",
              preview_2d_impostor_shared_framing(stale, preflight)["status"] == "error")
        source_before = preview["source_fingerprint"]
        mesh.vertices[0].co.x -= 0.25
        mesh.update()
        changed_preflight = validate_2d_impostor_bundle_request(request)
        changed = preview_2d_impostor_shared_framing(request, changed_preflight)
        check("fresh_source_change_bound", changed["status"] == "planned"
              and changed["source_fingerprint"] != source_before)
        mesh.vertices[0].co.x += 0.25
        mesh.update()
        modifier = obj.modifiers.new("Unsupported", "SUBSURF")
        blocked = preview_2d_impostor_shared_framing(request, preflight)
        check("child_dependency_blocked", blocked["status"] == "blocked"
              and any("modifiers_unsupported" in value for value in blocked["blockers"]))
        obj.modifiers.remove(modifier)
        restored = preview_2d_impostor_shared_framing(request, preflight)
        check("source_restored", restored["status"] == "planned"
              and restored["source_fingerprint"] == source_before)
        check("no_outputs_or_camera", sorted(path.name for path in root.iterdir()) == before_files
              and not any(item.type == "CAMERA" for item in scene.objects))
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("context_preserved", bpy.context.scene == original_scene
          and bpy.context.view_layer.objects.active == original_active
          and sorted(item.name for item in bpy.context.selected_objects) == original_selection)
    check("exact_teardown", before_names == [[item.name for item in collection]
                                              for collection in collections])
    print("GAMEASSETAI_RESULT=" + json.dumps(
        {"status": "passed", "check_count": len(checks), "checks": checks,
         "front_plan_fingerprint": preview["views"][0]["plan_fingerprint"],
         "diagonal_plan_fingerprint": preview["views"][1]["plan_fingerprint"],
         "blender_version": bpy.app.version_string}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
