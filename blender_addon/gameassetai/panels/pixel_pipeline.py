import bpy


class GAA_PT_pixel_pipeline(bpy.types.Panel):
    bl_label = "GameAssetAI"
    bl_idname = "GAA_PT_pixel_pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "GameAssetAI"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.gameassetai

        target = settings.material_target
        if target is None and context.active_object and context.active_object.type == "MESH":
            target = context.active_object
        box = layout.box()
        box.label(text="Pixel Scene Setup", icon="CAMERA_DATA")
        box.label(text=f"Target: {target.name}" if target else "Target: select a Mesh")
        box.prop(settings, "view_preset")
        row = box.row(align=True)
        row.prop(settings, "resolution_x")
        row.prop(settings, "resolution_y")
        box.prop(settings, "framing_margin")
        box.prop(settings, "pixel_scale")

        lighting = layout.box()
        lighting.label(text="Owned Neutral Lighting", icon="LIGHT")
        lighting.prop(settings, "key_energy")
        lighting.prop(settings, "fill_energy")

        row = layout.row(align=True)
        row.operator("gameassetai.setup_pixel_scene", icon="ADD")
        row.operator("gameassetai.remove_pixel_scene", icon="TRASH")

        compositor = layout.box()
        compositor.label(text="Compositor", icon="NODE_COMPOSITING")
        compositor.label(text="Downsample -> Pixelate -> Restore Size")
        row = compositor.row(align=True)
        row.operator("gameassetai.build_pixel_compositor", icon="NODETREE")
        row.operator("gameassetai.remove_pixel_compositor", icon="TRASH")

        animation = layout.box()
        animation.label(text="Action Preview", icon="ACTION")
        animation.prop(settings, "animation_armature")
        animation.prop(settings, "animation_action")
        animation.operator("gameassetai.preview_action", icon="PLAY")
        armature = settings.animation_armature
        active = armature.animation_data.action if armature and armature.animation_data else None
        animation.label(text=f"Active: {active.name}" if active else "Active: none")
        controls = animation.row(align=True)
        first = controls.operator("screen.frame_jump", text="First", icon="REW")
        first.end = False
        controls.operator("screen.animation_play", text="Play", icon="PLAY")
        last = controls.operator("screen.frame_jump", text="Last", icon="FF")
        last.end = True

        materials = layout.box()
        materials.label(text="Material Style Preview", icon="MATERIAL")
        materials.prop(settings, "material_target")
        materials.prop(settings, "material_preset")
        if settings.material_preset == "CEL_BANDED":
            materials.prop(settings, "shadow_bands")
        row = materials.row(align=True)
        row.operator("gameassetai.apply_material_preset", icon="SHADING_RENDERED")
        row.operator("gameassetai.remove_material_preset", icon="LOOP_BACK")

        export = layout.box()
        export.label(text="Single PNG Export", icon="IMAGE_DATA")
        export.prop(settings, "export_file")
        export.operator("gameassetai.export_preview_png", icon="EXPORT")
        export.label(text="New files only; current frame and camera")

        preset = layout.box()
        preset.label(text="Portable Preset", icon="PRESET")
        preset.prop(settings, "preset_file")
        row = preset.row(align=True)
        row.operator("gameassetai.save_preset", icon="FILE_TICK")
        row.operator("gameassetai.load_preset", icon="FILE_REFRESH")

        sequence = layout.box()
        sequence.label(text="Action PNG Sequence", icon="RENDER_ANIMATION")
        sequence.prop(settings, "sequence_helper_root")
        sequence.prop(settings, "sequence_output_directory")
        sequence.prop(settings, "sequence_prefix")
        row = sequence.row(align=True)
        row.prop(settings, "sequence_frame_step")
        row.prop(settings, "sequence_index_padding")
        sequence.operator("gameassetai.render_action_sequence", icon="RENDER_ANIMATION")
        sequence.label(text="Background Blender; all frames or rollback")

        sheet = layout.box()
        sheet.label(text="Sprite Sheet Handoff", icon="UV")
        sheet.prop(settings, "sprite_sheet_helper_root")
        sheet.prop(settings, "sprite_sheet_file")
        sheet.prop(settings, "sprite_sheet_metadata_file")
        row = sheet.row(align=True)
        row.prop(settings, "sprite_sheet_columns")
        row.prop(settings, "sprite_sheet_rows")
        sheet.prop(settings, "sprite_sheet_padding")
        sheet.operator("gameassetai.assemble_last_sequence_sheet", icon="IMAGE_DATA")


CLASSES = (GAA_PT_pixel_pipeline,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
