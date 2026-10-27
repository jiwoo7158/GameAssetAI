"""Render a hash-bound camera-basis shading-normal pass from an isolated Mesh."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import bpy


def _normal_pass_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normal_pass_regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _normal_material(name, axes):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    geometry = tree.nodes.new("ShaderNodeNewGeometry")
    channels = []
    for axis in axes:
        dot = tree.nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = axis
        tree.links.new(geometry.outputs["Normal"], dot.inputs[0])
        scale = tree.nodes.new("ShaderNodeMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = 0.5
        tree.links.new(dot.outputs["Value"], scale.inputs[0])
        offset = tree.nodes.new("ShaderNodeMath")
        offset.operation = "ADD"
        offset.inputs[1].default_value = 0.5
        tree.links.new(scale.outputs[0], offset.inputs[0])
        channels.append(offset)
    combine = tree.nodes.new("ShaderNodeCombineColor")
    for node, socket in zip(channels, ("Red", "Green", "Blue")):
        tree.links.new(node.outputs[0], combine.inputs[socket])
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0
    tree.links.new(combine.outputs["Color"], emission.inputs["Color"])
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def render_2d_normal_pass_job(job_file, expected_job_sha256, *, authorize=False):
    report = {"schema": "gameassetai.2d-normal-pass-result.v1", "status": "error",
              "errors": [], "png_published": False}
    stages, target, published_hash = [], None, None
    try:
        if authorize is not True:
            raise ValueError("Explicit isolated normal-pass render authorization is required")
        if not bpy.app.background or not bpy.data.filepath:
            raise ValueError("Normal-pass rendering requires background Blender with a loaded stage")
        job_path = Path(job_file)
        if not _normal_pass_regular(job_path):
            raise ValueError("Render job must be a regular file")
        job_data = job_path.read_bytes()
        if hashlib.sha256(job_data).hexdigest() != expected_job_sha256:
            raise ValueError("Render job changed before isolated execution")
        job = json.loads(job_data.decode("utf-8"))
        if (set(job) != {"schema", "request", "candidate", "framing", "source_stage"}
                or job.get("schema") != "gameassetai.2d-normal-pass-job.v1"):
            raise ValueError("Render job schema or fields are invalid")
        request, candidate, framing, source_stage = (job[key] for key in
            ("request", "candidate", "framing", "source_stage"))
        if request.get("schema") != "gameassetai.2d-normal-pass-request.v1":
            raise ValueError("Normal-pass request schema mismatch")
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
        request_sha = _normal_pass_hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or framing.get("plan_fingerprint") != _normal_pass_hash(framing.get("plan"))):
            raise ValueError("Reviewed request/candidate/framing chain is invalid")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if framing.get(key) != candidate.get(key) or not isinstance(candidate.get(key), str):
                raise ValueError("Candidate and framing fingerprints do not match")
        if (request["style"] != {"resolution": request["style"]["resolution"],
                                 "anti_aliasing": "DISABLED", "nearest_neighbor": True}
                or request["output"]["color_mode"] != "RGBA"
                or request["output"]["color_depth"] != 8
                or request["output"]["overwrite"] is not False):
            raise ValueError("Unsupported normal-pass sampling/output mode")
        mesh_objects = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        if len(bpy.data.scenes) != 1 or len(bpy.context.scene.objects) != 1 or len(mesh_objects) != 1:
            raise ValueError("Source stage must contain exactly one Mesh Object")
        obj = mesh_objects[0]

        token = job_path.name.removeprefix(".gameassetai-normal-pass-").removesuffix(".job.json")
        render_stage = target.parent / (".gameassetai-normal-pass-" + token + ".float.stage.exr")
        final_stage = target.parent / (".gameassetai-normal-pass-" + token + ".final.stage.png")
        stages = [render_stage, final_stage]
        if any(path.exists() or path.is_symlink() for path in stages):
            raise ValueError("Owned normal-pass stage path already exists")

        plan = framing["plan"]
        basis = plan["basis_columns"]
        normal_material = _normal_material(
            "GAI_NormalPass_" + token,
            (tuple(basis["right_x"]), tuple(basis["up_y"]), tuple(basis["back_z"])))
        obj.data.materials.clear()
        obj.data.materials.append(normal_material)
        for face in obj.data.polygons:
            face.material_index = 0

        scene = bpy.context.scene
        camera_data = bpy.data.cameras.new("GAI_NormalCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", plan["orthographic_scale"]
        camera_data.clip_start, camera_data.clip_end = plan["clip_start"], plan["clip_end"]
        camera = bpy.data.objects.new("GAI_NormalCamera_" + token, camera_data)
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
            raise ValueError("Float normal stage was not created")
        float_image = bpy.data.images.load(str(render_stage), check_existing=False)
        width, height = map(int, float_image.size)
        if [width, height] != request["style"]["resolution"]:
            raise ValueError("Float normal stage dimensions do not match the request")
        values = list(float_image.pixels[:])
        bpy.data.images.remove(float_image)
        converted, visible_count = [], 0
        for output_y in range(height):
            output_row = []
            source_y = height - 1 - output_y
            for x in range(width):
                index = (source_y * width + x) * 4
                red, green, blue, alpha = values[index:index + 4]
                if alpha > 0.0:
                    output_row.append(tuple(max(0, min(255, round(value * 255.0)))
                                            for value in (red, green, blue)) + (255,))
                    visible_count += 1
                else:
                    output_row.append((0, 0, 0, 0))
            converted.append(output_row)
        if visible_count == 0:
            raise ValueError("Rendered normal pass has no visible pixels")
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
        report.update(status="created", png_published=True, artifact=receipt["artifact"],
                      receipt_sha256=receipt["receipt_sha256"], request_sha256=request_sha,
                      source_stage_sha256=source_stage["sha256"],
                      camera_basis=candidate["camera_basis"],
                      normal_rgba_values=(visible_values if len(visible_values) <= 16 else None),
                      normal_rgba_value_count=len(visible_values))
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
    finally:
        for path in stages:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                report["errors"].append("normal-pass stage cleanup failed: " + str(cleanup))
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
    result = render_2d_normal_pass_job(args.job, args.job_sha256, authorize=True)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    if result["status"] != "created":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

