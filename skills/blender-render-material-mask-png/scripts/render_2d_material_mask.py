"""Render a hash-bound material-slot mask from an isolated staged Mesh."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import struct
import sys
import zlib

import bpy


def _material_mask_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _material_mask_regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _material_mask_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Rendered stage is not a PNG")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    chunks, position, interlace = [], 8, None
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        position += 12 + length
        if kind == b"IHDR":
            interlace = payload[12]
        elif kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            break
    if depth != 8 or color_type != 6 or interlace != 0:
        raise ValueError("Rendered stage must be non-interlaced RGBA8")
    raw, stride, previous, offset, rows = zlib.decompress(b"".join(chunks)), width * 4, bytearray(width * 4), 0, []

    def paeth(a, b, c):
        estimate = a + b - c
        values = (a, b, c)
        return values[min(range(3), key=lambda index: abs(estimate - values[index]))]

    for _ in range(height):
        filter_type = raw[offset]
        encoded = raw[offset + 1:offset + 1 + stride]
        offset += 1 + stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left, above = (row[index - 4] if index >= 4 else 0), previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            predictors = {0: 0, 1: left, 2: above, 3: (left + above) // 2,
                          4: paeth(left, above, upper_left)}
            if filter_type not in predictors:
                raise ValueError("Unsupported PNG row filter")
            row[index] = (value + predictors[filter_type]) & 255
        rows.append([tuple(row[index:index + 4]) for index in range(0, stride, 4)])
        previous = row
    return width, height, rows


def _id_material(name, color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    emission = tree.nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = color
    emission.inputs["Strength"].default_value = 1.0
    tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def render_2d_material_mask_job(job_file, expected_job_sha256, *, authorize=False):
    report = {"schema": "gameassetai.2d-material-mask-result.v1", "status": "error",
              "errors": [], "png_published": False}
    stages, target, published_hash = [], None, None
    try:
        if authorize is not True:
            raise ValueError("Explicit isolated material-mask render authorization is required")
        if not bpy.app.background or not bpy.data.filepath:
            raise ValueError("Material-mask rendering requires background Blender with a loaded stage")
        job_path = Path(job_file)
        if not _material_mask_regular(job_path):
            raise ValueError("Render job must be a regular file")
        job_data = job_path.read_bytes()
        if hashlib.sha256(job_data).hexdigest() != expected_job_sha256:
            raise ValueError("Render job changed before isolated execution")
        job = json.loads(job_data.decode("utf-8"))
        if (set(job) != {"schema", "request", "candidate", "framing", "source_stage"}
                or job.get("schema") != "gameassetai.2d-material-mask-job.v1"):
            raise ValueError("Render job schema or fields are invalid")
        request, candidate, framing, source_stage = (job[key] for key in
            ("request", "candidate", "framing", "source_stage"))
        if request.get("schema") != "gameassetai.2d-material-mask-request.v1":
            raise ValueError("Material-mask request schema mismatch")
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
        request_sha = _material_mask_hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or framing.get("plan_fingerprint") != _material_mask_hash(framing.get("plan"))):
            raise ValueError("Reviewed request/candidate/framing chain is invalid")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if framing.get(key) != candidate.get(key) or not isinstance(candidate.get(key), str):
                raise ValueError("Candidate and framing fingerprints do not match")
        if (request["style"] != {"resolution": request["style"]["resolution"],
                                 "anti_aliasing": "DISABLED", "nearest_neighbor": True}
                or request["output"]["color_mode"] != "RGBA"
                or request["output"]["color_depth"] != 8
                or request["output"]["overwrite"] is not False):
            raise ValueError("Unsupported material-mask sampling/output mode")
        mesh_objects = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        if len(bpy.data.scenes) != 1 or len(bpy.context.scene.objects) != 1 or len(mesh_objects) != 1:
            raise ValueError("Source stage must contain exactly one Mesh Object")
        obj = mesh_objects[0]
        slot_index = request["mask"]["material_slot_index"]
        if slot_index >= len(obj.material_slots):
            raise ValueError("Reviewed material slot is no longer present")
        if not any(face.material_index == slot_index for face in obj.data.polygons):
            raise ValueError("Reviewed material slot has no faces")

        token = job_path.name.removeprefix(".gameassetai-material-mask-").removesuffix(".job.json")
        render_stage = target.parent / (".gameassetai-material-mask-" + token + ".render.stage.png")
        final_stage = target.parent / (".gameassetai-material-mask-" + token + ".final.stage.png")
        stages = [render_stage, final_stage]
        if any(path.exists() or path.is_symlink() for path in stages):
            raise ValueError("Owned PNG stage path already exists")

        target_material = _id_material("GAI_MaskTarget_" + token, (1, 0, 0, 1))
        blocker_material = _id_material("GAI_MaskBlocker_" + token, (0, 1, 0, 1))
        slot_count = len(obj.data.materials)
        face_material_indices = [face.material_index for face in obj.data.polygons]
        obj.data.materials.clear()
        for index in range(slot_count):
            obj.data.materials.append(target_material if index == slot_index else blocker_material)
        for face, material_index in zip(obj.data.polygons, face_material_indices):
            face.material_index = material_index

        scene, plan = bpy.context.scene, framing["plan"]
        camera_data = bpy.data.cameras.new("GAI_MaskCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", plan["orthographic_scale"]
        camera_data.clip_start, camera_data.clip_end = plan["clip_start"], plan["clip_end"]
        camera = bpy.data.objects.new("GAI_MaskCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        basis = plan["basis_columns"]
        matrix = __import__("mathutils").Matrix((basis["right_x"], basis["up_y"], basis["back_z"])).transposed().to_4x4()
        matrix.translation = __import__("mathutils").Vector(plan["position"])
        camera.matrix_world, scene.camera = matrix, camera
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = request["style"]["resolution"]
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "8"
        scene.render.filter_size, scene.render.filepath = 0.0, str(render_stage)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        width, height, pixels = _material_mask_png(render_stage)
        color = tuple(round(float(value) * 255) for value in request["mask"]["visible_rgba"])
        converted, visible_count, occluder_count = [], 0, 0
        for row in pixels:
            output_row = []
            for red, green, blue, alpha in row:
                if alpha > 0 and red > green:
                    output_row.append(color)
                    visible_count += 1
                else:
                    output_row.append((0, 0, 0, 0))
                    if alpha > 0 and green > red:
                        occluder_count += 1
            converted.append(output_row)
        if visible_count == 0:
            raise ValueError("Rendered target material has no visible pixels")
        final_stage.write_bytes(encode_png_rgba8(converted))
        os.link(final_stage, target)
        published_hash = hashlib.sha256(target.read_bytes()).hexdigest()
        xs = [x for y, row in enumerate(converted) for x, pixel in enumerate(row) if pixel[3] > 0]
        ys = [y for y, row in enumerate(converted) for x, pixel in enumerate(row) if pixel[3] > 0]
        facts = {"width": width, "height": height, "color_depth": 8, "color_type": 6,
                 "alpha_bounds": [min(xs), min(ys), max(xs), max(ys)],
                 "foreground_pixels": visible_count,
                 "unique_rgba": len({pixel for row in converted for pixel in row})}
        receipt = build_2d_render_receipt(request, candidate, framing, facts)
        report.update(status="created", png_published=True, artifact=receipt["artifact"],
                      receipt_sha256=receipt["receipt_sha256"], request_sha256=request_sha,
                      source_stage_sha256=source_stage["sha256"],
                      material_slot=candidate["material_slot"], occluder_pixels=occluder_count)
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
    finally:
        for path in stages:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                report["errors"].append("PNG stage cleanup failed: " + str(cleanup))
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
    result = render_2d_material_mask_job(args.job, args.job_sha256, authorize=True)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    if result["status"] != "created":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
