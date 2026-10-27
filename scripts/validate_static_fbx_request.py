"""Development-only, read-only validation of an explicit static FBX export request.

This does not authorize export, inspect Blender IDs, create staging files, or certify
Unity import. The operator and destination must be rechecked immediately before use.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import stat


SCHEMA = "gameassetai.static-fbx-request.v1"
AXES = frozenset(("X", "Y", "Z", "-X", "-Y", "-Z"))
PATH_MODES = frozenset(("AUTO", "ABSOLUTE", "RELATIVE", "MATCH", "STRIP"))
SCALE_OPTIONS = frozenset(("FBX_SCALE_NONE", "FBX_SCALE_UNITS",
                           "FBX_SCALE_CUSTOM", "FBX_SCALE_ALL"))
OBSERVED_MIN_SCALE = 0.0010000000474974513
OBSERVED_MAX_SCALE = 1000.0
FIELDS = frozenset(("schema", "scene_name", "object_name", "target_file", "axis_forward",
                    "axis_up", "global_scale", "apply_unit_scale",
                    "apply_scale_options", "use_space_transform",
                    "bake_space_transform",
                    "use_mesh_modifiers", "path_mode", "overwrite"))


def _valid_target_stem(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if value.startswith(".") or value.endswith("."):
        return False
    if re.search(r'[\x00-\x1f/\\:*?"<>|]', value):
        return False
    base = value.split(".", 1)[0].upper()
    return base not in {"CON", "PRN", "AUX", "NUL",
                        *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)]}


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def _valid_scale(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return (math.isfinite(float(value))
                and OBSERVED_MIN_SCALE <= value <= OBSERVED_MAX_SCALE)
    except OverflowError:
        return False


def validate_static_fbx_request(request: object) -> dict:
    """Return a fail-closed preflight report; never mutate destination or request."""
    errors = []
    if not isinstance(request, dict):
        return {"schema": SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": ["request must be an object"]}
    if any(not isinstance(key, str) for key in request):
        return {"schema": SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": ["all request keys must be strings"]}
    missing = sorted(FIELDS - request.keys())
    unknown = sorted(request.keys() - FIELDS)
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if unknown:
        errors.append("unknown fields: " + ", ".join(unknown))
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    for key in ("scene_name", "object_name"):
        name = request.get(key)
        if not isinstance(name, str) or not name.strip() or name != name.strip():
            errors.append(key + " must be a nonempty exact name")
    forward = request.get("axis_forward")
    up = request.get("axis_up")
    if (not isinstance(forward, str) or forward not in AXES
            or not isinstance(up, str) or up not in AXES):
        errors.append("axis_forward and axis_up must be Blender FBX axis identifiers")
    elif forward.lstrip("-") == up.lstrip("-"):
        errors.append("axis_forward and axis_up must be perpendicular")
    scale = request.get("global_scale")
    if not _valid_scale(scale):
        errors.append("global_scale must be finite and within Blender 5.0.1 FBX RNA range")
    if request.get("apply_scale_options") not in SCALE_OPTIONS:
        errors.append("apply_scale_options must be an explicit FBX scaling enum")
    for key in ("apply_unit_scale", "use_space_transform", "bake_space_transform",
                "use_mesh_modifiers"):
        if not isinstance(request.get(key), bool):
            errors.append(key + " must be an explicit boolean")
    path_mode = request.get("path_mode")
    if not isinstance(path_mode, str) or path_mode not in PATH_MODES:
        errors.append("path_mode must be an explicit no-copy FBX enum; COPY is unsupported")
    if request.get("overwrite") is not False:
        errors.append("overwrite must be false")

    target_text = request.get("target_file")
    if (not isinstance(target_text, str) or not target_text
            or target_text != target_text.strip() or "\x00" in target_text):
        errors.append("target_file must be a nonempty absolute path")
    else:
        target = Path(target_text)
        if (not target.is_absolute() or target.suffix.lower() != ".fbx"
                or not _valid_target_stem(target.stem) or ".." in target.parts):
            errors.append("target_file must be an absolute .fbx path")
        else:
            try:
                if (not target.parent.is_dir()
                        or any(_is_link(parent) for parent in
                               (target.parent, *target.parent.parents))):
                    errors.append("target parent must exist and contain no link/reparse path")
                elif (_is_link(target) or target.exists()
                      or _is_link(Path(str(target) + ".meta"))
                      or Path(str(target) + ".meta").exists()):
                    errors.append("target_file or its .meta already exists")
            except OSError:
                errors.append("target path could not be inspected")
    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, "ready_for_blender_inspection": not errors,
            "request_sha256": digest, "errors": errors}
