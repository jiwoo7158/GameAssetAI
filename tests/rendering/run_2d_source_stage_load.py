"""Background regression: stage a reviewed Mesh copy, reopen that blend, verify, clean up."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import uuid

import bpy


def _arguments():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path)
    return parser.parse_args(tail)


def main():
    args = _arguments()
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError("Stage-load test requires background factory startup")
    root = args.artifact_root.resolve(strict=True)
    repo = args.repo_root.resolve(strict=True)
    helper_root = ((args.helper_root or (repo / "scripts")).resolve(strict=True))
    namespace = {"__name__": "gameassetai_2d_stage_load_helpers"}
    for name in ("validate_2d_static_render_request.py",
                 "inspect_2d_static_render_candidate.py",
                 "preview_2d_orthographic_framing.py",
                 "stage_2d_static_source.py", "build_2d_staged_render_job.py"):
        source = (helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    # Load the child entrypoint in its own globals, as Blender --python does. This
    # prevents the test harness's imported bpy from masking a missing entrypoint import.
    renderer_namespace = {"__name__": "gameassetai_2d_isolated_renderer"}
    for name in ("quantize_rgba.py", "build_2d_render_receipt.py",
                 "render_2d_staged_source.py"):
        source = (helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), renderer_namespace, renderer_namespace)

    token = uuid.uuid4().hex
    stage = root / (".gameassetai-2d-" + token + ".stage.blend")
    target = root / ("source-stage-load-" + token + ".png")
    job = root / (".gameassetai-2d-" + token + ".job.json")
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def run_renderer_cli(job_sha256, expect_success):
        previous = list(sys.argv)
        stream = io.StringIO()
        sys.argv = ["blender", "--", "--job", str(job),
                    "--job-sha256", job_sha256,
                    "--helper-root", str(helper_root)]
        exit_code = 0
        try:
            with contextlib.redirect_stdout(stream):
                renderer_namespace["main"]()
        except SystemExit as exc:
            exit_code = int(exc.code or 0)
        finally:
            sys.argv = previous
        lines = [line for line in stream.getvalue().splitlines()
                 if line.startswith("GAMEASSETAI_RESULT=")]
        if len(lines) != 1:
            raise AssertionError("renderer_cli_result")
        result = json.loads(lines[0].split("=", 1)[1])
        if (exit_code == 0) is not expect_success:
            raise AssertionError("renderer_cli_exit")
        return result

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        mesh = bpy.data.meshes.new("GAI_StageLoadMesh_" + token)
        # Two visible facets share a ridge but face different horizontal directions.
        # The owned off-axis light must therefore produce multiple live value bands.
        mesh.from_pydata([(-1, 0, -1), (0, -0.6, -1), (1, 0, -1),
                          (-1, 0, 1), (0, -0.6, 1), (1, 0, 1)],
                         [], [(0, 1, 4, 3), (1, 2, 5, 4)])
        obj = bpy.data.objects.new("GAI_StageLoadObject_" + token, mesh)
        scene.collection.objects.link(obj)
        material = bpy.data.materials.new("GAI_StageLoadMaterial_" + token)
        material.diffuse_color = (0.25, 0.5, 0.75, 1.0)
        mesh.materials.append(material)
        request = {"schema": namespace["SCHEMA"], "scene_name": scene.name,
            "object_name": obj.name,
            "profile": {"name": None, "reference_sha256": None,
                        "profile_sha256": None},
            "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                     "up": [0, 0, 1], "framing_margin": 0.1},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [32, 24],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "AUTO", "palette": [], "max_colors": 4,
                      "outline_mode": "OUTER", "outline_color": [0, 0, 0, 1],
                      "outline_width": 1, "shading_mode": "VALUE_STEPS",
                      "value_steps": 4},
            "output": {"target_file": str(target), "color_mode": "RGBA",
                       "color_depth": 8, "overwrite": False}}
        preflight = namespace["validate_2d_static_render_request"](request)
        candidate = namespace["inspect_2d_static_render_candidate"](request, preflight)
        framing = namespace["preview_2d_orthographic_framing"](request, candidate)
        staged = namespace["stage_2d_static_source"](
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("stage_created", staged["status"] == "created" and stage.is_file())
        expected_sha = staged["stage_sha256"]
        expected_size = staged["stage_size"]
        prepared = namespace["build_2d_staged_render_job"](
            request, candidate, framing, staged, str(job), authorize=True)
        check("job_created", prepared["status"] == "created" and job.is_file())

        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        check("stage_loaded", Path(bpy.data.filepath) == stage)
        mesh_objects = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        check("one_independent_mesh", len(bpy.data.scenes) == 1
              and len(bpy.context.scene.objects) == 1 and len(mesh_objects) == 1
              and mesh_objects[0].data is not None)
        loaded = mesh_objects[0]
        check("geometry_preserved", len(loaded.data.vertices) == 6
              and len(loaded.data.polygons) == 2)
        check("material_preserved", len(loaded.data.materials) == 1)
        check("stage_identity_preserved", stage.stat().st_size == expected_size
              and __import__("hashlib").sha256(stage.read_bytes()).hexdigest() == expected_sha)
        check("no_png_before_render", not target.exists())
        rendered = run_renderer_cli(prepared["job_sha256"], True)
        check("png_published", rendered["status"] == "created"
              and rendered["png_published"] and target.is_file())
        target_bytes = target.read_bytes()
        check("receipt_bound", rendered["artifact"]["sha256"] ==
              __import__("hashlib").sha256(target_bytes).hexdigest()
              and len(rendered["receipt_sha256"]) == 64)
        check("auto_palette_bounded", 1 <= len(rendered["auto_palette_rgba8"]) <= 4
              and rendered["artifact"]["unique_rgba"] <= 6)
        check("outer_outline_applied", rendered["outline_pixels"] > 0
              and rendered["outline_rgba8"] == [0, 0, 0, 255])
        check("multiple_value_steps_bounded", 2 <= len(rendered["shading_value_levels_rgba8"]) <= 4
              and all(level in {0, 85, 170, 255}
                      for level in rendered["shading_value_levels_rgba8"]))
        collision = run_renderer_cli(prepared["job_sha256"], False)
        check("target_collision_refused", collision["status"] == "error"
              and target.read_bytes() == target_bytes)
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "stage_sha256": expected_sha,
                  "artifact_sha256": rendered["artifact"]["sha256"],
                  "receipt_sha256": rendered["receipt_sha256"],
                  "alpha_bounds": rendered["artifact"]["alpha_bounds"],
                  "outline_pixels": rendered["outline_pixels"],
                  "shading_value_levels_rgba8": rendered["shading_value_levels_rgba8"],
                  "auto_palette_rgba8": rendered["auto_palette_rgba8"],
                  "blender_version": bpy.app.version_string}
    finally:
        target.unlink(missing_ok=True)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"] = len(checks)
    result["checks"] = checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
