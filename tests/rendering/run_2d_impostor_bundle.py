"""Blender end-to-end regression for one COLOR/NORMAL/DEPTH impostor bundle."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

import bpy


def _stack(helper_root, label, names):
    namespace = {"__name__": label}
    for name in names:
        source = (helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    return namespace


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path)
    args = parser.parse_args(tail)
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    helper_root = (args.helper_root.resolve(strict=True) if args.helper_root
                   else repo / "scripts")
    sys.path.insert(0, str(helper_root))
    from build_2d_impostor_bundle_job import build_2d_impostor_bundle_job
    from preview_2d_impostor_shared_framing import preview_2d_impostor_shared_framing
    from run_2d_impostor_bundle import run_2d_impostor_bundle_job
    from validate_2d_impostor_bundle_request import (
        SCHEMA as BUNDLE_SCHEMA, validate_2d_impostor_bundle_request)

    color = _stack(helper_root, "gai_color_stack", (
        "validate_2d_static_render_request.py", "inspect_2d_static_render_candidate.py",
        "preview_2d_orthographic_framing.py", "stage_2d_static_source.py",
        "build_2d_staged_render_job.py"))
    normal = _stack(helper_root, "gai_normal_stack", (
        "validate_2d_normal_pass_request.py", "inspect_2d_normal_pass_candidate.py",
        "preview_2d_normal_pass_framing.py", "stage_2d_normal_pass_source.py",
        "build_2d_normal_pass_job.py"))
    depth = _stack(helper_root, "gai_depth_stack", (
        "validate_2d_depth_pass_request.py", "inspect_2d_depth_pass_candidate.py",
        "preview_2d_depth_pass_framing.py", "stage_2d_depth_pass_source.py",
        "build_2d_depth_pass_job.py"))

    token = uuid.uuid4().hex
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selection = sorted(item.name for item in bpy.context.selected_objects)
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    before_names = [[item.name for item in collection] for collection in collections]
    before_files = sorted(path.name for path in root.iterdir())
    owned = []
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.data.scenes.new("GAI_ImpostorBundle_" + token)
    mesh = bpy.data.meshes.new("GAI_ImpostorBundleMesh_" + token)
    mesh.from_pydata([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                      (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [],
                     [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                      (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)])
    obj = bpy.data.objects.new("GAI_ImpostorBundleObject_" + token, mesh)
    scene.collection.objects.link(obj)
    material = bpy.data.materials.new("GAI_ImpostorBundleMaterial_" + token)
    material.diffuse_color = (0.6, 0.6, 0.6, 1.0)
    mesh.materials.append(material)
    view = {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
            "up": [0, 0, 1], "framing_margin": 0.1}
    sampling = {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                "nearest_neighbor": True}

    def output(name):
        path = root / ("impostor-" + token + "-" + name + ".png")
        owned.append(path)
        return {"target_file": str(path), "color_mode": "RGBA",
                "color_depth": 8, "overwrite": False}

    color_request = {"schema": color["SCHEMA"], "scene_name": scene.name,
                     "object_name": obj.name,
                     "profile": {"name": None, "reference_sha256": None,
                                 "profile_sha256": None}, "view": dict(view),
                     "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
                     "style": {"mode": "PIXEL", **sampling, "palette_mode": "NONE",
                               "palette": [], "max_colors": None, "outline_mode": "NONE",
                               "outline_color": None, "outline_width": 0,
                               "shading_mode": "NONE", "value_steps": None},
                     "output": output("color")}
    normal_request = {"schema": normal["SCHEMA"], "scene_name": scene.name,
                      "object_name": obj.name, "view": dict(view),
                      "normal": {"space": "CAMERA_BASIS", "source": "SHADING_NORMAL",
                                 "encoding": "SIGNED_XYZ_TO_UNORM_RGB",
                                 "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                      "style": dict(sampling), "output": output("normal")}
    depth_request = {"schema": depth["SCHEMA"], "scene_name": scene.name,
                     "object_name": obj.name, "view": dict(view),
                     "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                               "normalization": "OBJECT_VERTEX_BOUNDS",
                               "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                               "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                     "style": dict(sampling), "output": output("depth")}
    manifest = root / ("impostor-" + token + "-result.json")
    owned.append(manifest)
    request = {"schema": BUNDLE_SCHEMA,
               "items": [{"id": "front-color", "view_id": "front",
                           "pass_kind": "COLOR", "request": color_request},
                          {"id": "front-normal", "view_id": "front",
                           "pass_kind": "NORMAL", "request": normal_request},
                          {"id": "front-depth", "view_id": "front",
                           "pass_kind": "DEPTH", "request": depth_request}],
               "manifest": {"target_file": str(manifest), "overwrite": False},
               "policy": {"execution_order": "LIST_ORDER", "publication": "ALL_OR_NOTHING",
                          "on_failure": "ROLL_BACK_BUNDLE_OUTPUTS",
                          "framing_mismatch": "REJECT"}}
    stacks = {"COLOR": (color, "validate_2d_static_render_request",
                         "inspect_2d_static_render_candidate",
                         "preview_2d_orthographic_framing", "stage_2d_static_source",
                         "build_2d_staged_render_job", ".gameassetai-2d-"),
              "NORMAL": (normal, "validate_2d_normal_pass_request",
                          "inspect_2d_normal_pass_candidate",
                          "preview_2d_normal_pass_framing", "stage_2d_normal_pass_source",
                          "build_2d_normal_pass_job", ".gameassetai-normal-pass-"),
              "DEPTH": (depth, "validate_2d_depth_pass_request",
                         "inspect_2d_depth_pass_candidate",
                         "preview_2d_depth_pass_framing", "stage_2d_depth_pass_source",
                         "build_2d_depth_pass_job", ".gameassetai-depth-pass-")}
    descriptors = []
    result = None
    try:
        preflight = validate_2d_impostor_bundle_request(request)
        check("bundle_request_ready", preflight["status"] == "ready")
        shared = preview_2d_impostor_shared_framing(request, preflight)
        check("shared_framing_planned", shared["status"] == "planned"
              and shared["child_count"] == 3)
        for index, item in enumerate(request["items"]):
            namespace, validate_name, inspect_name, preview_name, stage_name, build_name, prefix = stacks[item["pass_kind"]]
            child = item["request"]
            child_preflight = namespace[validate_name](child)
            candidate = namespace[inspect_name](child, child_preflight)
            framing = namespace[preview_name](child, candidate)
            check("child_plan_matches_" + item["pass_kind"].lower(),
                  {key: value for key, value in framing["plan"].items()
                   if key != "camera_frame"} == shared["views"][0]["plan"])
            stage_path = root / (prefix + token + f"-{index}.stage.blend")
            job_path = root / (prefix + token + f"-{index}.job.json")
            owned.extend((stage_path, job_path))
            stage = namespace[stage_name](child, child_preflight, candidate, framing,
                                          str(stage_path), authorize=True)
            check("stage_created_" + item["pass_kind"].lower(), stage["status"] == "created")
            job = namespace[build_name](child, candidate, framing, stage,
                                        str(job_path), authorize=True)
            check("job_created_" + item["pass_kind"].lower(), job["status"] == "created")
            descriptors.append({"id": item["id"], "pass_kind": item["pass_kind"],
                                "stage_file": str(stage_path),
                                "stage_sha256": stage["stage_sha256"],
                                "job_file": str(job_path), "job_sha256": job["job_sha256"],
                                "helper_root": str(repo / "scripts")})
        bundle_job_path = root / (".gameassetai-impostor-bundle-" + token + ".job.json")
        owned.append(bundle_job_path)
        bundle_job = build_2d_impostor_bundle_job(
            request, shared, descriptors, str(bundle_job_path), authorize=True)
        check("bundle_job_created", bundle_job["status"] == "created")
        result = run_2d_impostor_bundle_job(
            str(bundle_job_path), bundle_job["job_sha256"], bpy.app.binary_path)
        check("bundle_render_created", result["status"] == "created"
              and result["published_count"] == 3 and result["manifest_published"])
        metadata = json.loads(manifest.read_text(encoding="utf-8"))
        check("manifest_order", [entry["pass_kind"] for entry in metadata["artifacts"]]
              == ["COLOR", "NORMAL", "DEPTH"])
        check("all_outputs_nonempty", all(Path(path).stat().st_size > 0
              for path in preflight["outputs"]))
        check("no_unexpected_token_files", set(path.name for path in root.iterdir()
              if token in path.name) == {path.name for path in owned})
    finally:
        for path in reversed(owned):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("artifact_root_restored", sorted(path.name for path in root.iterdir()) == before_files)
    check("context_preserved", bpy.context.scene == original_scene
          and bpy.context.view_layer.objects.active == original_active
          and sorted(item.name for item in bpy.context.selected_objects) == original_selection)
    check("exact_data_teardown", before_names == [[item.name for item in collection]
                                                   for collection in collections])
    print("GAMEASSETAI_RESULT=" + json.dumps(
        {"status": "passed", "check_count": len(checks), "checks": checks,
         "bundle_receipt_sha256": result["receipt_sha256"],
         "blender_version": bpy.app.version_string}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
