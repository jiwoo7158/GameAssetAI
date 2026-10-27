"""Isolated Blender probe for camera-linear base-Mesh depth pixels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

import bpy
from mathutils import Matrix, Vector


def _depth_material(name, direction, near_projection, span):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    geometry = nodes.new("ShaderNodeNewGeometry")
    dot = nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = direction
    links.new(geometry.outputs["Position"], dot.inputs[0])
    subtract = nodes.new("ShaderNodeMath")
    subtract.operation = "SUBTRACT"
    subtract.inputs[0].default_value = near_projection
    links.new(dot.outputs["Value"], subtract.inputs[1])
    divide = nodes.new("ShaderNodeMath")
    divide.operation = "DIVIDE"
    divide.inputs[1].default_value = span
    divide.use_clamp = True
    links.new(subtract.outputs[0], divide.inputs[0])
    combine = nodes.new("ShaderNodeCombineColor")
    for socket in ("Red", "Green", "Blue"):
        links.new(divide.outputs[0], combine.inputs[socket])
    emission = nodes.new("ShaderNodeEmission")
    links.new(combine.outputs["Color"], emission.inputs["Color"])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    args = parser.parse_args(tail)
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    namespace = {"__name__": "depth_probe_codec"}
    for name in ("validate_2d_silhouette_mask_request.py", "quantize_rgba.py"):
        source = (repo / "scripts" / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    decode, encode = namespace["decode_png_rgba8"], namespace["encode_png_rgba8"]
    token = uuid.uuid4().hex
    stage = root / (".gameassetai-depth-" + token + ".stage.blend")
    exr = root / (".gameassetai-depth-" + token + ".float.stage.exr")
    png = root / (".gameassetai-depth-" + token + ".cpu.stage.png")
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        mesh = bpy.data.meshes.new("GAI_DepthProbeMesh_" + token)
        mesh.from_pydata([(-1, -1, -1), (1, 0, -1), (0, 1, 1)], [], [(0, 1, 2)])
        obj = bpy.data.objects.new("GAI_DepthProbeObject_" + token, mesh)
        scene.collection.objects.link(obj)
        direction, up, right = Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0))
        obj.data.materials.append(_depth_material(
            "GAI_DepthProbeMaterial_" + token, direction, 1.0, 2.0))
        camera_data = bpy.data.cameras.new("GAI_DepthProbeCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", 3.0
        camera = bpy.data.objects.new("GAI_DepthProbeCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        camera.matrix_world = Matrix((right, up, direction)).transposed().to_4x4()
        camera.matrix_world.translation = Vector((0, -5, 0))
        scene.camera = camera
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 48, 48
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "OPEN_EXR"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "32"
        scene.render.filter_size, scene.render.filepath = 0.0, str(exr)
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        scene.view_settings.exposure, scene.view_settings.gamma = 0.0, 1.0
        bpy.ops.wm.save_as_mainfile(filepath=str(stage), check_existing=False)
        check("stage_created", stage.is_file())
        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        check("stage_reopened", Path(bpy.data.filepath) == stage)
        bpy.context.scene.render.filepath = str(exr)
        bpy.ops.render.render(write_still=True, scene=bpy.context.scene.name)
        check("float_exr_created", exr.is_file() and exr.stat().st_size > 0)
        image = bpy.data.images.load(str(exr), check_existing=False)
        width, height = map(int, image.size)
        check("float_exr_loaded", (width, height) == (48, 48))
        values = list(image.pixels[:])
        bpy.data.images.remove(image)
        rows = []
        for output_y in range(height):
            row, source_y = [], height - 1 - output_y
            for x in range(width):
                index = (source_y * width + x) * 4
                red, green, blue, alpha = values[index:index + 4]
                if alpha <= 0:
                    row.append((0, 0, 0, 0))
                else:
                    row.append(tuple(max(0, min(255, round(value * 255.0)))
                                     for value in (red, green, blue)) + (255,))
            rows.append(row)
        png.write_bytes(encode(rows))
        _, decoded_width, decoded_height, pixels = decode(png)
        check("rgba8_dimensions", (decoded_width, decoded_height) == (48, 48))
        visible = [pixel for row in pixels for pixel in row if pixel[3] > 0]
        check("visible_pixels", bool(visible))
        check("grayscale_encoding", all(r == g == b for r, g, b, _ in visible))
        levels = sorted({pixel[0] for pixel in visible})
        check("linear_depth_gradient", len(levels) >= 16 and levels[0] < 64 and levels[-1] > 192)
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "visible_pixels": len(visible), "depth_level_count": len(levels),
                  "depth_level_min": levels[0], "depth_level_max": levels[-1],
                  "blender_version": bpy.app.version_string}
    finally:
        png.unlink(missing_ok=True)
        exr.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
