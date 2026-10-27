"""Blender read-only probe for camera-basis normal signs and encoding."""
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
    namespace = {"__name__": "gameassetai_normal_candidate_test"}
    for name in ("validate_2d_normal_pass_request.py", "inspect_2d_normal_pass_candidate.py"):
        source = (repo / "scripts" / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    token = uuid.uuid4().hex
    target_file = root / ("normal-candidate-" + token + ".png")
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
    mesh = bpy.data.meshes.new("GAI_NormalProbeMesh_" + token)
    # Cross((1,-1,0), (1,0,-1)) = (1,1,1), giving camera components (+,+,-).
    mesh.from_pydata([(0, 0, 0), (1, -1, 0), (1, 0, -1)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new("GAI_NormalProbeObject_" + token, mesh)
    scene.collection.objects.link(obj)
    request = {"schema": namespace["SCHEMA"], "scene_name": scene.name, "object_name": obj.name,
               "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                        "up": [0, 0, 1], "framing_margin": 0.1},
               "normal": {"space": "CAMERA_BASIS", "source": "SHADING_NORMAL",
                          "encoding": "SIGNED_XYZ_TO_UNORM_RGB",
                          "background_rgba": [0.0, 0.0, 0.0, 0.0]},
               "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                         "nearest_neighbor": True},
               "output": {"target_file": str(target_file), "color_mode": "RGBA",
                          "color_depth": 8, "overwrite": False}}
    preflight = namespace["validate_2d_normal_pass_request"](request)
    check("request_valid", preflight["ready_for_blender_inspection"])
    candidate = namespace["inspect_2d_normal_pass_candidate"](request, preflight)
    check("candidate_reviewed", candidate["status"] == "candidate_for_review")
    sample = candidate["flat_face_reference_samples"][0]
    components = sample["camera_basis_reference"]
    check("camera_basis_signs", components[0] > 0 and components[1] > 0 and components[2] < 0)
    check("encoded_reference", sample["encoded_rgb_reference"] == [201, 201, 54])
    check("read_only_output", not target_file.exists()
          and sorted(path.name for path in root.iterdir()) == before_files)
    check("scene_count_preserved", len(bpy.data.scenes) == before_scenes)
    print("GAMEASSETAI_RESULT=" + json.dumps(
        {"status": "passed", "check_count": len(checks), "checks": checks,
         "camera_basis_reference": components,
         "encoded_rgb_reference": sample["encoded_rgb_reference"],
         "blender_version": bpy.app.version_string}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
