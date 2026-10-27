"""Blender background-process probe for isolated staged PNG rendering.

Run only with ``--background --factory-startup``. It owns every Blender ID in that
process and removes only its two unique output paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import uuid
import zlib

import bpy


def _arguments():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    return parser.parse_args(tail)


def _png_header(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise AssertionError("png_signature")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    return data, width, height, depth, color_type


def _rgba8_pixels(data, width, height):
    chunks = []
    position = 8
    interlace = None
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
    if interlace != 0:
        raise AssertionError("png_noninterlaced")
    raw = zlib.decompress(b"".join(chunks))
    stride, bpp = width * 4, 4
    rows, previous, offset = [], bytearray(stride), 0

    def paeth(a, b, c):
        estimate = a + b - c
        distances = (abs(estimate - a), abs(estimate - b), abs(estimate - c))
        return (a, b, c)[distances.index(min(distances))]

    for _ in range(height):
        filter_type = raw[offset]
        encoded = raw[offset + 1:offset + 1 + stride]
        offset += 1 + stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - bpp] if index >= bpp else 0
            above = previous[index]
            upper_left = previous[index - bpp] if index >= bpp else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                predictor = paeth(left, above, upper_left)
            else:
                raise AssertionError("png_filter_supported")
            row[index] = (value + predictor) & 255
        rows.append(row)
        previous = row
    return [[tuple(row[index:index + 4]) for index in range(0, stride, 4)] for row in rows]


def main():
    args = _arguments()
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError("Probe requires background factory startup without a blend file")
    root = args.artifact_root.resolve(strict=True)
    repo = args.repo_root.resolve(strict=True)
    if not root.is_dir():
        raise RuntimeError("artifact root must be an existing directory")
    namespace = {}
    for relative in ("scripts/validate_2d_static_render_request.py",
                     "scripts/inspect_2d_static_render_candidate.py",
                     "scripts/preview_2d_orthographic_framing.py",
                     "scripts/quantize_rgba.py",
                     "scripts/build_2d_render_receipt.py"):
        source = (repo / relative).read_text(encoding="utf-8-sig")
        exec(compile(source, relative, "exec"), namespace, namespace)
    token = uuid.uuid4().hex
    stage = root / f".gameassetai-2d-{token}.stage.png"
    repeat_stage = root / f".gameassetai-2d-{token}.repeat.stage.png"
    quantized_stage = root / f".gameassetai-2d-{token}.quantized.stage.png"
    target = root / f"gameassetai-2d-{token}.png"
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        check("factory_background", bpy.app.background and not bpy.data.filepath)
        scene = bpy.context.scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

        mesh = bpy.data.meshes.new("GAI_RenderMesh_" + token)
        mesh.from_pydata([(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                          (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
                         [], [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
                              (1, 5, 6, 2), (2, 6, 7, 3), (4, 0, 3, 7)])
        obj = bpy.data.objects.new("GAI_RenderObject_" + token, mesh)
        scene.collection.objects.link(obj)
        material = bpy.data.materials.new("GAI_RenderMaterial_" + token)
        material.diffuse_color = (0.8, 0.2, 0.1, 1.0)
        obj.data.materials.append(material)

        request = {
            "schema": namespace["SCHEMA"], "scene_name": scene.name,
            "object_name": obj.name,
            "profile": {"name": None, "reference_sha256": None,
                        "profile_sha256": None},
            "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                     "up": [0, 0, 1], "framing_margin": 0.1},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [32, 24],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "FIXED",
                      "palette": [[0, 0, 0, 1], [0.8, 0.2, 0.1, 1], [1, 1, 1, 1]],
                      "max_colors": None, "outline_mode": "NONE",
                      "outline_color": None, "outline_width": 0,
                      "shading_mode": "NONE", "value_steps": None},
            "output": {"target_file": str(target), "color_mode": "RGBA",
                       "color_depth": 8, "overwrite": False},
        }
        preflight = namespace["validate_2d_static_render_request"](request)
        check("request_preflight", preflight["ready_for_blender_inspection"])
        candidate = namespace["inspect_2d_static_render_candidate"](request, preflight)
        check("candidate_reviewed", candidate["status"] == "candidate_for_review")
        framing = namespace["preview_2d_orthographic_framing"](request, candidate)
        check("framing_bound", framing["status"] == "planned"
              and framing["request_sha256"] == candidate["request_sha256"]
              and framing["source_fingerprint"] == candidate["source_fingerprint"])
        plan = framing["plan"]

        camera_data = bpy.data.cameras.new("GAI_RenderCameraData_" + token)
        camera_data.type = "ORTHO"
        camera_data.ortho_scale = plan["orthographic_scale"]
        camera_data.clip_start = plan["clip_start"]
        camera_data.clip_end = plan["clip_end"]
        camera = bpy.data.objects.new("GAI_RenderCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        mathutils = __import__("mathutils")
        basis = plan["basis_columns"]
        camera_matrix = mathutils.Matrix((basis["right_x"], basis["up_y"],
                                          basis["back_z"])).transposed().to_4x4()
        camera_matrix.translation = mathutils.Vector(plan["position"])
        camera.matrix_world = camera_matrix
        scene.camera = camera

        light_data = bpy.data.lights.new("GAI_RenderLightData_" + token, "AREA")
        light_data.energy = 800.0
        light_data.shape = "DISK"
        light_data.size = 5.0
        light = bpy.data.objects.new("GAI_RenderLight_" + token, light_data)
        scene.collection.objects.link(light)
        light.location = (3.0, -4.0, 6.0)
        light.rotation_euler = ((obj.location - light.location).to_track_quat("-Z", "Y")
                                .to_euler())

        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = request["style"]["resolution"]
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.image_settings.color_depth = "8"
        scene.render.filter_size = 0.0
        check("pixel_filter_disabled", scene.render.filter_size == 0.0)
        scene.render.filepath = str(stage)
        check("targets_absent", not stage.exists() and not repeat_stage.exists()
              and not quantized_stage.exists()
              and not target.exists())
        bpy.ops.render.render(write_still=True, scene=scene.name)
        check("stage_created", stage.is_file() and stage.stat().st_size > 0)
        data, width, height, depth, color_type = _png_header(stage)
        check("png_dimensions", (width, height) == (32, 24))
        check("png_rgba8", depth == 8 and color_type == 6)
        pixels = _rgba8_pixels(data, width, height)
        foreground = [(x, y, pixel) for y, row in enumerate(pixels)
                      for x, pixel in enumerate(row) if pixel[3] > 0]
        check("alpha_subject_present", 0 < len(foreground) < width * height)
        xs = [item[0] for item in foreground]
        ys = [item[1] for item in foreground]
        alpha_bounds = [min(xs), min(ys), max(xs), max(ys)]
        if not (alpha_bounds[0] > 0 and alpha_bounds[1] > 0
                and alpha_bounds[2] < width - 1 and alpha_bounds[3] < height - 1):
            raise AssertionError("framing_margin_visible: " + repr(alpha_bounds))
        checks.append("framing_margin_visible")
        quantized_pixels = namespace["quantize_fixed_rgba8"](
            pixels, request["style"]["palette"])
        quantized_data = namespace["encode_png_rgba8"](quantized_pixels)
        quantized_stage.write_bytes(quantized_data)
        palette_rgb = {tuple(round(value * 255) for value in color[:3])
                       for color in request["style"]["palette"]}
        visible_quantized = {pixel[:3] for row in quantized_pixels for pixel in row
                             if pixel[3] > 0}
        check("fixed_palette_applied", visible_quantized <= palette_rgb
              and len(visible_quantized) <= len(palette_rgb))
        check("quantization_alpha_preserved", [[pixel[3] for pixel in row]
              for row in quantized_pixels] == [[pixel[3] for pixel in row] for row in pixels])
        os.link(quantized_stage, target)
        check("published_without_overwrite", target.read_bytes() == quantized_data)
        artifact_facts = {"width": width, "height": height, "color_depth": depth,
                          "color_type": color_type, "alpha_bounds": alpha_bounds,
                          "foreground_pixels": len(foreground),
                          "unique_rgba": len({pixel for row in quantized_pixels
                                             for pixel in row})}
        receipt = namespace["build_2d_render_receipt"](
            request, candidate, framing, artifact_facts)
        check("receipt_bound", receipt["artifact"]["sha256"] ==
              hashlib.sha256(quantized_data).hexdigest()
              and len(receipt["receipt_sha256"]) == 64)
        try:
            os.link(quantized_stage, target)
        except FileExistsError:
            checks.append("collision_refused")
        else:
            raise AssertionError("collision_refused")
        scene.render.filepath = str(repeat_stage)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        repeat_data, repeat_width, repeat_height, repeat_depth, repeat_color_type = _png_header(
            repeat_stage)
        repeat_pixels = _rgba8_pixels(repeat_data, repeat_width, repeat_height)
        check("same_process_pixel_deterministic", (repeat_width, repeat_height,
              repeat_depth, repeat_color_type) == (width, height, depth, color_type)
              and repeat_pixels == pixels)
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "width": width, "height": height, "color_depth": depth,
                  "color_type": color_type,
                  "source_png_sha256": hashlib.sha256(data).hexdigest(),
                  "sha256": hashlib.sha256(quantized_data).hexdigest(),
                  "request_sha256": candidate["request_sha256"],
                  "source_fingerprint": candidate["source_fingerprint"],
                  "setup_fingerprint": candidate["setup_fingerprint"],
                  "output_fingerprint": candidate["output_fingerprint"],
                  "plan_fingerprint": framing["plan_fingerprint"],
                  "alpha_bounds": alpha_bounds,
                  "foreground_pixels": len(foreground),
                  "partial_alpha_pixels": sum(0 < pixel[3] < 255 for row in pixels
                                              for pixel in row),
                  "source_unique_rgba": len({pixel for row in pixels for pixel in row}),
                  "quantized_unique_rgba": len({pixel for row in quantized_pixels
                                                for pixel in row}),
                  "receipt_sha256": receipt["receipt_sha256"],
                  "repeat_file_bytes_identical": repeat_data == data,
                  "blender_version": bpy.app.version_string}
    finally:
        for path in (target, quantized_stage, repeat_stage, stage):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"] = len(checks)
    result["checks"] = checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
