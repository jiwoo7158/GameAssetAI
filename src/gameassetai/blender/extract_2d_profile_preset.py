"""Extract one optional exact 2D preset block from a read-only Workspace Profile context."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

from validate_2d_static_render_request import validate_2d_static_render_request


PRESET_SCHEMA = "gameassetai.2d-profile-preset.v1"
_BLOCK = re.compile(
    r"^```gameassetai-2d-preset[ \t]*\r?\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL)
_FIELDS = {"schema", "view", "lighting", "style", "sequence", "sprite_sheet"}


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def extract_2d_profile_preset(context):
    """Return absent/ready/error without reading files, changing context, or choosing defaults."""
    report = {"schema": PRESET_SCHEMA, "status": "error", "errors": [],
              "preset_available": False}
    try:
        if (not isinstance(context, dict)
                or context.get("schema") != "gameassetai.profile-context.v1"):
            raise ValueError("An exact gameassetai.profile-context.v1 object is required")
        name, path, markdown = context.get("profile"), context.get("path"), context.get("markdown")
        reference_sha, profile_sha = context.get("reference_sha256"), context.get("profile_sha256")
        if name is None:
            if path is not None or markdown is not None or profile_sha is not None:
                raise ValueError("Null Profile context fields are inconsistent")
            report.update(status="absent", reason="no_active_profile")
            return report
        if (not isinstance(name, str) or not name or not isinstance(path, str)
                or not Path(path).is_absolute() or not isinstance(markdown, str)
                or not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                           for value in (reference_sha, profile_sha))):
            raise ValueError("Active Profile context provenance is incomplete")
        matches = _BLOCK.findall(markdown)
        if not matches:
            report.update(status="absent", reason="no_explicit_2d_preset",
                          profile=name, reference_sha256=reference_sha,
                          profile_sha256=profile_sha)
            return report
        if len(matches) != 1:
            raise ValueError("Profile must contain at most one gameassetai-2d-preset block")
        preset = json.loads(matches[0])
        if not isinstance(preset, dict) or set(preset) != _FIELDS:
            raise ValueError("2D Profile preset fields must be exact")
        if preset.get("schema") != PRESET_SCHEMA:
            raise ValueError("2D Profile preset schema is unsupported")
        sequence, sprite_sheet = preset.get("sequence"), preset.get("sprite_sheet")
        if not isinstance(sequence, dict) or set(sequence) != {"playback_fps"}:
            raise ValueError("preset.sequence must contain only playback_fps")
        fps = sequence.get("playback_fps")
        if (isinstance(fps, bool) or not isinstance(fps, (int, float))
                or not math.isfinite(float(fps)) or not 0 < float(fps) <= 240):
            raise ValueError("preset playback_fps must be finite in (0, 240]")
        if (not isinstance(sprite_sheet, dict)
                or set(sprite_sheet) != {"padding", "order"}
                or isinstance(sprite_sheet.get("padding"), bool)
                or not isinstance(sprite_sheet.get("padding"), int)
                or not 0 <= sprite_sheet["padding"] <= 256
                or sprite_sheet.get("order") != "ROW_MAJOR_TOP_LEFT"):
            raise ValueError("preset.sprite_sheet requires bounded padding and ROW_MAJOR_TOP_LEFT")

        validation_target = Path(path).parent / (
            "gameassetai-profile-preset-validation-" + _hash(preset)[:16] + ".png")
        static_request = {
            "schema": "gameassetai.2d-static-render-request.v3",
            "scene_name": "PROFILE_VALIDATION_SCENE",
            "object_name": "PROFILE_VALIDATION_OBJECT",
            "profile": {"name": name, "reference_sha256": reference_sha,
                        "profile_sha256": profile_sha},
            "view": preset["view"], "lighting": preset["lighting"],
            "style": preset["style"],
            "output": {"target_file": str(validation_target), "color_mode": "RGBA",
                       "color_depth": 8, "overwrite": False},
        }
        static = validate_2d_static_render_request(static_request)
        if not static.get("ready_for_blender_inspection"):
            raise ValueError("Invalid static 2D preset: " + "; ".join(static.get("errors", [])))
        report.update(status="ready", preset_available=True, profile=name,
                      reference_sha256=reference_sha, profile_sha256=profile_sha,
                      preset=preset, preset_sha256=_hash(preset),
                      limitations=["Preset values are explicit only; no missing value is inferred",
                                   "Output paths, frame ranges, Actions and grid dimensions remain per-request"])
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, OSError) as exc:
        report["errors"].append(str(exc))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
