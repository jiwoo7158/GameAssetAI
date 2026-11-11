"""Validate one explicit, game-neutral static 3D-to-2D render request.

This is a read-only contract gate. It does not read a Workspace, inspect Blender, render,
authorize output, create directories, or infer missing game rules.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import stat


SCHEMA_V1 = "gameassetai.2d-static-render-request.v1"
SCHEMA_V2 = "gameassetai.2d-static-render-request.v2"
SCHEMA = "gameassetai.2d-static-render-request.v3"
TOP_FIELDS = frozenset(("schema", "scene_name", "object_name", "profile",
                        "view", "lighting", "style", "output"))
PROFILE_FIELDS = frozenset(("name", "reference_sha256", "profile_sha256"))
VIEW_FIELDS = frozenset(("projection", "direction", "up", "framing_margin"))
LIGHTING_FIELDS = frozenset(("mode", "transparent_background"))
STYLE_FIELDS_V1 = frozenset(("mode", "resolution", "anti_aliasing",
                             "nearest_neighbor", "palette_mode", "palette", "max_colors"))
STYLE_FIELDS_V2 = STYLE_FIELDS_V1 | frozenset(("outline_mode", "outline_color", "outline_width"))
STYLE_FIELDS = STYLE_FIELDS_V2 | frozenset(("shading_mode", "value_steps"))
OUTPUT_FIELDS = frozenset(("target_file", "color_mode", "color_depth", "overwrite"))
STYLE_MODES = frozenset(("PIXEL", "CEL", "FLAT_TOON"))
LIGHTING_MODES = frozenset(("SOURCE_COPY", "OWNED_NEUTRAL"))
PALETTE_MODES = frozenset(("NONE", "AUTO", "FIXED"))


def _valid_file_stem(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if value.startswith(".") or value.endswith(".") or re.search(r'[\x00-\x1f/\\:*?"<>|]', value):
        return False
    base = value.split(".", 1)[0].upper()
    return base not in {"CON", "PRN", "AUX", "NUL",
                        *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)]}


def _exact_fields(value: object, fields: frozenset[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        errors.append(f"{label} must be an object with string keys")
        return False
    missing = sorted(fields - value.keys())
    unknown = sorted(value.keys() - fields)
    if missing:
        errors.append(f"{label} missing fields: " + ", ".join(missing))
    if unknown:
        errors.append(f"{label} unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _finite_number(value: object) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(float(value)))


def _unit_vector(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 3 or not all(_finite_number(v) for v in value):
        return False
    return abs(math.sqrt(sum(float(v) ** 2 for v in value)) - 1.0) <= 1e-6


def _rgba(value: object) -> bool:
    return (isinstance(value, list) and len(value) == 4
            and all(_finite_number(v) and 0.0 <= float(v) <= 1.0 for v in value))


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def validate_2d_static_render_request(request: object) -> dict:
    """Return a deterministic fail-closed report without mutating request or filesystem."""
    errors: list[str] = []
    if not _exact_fields(request, TOP_FIELDS, "request", errors):
        return {"schema": SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": errors}
    schema = request.get("schema")
    if schema not in {SCHEMA_V1, SCHEMA_V2, SCHEMA}:
        errors.append("schema mismatch")
    for key in ("scene_name", "object_name"):
        value = request.get(key)
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            errors.append(f"{key} must be a nonempty exact name")

    profile = request["profile"]
    if _exact_fields(profile, PROFILE_FIELDS, "profile", errors):
        values = (profile["name"], profile["reference_sha256"], profile["profile_sha256"])
        if values != (None, None, None):
            if (not isinstance(values[0], str) or not _valid_file_stem(values[0])):
                errors.append("profile.name must be a nonempty exact name or null")
            for key, value in zip(("reference_sha256", "profile_sha256"), values[1:]):
                if (not isinstance(value, str) or len(value) != 64
                        or any(c not in "0123456789abcdef" for c in value)):
                    errors.append(f"profile.{key} must be a lowercase SHA-256")

    view = request["view"]
    if _exact_fields(view, VIEW_FIELDS, "view", errors):
        if view["projection"] != "ORTHOGRAPHIC":
            errors.append("view.projection must be ORTHOGRAPHIC")
        if not _unit_vector(view["direction"]) or not _unit_vector(view["up"]):
            errors.append("view.direction and view.up must be finite unit 3-vectors")
        else:
            dot = sum(float(a) * float(b) for a, b in zip(view["direction"], view["up"]))
            if abs(dot) > 1e-6:
                errors.append("view.direction and view.up must be perpendicular")
        margin = view["framing_margin"]
        if not _finite_number(margin) or not 0.0 <= float(margin) <= 1.0:
            errors.append("view.framing_margin must be finite in [0, 1]")

    lighting = request["lighting"]
    if _exact_fields(lighting, LIGHTING_FIELDS, "lighting", errors):
        if lighting["mode"] not in LIGHTING_MODES:
            errors.append("lighting.mode must be SOURCE_COPY or OWNED_NEUTRAL")
        if not isinstance(lighting["transparent_background"], bool):
            errors.append("lighting.transparent_background must be boolean")

    style = request["style"]
    style_fields = (STYLE_FIELDS_V1 if schema == SCHEMA_V1 else
                    STYLE_FIELDS_V2 if schema == SCHEMA_V2 else STYLE_FIELDS)
    if _exact_fields(style, style_fields, "style", errors):
        if style["mode"] not in STYLE_MODES:
            errors.append("style.mode must be PIXEL, CEL or FLAT_TOON")
        resolution = style["resolution"]
        if (not isinstance(resolution, list) or len(resolution) != 2
                or any(isinstance(v, bool) or not isinstance(v, int) or not 1 <= v <= 16384
                       for v in resolution)):
            errors.append("style.resolution must be two integers in [1, 16384]")
        if style["anti_aliasing"] not in {"DISABLED", "ENGINE_DEFAULT"}:
            errors.append("style.anti_aliasing must be DISABLED or ENGINE_DEFAULT")
        if not isinstance(style["nearest_neighbor"], bool):
            errors.append("style.nearest_neighbor must be boolean")
        mode, palette, maximum = style["palette_mode"], style["palette"], style["max_colors"]
        if mode not in PALETTE_MODES:
            errors.append("style.palette_mode must be NONE, AUTO or FIXED")
        if not isinstance(palette, list) or not all(_rgba(color) for color in palette):
            errors.append("style.palette must be a list of RGBA colors in [0, 1]")
        elif mode == "FIXED" and (not palette or maximum is not None):
            errors.append("FIXED palette requires colors and null max_colors")
        elif mode == "AUTO" and (palette or isinstance(maximum, bool)
                                  or not isinstance(maximum, int) or not 2 <= maximum <= 256):
            errors.append("AUTO palette requires no fixed colors and max_colors in [2, 256]")
        elif mode == "NONE" and (palette or maximum is not None):
            errors.append("NONE palette requires no colors and null max_colors")
        if schema in {SCHEMA_V2, SCHEMA}:
            outline_mode = style["outline_mode"]
            outline_color = style["outline_color"]
            outline_width = style["outline_width"]
            if outline_mode == "NONE":
                if outline_color is not None or outline_width != 0:
                    errors.append("NONE outline requires null color and width 0")
            elif outline_mode == "OUTER":
                if (not _rgba(outline_color) or float(outline_color[3]) != 1.0
                        or outline_width != 1):
                    errors.append("OUTER outline requires one opaque RGBA color and width 1")
            else:
                errors.append("style.outline_mode must be NONE or OUTER")
        if schema == SCHEMA:
            shading_mode = style["shading_mode"]
            value_steps = style["value_steps"]
            if shading_mode == "NONE":
                if value_steps is not None:
                    errors.append("NONE shading requires null value_steps")
            elif shading_mode == "VALUE_STEPS":
                if (isinstance(value_steps, bool) or not isinstance(value_steps, int)
                        or not 2 <= value_steps <= 32):
                    errors.append("VALUE_STEPS shading requires value_steps in [2, 32]")
            else:
                errors.append("style.shading_mode must be NONE or VALUE_STEPS")

    output = request["output"]
    if _exact_fields(output, OUTPUT_FIELDS, "output", errors):
        if output["color_mode"] not in {"RGB", "RGBA"}:
            errors.append("output.color_mode must be RGB or RGBA")
        if output["color_depth"] not in {8, 16}:
            errors.append("output.color_depth must be 8 or 16")
        if output["overwrite"] is not False:
            errors.append("output.overwrite must be false")
        target_text = output["target_file"]
        if (not isinstance(target_text, str) or not target_text
                or target_text != target_text.strip() or "\x00" in target_text):
            errors.append("output.target_file must be a nonempty absolute path")
        else:
            target = Path(target_text)
            try:
                if (not target.is_absolute() or target.suffix.lower() != ".png"
                        or not _valid_file_stem(target.stem) or ".." in target.parts):
                    errors.append("output.target_file must be an absolute .png path")
                elif (not target.parent.is_dir()
                      or any(_is_link(parent) for parent in (target.parent, *target.parent.parents))):
                    errors.append("output parent must exist and contain no link/reparse path")
                elif (_is_link(target) or target.exists()
                      or _is_link(Path(str(target) + ".meta"))
                      or Path(str(target) + ".meta").exists()):
                    errors.append("output target or its .meta already exists")
            except OSError:
                errors.append("output path could not be inspected")

    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, "ready_for_blender_inspection": not errors,
            "request_sha256": digest, "errors": errors}
# Retained bounded Blender capability; product support remains evidence-scoped.
