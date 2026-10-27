"""Blender regression for explicit target-Object visibility-mask publication."""
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
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    helpers = (args.helper_root or repo / "scripts").resolve(strict=True)
    namespace = {"__name__": "gameassetai_object_mask_test"}
    for name in ("validate_2d_object_mask_request.py", "inspect_2d_object_mask_candidate.py",
                 "preview_2d_object_mask_framing.py", "stage_2d_object_mask_source.py",
                 "build_2d_object_mask_job.py", "quantize_rgba.py",
                 "build_2d_render_receipt.py", "render_2d_object_mask.py"):
        source = (helpers / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    token = uuid.uuid4().hex
    target_file = root / ("object-mask-" + token + ".png")
    stage = root / (".gameassetai-object-mask-" + token + ".stage.blend")
    job = root / (".gameassetai-object-mask-" + token + ".job.json")
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def quad(name, vertices):
        mesh = bpy.data.meshes.new(name + "Mesh")
        mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        return obj

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        target = quad("Target_" + token,
                      [(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)])
        blocker = quad("Blocker_" + token,
                       [(0, -0.1, -1), (1, -0.1, -1), (1, -0.1, 1), (0, -0.1, 1)])
        unrelated = quad("Unrelated_" + token,
                         [(-4, -0.2, -1), (-3, -0.2, -1), (-3, -0.2, 1), (-4, -0.2, 1)])
        request = {"schema": namespace["SCHEMA"], "scene_name": scene.name,
                   "target_object_name": target.name, "occluder_object_names": [blocker.name],
                   "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                            "up": [0, 0, 1], "framing_margin": 0.1},
                   "mask": {"visible_rgba": [1, 1, 1, 1]},
                   "style": {"resolution": [32, 24], "anti_aliasing": "DISABLED",
                             "nearest_neighbor": True},
                   "output": {"target_file": str(target_file), "color_mode": "RGBA",
                              "color_depth": 8, "overwrite": False}}
        preflight = namespace["validate_2d_object_mask_request"](request)
        check("request_valid", preflight["ready_for_blender_inspection"])
        candidate = namespace["inspect_2d_object_mask_candidate"](request, preflight)
        check("candidate_exact_objects", candidate["status"] == "candidate_for_review"
              and candidate["target_object"] == target.name
              and candidate["occluder_objects"] == [blocker.name]
              and unrelated.name not in [item["name"] for item in candidate["objects"]])
        framing = namespace["preview_2d_object_mask_framing"](request, candidate)
        check("union_framing_planned", framing["status"] == "planned")
        target.location.x = 0.1
        bpy.context.view_layer.update()
        stale = namespace["stage_2d_object_mask_source"](
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("source_drift_refused", stale["status"] == "error" and not stage.exists())
        target.location.x = 0
        bpy.context.view_layer.update()
        candidate = namespace["inspect_2d_object_mask_candidate"](request, preflight)
        framing = namespace["preview_2d_object_mask_framing"](request, candidate)
        staged = namespace["stage_2d_object_mask_source"](
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("only_requested_objects_staged", staged["status"] == "created"
              and staged["staged_objects"] == 2 and stage.is_file())
        prepared = namespace["build_2d_object_mask_job"](
            request, candidate, framing, staged, str(job), authorize=True)
        check("job_created", prepared["status"] == "created" and job.is_file())
        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        rendered = namespace["render_2d_object_mask_job"](
            str(job), prepared["job_sha256"], authorize=True)
        check("mask_published", rendered["status"] == "created"
              and rendered["png_published"] and target_file.is_file())
        check("binary_target_pixels", rendered["artifact"]["unique_rgba"] == 2
              and rendered["artifact"]["foreground_pixels"] == 200)
        check("explicit_occluder_preserved", rendered["occluder_pixels"] == 200)
        check("receipt_bound", rendered["artifact"]["sha256"] ==
              hashlib.sha256(target_file.read_bytes()).hexdigest()
              and len(rendered["receipt_sha256"]) == 64)
        collision = namespace["render_2d_object_mask_job"](
            str(job), prepared["job_sha256"], authorize=True)
        check("collision_refused", collision["status"] == "error" and target_file.is_file())
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "artifact_sha256": rendered["artifact"]["sha256"],
                  "receipt_sha256": rendered["receipt_sha256"],
                  "alpha_bounds": rendered["artifact"]["alpha_bounds"],
                  "foreground_pixels": rendered["artifact"]["foreground_pixels"],
                  "occluder_pixels": rendered["occluder_pixels"],
                  "blender_version": bpy.app.version_string}
    finally:
        target_file.unlink(missing_ok=True)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
        for path in root.glob(".gameassetai-object-mask-*"):
            path.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
