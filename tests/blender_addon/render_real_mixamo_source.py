import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def point_at(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    scene = bpy.context.scene
    collection = bpy.data.collections["GAA M3 Real Mixamo Source"]
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise AssertionError("expected one retained Mixamo source Mesh")
    mesh = meshes[0]
    hidden = {obj: obj.hide_render for obj in scene.objects if obj != mesh}
    for obj in hidden:
        obj.hide_render = True
    scene.frame_set(1)
    corners = [mesh.matrix_world @ Vector(corner) for corner in mesh.bound_box]
    low = Vector(tuple(min(point[i] for point in corners) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in corners) for i in range(3)))
    center = (low + high) * 0.5
    height = high.z - low.z
    camera_data = bpy.data.cameras.new("GAA M3 Source Review Camera")
    camera = bpy.data.objects.new("GAA M3 Source Review Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 1.10
    light_data = bpy.data.lights.new("GAA M3 Source Review Light", "AREA")
    light_data.energy = 1000
    light_data.size = height * 2
    light = bpy.data.objects.new("GAA M3 Source Review Light", light_data)
    scene.collection.objects.link(light)
    point_at(light, center + Vector((height * 1.5, -height * 2, height * 1.5)), center)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = True
    for frame in (1, 8, 16, 24, 32):
        scene.frame_set(frame)
        for view, offset in {"front": (0, -height * 3.2, 0),
                             "side": (height * 3.2, 0, 0)}.items():
            point_at(camera, center + Vector(offset), center)
            scene.render.filepath = str(args.output / f"source-frame-{frame:02d}-{view}.png")
            bpy.ops.render.render(write_still=True)
    print("GAMEASSETAI_REAL_MIXAMO_SOURCE_RENDER pass")


if __name__ == "__main__":
    main()
