import hashlib
from pathlib import Path

import bpy


def export_mixamo_handoff(scene_name, mesh_object_name, armature_object_name, target_file,
                           *, authorized=False):
    if authorized is not True:
        raise ValueError("authorized=true is required for FBX output")
    path = Path(target_file)
    if not path.is_absolute() or path.suffix.lower() != ".fbx" or path.exists() or path.is_symlink():
        raise ValueError("target_file must be an unused absolute regular .fbx path")
    if not path.parent.is_dir():
        raise ValueError("target_file parent directory must already exist")
    scene = bpy.data.scenes.get(scene_name)
    mesh = scene.objects.get(mesh_object_name) if scene else None
    armature = scene.objects.get(armature_object_name) if scene else None
    if mesh is None or mesh.type != "MESH" or armature is None or armature.type != "ARMATURE":
        raise ValueError("explicit Mesh/Armature target does not exist")
    if not any(mod.type == "ARMATURE" and mod.object == armature for mod in mesh.modifiers):
        raise ValueError("Mesh is not bound to the explicit Armature")
    previous_selected = list(bpy.context.selected_objects)
    previous_active = bpy.context.view_layer.objects.active
    try:
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        mesh.select_set(True); armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                                 object_types={"ARMATURE", "MESH"}, bake_anim=False,
                                 add_leaf_bones=False, axis_forward="-Z", axis_up="Y",
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS")
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Blender did not create the handoff FBX")
        return {"status": "created", "target_file": str(path), "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "mesh_object": mesh.name, "armature_object": armature.name,
                "animation_included": False, "overwrite": False}
    except Exception:
        if path.is_file():
            path.unlink()
        raise
    finally:
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in previous_selected:
            if bpy.data.objects.get(obj.name): obj.select_set(True)
        if previous_active and bpy.data.objects.get(previous_active.name):
            bpy.context.view_layer.objects.active = previous_active
# Retained bounded Blender capability; product support remains evidence-scoped.
