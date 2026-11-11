"""Fail-closed validation for one explicit Unity animated-FBX export request."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import stat


ANIMATED_FBX_SCHEMA = "gameassetai.animated-fbx-export-request.v1"
_FIELDS = {"schema", "scene_name", "mesh_object_name", "armature_object_name", "action_name",
           "action_slot_identifier", "clip", "target", "transform", "geometry", "materials",
           "rig", "animation", "policy"}
_PARTS = {
    "clip": {"frame_start", "frame_end", "fps"},
    "target": {"engine", "target_file"},
    "transform": {"axis_forward", "axis_up", "global_scale", "apply_unit_scale",
                  "apply_scale_options", "use_space_transform", "bake_space_transform"},
    "geometry": {"use_mesh_modifiers"},
    "materials": {"mode", "path_mode"},
    "rig": {"add_leaf_bones", "deform_bones_only", "armature_nodetype", "validation_bones"},
    "animation": {"bake_step", "simplify_factor", "loop", "root_motion"},
    "policy": {"preserve_source", "overwrite", "failure"},
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def _is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def _exact(value, keys, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    missing, unknown = sorted(keys - set(value)), sorted(set(value) - keys)
    if missing:
        errors.append(f"missing {label} fields: " + ", ".join(missing))
    if unknown:
        errors.append(f"unknown {label} fields: " + ", ".join(unknown))
    return not missing and not unknown


def _name(value, label, errors):
    if not isinstance(value, str) or not value or value != value.strip():
        errors.append(f"{label} must be an exact nonempty name")


def validate_animated_fbx_request(request):
    errors = []
    if not _exact(request, _FIELDS, "request", errors):
        return {"schema": ANIMATED_FBX_SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": errors}
    if request["schema"] != ANIMATED_FBX_SCHEMA:
        errors.append("schema mismatch")
    for key in ("scene_name", "mesh_object_name", "armature_object_name", "action_name",
                "action_slot_identifier"):
        _name(request[key], key, errors)
    for key, fields in _PARTS.items():
        _exact(request[key], fields, key, errors)
    if errors:
        return {"schema": ANIMATED_FBX_SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "errors": errors}
    clip = request["clip"]
    for key in ("frame_start", "frame_end", "fps"):
        if isinstance(clip[key], bool) or not isinstance(clip[key], int):
            errors.append(f"clip.{key} must be an integer")
    if not errors and (clip["frame_end"] <= clip["frame_start"]
                       or clip["frame_end"] - clip["frame_start"] > 10000):
        errors.append("clip range must contain 2..10001 inclusive integer frames")
    if not errors and not 1 <= clip["fps"] <= 240:
        errors.append("clip.fps must be within 1..240")
    target = request["target"]
    if target["engine"] != "UNITY":
        errors.append("target.engine must be UNITY")
    target_file = Path(target["target_file"]) if isinstance(target["target_file"], str) else None
    if (target_file is None or not target_file.is_absolute()
            or target_file.suffix.lower() != ".fbx" or ".." in target_file.parts
            or not re.fullmatch(r"[^\x00-\x1f/\\:*?\"<>|]+", target_file.stem or "")):
        errors.append("target.target_file must be an absolute portable .fbx path")
    else:
        meta = Path(str(target_file) + ".meta")
        try:
            if (not target_file.parent.is_dir()
                    or any(_is_link(path) for path in (target_file.parent, *target_file.parent.parents))):
                errors.append("target parent must be an existing real directory")
            elif target_file.exists() or _is_link(target_file) or meta.exists() or _is_link(meta):
                errors.append("target FBX or .meta already exists")
        except OSError:
            errors.append("target path could not be inspected")
    transform = request["transform"]
    required_transform = {"axis_forward": "-Z", "axis_up": "Y", "global_scale": 1.0,
                          "apply_unit_scale": True, "apply_scale_options": "FBX_SCALE_UNITS",
                          "use_space_transform": True, "bake_space_transform": False}
    for key, expected in required_transform.items():
        value = transform[key]
        if key == "global_scale":
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(float(value)) or float(value) != expected):
                errors.append("transform.global_scale must be 1.0")
        elif value != expected:
            errors.append(f"transform.{key} must be {expected!r} for the tested Unity path")
    if request["geometry"]["use_mesh_modifiers"] is not True:
        errors.append("geometry.use_mesh_modifiers must be true")
    if request["materials"] != {"mode": "BLENDER_MATERIALS_NO_TEXTURE_COPY", "path_mode": "STRIP"}:
        errors.append("materials policy must be BLENDER_MATERIALS_NO_TEXTURE_COPY/STRIP")
    rig = request["rig"]
    if rig["add_leaf_bones"] is not False or rig["deform_bones_only"] is not True:
        errors.append("rig requires add_leaf_bones=false and deform_bones_only=true")
    if rig["armature_nodetype"] != "NULL":
        errors.append("rig.armature_nodetype must be NULL")
    bones = rig["validation_bones"]
    if (not isinstance(bones, list) or len(bones) < 2 or len(bones) > 32
            or any(not isinstance(name, str) or not name or name != name.strip() for name in bones)
            or len(set(bones)) != len(bones)):
        errors.append("rig.validation_bones must contain 2..32 unique exact names")
    animation = request["animation"]
    if animation != {"bake_step": 1.0, "simplify_factor": 0.0, "loop": False,
                     "root_motion": "IN_PLACE"}:
        errors.append("animation must use step 1, simplify 0, loop false and IN_PLACE")
    if request["policy"] != {"preserve_source": True, "overwrite": False,
                             "failure": "ROLL_BACK_TEMPORARY_DATA"}:
        errors.append("policy must preserve source, refuse overwrite and roll back temporary data")
    digest = None if errors else hashlib.sha256(_canonical(request).encode("utf-8")).hexdigest()
    return {"schema": ANIMATED_FBX_SCHEMA, "ready_for_blender_inspection": not errors,
            "request_sha256": digest, "errors": errors}
# Retained bounded Blender capability; product support remains evidence-scoped.
