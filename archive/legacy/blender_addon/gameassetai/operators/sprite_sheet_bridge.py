import json
from pathlib import Path
import sys

import bpy


HELPERS = (
    "validate_2d_static_render_request.py",
    "validate_2d_sprite_sheet_request.py",
    "quantize_rgba.py",
    "assemble_2d_sprite_sheet.py",
)


def _load_helpers(root):
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    namespace = {"__builtins__": __builtins__}
    for name in HELPERS:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Missing sprite-sheet helper: {name}")
        source = path.read_text(encoding="utf-8-sig")
        exec(compile(source, str(path), "exec"), namespace, namespace)
    return namespace


def _request(scene, settings):
    receipt = json.loads(scene["gaa_last_sequence_receipt"])
    artifacts = receipt.get("artifacts", [])
    frames = [{"source_frame": item["source_frame"],
               "sequence_index": item["sequence_index"],
               "path": item["path"], "sha256": item["sha256"],
               "anchor_pixel_from_bottom_left": item["anchor_pixel_from_bottom_left"]}
              for item in artifacts]
    cell_size = [artifacts[0]["width"], artifacts[0]["height"]] if artifacts else [0, 0]
    return {
        "schema": "gameassetai.2d-sprite-sheet-request.v2",
        "profile": {"name": None, "reference_sha256": None,
                    "profile_sha256": None, "preset_sha256": None},
        "frames": frames,
        "layout": {"cell_size": cell_size, "columns": settings.sprite_sheet_columns,
                   "rows": settings.sprite_sheet_rows, "padding": settings.sprite_sheet_padding,
                   "order": "ROW_MAJOR_TOP_LEFT"},
        "output": {"target_file": str(Path(bpy.path.abspath(settings.sprite_sheet_file)).resolve()),
                   "metadata_file": str(Path(bpy.path.abspath(settings.sprite_sheet_metadata_file)).resolve()),
                   "overwrite": False},
    }


class GAA_OT_assemble_last_sequence_sheet(bpy.types.Operator):
    bl_idname = "gameassetai.assemble_last_sequence_sheet"
    bl_label = "Assemble Last Sequence"
    bl_description = "Assemble the last verified sequence with the existing atomic sprite-sheet helper"

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(settings and "gaa_last_sequence_receipt" in context.scene
                    and settings.sprite_sheet_helper_root.strip()
                    and settings.sprite_sheet_file.strip()
                    and settings.sprite_sheet_metadata_file.strip())

    def execute(self, context):
        settings = context.scene.gameassetai
        helper_root = Path(bpy.path.abspath(settings.sprite_sheet_helper_root)).resolve()
        try:
            namespace = _load_helpers(helper_root)
            request = _request(context.scene, settings)
            preview = namespace["validate_2d_sprite_sheet_request"](request)
            if preview.get("status") != "ready":
                raise ValueError("; ".join(preview.get("errors", [])))
            result = namespace["assemble_2d_sprite_sheet"](request, preview, authorize=True)
            if result.get("status") != "created" or not result.get("artifacts_published"):
                raise RuntimeError("; ".join(result.get("errors", ["Sprite-sheet assembly failed"])))
            context.scene["gaa_last_sprite_sheet_receipt"] = json.dumps(result, separators=(",", ":"))
            self.report({"INFO"}, f"Created {Path(result['target_file']).name}")
            return {"FINISHED"}
        except (ValueError, RuntimeError, OSError, KeyError, json.JSONDecodeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}


CLASSES = (GAA_OT_assemble_last_sequence_sheet,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
