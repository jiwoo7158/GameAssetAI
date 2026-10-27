import bpy

from ..constants import (
    ADDON_OWNER_KEY,
    ADDON_OWNER_VALUE,
    COMPOSITOR_TREE_NAME,
)


def _is_owned(data_block):
    return data_block is not None and data_block.get(ADDON_OWNER_KEY) == ADDON_OWNER_VALUE


def _remove_owned_tree(scene):
    tree = bpy.data.node_groups.get(COMPOSITOR_TREE_NAME)
    if tree is not None and not _is_owned(tree):
        raise RuntimeError(f"Node group name is occupied by non-GameAssetAI data: {COMPOSITOR_TREE_NAME}")
    if tree is not None:
        if scene.compositing_node_group == tree:
            scene.compositing_node_group = None
        bpy.data.node_groups.remove(tree)


def build_pixel_compositor(context):
    scene = context.scene
    settings = scene.gameassetai
    if not hasattr(scene, "compositing_node_group"):
        raise RuntimeError("This Blender version does not expose Scene.compositing_node_group")

    if "gaa_previous_use_nodes" not in scene:
        previous = scene.compositing_node_group
        scene["gaa_previous_use_nodes"] = bool(scene.use_nodes)
        scene["gaa_previous_compositor_name"] = previous.name if previous else ""

    _remove_owned_tree(scene)
    tree = bpy.data.node_groups.new(COMPOSITOR_TREE_NAME, "CompositorNodeTree")
    tree[ADDON_OWNER_KEY] = ADDON_OWNER_VALUE
    try:
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        nodes = tree.nodes
        links = tree.links

        render_layers = nodes.new("CompositorNodeRLayers")
        render_layers.name = "GAA Render Layers"
        render_layers.label = "Scene Render"
        render_layers.location = (-520, 0)

        scale_down = nodes.new("CompositorNodeScale")
        scale_down.name = "GAA Downsample"
        scale_down.label = f"Downsample 1/{settings.pixel_scale}"
        scale_down.location = (-300, 0)
        scale_down.inputs["Type"].default_value = "Relative"
        scale_down.inputs["Interpolation"].default_value = "Nearest"
        scale_down.inputs["X"].default_value = 1.0 / settings.pixel_scale
        scale_down.inputs["Y"].default_value = 1.0 / settings.pixel_scale

        pixelate = nodes.new("CompositorNodePixelate")
        pixelate.name = "GAA Pixelate"
        pixelate.label = "Nearest Pixel Cells"
        pixelate.location = (-80, 0)

        scale_up = nodes.new("CompositorNodeScale")
        scale_up.name = "GAA Restore Size"
        scale_up.label = "Restore Render Size"
        scale_up.location = (140, 0)
        scale_up.inputs["Type"].default_value = "Render Size"
        scale_up.inputs["Interpolation"].default_value = "Nearest"

        output = nodes.new("NodeGroupOutput")
        output.name = "GAA Output"
        output.location = (380, 0)
        output.is_active_output = True

        links.new(render_layers.outputs["Image"], scale_down.inputs["Image"])
        links.new(scale_down.outputs["Image"], pixelate.inputs["Color"])
        links.new(pixelate.outputs["Color"], scale_up.inputs["Image"])
        links.new(scale_up.outputs["Image"], output.inputs["Image"])

        scene.use_nodes = True
        scene.compositing_node_group = tree
        return tree
    except Exception as exc:
        if scene.compositing_node_group == tree:
            scene.compositing_node_group = None
        bpy.data.node_groups.remove(tree)
        raise RuntimeError(f"Could not build Blender 5 compositor graph: {exc}") from exc


def remove_pixel_compositor(context):
    scene = context.scene
    _remove_owned_tree(scene)

    previous_name = scene.get("gaa_previous_compositor_name", "")
    previous = bpy.data.node_groups.get(previous_name) if previous_name else None
    if previous is not None and isinstance(previous, bpy.types.CompositorNodeTree):
        scene.compositing_node_group = previous
    if "gaa_previous_use_nodes" in scene:
        scene.use_nodes = bool(scene["gaa_previous_use_nodes"])
    for key in ("gaa_previous_use_nodes", "gaa_previous_compositor_name"):
        if key in scene:
            del scene[key]


class GAA_OT_build_pixel_compositor(bpy.types.Operator):
    bl_idname = "gameassetai.build_pixel_compositor"
    bl_label = "Build Pixel Nodes"
    bl_description = "Build an owned downsample, pixelate and restore-size compositor graph"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            tree = build_pixel_compositor(context)
        except (RuntimeError, TypeError, KeyError, AttributeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Built {tree.name}")
        return {"FINISHED"}


class GAA_OT_remove_pixel_compositor(bpy.types.Operator):
    bl_idname = "gameassetai.remove_pixel_compositor"
    bl_label = "Remove Pixel Nodes"
    bl_description = "Remove only the owned pixel compositor and restore the previous graph"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            remove_pixel_compositor(context)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, "Removed GameAssetAI pixel compositor")
        return {"FINISHED"}


CLASSES = (GAA_OT_build_pixel_compositor, GAA_OT_remove_pixel_compositor)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
