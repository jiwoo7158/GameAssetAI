"""Render a hash-bound multi-Object color-ID pass from isolated Mesh copies."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import bpy


def _object_id_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _object_id_regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _id_material(name, code):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    emission.inputs["Color"].default_value = (code / 255.0, 0.0, 0.0, 1.0)
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def render_2d_object_id_job(job_file, expected_job_sha256, *, authorize=False):
    report = {"schema": "gameassetai.2d-object-id-result.v1", "status": "error",
              "errors": [], "png_published": False}
    stages, target, published_hash = [], None, None
    try:
        if authorize is not True:
            raise ValueError("Explicit isolated object-id render authorization is required")
        if not bpy.app.background or not bpy.data.filepath:
            raise ValueError("Object-ID rendering requires background Blender with a loaded stage")
        job_path = Path(job_file)
        if not _object_id_regular(job_path):
            raise ValueError("Render job must be a regular file")
        job_data = job_path.read_bytes()
        if hashlib.sha256(job_data).hexdigest() != expected_job_sha256:
            raise ValueError("Render job changed before isolated execution")
        job = json.loads(job_data.decode("utf-8"))
        if (set(job) != {"schema", "request", "candidate", "framing", "source_stage"}
                or job.get("schema") != "gameassetai.2d-object-id-job.v1"):
            raise ValueError("Render job schema or fields are invalid")
        request, candidate, framing, source_stage = (job[key] for key in
            ("request", "candidate", "framing", "source_stage"))
        if request.get("schema") != "gameassetai.2d-object-id-request.v1":
            raise ValueError("Object-ID request schema mismatch")
        target, loaded = Path(request["output"]["target_file"]), Path(bpy.data.filepath)
        if (target.parent != job_path.parent or loaded != Path(source_stage["path"])
                or loaded.parent != target.parent):
            raise ValueError("Loaded stage, job and target must share the reviewed directory")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta already exists")
        stage_data = loaded.read_bytes()
        if (len(stage_data) != source_stage["size"]
                or hashlib.sha256(stage_data).hexdigest() != source_stage["sha256"]):
            raise ValueError("Loaded source stage does not match the render job")
        request_sha = _object_id_hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or framing.get("plan_fingerprint") != _object_id_hash(framing.get("plan"))):
            raise ValueError("Reviewed request/candidate/framing chain is invalid")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if framing.get(key) != candidate.get(key) or not isinstance(candidate.get(key), str):
                raise ValueError("Candidate and framing fingerprints do not match")
        if (request["style"] != {"resolution": request["style"]["resolution"],
                                 "anti_aliasing": "DISABLED", "nearest_neighbor": True}
                or request["output"]["color_mode"] != "RGBA"
                or request["output"]["color_depth"] != 8
                or request["output"]["overwrite"] is not False):
            raise ValueError("Unsupported object-id sampling/output mode")
        mesh_objects = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        if (len(bpy.data.scenes) != 1 or len(bpy.context.scene.objects) != len(request["objects"])
                or len(mesh_objects) != len(request["objects"])):
            raise ValueError("Source stage must contain exactly the requested Mesh Objects")
        try:
            mesh_objects.sort(key=lambda item: int(item["gameassetai_object_id_index"]))
        except (KeyError, TypeError, ValueError):
            raise ValueError("Staged Object-ID indices are missing or invalid")
        expected_indices = list(range(1, len(request["objects"]) + 1))
        if ([int(obj["gameassetai_object_id_index"]) for obj in mesh_objects] != expected_indices
                or [obj.get("gameassetai_object_id_source_name") for obj in mesh_objects]
                != [entry["object_name"] for entry in request["objects"]]):
            raise ValueError("Staged Object-ID membership/order does not match the request")

        token = job_path.name.removeprefix(".gameassetai-object-id-").removesuffix(".job.json")
        render_stage = target.parent / (".gameassetai-object-id-" + token + ".float.stage.exr")
        final_stage = target.parent / (".gameassetai-object-id-" + token + ".final.stage.png")
        stages = [render_stage, final_stage]
        if any(path.exists() or path.is_symlink() for path in stages):
            raise ValueError("Owned object-id stage path already exists")

        plan = framing["plan"]
        basis = plan["basis_columns"]
        for code, obj in enumerate(mesh_objects, 1):
            material = _id_material("GAI_IdPass_" + str(code) + "_" + token, code)
            obj.data.materials.clear()
            obj.data.materials.append(material)
            for face in obj.data.polygons:
                face.material_index = 0

        scene = bpy.context.scene
        camera_data = bpy.data.cameras.new("GAI_IdCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", plan["orthographic_scale"]
        camera_data.clip_start, camera_data.clip_end = plan["clip_start"], plan["clip_end"]
        camera = bpy.data.objects.new("GAI_IdCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        matrix = __import__("mathutils").Matrix((basis["right_x"], basis["up_y"], basis["back_z"])).transposed().to_4x4()
        matrix.translation = __import__("mathutils").Vector(plan["position"])
        camera.matrix_world, scene.camera = matrix, camera
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = request["style"]["resolution"]
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "OPEN_EXR"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "32"
        scene.render.filter_size, scene.render.filepath = 0.0, str(render_stage)
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        scene.view_settings.exposure, scene.view_settings.gamma = 0.0, 1.0
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if not render_stage.is_file() or render_stage.stat().st_size == 0:
            raise ValueError("Float id stage was not created")
        float_image = bpy.data.images.load(str(render_stage), check_existing=False)
        width, height = map(int, float_image.size)
        if [width, height] != request["style"]["resolution"]:
            raise ValueError("Float id stage dimensions do not match the request")
        values = list(float_image.pixels[:])
        bpy.data.images.remove(float_image)
        output_colors = {index: tuple(round(float(value) * 255) for value in entry["id_rgba"])
                         for index, entry in enumerate(request["objects"], 1)}
        visible_counts = {index: 0 for index in output_colors}
        converted, visible_count = [], 0
        for output_y in range(height):
            output_row = []
            source_y = height - 1 - output_y
            for x in range(width):
                index = (source_y * width + x) * 4
                red, green, blue, alpha = values[index:index + 4]
                if alpha > 0.0:
                    code = round(red * 255.0)
                    if code not in output_colors:
                        raise ValueError("Rendered pixel contains an unknown internal Object ID")
                    output_row.append(output_colors[code])
                    visible_counts[code] += 1
                    visible_count += 1
                else:
                    output_row.append((0, 0, 0, 0))
            converted.append(output_row)
        if visible_count == 0:
            raise ValueError("Rendered id pass has no visible pixels")
        final_stage.write_bytes(encode_png_rgba8(converted))
        os.link(final_stage, target)
        published_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        xs = [x for y, row in enumerate(converted) for x, pixel in enumerate(row) if pixel[3] > 0]
        ys = [y for y, row in enumerate(converted) for x, pixel in enumerate(row) if pixel[3] > 0]
        facts = {"width": width, "height": height, "color_depth": 8, "color_type": 6,
                 "alpha_bounds": [min(xs), min(ys), max(xs), max(ys)],
                 "foreground_pixels": visible_count,
                 "unique_rgba": len({pixel for row in converted for pixel in row})}
        visible_values = sorted({pixel for row in converted for pixel in row if pixel[3] > 0})
        receipt = build_2d_render_receipt(request, candidate, framing, facts)
        object_results = [
            {"object_name": entry["object_name"], "id_rgba8": list(output_colors[index]),
             "visible_pixels": visible_counts[index]}
            for index, entry in enumerate(request["objects"], 1)]
        report.update(status="created", png_published=True, artifact=receipt["artifact"],
                      receipt_sha256=receipt["receipt_sha256"], request_sha256=request_sha,
                      source_stage_sha256=source_stage["sha256"],
                      camera_basis=candidate["camera_basis"], objects=object_results,
                      visible_id_rgba8=[list(value) for value in visible_values])
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
    finally:
        for path in stages:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                report["errors"].append("object-id stage cleanup failed: " + str(cleanup))
                report["status"] = "error"
        if report["status"] != "created" and target is not None and published_hash:
            try:
                if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == published_hash:
                    target.unlink()
                    report["png_published"] = False
            except OSError as cleanup:
                report["errors"].append("published PNG rollback failed: " + str(cleanup))
    return report


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--helper-root", required=True, type=Path)
    args = parser.parse_args(tail)
    namespace = globals()
    for name in ("quantize_rgba.py", "build_2d_render_receipt.py"):
        source = (args.helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    result = render_2d_object_id_job(args.job, args.job_sha256, authorize=True)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    if result["status"] != "created":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
