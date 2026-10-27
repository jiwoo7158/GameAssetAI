"""Blender read-only probe for camera-linear vertex range and encoding."""
from __future__ import annotations

import argparse
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
    args = parser.parse_args(tail)
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    namespace = {"__name__": "gameassetai_depth_candidate_test"}
    for name in ("validate_2d_depth_pass_request.py", "inspect_2d_depth_pass_candidate.py"):
        source = (repo / "scripts" / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    token = uuid.uuid4().hex
    target_file = root / ("depth-candidate-" + token + ".png")
    before_files = sorted(path.name for path in root.iterdir())
    before_scenes = len(bpy.data.scenes)
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.context.scene
    for existing in list(scene.objects):
        bpy.data.objects.remove(existing, do_unlink=True)
    mesh = bpy.data.meshes.new("GAI_DepthProbeMesh_" + token)
    # Under back-to-camera -Y, projections are near=+1, middle=0, far=-1.
    mesh.from_pydata([(-1, -1, -1), (1, 0, -1), (0, 1, 1)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new("GAI_DepthProbeObject_" + token, mesh)
    scene.collection.objects.link(obj)
    request = {"schema": namespace["SCHEMA"], "scene_name": scene.name, "object_name": obj.name,
               "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                        "up": [0, 0, 1], "framing_margin": 0.1},
               "depth": {"space": "CAMERA_LINEAR", "source": "BASE_MESH_POSITION",
                          "normalization": "OBJECT_VERTEX_BOUNDS",
                          "encoding": "NEAR_BLACK_FAR_WHITE_UNORM_RGB",
                          "background_rgba": [0.0, 0.0, 0.0, 0.0]},
               "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                         "nearest_neighbor": True},
               "output": {"target_file": str(target_file), "color_mode": "RGBA",
                          "color_depth": 8, "overwrite": False}}
    preflight = namespace["validate_2d_depth_pass_request"](request)
    check("request_valid", preflight["ready_for_blender_inspection"])
    candidate = namespace["inspect_2d_depth_pass_candidate"](request, preflight)
    check("candidate_reviewed", candidate["status"] == "candidate_for_review")
    depth_range = candidate["depth_range"]
    samples = candidate["vertex_reference_samples"]
    check("exact_vertex_range", depth_range["near_projection"] == 1.0
          and depth_range["far_projection"] == -1.0 and depth_range["span"] == 2.0)
    check("near_middle_far_encoding",
          [sample["encoded_rgb_reference"] for sample in samples]
          == [[0, 0, 0], [128, 128, 128], [255, 255, 255]])
    for vertex in mesh.vertices:
        vertex.co.y = 0
    mesh.update()
    blocked = namespace["inspect_2d_depth_pass_candidate"](request, preflight)
    check("zero_span_blocked", blocked["status"] == "blocked"
          and "base_mesh_depth_span_too_small" in blocked["blockers"])
    check("read_only_output", not target_file.exists()
          and sorted(path.name for path in root.iterdir()) == before_files)
    check("scene_count_preserved", len(bpy.data.scenes) == before_scenes)
    print("GAMEASSETAI_RESULT=" + json.dumps(
        {"status": "passed", "check_count": len(checks), "checks": checks,
         "depth_range": depth_range,
         "encoded_rgb_references": [sample["encoded_rgb_reference"] for sample in samples],
         "blender_version": bpy.app.version_string}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
