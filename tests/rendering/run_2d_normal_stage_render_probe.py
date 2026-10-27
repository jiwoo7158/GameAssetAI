"""Isolated Blender probe for flat and smooth camera-basis normal pixels."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid

import bpy
from mathutils import Vector


def _normal_material(name, axes):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    geometry = nodes.new("ShaderNodeNewGeometry")
    channels = []
    for axis in axes:
        dot = nodes.new("ShaderNodeVectorMath")
        dot.operation = "DOT_PRODUCT"
        dot.inputs[1].default_value = axis
        links.new(geometry.outputs["Normal"], dot.inputs[0])
        scale = nodes.new("ShaderNodeMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = 0.5
        links.new(dot.outputs["Value"], scale.inputs[0])
        offset = nodes.new("ShaderNodeMath")
        offset.operation = "ADD"
        offset.inputs[1].default_value = 0.5
        links.new(scale.outputs[0], offset.inputs[0])
        channels.append(offset)
    combine = nodes.new("ShaderNodeCombineColor")
    for node, socket in zip(channels, ("Red", "Green", "Blue")):
        links.new(node.outputs[0], combine.inputs[socket])
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
    namespace = {"__name__": "normal_probe_decoder"}
    for name in ("validate_2d_silhouette_mask_request.py", "quantize_rgba.py"):
        source = (repo / "scripts" / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    decode = namespace["decode_png_rgba8"]
    encode = namespace["encode_png_rgba8"]
    token = uuid.uuid4().hex
    stage = root / (".gameassetai-normal-" + token + ".stage.blend")
    png = root / (".gameassetai-normal-" + token + ".render.stage.png")
    exr = root / (".gameassetai-normal-" + token + ".float.stage.exr")
    cpu_png = root / (".gameassetai-normal-" + token + ".cpu.stage.png")
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
        # Flat triangle normal: normalize((1,1,1)); camera components are (+,+,-).
        mesh = bpy.data.meshes.new("GAI_NormalFlatMesh_" + token)
        mesh.from_pydata([(-2, 0, 0), (-1, -1, 0), (-1, 0, -1)], [], [(0, 1, 2)])
        flat = bpy.data.objects.new("GAI_NormalFlat_" + token, mesh)
        scene.collection.objects.link(flat)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.75,
                                             location=(1.1, 0, -0.4))
        smooth = bpy.context.object
        smooth.name = "GAI_NormalSmooth_" + token
        for face in smooth.data.polygons:
            face.use_smooth = True
        material = _normal_material("GAI_NormalMaterial_" + token,
                                    ((1, 0, 0), (0, 0, 1), (0, -1, 0)))
        flat.data.materials.append(material)
        smooth.data.materials.append(material)
        camera_data = bpy.data.cameras.new("GAI_NormalCameraData_" + token)
        camera_data.type, camera_data.ortho_scale = "ORTHO", 5.0
        camera = bpy.data.objects.new("GAI_NormalCamera_" + token, camera_data)
        scene.collection.objects.link(camera)
        camera.location = (0, -6, 0)
        camera.rotation_euler = (Vector((0, 0, -0.3)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.camera = camera
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x, scene.render.resolution_y = 64, 32
        scene.render.resolution_percentage, scene.render.film_transparent = 100, True
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "RGBA", "8"
        scene.render.filter_size, scene.render.filepath = 0.0, str(png)
        # Raw is essential: Standard/sRGB display conversion would change the encoded vector bytes.
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        scene.view_settings.exposure, scene.view_settings.gamma = 0.0, 1.0
        bpy.ops.wm.save_as_mainfile(filepath=str(stage), check_existing=False)
        check("stage_created", stage.is_file())
        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        check("stage_reopened", Path(bpy.data.filepath) == stage)
        bpy.context.scene.render.filepath = str(png)
        bpy.ops.render.render(write_still=True, scene=bpy.context.scene.name)
        _, width, height, pixels = decode(png)
        check("rgba8_dimensions", (width, height) == (64, 32))
        visible = [(x, y, pixel) for y, row in enumerate(pixels) for x, pixel in enumerate(row)
                   if pixel[3] > 0]
        check("visible_pixels", bool(visible) and all(pixel[3] == 255 for _, _, pixel in visible))
        left = [pixel for x, _, pixel in visible if x < width // 2]
        right = [pixel for x, _, pixel in visible if x >= width // 2]
        flat_colors, smooth_colors = set(left), set(right)
        print("GAMEASSETAI_NORMAL_DIAGNOSTIC=" + json.dumps({
            "flat_colors": sorted([list(color) for color in flat_colors]),
            "smooth_unique_rgba": len(smooth_colors),
            "smooth_sample": sorted([list(color) for color in smooth_colors])[:12],
        }, sort_keys=True))
        # The triangle is viewed from its back side. Blender's SHADING_NORMAL is
        # face-forward, so the geometric [201,201,54] reference flips to about
        # [54,54,201]. Direct GPU-to-PNG conversion also varies by one byte.
        check("backface_shading_normal_flipped", all(
            53 <= color[0] <= 55 and 53 <= color[1] <= 55
            and 201 <= color[2] <= 202 and color[3] == 255 for color in flat_colors))
        check("direct_png_not_exact_geometric_reference",
              (201, 201, 54, 255) not in flat_colors and 1 <= len(flat_colors) <= 4)
        check("smooth_interpolates", len(smooth_colors) >= 8)

        scene = bpy.context.scene
        scene.render.image_settings.file_format = "OPEN_EXR"
        scene.render.image_settings.color_mode = "RGBA"
        scene.render.image_settings.color_depth = "32"
        scene.render.filepath = str(exr)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        check("float_exr_created", exr.is_file() and exr.stat().st_size > 0)
        float_image = bpy.data.images.load(str(exr), check_existing=False)
        check("float_exr_loaded", tuple(float_image.size) == (64, 32))
        float_values = list(float_image.pixels[:])
        cpu_rows = []
        for y in range(height):
            row = []
            for x in range(width):
                index = (y * width + x) * 4
                red, green, blue, alpha = float_values[index:index + 4]
                if alpha <= 0.0:
                    row.append((0, 0, 0, 0))
                else:
                    row.append(tuple(max(0, min(255, round(value * 255.0)))
                                     for value in (red, green, blue)) + (255,))
            cpu_rows.append(row)
        bpy.data.images.remove(float_image)
        cpu_png.write_bytes(encode(cpu_rows))
        _, cpu_width, cpu_height, cpu_pixels = decode(cpu_png)
        check("cpu_rgba8_dimensions", (cpu_width, cpu_height) == (64, 32))
        cpu_visible = [(x, y, pixel) for y, row in enumerate(cpu_pixels)
                       for x, pixel in enumerate(row) if pixel[3] > 0]
        cpu_flat = {pixel for x, _, pixel in cpu_visible if x < cpu_width // 2}
        cpu_smooth = {pixel for x, _, pixel in cpu_visible if x >= cpu_width // 2}
        check("cpu_flat_is_exact", cpu_flat == {(54, 54, 201, 255)})
        check("cpu_smooth_interpolates", len(cpu_smooth) >= 8)

        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "flat_rgba_values": sorted([list(color) for color in flat_colors]),
                  "smooth_unique_rgba": len(smooth_colors),
                  "cpu_flat_rgba": list(next(iter(cpu_flat))),
                  "cpu_smooth_unique_rgba": len(cpu_smooth),
                  "visible_pixels": len(visible), "blender_version": bpy.app.version_string}
    finally:
        cpu_png.unlink(missing_ok=True)
        exr.unlink(missing_ok=True)
        png.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
