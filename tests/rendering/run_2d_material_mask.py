"""Blender regression for reviewed, staged material-slot mask publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

import bpy


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path)
    args = parser.parse_args(tail)
    root = args.artifact_root.resolve(strict=True)
    repo = args.repo_root.resolve(strict=True)
    helpers = (args.helper_root or repo / "scripts").resolve(strict=True)
    namespace = {"__name__": "gameassetai_material_mask_test"}
    for name in ("validate_2d_material_mask_request.py", "inspect_2d_material_mask_candidate.py",
                 "preview_2d_material_mask_framing.py", "stage_2d_material_mask_source.py",
                 "build_2d_material_mask_job.py", "quantize_rgba.py",
                 "build_2d_render_receipt.py", "render_2d_material_mask.py"):
        source = (helpers / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)

    token = uuid.uuid4().hex
    target = root / ("material-mask-" + token + ".png")
    stage = root / (".gameassetai-material-mask-" + token + ".stage.blend")
    job = root / (".gameassetai-material-mask-" + token + ".job.json")
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        mesh = bpy.data.meshes.new("GAI_MaterialMaskMesh_" + token)
        # Target quad fills the frame. A closer non-target quad hides its right half.
        mesh.from_pydata([(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1),
                          (0, -0.1, -1), (1, -0.1, -1), (1, -0.1, 1), (0, -0.1, 1)],
                         [], [(0, 1, 2, 3), (4, 5, 6, 7)])
        mesh.polygons[0].material_index = 0
        mesh.polygons[1].material_index = 1
        obj = bpy.data.objects.new("GAI_MaterialMaskObject_" + token, mesh)
        scene.collection.objects.link(obj)
        target_material = bpy.data.materials.new("Target_" + token)
        blocker_material = bpy.data.materials.new("Blocker_" + token)
        mesh.materials.append(target_material)
        mesh.materials.append(blocker_material)
        request = {"schema": namespace["SCHEMA"], "scene_name": scene.name,
                   "object_name": obj.name,
                   "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                            "up": [0, 0, 1], "framing_margin": 0.1},
                   "mask": {"material_slot_index": 0, "visible_rgba": [1, 1, 1, 1]},
                   "style": {"resolution": [32, 24], "anti_aliasing": "DISABLED",
                             "nearest_neighbor": True},
                   "output": {"target_file": str(target), "color_mode": "RGBA",
                              "color_depth": 8, "overwrite": False}}
        preflight = namespace["validate_2d_material_mask_request"](request)
        check("request_valid", preflight["ready_for_blender_inspection"])
        candidate = namespace["inspect_2d_material_mask_candidate"](request, preflight)
        check("candidate_reviewed", candidate["status"] == "candidate_for_review"
              and candidate["material_slot"]["assigned_polygons"] == 1)
        framing = namespace["preview_2d_material_mask_framing"](request, candidate)
        check("framing_planned", framing["status"] == "planned")

        stale_request = json.loads(json.dumps(request))
        stale_request["mask"]["material_slot_index"] = 1
        stale = namespace["stage_2d_material_mask_source"](
            stale_request, preflight, candidate, framing, str(stage), authorize=True)
        check("stale_request_refused", stale["status"] == "error" and not stage.exists())
        staged = namespace["stage_2d_material_mask_source"](
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("source_staged", staged["status"] == "created" and stage.is_file())
        prepared = namespace["build_2d_material_mask_job"](
            request, candidate, framing, staged, str(job), authorize=True)
        check("job_created", prepared["status"] == "created" and job.is_file())

        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        rendered = namespace["render_2d_material_mask_job"](
            str(job), prepared["job_sha256"], authorize=True)
        check("mask_published", rendered["status"] == "created"
              and rendered["png_published"] and target.is_file())
        check("rgba_binary", rendered["artifact"]["unique_rgba"] == 2
              and rendered["artifact"]["foreground_pixels"] > 0)
        check("non_target_occludes", rendered["occluder_pixels"] > 0)
        check("receipt_bound", rendered["artifact"]["sha256"] ==
              hashlib.sha256(target.read_bytes()).hexdigest()
              and len(rendered["receipt_sha256"]) == 64)
        collision = namespace["render_2d_material_mask_job"](
            str(job), prepared["job_sha256"], authorize=True)
        check("collision_refused", collision["status"] == "error" and target.is_file())
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "artifact_sha256": rendered["artifact"]["sha256"],
                  "receipt_sha256": rendered["receipt_sha256"],
                  "alpha_bounds": rendered["artifact"]["alpha_bounds"],
                  "foreground_pixels": rendered["artifact"]["foreground_pixels"],
                  "occluder_pixels": rendered["occluder_pixels"],
                  "blender_version": bpy.app.version_string}
    finally:
        target.unlink(missing_ok=True)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
        for path in root.glob(".gameassetai-material-mask-*"):
            path.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
