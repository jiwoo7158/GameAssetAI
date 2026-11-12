import os
from pathlib import Path
import uuid

import bpy


class GAA_OT_export_preview_png(bpy.types.Operator):
    bl_idname = "gameassetai.export_preview_png"
    bl_label = "Export Preview PNG"
    bl_description = "Render the configured preview to a new PNG and publish it atomically"

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(settings and settings.export_file.strip() and context.scene.camera)

    def execute(self, context):
        scene = context.scene
        settings = scene.gameassetai
        target = Path(bpy.path.abspath(settings.export_file)).resolve()
        if target.suffix.lower() != ".png" or not target.is_absolute():
            self.report({"ERROR"}, "Choose an absolute .png output path")
            return {"CANCELLED"}
        if not target.parent.is_dir():
            self.report({"ERROR"}, "Output directory does not exist")
            return {"CANCELLED"}
        if target.exists():
            self.report({"ERROR"}, "Output file already exists; overwrite is disabled")
            return {"CANCELLED"}
        temporary = target.with_name(f".{target.stem}.{uuid.uuid4().hex}.stage.png")
        render = scene.render
        image = render.image_settings
        previous = {
            "resolution_x": render.resolution_x,
            "resolution_y": render.resolution_y,
            "resolution_percentage": render.resolution_percentage,
            "film_transparent": render.film_transparent,
            "file_format": image.file_format,
            "color_mode": image.color_mode,
            "color_depth": image.color_depth,
        }
        try:
            render.resolution_x = settings.resolution_x
            render.resolution_y = settings.resolution_y
            render.resolution_percentage = 100
            render.film_transparent = True
            image.file_format = "PNG"
            image.color_mode = "RGBA"
            image.color_depth = "8"
            bpy.ops.render.render()
            bpy.data.images["Render Result"].save_render(str(temporary), scene=scene)
            if not temporary.is_file() or temporary.stat().st_size < 8:
                raise RuntimeError("Blender did not create a valid staged PNG")
            with temporary.open("rb") as handle:
                if handle.read(8) != b"\x89PNG\r\n\x1a\n":
                    raise RuntimeError("Staged output is not a PNG")
            os.replace(temporary, target)
        except Exception as exc:
            if temporary.exists():
                temporary.unlink()
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            render.resolution_x = previous["resolution_x"]
            render.resolution_y = previous["resolution_y"]
            render.resolution_percentage = previous["resolution_percentage"]
            render.film_transparent = previous["film_transparent"]
            image.file_format = previous["file_format"]
            image.color_mode = previous["color_mode"]
            image.color_depth = previous["color_depth"]
        self.report({"INFO"}, f"Created {target.name}")
        return {"FINISHED"}


CLASSES = (GAA_OT_export_preview_png,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
