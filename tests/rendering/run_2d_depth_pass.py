"""Blender regression for reviewed, staged camera-linear depth publication."""
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
    namespace = {"__name__": "gameassetai_depth_pass_test"}
    for name in ("validate_2d_depth_pass_request.py", "inspect_2d_depth_pass_candidate.py",
                 "preview_2d_depth_pass_framing.py", "stage_2d_depth_pass_source.py",
                 "build_2d_depth_pass_job.py", "quantize_rgba.py",
                 "build_2d_render_receipt.py", "render_2d_depth_pass.py"):
        source = (helpers / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)

    token = uuid.uuid4().hex
    target = root / ("depth-pass-" + token + ".png")
    stage = root / (".gameassetai-depth-pass-" + token + ".stage.blend")
    job = root / (".gameassetai-depth-pass-" + token + ".job.json")
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
        mesh = bpy.data.meshes.new("GAI_DepthPassMesh_" + token)
        # A tilted triangle produces a visible camera-linear depth gradient.
        mesh.from_pydata([(-1, -1, -1), (1, 0, -1), (0, 1, 1)], [], [(0, 1, 2)])
        obj = bpy.data.objects.new("GAI_DepthPassObject_" + token, mesh)
        scene.collection.objects.link(obj)
        request = {"schema": namespace["SCHEMA"], "scene_name": scene.name,
                   "object_name": obj.name,
                   "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                            "up": [0, 0, 1], "framing_margin": 0.1},
                   "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                              "normalization": "OBJECT_VERTEX_BOUNDS",
                              "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                              "background_rgba": [0.0, 0.0, 0.0, 0.0]},
                   "style": {"resolution": [32, 24], "anti_aliasing": "DISABLED",
                             "nearest_neighbor": True},
                   "output": {"target_file": str(target), "color_mode": "RGBA",
                              "color_depth": 8, "overwrite": False}}
        preflight = namespace["validate_2d_depth_pass_request"](request)
        check("request_valid", preflight["ready_for_blender_inspection"])
        candidate = namespace["inspect_2d_depth_pass_candidate"](request, preflight)
        check("candidate_reviewed", candidate["status"] == "candidate_for_review"
              and candidate["mesh"]["polygons"] == 1)
        framing = namespace["preview_2d_depth_pass_framing"](request, candidate)
        check("framing_planned", framing["status"] == "planned")

        stale_request = json.loads(json.dumps(request))
        stale_request["depth"]["space"] = "CAMERA_CLIP"
        stale = namespace["stage_2d_depth_pass_source"](
            stale_request, preflight, candidate, framing, str(stage), authorize=True)
        check("stale_request_refused", stale["status"] == "error" and not stage.exists())
        staged = namespace["stage_2d_depth_pass_source"](
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("source_staged", staged["status"] == "created" and stage.is_file())
        prepared = namespace["build_2d_depth_pass_job"](
            request, candidate, framing, staged, str(job), authorize=True)
        check("job_created", prepared["status"] == "created" and job.is_file())

        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        rendered = namespace["render_2d_depth_pass_job"](
            str(job), prepared["job_sha256"], authorize=True)
        print("GAMEASSETAI_DEPTH_PASS_DIAGNOSTIC="
              + json.dumps(rendered, sort_keys=True, allow_nan=False))
        check("depth_published", rendered["status"] == "created"
              and rendered["png_published"] and target.is_file())
        check("linear_depth_gradient", rendered["depth_rgba_value_count"] >= 16
              and rendered["artifact"]["unique_rgba"] == rendered["depth_rgba_value_count"] + 1
              and rendered["depth_range"]["span"] == 2.0
              and rendered["artifact"]["foreground_pixels"] > 0)
        check("receipt_bound", rendered["artifact"]["sha256"] ==
              hashlib.sha256(target.read_bytes()).hexdigest()
              and len(rendered["receipt_sha256"]) == 64)
        collision = namespace["render_2d_depth_pass_job"](
            str(job), prepared["job_sha256"], authorize=True)
        check("collision_refused", collision["status"] == "error" and target.is_file())
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "artifact_sha256": rendered["artifact"]["sha256"],
                  "receipt_sha256": rendered["receipt_sha256"],
                  "alpha_bounds": rendered["artifact"]["alpha_bounds"],
                  "foreground_pixels": rendered["artifact"]["foreground_pixels"],
                  "depth_rgba_values": rendered["depth_rgba_values"],
                  "blender_version": bpy.app.version_string}
    finally:
        target.unlink(missing_ok=True)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
        for path in root.glob(".gameassetai-depth-pass-*"):
            path.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
