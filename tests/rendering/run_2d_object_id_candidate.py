"""Blender read-only probe for explicit multi-Object color-ID membership."""
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
    namespace = {"__name__": "gameassetai_object_id_candidate_test"}
    for name in ("validate_2d_object_id_request.py", "inspect_2d_object_id_candidate.py"):
        source = (repo / "scripts" / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    token = uuid.uuid4().hex
    target = root / ("object-id-candidate-" + token + ".png")
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
    objects = []
    for label, location in (("A", (-2, 0, 0)), ("B", (2, 0, 0)), ("Unlisted", (100, 0, 0))):
        bpy.ops.mesh.primitive_cube_add(size=1, location=location)
        obj = bpy.context.object
        obj.name = "GAI_Id" + label + "_" + token
        objects.append(obj)
    request = {"schema": namespace["SCHEMA"], "scene_name": scene.name,
               "objects": [
                   {"object_name": objects[0].name, "id_rgba": [1, 0, 0, 1]},
                   {"object_name": objects[1].name, "id_rgba": [0, 1, 0, 1]}],
               "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                        "up": [0, 0, 1], "framing_margin": 0.1},
               "style": {"resolution": [32, 32], "anti_aliasing": "DISABLED",
                         "nearest_neighbor": True},
               "output": {"target_file": str(target), "color_mode": "RGBA",
                          "color_depth": 8, "overwrite": False}}
    preflight = namespace["validate_2d_object_id_request"](request)
    check("request_valid", preflight["ready_for_blender_inspection"])
    candidate = namespace["inspect_2d_object_id_candidate"](request, preflight)
    check("candidate_reviewed", candidate["status"] == "candidate_for_review")
    check("exact_order_and_colors", [item["name"] for item in candidate["objects"]]
          == [objects[0].name, objects[1].name]
          and [item["id_rgba8"] for item in candidate["objects"]]
          == [[255, 0, 0, 255], [0, 255, 0, 255]])
    check("unlisted_excluded", candidate["world_bounds"]["maximum"][0] < 10
          and objects[2].name not in [item["name"] for item in candidate["objects"]])
    objects[1].modifiers.new("GAI_Blocker_" + token, "BEVEL")
    blocked = namespace["inspect_2d_object_id_candidate"](request, preflight)
    check("dependency_blocked", blocked["status"] == "blocked"
          and any("modifiers_unsupported" in item for item in blocked["blockers"]))
    check("read_only_output", not target.exists()
          and sorted(path.name for path in root.iterdir()) == before_files)
    check("scene_count_preserved", len(bpy.data.scenes) == before_scenes)
    print("GAMEASSETAI_RESULT=" + json.dumps(
        {"status": "passed", "check_count": len(checks), "checks": checks,
         "objects": candidate["objects"], "world_bounds": candidate["world_bounds"],
         "blender_version": bpy.app.version_string}, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
