"""Render one hash-bound static Mesh stage in an isolated background Blender process."""
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


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _png(path):
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
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            predictors = {0: 0, 1: left, 2: above, 3: (left + above) // 2,
                          4: paeth(left, above, upper_left)}
            if filter_type not in predictors:
                raise ValueError("Unsupported PNG row filter")
            row[index] = (value + predictors[filter_type]) & 255
        rows.append([tuple(row[index:index + 4]) for index in range(0, stride, 4)])
        previous = row
    return data, width, height, depth, color_type, rows


def render_2d_staged_job(job_file, expected_job_sha256, *, authorize=False):
    report = {"schema": "gameassetai.2d-staged-render-result.v1", "status": "error",
              "errors": [], "png_published": False}
    stages = []
    target = None
    published = False
    try:
        if authorize is not True:
            raise ValueError("Explicit isolated render authorization is required")
        if not bpy.app.background or not bpy.data.filepath:
            raise ValueError("Staged rendering requires a background Blender with a loaded blend")
        job_path = Path(job_file)
        if not _regular(job_path):
            raise ValueError("Render job must be a regular file")
        job_data = job_path.read_bytes()
        if (not isinstance(expected_job_sha256, str) or len(expected_job_sha256) != 64
                or hashlib.sha256(job_data).hexdigest() != expected_job_sha256):
            raise ValueError("Render job changed before isolated execution")
        job = json.loads(job_data.decode("utf-8"))
        if set(job) != {"schema", "request", "candidate", "framing", "source_stage"} or job.get("schema") != "gameassetai.2d-staged-render-job.v1":
            raise ValueError("Render job schema or fields are invalid")
        request, candidate, framing, source_stage = (job[key] for key in
            ("request", "candidate", "framing", "source_stage"))
        target = Path(request["output"]["target_file"])
        loaded = Path(bpy.data.filepath)
        if (not target.is_absolute() or target.parent != job_path.parent
                or loaded != Path(source_stage["path"]) or loaded.parent != target.parent):
            raise ValueError("Loaded stage, job and target must share the reviewed directory")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta already exists")
        stage_data = loaded.read_bytes()
        if (len(stage_data) != source_stage.get("size")
                or hashlib.sha256(stage_data).hexdigest() != source_stage.get("sha256")):
            raise ValueError("Loaded source stage does not match the render job")
        request_sha = _hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or framing.get("plan_fingerprint") != _hash(framing.get("plan"))):
            raise ValueError("Reviewed request/candidate/framing chain is invalid")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if (not isinstance(candidate.get(key), str) or len(candidate[key]) != 64
                    or framing.get(key) != candidate[key]):
                raise ValueError("Candidate and framing fingerprints do not match")
        if (request["style"]["mode"] != "PIXEL"
                or request["style"]["anti_aliasing"] != "DISABLED"
                or request["style"]["nearest_neighbor"] is not True
                or request["lighting"]["mode"] != "OWNED_NEUTRAL"
                or request["output"]["color_mode"] != "RGBA"
                or request["output"]["color_depth"] != 8
                or request["output"]["overwrite"] is not False
                or request["style"]["palette_mode"] not in {"NONE", "AUTO", "FIXED"}
                or request["style"].get("shading_mode", "NONE") not in {"NONE", "VALUE_STEPS"}):
            raise ValueError("Job requests an unsupported first-version render mode")
        mesh_objects = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        if len(bpy.data.scenes) != 1 or len(bpy.context.scene.objects) != 1 or len(mesh_objects) != 1:
            raise ValueError("Source stage must contain exactly one Mesh Object")

        token = job_path.name.removeprefix(".gameassetai-2d-").removesuffix(".job.json")
        render_stage = target.parent / (".gameassetai-2d-" + token + ".render.stage.png")
        quantized_stage = target.parent / (".gameassetai-2d-" + token + ".quantized.stage.png")
        stages = [render_stage, quantized_stage]
        if any(path.exists() or path.is_symlink() for path in stages):
            raise ValueError("Owned PNG stage path already exists")

        scene, obj, plan = bpy.context.scene, mesh_objects[0], framing["plan"]
        camera_data = bpy.data.cameras.new("GAI_RenderCameraData_" + token)
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = plan["orthographic_scale"]
        camera_data.clip_start, camera_data.clip_end = plan["clip_start"], plan["clip_end"]
        camera = bpy.data.objects.new("GAI_RenderCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        basis = plan["basis_columns"]
        matrix = __import__("mathutils").Matrix((basis["right_x"], basis["up_y"],
                                                  basis["back_z"])).transposed().to_4x4()
        matrix.translation = __import__("mathutils").Vector(plan["position"])
        camera.matrix_world, scene.camera = matrix, camera
        light_data = bpy.data.lights.new("GAI_RenderLightData_" + token, "AREA")
        light_data.energy, light_data.shape, light_data.size = 800.0, "DISK", 5.0
        light = bpy.data.objects.new("GAI_RenderLight_" + token, light_data)
        scene.collection.objects.link(light)
        light.location = (3.0, -4.0, 6.0)
        light.rotation_euler = ((obj.location - light.location).to_track_quat("-Z", "Y").to_euler())
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = request["style"]["resolution"]
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "8"
        scene.render.filter_size, scene.render.filepath = 0.0, str(render_stage)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        data, width, height, depth, color_type, pixels = _png(render_stage)
        final_stage = render_stage
        processed = False
        source_visible = [(x, y, pixel) for y, row in enumerate(pixels)
                          for x, pixel in enumerate(row) if pixel[3] > 0]
        shading_mode = request["style"].get("shading_mode", "NONE")
        if shading_mode == "VALUE_STEPS":
            pixels = quantize_value_steps_rgba8(
                pixels, request["style"]["value_steps"])
            processed = True
            report["shading_value_levels_rgba8"] = sorted({
                max(pixel[:3]) for row in pixels for pixel in row if pixel[3] > 0})
        elif shading_mode != "NONE":
            raise ValueError("Job requests an unsupported shading mode")
        if request["style"]["palette_mode"] == "FIXED":
            pixels = quantize_fixed_rgba8(pixels, request["style"]["palette"])
            processed = True
        elif request["style"]["palette_mode"] == "AUTO":
            pixels, auto_palette = quantize_auto_rgba8(
                pixels, request["style"]["max_colors"])
            processed = True
            report["auto_palette_rgba8"] = [list(color) for color in auto_palette]
        outline_mode = request["style"].get("outline_mode", "NONE")
        if outline_mode == "OUTER":
            pixels = apply_outer_outline_rgba8(
                pixels, request["style"]["outline_color"],
                request["style"]["outline_width"])
            processed = True
            report["outline_rgba8"] = list(_rgba8_palette(
                [request["style"]["outline_color"]])[0])
        elif outline_mode != "NONE":
            raise ValueError("Job requests an unsupported outline mode")
        if processed:
            quantized_stage.write_bytes(encode_png_rgba8(pixels))
            final_stage = quantized_stage
        visible = [(x, y, pixel) for y, row in enumerate(pixels)
                   for x, pixel in enumerate(row) if pixel[3] > 0]
        if not visible:
            raise ValueError("Published render contains no visible pixels")
        report["outline_pixels"] = len(visible) - len(source_visible)
        xs, ys = [item[0] for item in visible], [item[1] for item in visible]
        facts = {"width": width, "height": height, "color_depth": depth,
                 "color_type": color_type,
                 "alpha_bounds": [min(xs), min(ys), max(xs), max(ys)],
                 "foreground_pixels": len(visible),
                 "unique_rgba": len({pixel for row in pixels for pixel in row})}
        os.link(final_stage, target)
        published = True
        receipt = build_2d_render_receipt(request, candidate, framing, facts)
        report.update(status="created", png_published=True, artifact=receipt["artifact"],
                      receipt_sha256=receipt["receipt_sha256"],
                      request_sha256=request_sha,
                      source_stage_sha256=source_stage["sha256"])
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
        if report["status"] != "created" and published and target is not None:
            try:
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
    result = render_2d_staged_job(args.job, args.job_sha256, authorize=True)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    if result["status"] != "created":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
