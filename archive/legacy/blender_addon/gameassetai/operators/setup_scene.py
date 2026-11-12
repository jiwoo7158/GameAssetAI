import bpy
from mathutils import Vector

from ..constants import (
    ADDON_OWNER_KEY,
    ADDON_OWNER_VALUE,
    FILL_LIGHT_NAME,
    KEY_LIGHT_NAME,
    PREVIEW_CAMERA_NAME,
    PREVIEW_COLLECTION_NAME,
    SCENE_STATE_KEYS,
)


def _is_owned(data_block):
    return data_block is not None and data_block.get(ADDON_OWNER_KEY) == ADDON_OWNER_VALUE


def _tag(data_block):
    data_block[ADDON_OWNER_KEY] = ADDON_OWNER_VALUE
    return data_block


def _world_corners(obj):
    return [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]


def _bounds(obj):
    corners = _world_corners(obj)
    minimum = Vector((min(p.x for p in corners), min(p.y for p in corners), min(p.z for p in corners)))
    maximum = Vector((max(p.x for p in corners), max(p.y for p in corners), max(p.z for p in corners)))
    return corners, (minimum + maximum) * 0.5


def _direction(view_preset):
    values = {
        "FRONT": Vector((0.0, -1.0, 0.0)),
        "SIDE": Vector((1.0, 0.0, 0.0)),
        "QUARTER": Vector((1.0, -1.0, 0.75)),
        "TOP": Vector((0.0, 0.0, 1.0)),
    }
    return values[view_preset].normalized()


def _point_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def _remember_scene(scene):
    if "gaa_previous_resolution_x" in scene:
        return
    scene["gaa_previous_camera_name"] = scene.camera.name if scene.camera else ""
    scene["gaa_previous_resolution_x"] = scene.render.resolution_x
    scene["gaa_previous_resolution_y"] = scene.render.resolution_y
    scene["gaa_previous_resolution_percentage"] = scene.render.resolution_percentage
    scene["gaa_previous_film_transparent"] = bool(scene.render.film_transparent)


def _remove_owned_preview(scene):
    collection = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)
    if collection is not None and not _is_owned(collection):
        raise RuntimeError(f"Collection name is occupied by non-GameAssetAI data: {PREVIEW_COLLECTION_NAME}")
    if collection is not None:
        for obj in list(collection.objects):
            if not _is_owned(obj):
                raise RuntimeError(f"Preview collection contains unowned Object: {obj.name}")
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data is not None and _is_owned(data) and data.users == 0:
                if isinstance(data, bpy.types.Camera):
                    bpy.data.cameras.remove(data)
                elif isinstance(data, bpy.types.Light):
                    bpy.data.lights.remove(data)
        bpy.data.collections.remove(collection)


def build_pixel_scene(context):
    scene = context.scene
    target = context.active_object
    if target is None or target.type != "MESH":
        raise RuntimeError("Select one active Mesh Object before setting up the pixel scene")
    if target.library or (target.data and target.data.library):
        raise RuntimeError("Linked target data is not supported")

    settings = scene.gameassetai
    _remember_scene(scene)
    _remove_owned_preview(scene)

    collection = _tag(bpy.data.collections.new(PREVIEW_COLLECTION_NAME))
    scene.collection.children.link(collection)

    corners, center = _bounds(target)
    direction = _direction(settings.view_preset)
    distance = max(4.0, max((p - center).length for p in corners) * 4.0)

    camera_data = _tag(bpy.data.cameras.new(PREVIEW_CAMERA_NAME))
    camera = _tag(bpy.data.objects.new(PREVIEW_CAMERA_NAME, camera_data))
    collection.objects.link(camera)
    camera.location = center + direction * distance
    _point_at(camera, center)
    camera_data.type = "ORTHO"

    inverse_rotation = camera.matrix_world.to_quaternion().inverted()
    local = [inverse_rotation @ (p - center) for p in corners]
    half_x = max(abs(p.x) for p in local)
    half_y = max(abs(p.y) for p in local)
    aspect = settings.resolution_x / settings.resolution_y
    fit_height = max(2.0 * half_y, (2.0 * half_x) / aspect)
    camera_data.ortho_scale = max(0.001, fit_height * (1.0 + 2.0 * settings.framing_margin))
    camera_data.clip_start = max(0.001, distance * 0.1)
    camera_data.clip_end = distance * 3.0

    for name, energy, offset, size in (
        (KEY_LIGHT_NAME, settings.key_energy, Vector((-1.5, -1.5, 2.0)), 4.0),
        (FILL_LIGHT_NAME, settings.fill_energy, Vector((1.5, -0.5, 0.75)), 3.0),
    ):
        light_data = _tag(bpy.data.lights.new(name, "AREA"))
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = _tag(bpy.data.objects.new(name, light_data))
        collection.objects.link(light)
        light.location = center + offset * max(1.0, distance * 0.5)
        _point_at(light, center)

    scene.camera = camera
    scene.render.resolution_x = settings.resolution_x
    scene.render.resolution_y = settings.resolution_y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    return camera


def remove_pixel_scene(context):
    scene = context.scene
    current_camera = scene.camera
    if current_camera is not None and _is_owned(current_camera):
        scene.camera = None

    _remove_owned_preview(scene)

    previous_name = scene.get("gaa_previous_camera_name", "")
    previous_camera = bpy.data.objects.get(previous_name) if previous_name else None
    if previous_camera is not None and previous_camera.type == "CAMERA":
        scene.camera = previous_camera
    if "gaa_previous_resolution_x" in scene:
        scene.render.resolution_x = int(scene["gaa_previous_resolution_x"])
        scene.render.resolution_y = int(scene["gaa_previous_resolution_y"])
        scene.render.resolution_percentage = int(scene["gaa_previous_resolution_percentage"])
        scene.render.film_transparent = bool(scene["gaa_previous_film_transparent"])
    for key in SCENE_STATE_KEYS:
        if key in scene:
            del scene[key]


class GAA_OT_setup_pixel_scene(bpy.types.Operator):
    bl_idname = "gameassetai.setup_pixel_scene"
    bl_label = "Setup Pixel Scene"
    bl_description = "Create an owned orthographic camera and neutral preview lighting around the active Mesh"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            camera = build_pixel_scene(context)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Created {camera.name} without modifying the target Mesh")
        return {"FINISHED"}


class GAA_OT_remove_pixel_scene(bpy.types.Operator):
    bl_idname = "gameassetai.remove_pixel_scene"
    bl_label = "Remove Pixel Scene"
    bl_description = "Remove only GameAssetAI-owned preview data and restore prior render settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            remove_pixel_scene(context)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, "Removed GameAssetAI pixel preview setup")
        return {"FINISHED"}


CLASSES = (GAA_OT_setup_pixel_scene, GAA_OT_remove_pixel_scene)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
