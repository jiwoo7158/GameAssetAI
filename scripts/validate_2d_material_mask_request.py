"""Validate one explicit static material-mask PNG request without Blender writes."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import stat


SCHEMA = "gameassetai.2d-material-mask-request.v1"
TOP_FIELDS = frozenset(("schema", "scene_name", "object_name", "view", "mask", "style", "output"))
VIEW_FIELDS = frozenset(("projection", "direction", "up", "framing_margin"))
MASK_FIELDS = frozenset(("material_slot_index", "visible_rgba"))
STYLE_FIELDS = frozenset(("resolution", "anti_aliasing", "nearest_neighbor"))
OUTPUT_FIELDS = frozenset(("target_file", "color_mode", "color_depth", "overwrite"))


def _exact_fields(value, fields, label, errors):
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


def _finite(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _unit(value):
    return (isinstance(value, list) and len(value) == 3 and all(_finite(item) for item in value)
            and abs(math.sqrt(sum(float(item) ** 2 for item in value)) - 1.0) <= 1e-6)


def _opaque_rgba(value):
    return (isinstance(value, list) and len(value) == 4
            and all(_finite(item) and 0.0 <= float(item) <= 1.0 for item in value)
            and float(value[3]) == 1.0)


def _valid_stem(value):
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if value.startswith(".") or value.endswith(".") or re.search(r'[\x00-\x1f/\\:*?"<>|]', value):
        return False
    base = value.split(".", 1)[0].upper()
    return base not in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)]}


def _is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def validate_2d_material_mask_request(request):
    errors = []
    if not _exact_fields(request, TOP_FIELDS, "request", errors):
        return {"schema": SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": errors}
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    for key in ("scene_name", "object_name"):
        value = request.get(key)
        if not isinstance(value, str) or not value or value != value.strip():
            errors.append(f"{key} must be a nonempty exact name")

    view = request["view"]
    if _exact_fields(view, VIEW_FIELDS, "view", errors):
        if view["projection"] != "ORTHOGRAPHIC":
            errors.append("view.projection must be ORTHOGRAPHIC")
        if not _unit(view["direction"]) or not _unit(view["up"]):
            errors.append("view.direction and view.up must be finite unit 3-vectors")
        elif abs(sum(float(a) * float(b) for a, b in zip(view["direction"], view["up"]))) > 1e-6:
            errors.append("view.direction and view.up must be perpendicular")
        if not _finite(view["framing_margin"]) or not 0.0 <= float(view["framing_margin"]) <= 1.0:
            errors.append("view.framing_margin must be finite in [0, 1]")

    mask = request["mask"]
    if _exact_fields(mask, MASK_FIELDS, "mask", errors):
        index = mask["material_slot_index"]
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            errors.append("mask.material_slot_index must be a nonnegative integer")
        if not _opaque_rgba(mask["visible_rgba"]):
            errors.append("mask.visible_rgba must be an opaque RGBA color in [0, 1]")

    style = request["style"]
    if _exact_fields(style, STYLE_FIELDS, "style", errors):
        resolution = style["resolution"]
        if (not isinstance(resolution, list) or len(resolution) != 2
                or any(isinstance(item, bool) or not isinstance(item, int) or not 1 <= item <= 16384
                       for item in resolution)):
            errors.append("style.resolution must be two integers in [1, 16384]")
        if style["anti_aliasing"] != "DISABLED":
            errors.append("style.anti_aliasing must be DISABLED")
        if style["nearest_neighbor"] is not True:
            errors.append("style.nearest_neighbor must be true")

    output = request["output"]
    if _exact_fields(output, OUTPUT_FIELDS, "output", errors):
        if output["color_mode"] != "RGBA" or output["color_depth"] != 8:
            errors.append("output must be RGBA8")
        if output["overwrite"] is not False:
            errors.append("output.overwrite must be false")
        text = output["target_file"]
        if not isinstance(text, str) or not text or text != text.strip() or "\x00" in text:
            errors.append("output.target_file must be a nonempty absolute path")
        else:
            target = Path(text)
            try:
                meta = Path(str(target) + ".meta")
                if (not target.is_absolute() or target.suffix.lower() != ".png"
                        or not _valid_stem(target.stem) or ".." in target.parts):
                    errors.append("output.target_file must be an absolute .png path")
                elif (not target.parent.is_dir()
                      or any(_is_link(parent) for parent in (target.parent, *target.parent.parents))):
                    errors.append("output parent must exist and contain no link/reparse path")
                elif target.exists() or _is_link(target) or meta.exists() or _is_link(meta):
                    errors.append("output target or its .meta already exists")
            except OSError:
                errors.append("output path could not be inspected")

    digest = None
    if not errors:
        encoded = json.dumps(request, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        digest = hashlib.sha256(encoded).hexdigest()
    return {"schema": SCHEMA, "ready_for_blender_inspection": not errors,
            "request_sha256": digest, "errors": errors}
