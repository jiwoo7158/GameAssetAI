"""Validate one explicit Action-to-PNG-sequence request without opening Blender."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from validate_2d_static_render_request import (
    SCHEMA as STATIC_SCHEMA,
    _valid_file_stem,
    validate_2d_static_render_request,
)


SCHEMA = "gameassetai.2d-action-sequence-request.v1"
TOP_FIELDS = frozenset(("schema", "static_template", "animation", "framing", "output"))
STATIC_TEMPLATE_FIELDS = frozenset(("schema", "scene_name", "object_name", "profile",
                                    "view", "lighting", "style"))
ANIMATION_FIELDS = frozenset(("armature_name", "action_name", "slot_identifier",
                              "frame_start", "frame_end", "frame_step", "playback_fps"))
FRAMING_FIELDS = frozenset(("bounds_policy", "anchor_policy"))
OUTPUT_FIELDS = frozenset(("target_directory", "filename_prefix", "index_start",
                           "index_padding", "overwrite"))
MAX_SEQUENCE_FRAMES = 2048


def _exact(value, fields, label, errors):
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        errors.append(f"{label} must be an object with string keys")
        return False
    missing, unknown = sorted(fields - value.keys()), sorted(value.keys() - fields)
    if missing:
        errors.append(f"{label} missing fields: " + ", ".join(missing))
    if unknown:
        errors.append(f"{label} unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _integer(value):
    return not isinstance(value, bool) and isinstance(value, int)


def _digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_2d_action_sequence_request(request):
    """Return a deterministic frame plan; never inspect Blender or create output."""
    errors, frames = [], []
    if not _exact(request, TOP_FIELDS, "request", errors):
        return {"schema": SCHEMA, "ready_for_blender_inspection": False,
                "request_sha256": None, "frame_plan_sha256": None,
                "frame_count": 0, "frames": [], "errors": errors}
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")

    template = request["static_template"]
    if _exact(template, STATIC_TEMPLATE_FIELDS, "static_template", errors):
        if template["schema"] != STATIC_SCHEMA:
            errors.append(f"static_template.schema must be {STATIC_SCHEMA}")

    animation = request["animation"]
    sample_frames = []
    if _exact(animation, ANIMATION_FIELDS, "animation", errors):
        for key in ("armature_name", "action_name"):
            value = animation[key]
            if not isinstance(value, str) or not value or value != value.strip():
                errors.append(f"animation.{key} must be a nonempty exact name")
        slot = animation["slot_identifier"]
        if slot is not None and (not isinstance(slot, str) or not slot or slot != slot.strip()):
            errors.append("animation.slot_identifier must be null or a nonempty exact identifier")
        start, end, step = (animation[key] for key in
                            ("frame_start", "frame_end", "frame_step"))
        if not all(_integer(value) for value in (start, end, step)):
            errors.append("animation frame_start, frame_end and frame_step must be integers")
        elif step < 1 or end < start or (end - start) % step:
            errors.append("animation range must be ascending, positive-step and include frame_end exactly")
        else:
            sample_frames = list(range(start, end + 1, step))
            if len(sample_frames) > MAX_SEQUENCE_FRAMES:
                errors.append(f"animation range exceeds {MAX_SEQUENCE_FRAMES} output frames")
        fps = animation["playback_fps"]
        if (isinstance(fps, bool) or not isinstance(fps, (int, float))
                or not math.isfinite(float(fps)) or not 0.0 < float(fps) <= 240.0):
            errors.append("animation.playback_fps must be finite in (0, 240]")

    framing = request["framing"]
    if _exact(framing, FRAMING_FIELDS, "framing", errors):
        if framing["bounds_policy"] != "ACTION_RANGE":
            errors.append("framing.bounds_policy must be ACTION_RANGE")
        if framing["anchor_policy"] != "OBJECT_ORIGIN":
            errors.append("framing.anchor_policy must be OBJECT_ORIGIN")

    output = request["output"]
    if _exact(output, OUTPUT_FIELDS, "output", errors):
        directory = output["target_directory"]
        prefix = output["filename_prefix"]
        index_start, padding = output["index_start"], output["index_padding"]
        if (not isinstance(directory, str) or not directory
                or directory != directory.strip() or "\x00" in directory
                or not Path(directory).is_absolute()):
            errors.append("output.target_directory must be a nonempty absolute path")
        if not isinstance(prefix, str) or not _valid_file_stem(prefix):
            errors.append("output.filename_prefix must be a safe nonempty file prefix")
        if not _integer(index_start) or index_start < 0:
            errors.append("output.index_start must be a nonnegative integer")
        if not _integer(padding) or not 1 <= padding <= 8:
            errors.append("output.index_padding must be an integer in [1, 8]")
        if output["overwrite"] is not False:
            errors.append("output.overwrite must be false")
        if (sample_frames and _integer(index_start) and index_start >= 0
                and _integer(padding) and 1 <= padding <= 8
                and index_start + len(sample_frames) - 1 >= 10 ** padding):
            errors.append("output.index_padding is too small for the planned final index")

    if not errors:
        directory = Path(output["target_directory"])
        for offset, source_frame in enumerate(sample_frames):
            index = output["index_start"] + offset
            target = directory / f"{output['filename_prefix']}{index:0{output['index_padding']}d}.png"
            static_request = {**template,
                "output": {"target_file": str(target), "color_mode": "RGBA",
                           "color_depth": 8, "overwrite": False}}
            static_report = validate_2d_static_render_request(static_request)
            if not static_report["ready_for_blender_inspection"]:
                errors.extend(f"frame {source_frame}: {error}"
                              for error in static_report["errors"])
                break
            frames.append({"source_frame": source_frame, "sequence_index": index,
                           "target_file": str(target),
                           "static_request_sha256": static_report["request_sha256"]})

    request_sha = _digest(request) if not errors else None
    plan_sha = _digest(frames) if not errors else None
    return {"schema": SCHEMA, "ready_for_blender_inspection": not errors,
            "request_sha256": request_sha, "frame_plan_sha256": plan_sha,
            "frame_count": len(frames) if not errors else 0,
            "frames": frames if not errors else [], "errors": errors}


