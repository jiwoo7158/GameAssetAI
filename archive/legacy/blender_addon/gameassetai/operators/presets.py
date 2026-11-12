import json
import os
from pathlib import Path
import uuid

import bpy


SCHEMA = "gameassetai.blender-addon-preset.v1"
FIELDS = {
    "resolution_x": (int, 8, 4096),
    "resolution_y": (int, 8, 4096),
    "framing_margin": ((int, float), 0.0, 1.0),
    "view_preset": ({"FRONT", "SIDE", "QUARTER", "TOP"}, None, None),
    "key_energy": ((int, float), 0.0, None),
    "fill_energy": ((int, float), 0.0, None),
    "pixel_scale": (int, 1, 64),
    "material_preset": ({"FLAT_LIT", "CEL_BANDED", "EMISSION_UNLIT"}, None, None),
    "shadow_bands": (int, 2, 6),
}


def _path(settings):
    return Path(bpy.path.abspath(settings.preset_file)).resolve()


def _values(settings):
    return {name: getattr(settings, name) for name in FIELDS}


def _validate(document):
    if not isinstance(document, dict) or set(document) != {"schema", "settings"}:
        raise ValueError("Preset fields must be exactly schema and settings")
    if document["schema"] != SCHEMA or not isinstance(document["settings"], dict):
        raise ValueError(f"Preset schema must be {SCHEMA}")
    values = document["settings"]
    if set(values) != set(FIELDS):
        raise ValueError("Preset settings fields do not match this Add-on version")
    for name, (kind, minimum, maximum) in FIELDS.items():
        value = values[name]
        if isinstance(kind, set):
            if value not in kind:
                raise ValueError(f"Invalid {name}")
        else:
            if isinstance(value, bool) or not isinstance(value, kind):
                raise ValueError(f"Invalid type for {name}")
            if minimum is not None and value < minimum or maximum is not None and value > maximum:
                raise ValueError(f"{name} is outside the supported range")
    return values


class GAA_OT_save_preset(bpy.types.Operator):
    bl_idname = "gameassetai.save_preset"
    bl_label = "Save Preset"
    bl_description = "Save portable preview settings to a new JSON file"

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(settings and settings.preset_file.strip())

    def execute(self, context):
        target = _path(context.scene.gameassetai)
        if target.suffix.lower() != ".json" or not target.parent.is_dir():
            self.report({"ERROR"}, "Choose a .json path in an existing directory")
            return {"CANCELLED"}
        if target.exists():
            self.report({"ERROR"}, "Preset already exists; overwrite is disabled")
            return {"CANCELLED"}
        stage = target.with_name(f".{target.stem}.{uuid.uuid4().hex}.stage.json")
        document = {"schema": SCHEMA, "settings": _values(context.scene.gameassetai)}
        try:
            stage.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            _validate(json.loads(stage.read_text(encoding="utf-8")))
            os.replace(stage, target)
        except Exception as exc:
            if stage.exists():
                stage.unlink()
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Saved {target.name}")
        return {"FINISHED"}


class GAA_OT_load_preset(bpy.types.Operator):
    bl_idname = "gameassetai.load_preset"
    bl_label = "Load Preset"
    bl_description = "Validate and load portable preview settings without changing scene data"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(settings and settings.preset_file.strip())

    def execute(self, context):
        source = _path(context.scene.gameassetai)
        if source.suffix.lower() != ".json" or not source.is_file():
            self.report({"ERROR"}, "Preset JSON does not exist")
            return {"CANCELLED"}
        try:
            values = _validate(json.loads(source.read_text(encoding="utf-8")))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        settings = context.scene.gameassetai
        for name, value in values.items():
            setattr(settings, name, value)
        self.report({"INFO"}, f"Loaded {source.name}")
        return {"FINISHED"}


CLASSES = (GAA_OT_save_preset, GAA_OT_load_preset)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
