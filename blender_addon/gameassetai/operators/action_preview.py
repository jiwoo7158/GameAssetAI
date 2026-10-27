import bpy


class GAA_OT_preview_action(bpy.types.Operator):
    bl_idname = "gameassetai.preview_action"
    bl_label = "Preview Action"
    bl_description = "Bind the explicitly selected Action for viewport review without deleting any data"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(
            settings
            and settings.animation_armature
            and settings.animation_action
            and settings.animation_armature.name in context.scene.objects
        )

    def execute(self, context):
        settings = context.scene.gameassetai
        armature = settings.animation_armature
        action = settings.animation_action
        animation_data = armature.animation_data_create()
        animation_data.action = action
        start, end = (int(round(value)) for value in action.frame_range)
        if end <= start:
            self.report({"ERROR"}, "The selected Action has no usable frame range")
            return {"CANCELLED"}
        context.scene.frame_start = start
        context.scene.frame_end = end
        context.scene.frame_set(start)
        self.report({"INFO"}, f"Previewing {action.name} on {armature.name}")
        return {"FINISHED"}


CLASSES = (GAA_OT_preview_action,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
