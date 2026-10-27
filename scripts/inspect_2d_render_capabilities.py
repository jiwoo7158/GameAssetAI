"""Read-only Blender capability inventory for future 3D-to-2D rendering."""
from __future__ import annotations

import bpy


def _enum_identifiers(owner, property_name):
    prop = owner.bl_rna.properties.get(property_name)
    if prop is None:
        return []
    try:
        return [item.identifier for item in prop.enum_items]
    except Exception:
        return []


def _rna_has_property(owner, property_name):
    """Check an RNA property without relying on Python descriptors on bpy.types."""
    return owner.bl_rna.properties.get(property_name) is not None


def _rna_has_function(owner, function_name):
    """Check an RNA function without assuming it is callable on the type object."""
    return owner.bl_rna.functions.get(function_name) is not None


def _render_capability_snapshot(scene):
    view_layer = bpy.context.view_layer
    active = view_layer.objects.active if view_layer else None
    return {
        "scene": bpy.context.scene.name if bpy.context.scene else None,
        "mode": bpy.context.mode,
        "frame": (scene.frame_current, float(scene.frame_subframe)),
        "objects": sorted(scene.objects.keys()),
        "selection": sorted(obj.name for obj in bpy.context.selected_objects),
        "active": active.name if active else None,
        "render": {
            "engine": scene.render.engine,
            "resolution": (scene.render.resolution_x, scene.render.resolution_y,
                           scene.render.resolution_percentage),
            "film_transparent": scene.render.film_transparent,
            "filepath": scene.render.filepath,
            "file_format": scene.render.image_settings.file_format,
            "color_mode": scene.render.image_settings.color_mode,
            "color_depth": scene.render.image_settings.color_depth,
        },
        "data_counts": {
            "scenes": len(bpy.data.scenes), "objects": len(bpy.data.objects),
            "cameras": len(bpy.data.cameras), "lights": len(bpy.data.lights),
            "materials": len(bpy.data.materials), "images": len(bpy.data.images),
            "node_groups": len(bpy.data.node_groups),
        },
    }


def inspect_2d_render_capabilities():
    """Return available APIs and current settings without changing Blender state."""
    scene = bpy.context.scene
    if scene is None:
        return {"schema": "gameassetai.2d-render-capabilities.v1", "status": "error",
                "errors": ["No active Scene"]}
    before = _render_capability_snapshot(scene)
    image_settings = scene.render.image_settings
    view_settings = scene.view_settings
    compositor_types = [
        "CompositorNodeRLayers", "CompositorNodeComposite", "CompositorNodeScale",
        "CompositorNodePixelate", "CompositorNodeValToRGB", "CompositorNodeSetAlpha",
        "CompositorNodeAlphaOver", "CompositorNodeOutputFile",
    ]
    report = {
        "schema": "gameassetai.2d-render-capabilities.v1",
        "status": "ok",
        "errors": [],
        "blender_version": bpy.app.version_string,
        "scene": scene.name,
        "render": {
            "current_engine": scene.render.engine,
            "render_operator_available": hasattr(bpy.ops, "render") and hasattr(bpy.ops.render, "render"),
            "render_operator_poll": bool(bpy.ops.render.render.poll()),
            "resolution_properties": all(hasattr(scene.render, name) for name in
                                         ("resolution_x", "resolution_y", "resolution_percentage")),
            "transparent_background_property": hasattr(scene.render, "film_transparent"),
            "filepath_property": hasattr(scene.render, "filepath"),
        },
        "image_output": {
            "file_formats": _enum_identifiers(image_settings, "file_format"),
            "color_modes": _enum_identifiers(image_settings, "color_mode"),
            "color_depths": _enum_identifiers(image_settings, "color_depth"),
            "image_save": _rna_has_function(bpy.types.Image, "save"),
            "image_save_render": _rna_has_function(bpy.types.Image, "save_render"),
            "path_abspath": callable(getattr(bpy.path, "abspath", None)),
        },
        "camera": {
            "types": _enum_identifiers(bpy.types.Camera, "type"),
            "orthographic_scale_property": _rna_has_property(bpy.types.Camera, "ortho_scale"),
        },
        "compositor": {
            "scene_use_nodes_property": hasattr(scene, "use_nodes"),
            "scene_node_tree_property": hasattr(scene, "node_tree"),
            "scene_compositing_node_group_property": hasattr(scene, "compositing_node_group"),
            "node_types": {name: hasattr(bpy.types, name) for name in compositor_types},
        },
        "color_management": {
            "view_transform": getattr(view_settings, "view_transform", None),
            "view_transforms": _enum_identifiers(view_settings, "view_transform"),
            "look": getattr(view_settings, "look", None),
            "looks": _enum_identifiers(view_settings, "look"),
            "exposure_property": hasattr(view_settings, "exposure"),
            "gamma_property": hasattr(view_settings, "gamma"),
        },
        "limits": [
            "Dynamic render-engine availability is not inferred from RNA enum metadata",
            "Color-management enum metadata may under-report dynamically available values",
            "Blender 5 uses Scene.compositing_node_group; legacy Scene.node_tree may be absent",
            "Capability presence does not validate rendered pixels, color accuracy or output publication",
            "No compositor graph, camera, light, image or file is created by this inventory",
        ],
    }
    after = _render_capability_snapshot(scene)
    report["preserved"] = before == after
    if not report["preserved"]:
        report["status"] = "error"
        report["errors"].append("Blender state changed during read-only capability inventory")
    return report
