import json

import bpy

from ..constants import ADDON_OWNER_KEY, MATERIAL_OWNER_VALUE, MATERIAL_STATE_KEY


def _base_color(material):
    if material and material.use_nodes and material.node_tree:
        principled = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
        if principled:
            value = principled.inputs[0].default_value
            return tuple(float(channel) for channel in value)
    if material:
        return tuple(float(channel) for channel in material.diffuse_color)
    return (0.8, 0.8, 0.8, 1.0)


def _owned_name(obj, preset, index):
    return f"GAA {obj.name} {preset} {index:02d}"


def _build_flat_lit(material, color):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs[0].default_value = color
    shader.inputs[1].default_value = 0.0
    shader.inputs[2].default_value = 1.0
    links.new(shader.outputs[0], output.inputs[0])


def _build_emission(material, color):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeEmission")
    shader.inputs[0].default_value = color
    shader.inputs[1].default_value = 1.0
    links.new(shader.outputs[0], output.inputs[0])


def _build_cel(material, color, bands):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    output = nodes.new("ShaderNodeOutputMaterial")
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    to_rgb = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    while len(ramp.color_ramp.elements) > 2:
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
    elements = ramp.color_ramp.elements
    while len(elements) < bands:
        elements.new(len(elements) / bands)
    for index, element in enumerate(sorted(elements, key=lambda item: item.position)):
        level = 0.35 + 0.65 * index / (bands - 1)
        element.position = index / bands
        element.color = (level, level, level, 1.0)
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    multiply.inputs[2].default_value = color
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs[1].default_value = 1.0
    links.new(diffuse.outputs[0], to_rgb.inputs[0])
    links.new(to_rgb.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs[0], multiply.inputs[1])
    links.new(multiply.outputs[0], emission.inputs[0])
    links.new(emission.outputs[0], output.inputs[0])


def _create_owned_material(name, source, preset, bands):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = _base_color(source)
    material[ADDON_OWNER_KEY] = MATERIAL_OWNER_VALUE
    material["gaa_source_material"] = source.name if source else ""
    material["gaa_material_preset"] = preset
    material["gaa_shadow_bands"] = bands
    material.node_tree.nodes.clear()
    if preset == "FLAT_LIT":
        _build_flat_lit(material, material.diffuse_color)
    elif preset == "CEL_BANDED":
        _build_cel(material, material.diffuse_color, bands)
    else:
        _build_emission(material, material.diffuse_color)
    return material


def _target(context):
    settings = getattr(context.scene, "gameassetai", None)
    return settings.material_target if settings else None


class GAA_OT_apply_material_preset(bpy.types.Operator):
    bl_idname = "gameassetai.apply_material_preset"
    bl_label = "Apply Style Preview"
    bl_description = "Replace slots with reversible Add-on-owned style materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = _target(context)
        return bool(obj and obj.name in context.scene.objects and MATERIAL_STATE_KEY not in obj)

    def execute(self, context):
        obj = _target(context)
        if obj.library or obj.data.library:
            self.report({"ERROR"}, "Linked Objects and Meshes are not supported")
            return {"CANCELLED"}
        settings = context.scene.gameassetai
        originals = [slot.material for slot in obj.material_slots]
        if not originals:
            self.report({"ERROR"}, "Target Mesh has no material slots")
            return {"CANCELLED"}
        names = [_owned_name(obj, settings.material_preset, index) for index in range(len(originals))]
        collisions = [name for name in names if bpy.data.materials.get(name)]
        if collisions:
            self.report({"ERROR"}, f"Owned material name already exists: {collisions[0]}")
            return {"CANCELLED"}
        created = []
        try:
            for index, source in enumerate(originals):
                created.append(_create_owned_material(names[index], source, settings.material_preset, settings.shadow_bands))
            state = {
                "original_materials": [material.name if material else None for material in originals],
                "owned_materials": names,
                "preset": settings.material_preset,
                "shadow_bands": settings.shadow_bands,
            }
            obj[MATERIAL_STATE_KEY] = json.dumps(state, separators=(",", ":"))
            for slot, material in zip(obj.material_slots, created):
                slot.material = material
        except Exception:
            for material in created:
                if material.users == 0:
                    bpy.data.materials.remove(material)
            if MATERIAL_STATE_KEY in obj:
                del obj[MATERIAL_STATE_KEY]
            raise
        self.report({"INFO"}, f"Applied {settings.material_preset} to {obj.name}")
        return {"FINISHED"}


class GAA_OT_remove_material_preset(bpy.types.Operator):
    bl_idname = "gameassetai.remove_material_preset"
    bl_label = "Restore Materials"
    bl_description = "Restore original slots and remove only the owned style materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = _target(context)
        return bool(obj and obj.name in context.scene.objects and MATERIAL_STATE_KEY in obj)

    def execute(self, context):
        obj = _target(context)
        try:
            state = json.loads(obj[MATERIAL_STATE_KEY])
        except (TypeError, ValueError, KeyError):
            self.report({"ERROR"}, "Material restore state is invalid")
            return {"CANCELLED"}
        owned = [bpy.data.materials.get(name) for name in state["owned_materials"]]
        if len(owned) != len(obj.material_slots) or any(material is None for material in owned):
            self.report({"ERROR"}, "An owned material is missing; refusing partial restore")
            return {"CANCELLED"}
        if any(material.get(ADDON_OWNER_KEY) != MATERIAL_OWNER_VALUE for material in owned):
            self.report({"ERROR"}, "Material ownership mismatch; refusing removal")
            return {"CANCELLED"}
        if any(slot.material != material for slot, material in zip(obj.material_slots, owned)):
            self.report({"ERROR"}, "Material slots changed after preview; refusing destructive restore")
            return {"CANCELLED"}
        originals = []
        for name in state["original_materials"]:
            material = bpy.data.materials.get(name) if name else None
            if name and material is None:
                self.report({"ERROR"}, f"Original material is missing: {name}")
                return {"CANCELLED"}
            originals.append(material)
        for slot, material in zip(obj.material_slots, originals):
            slot.material = material
        del obj[MATERIAL_STATE_KEY]
        for material in owned:
            if material.users == 0:
                bpy.data.materials.remove(material)
        self.report({"INFO"}, f"Restored original materials on {obj.name}")
        return {"FINISHED"}


CLASSES = (GAA_OT_apply_material_preset, GAA_OT_remove_material_preset)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
