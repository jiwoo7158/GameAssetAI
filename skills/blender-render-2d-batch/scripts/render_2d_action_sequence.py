"""Render one hash-bound Action sequence in an isolated background Blender process."""
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


SEQUENCE_RESULT_SCHEMA = "gameassetai.2d-action-sequence-result.v1"


def _sequence_render_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _sequence_render_regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _decode_sequence_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Rendered sequence stage is not a PNG")
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
        raise ValueError("Rendered sequence stages must be non-interlaced RGBA8")
    raw = zlib.decompress(b"".join(chunks))
    stride, previous, offset, rows = width * 4, bytearray(width * 4), 0, []

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


def render_2d_action_sequence_job(job_file, expected_job_sha256, *, authorize=False):
    """Render and verify all owned stages before publishing; roll back partial publication."""
    report = {"schema": SEQUENCE_RESULT_SCHEMA, "status": "error", "errors": [],
              "pngs_published": False, "published_count": 0}
    temporary, published = [], []
    try:
        if authorize is not True:
            raise ValueError("Explicit isolated Action-sequence render authorization is required")
        if not bpy.app.background or not bpy.data.filepath:
            raise ValueError("Action-sequence rendering requires background Blender with a loaded blend")
        job_path = Path(job_file)
        if not _sequence_render_regular(job_path):
            raise ValueError("Action-sequence render job must be a regular file")
        job_data = job_path.read_bytes()
        if (not isinstance(expected_job_sha256, str) or len(expected_job_sha256) != 64
                or hashlib.sha256(job_data).hexdigest() != expected_job_sha256):
            raise ValueError("Action-sequence render job changed before execution")
        job = json.loads(job_data.decode("utf-8"))
        expected_fields = {"schema", "request", "frames", "candidate", "framing",
                           "source_stage"}
        if set(job) != expected_fields or job.get("schema") != SEQUENCE_JOB_SCHEMA:
            raise ValueError("Action-sequence render job schema or fields are invalid")
        request, frames, candidate, framing, source_stage = (
            job[key] for key in ("request", "frames", "candidate", "framing", "source_stage"))
        directory = Path(request["output"]["target_directory"])
        loaded = Path(bpy.data.filepath)
        if (not directory.is_absolute() or job_path.parent != directory
                or loaded != Path(source_stage["path"]) or loaded.parent != directory):
            raise ValueError("Loaded stage, job and targets must share the reviewed directory")
        stage_data = loaded.read_bytes()
        if (len(stage_data) != source_stage.get("size")
                or hashlib.sha256(stage_data).hexdigest() != source_stage.get("sha256")):
            raise ValueError("Loaded Action-sequence stage does not match the job")
        request_sha = _sequence_render_hash(request)
        frame_plan_sha = _sequence_render_hash(frames)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or candidate.get("frame_plan_sha256") != frame_plan_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or framing.get("frame_plan_sha256") != frame_plan_sha
                or framing.get("plan_fingerprint") != _sequence_render_hash(framing.get("plan"))):
            raise ValueError("Reviewed Action-sequence request/candidate/framing chain is invalid")
        for key in ("source_fingerprint", "action_fingerprint", "evaluation_fingerprint"):
            if (not isinstance(candidate.get(key), str) or len(candidate[key]) != 64
                    or framing.get(key) != candidate[key]):
                raise ValueError("Action-sequence candidate and framing fingerprints differ")
        targets = [Path(frame["target_file"]) for frame in frames]
        if (not frames or len(frames) != candidate.get("frame_count")
                or len(set(targets)) != len(targets)
                or any(not target.is_absolute() or target.parent != directory
                       or target.suffix.lower() != ".png" for target in targets)):
            raise ValueError("Action-sequence frame plan targets are invalid")
        if any(target.exists() or Path(str(target) + ".meta").exists() for target in targets):
            raise ValueError("A planned PNG or sibling .meta already exists")

        scene = bpy.context.scene
        meshes = [item for item in scene.objects if item.type == "MESH"]
        rigs = [item for item in scene.objects if item.type == "ARMATURE"]
        if (len(bpy.data.scenes) != 1 or len(meshes) != 1 or len(rigs) != 1
                or len(bpy.data.actions) != 1):
            raise ValueError("Sequence stage must contain one Scene, Mesh, Armature and Action")
        mesh_obj, rig, action = meshes[0], rigs[0], bpy.data.actions[0]
        modifiers = [item for item in mesh_obj.modifiers if item.type == "ARMATURE"]
        if (len(modifiers) != 1 or modifiers[0].object != rig
                or rig.animation_data is None or rig.animation_data.action != action):
            raise ValueError("Sequence stage binding or Armature modifier is invalid")

        style = request["static_template"]["style"]
        lighting = request["static_template"]["lighting"]
        if (style["mode"] != "PIXEL" or style["anti_aliasing"] != "DISABLED"
                or style["nearest_neighbor"] is not True
                or style["palette_mode"] not in {"NONE", "AUTO", "FIXED"}
                or style.get("shading_mode", "NONE") not in {"NONE", "VALUE_STEPS"}
                or lighting["mode"] != "OWNED_NEUTRAL"
                or lighting["transparent_background"] is not True):
            raise ValueError("Job requests an unsupported Action-sequence render mode")

        token = job_path.name.removeprefix(".gameassetai-2d-sequence-").removesuffix(".job.json")
        plan = framing["plan"]
        camera_data = bpy.data.cameras.new("GAI_SequenceCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", plan["orthographic_scale"]
        camera_data.clip_start, camera_data.clip_end = plan["clip_start"], plan["clip_end"]
        camera = bpy.data.objects.new("GAI_SequenceCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        basis = plan["basis_columns"]
        matrix = __import__("mathutils").Matrix((basis["right_x"], basis["up_y"],
                                                  basis["back_z"])).transposed().to_4x4()
        matrix.translation = __import__("mathutils").Vector(plan["position"])
        camera.matrix_world, scene.camera = matrix, camera
        light_data = bpy.data.lights.new("GAI_SequenceLightData_" + token, "AREA")
        light_data.energy, light_data.shape, light_data.size = 800.0, "DISK", 5.0
        light = bpy.data.objects.new("GAI_SequenceLight_" + token, light_data)
        scene.collection.objects.link(light)
        light.location = (3.0, -4.0, 6.0)
        light.rotation_euler = ((mesh_obj.location - light.location)
                                .to_track_quat("-Z", "Y").to_euler())
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = style["resolution"]
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "8"
        scene.render.filter_size = 0.0

        artifacts = []
        final_stages = []
        for ordinal, (planned, target) in enumerate(zip(frames, targets)):
            render_stage = directory / (
                f".gameassetai-2d-sequence-{token}.{ordinal:06d}.render.stage.png")
            processed_stage = directory / (
                f".gameassetai-2d-sequence-{token}.{ordinal:06d}.processed.stage.png")
            temporary.extend((render_stage, processed_stage))
            if any(path.exists() or path.is_symlink() for path in (render_stage, processed_stage)):
                raise ValueError("Owned Action-sequence PNG stage path already exists")
            scene.frame_set(planned["source_frame"])
            scene.render.filepath = str(render_stage)
            bpy.ops.render.render(write_still=True, scene=scene.name)
            _, width, height, depth, color_type, pixels = _decode_sequence_png(render_stage)
            source_visible = sum(pixel[3] > 0 for row in pixels for pixel in row)
            processed = False
            if style.get("shading_mode", "NONE") == "VALUE_STEPS":
                pixels = quantize_value_steps_rgba8(pixels, style["value_steps"])
                processed = True
            if style["palette_mode"] == "FIXED":
                pixels = quantize_fixed_rgba8(pixels, style["palette"])
                processed = True
            elif style["palette_mode"] == "AUTO":
                pixels, _ = quantize_auto_rgba8(pixels, style["max_colors"])
                processed = True
            if style.get("outline_mode", "NONE") == "OUTER":
                pixels = apply_outer_outline_rgba8(
                    pixels, style["outline_color"], style["outline_width"])
                processed = True
            elif style.get("outline_mode", "NONE") != "NONE":
                raise ValueError("Unsupported Action-sequence outline mode")
            final_stage = render_stage
            if processed:
                processed_stage.write_bytes(encode_png_rgba8(pixels))
                final_stage = processed_stage
            visible = [(x, y, pixel) for y, row in enumerate(pixels)
                       for x, pixel in enumerate(row) if pixel[3] > 0]
            if not visible:
                raise ValueError("A rendered Action-sequence frame contains no visible pixels")
            xs, ys = [item[0] for item in visible], [item[1] for item in visible]
            final_data = final_stage.read_bytes()
            artifacts.append({"source_frame": planned["source_frame"],
                              "sequence_index": planned["sequence_index"],
                              "path": str(target), "size": len(final_data),
                              "sha256": hashlib.sha256(final_data).hexdigest(),
                              "width": width, "height": height,
                              "color_depth": depth, "color_type": color_type,
                              "alpha_bounds": [min(xs), min(ys), max(xs), max(ys)],
                              "foreground_pixels": len(visible),
                              "outline_pixels": len(visible) - source_visible,
                              "unique_rgba": len({pixel for row in pixels for pixel in row}),
                              "anchor_pixel_from_bottom_left": plan["anchor_pixel_from_bottom_left"]})
            final_stages.append(final_stage)

        if any(target.exists() or Path(str(target) + ".meta").exists() for target in targets):
            raise ValueError("A planned target appeared before Action-sequence publication")
        for final_stage, target in zip(final_stages, targets):
            os.link(final_stage, target)
            published.append(target)
        receipt = {"schema": "gameassetai.2d-action-sequence-receipt.v1",
                   "request_sha256": request_sha,
                   "frame_plan_sha256": frame_plan_sha,
                   "source_fingerprint": candidate["source_fingerprint"],
                   "action_fingerprint": candidate["action_fingerprint"],
                   "evaluation_fingerprint": candidate["evaluation_fingerprint"],
                   "plan_fingerprint": framing["plan_fingerprint"],
                   "source_stage_sha256": source_stage["sha256"],
                   "artifacts": artifacts}
        receipt["receipt_sha256"] = _sequence_render_hash(receipt)
        report.update(status="created", pngs_published=True,
                      published_count=len(published), frame_count=len(frames),
                      request_sha256=request_sha, frame_plan_sha256=frame_plan_sha,
                      artifacts=artifacts, receipt_sha256=receipt["receipt_sha256"])
    except (ValueError, TypeError, KeyError, OSError, RuntimeError,
            json.JSONDecodeError, struct.error, zlib.error) as exc:
        report["errors"].append(str(exc))
    finally:
        for path in temporary:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                report["errors"].append("Sequence PNG stage cleanup failed: " + str(cleanup))
                report["status"] = "error"
        if report["status"] != "created":
            for path in reversed(published):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                except OSError as cleanup:
                    report["errors"].append("Published sequence rollback failed: " + str(cleanup))
            report["pngs_published"] = False
            report["published_count"] = sum(path.exists() for path in published)
    return report


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--helper-root", required=True, type=Path)
    args = parser.parse_args(tail)
    namespace = globals()
    for name in ("quantize_rgba.py", "build_2d_action_sequence_job.py"):
        source = (args.helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    result = render_2d_action_sequence_job(args.job, args.job_sha256, authorize=True)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    if result["status"] != "created":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

