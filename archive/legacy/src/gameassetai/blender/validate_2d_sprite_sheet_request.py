"""Validate an explicit PNG-frame to sprite-sheet request without writing files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat
import struct


SPRITE_SHEET_SCHEMA_V1 = "gameassetai.2d-sprite-sheet-request.v1"
SPRITE_SHEET_SCHEMA = "gameassetai.2d-sprite-sheet-request.v2"
MAX_SHEET_PIXELS = 16_777_216
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TOP_FIELDS_V1 = {"schema", "frames", "layout", "output"}
_TOP_FIELDS = _TOP_FIELDS_V1 | {"profile"}
_PROFILE_FIELDS = {"name", "reference_sha256", "profile_sha256", "preset_sha256"}
_FRAME_FIELDS = {"source_frame", "sequence_index", "path", "sha256",
                 "anchor_pixel_from_bottom_left"}
_LAYOUT_FIELDS = {"cell_size", "columns", "rows", "padding", "order"}
_OUTPUT_FIELDS = {"target_file", "metadata_file", "overwrite"}


def _sheet_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _integer(value, minimum=None, maximum=None):
    return (not isinstance(value, bool) and isinstance(value, int)
            and (minimum is None or value >= minimum)
            and (maximum is None or value <= maximum))


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _png_header(path):
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"Input is not a PNG: {path}")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29])
    if depth != 8 or color_type != 6 or compression or filtering or interlace:
        raise ValueError(f"Input must be non-interlaced RGBA8 PNG: {path}")
    return data, width, height


def validate_2d_sprite_sheet_request(request):
    """Return verified source facts and layout mapping; never create or modify a file."""
    report = {"schema": SPRITE_SHEET_SCHEMA, "status": "error", "errors": [],
              "ready_for_assembly": False}
    errors = report["errors"]
    try:
        schema = request.get("schema") if isinstance(request, dict) else None
        fields = _TOP_FIELDS_V1 if schema == SPRITE_SHEET_SCHEMA_V1 else _TOP_FIELDS
        if not _exact(request, fields, "request", errors):
            return report
        if schema not in (SPRITE_SHEET_SCHEMA_V1, SPRITE_SHEET_SCHEMA):
            errors.append("schema must be gameassetai.2d-sprite-sheet-request.v1 or v2")
        if schema == SPRITE_SHEET_SCHEMA:
            profile = request.get("profile")
            if _exact(profile, _PROFILE_FIELDS, "profile", errors):
                values = [profile[key] for key in ("name", "reference_sha256",
                                                   "profile_sha256", "preset_sha256")]
                if any(value is not None for value in values):
                    if not isinstance(values[0], str) or not values[0].strip():
                        errors.append("profile.name must be a nonempty exact name or null")
                    for key, value in zip(("reference_sha256", "profile_sha256",
                                           "preset_sha256"), values[1:]):
                        if not isinstance(value, str) or not _SHA256.fullmatch(value):
                            errors.append(f"profile.{key} must be a lowercase SHA-256")
        frames, layout, output = request.get("frames"), request.get("layout"), request.get("output")
        if not isinstance(frames, list) or not frames or len(frames) > 2048:
            errors.append("frames must contain 1 through 2048 entries")
            frames = []
        if not _exact(layout, _LAYOUT_FIELDS, "layout", errors):
            layout = {}
        if not _exact(output, _OUTPUT_FIELDS, "output", errors):
            output = {}

        cell_size = layout.get("cell_size")
        if (not isinstance(cell_size, list) or len(cell_size) != 2
                or not all(_integer(value, 1, 16384) for value in cell_size)):
            errors.append("layout.cell_size must contain two integers in [1, 16384]")
        columns, rows, padding = layout.get("columns"), layout.get("rows"), layout.get("padding")
        if not _integer(columns, 1, 2048) or not _integer(rows, 1, 2048):
            errors.append("layout columns and rows must be integers in [1, 2048]")
        if not _integer(padding, 0, 256):
            errors.append("layout.padding must be an integer in [0, 256]")
        if layout.get("order") != "ROW_MAJOR_TOP_LEFT":
            errors.append("layout.order must be ROW_MAJOR_TOP_LEFT")
        if (_integer(columns, 1) and _integer(rows, 1) and frames
                and columns * rows < len(frames)):
            errors.append("layout does not have enough cells for every frame")

        targets = []
        for key, suffix in (("target_file", ".png"), ("metadata_file", ".json")):
            value = output.get(key)
            path = Path(value) if isinstance(value, str) else Path()
            if (not isinstance(value, str) or not value or not path.is_absolute()
                    or path.suffix.lower() != suffix or not path.parent.is_dir()
                    or path.parent.is_symlink()):
                errors.append(f"output.{key} must be an absolute new {suffix} in an existing real directory")
            else:
                targets.append(path)
                if path.exists() or path.is_symlink() or Path(str(path) + ".meta").exists():
                    errors.append(f"output.{key} or sibling .meta already exists")
        if len(targets) == 2 and (targets[0] == targets[1] or targets[0].parent != targets[1].parent):
            errors.append("PNG and metadata targets must be distinct siblings")
        if output.get("overwrite") is not False:
            errors.append("output.overwrite must be false")

        verified, paths, indices = [], set(), []
        for position, frame in enumerate(frames):
            label = f"frames[{position}]"
            if not _exact(frame, _FRAME_FIELDS, label, errors):
                continue
            source_frame, sequence_index = frame.get("source_frame"), frame.get("sequence_index")
            if not _integer(source_frame) or not _integer(sequence_index, 0):
                errors.append(f"{label} frame and index must be integers; index is nonnegative")
            else:
                indices.append(sequence_index)
            anchor = frame.get("anchor_pixel_from_bottom_left")
            if (not isinstance(anchor, list) or len(anchor) != 2
                    or any(isinstance(value, bool) or not isinstance(value, (int, float))
                           for value in anchor)):
                errors.append(f"{label} anchor must contain two finite numbers")
            elif any(not __import__("math").isfinite(float(value)) for value in anchor):
                errors.append(f"{label} anchor must contain two finite numbers")
            value = frame.get("path")
            path = Path(value) if isinstance(value, str) else Path()
            if not isinstance(value, str) or not value or not path.is_absolute() or not _regular(path):
                errors.append(f"{label}.path must name an existing regular absolute PNG")
                continue
            if path in paths:
                errors.append("frame paths must be unique")
                continue
            paths.add(path)
            sha = frame.get("sha256")
            if not isinstance(sha, str) or not _SHA256.fullmatch(sha):
                errors.append(f"{label}.sha256 must be lowercase SHA-256")
                continue
            try:
                data, width, height = _png_header(path)
            except (OSError, ValueError, struct.error) as exc:
                errors.append(str(exc))
                continue
            actual = hashlib.sha256(data).hexdigest()
            if actual != sha:
                errors.append(f"{label} SHA-256 does not match the input file")
            if isinstance(cell_size, list) and len(cell_size) == 2 and [width, height] != cell_size:
                errors.append(f"{label} dimensions do not match layout.cell_size")
            verified.append({"position": position, "path": str(path), "size": len(data),
                             "sha256": actual, "width": width, "height": height,
                             "source_frame": source_frame, "sequence_index": sequence_index,
                             "anchor_pixel_from_bottom_left": anchor})
        if indices and indices != sorted(indices):
            errors.append("frames must be listed in increasing sequence_index order")
        if len(indices) != len(set(indices)):
            errors.append("sequence_index values must be unique")

        if errors:
            return report
        sheet_width = columns * cell_size[0] + (columns - 1) * padding
        sheet_height = rows * cell_size[1] + (rows - 1) * padding
        if (sheet_width > 32768 or sheet_height > 32768
                or sheet_width * sheet_height > MAX_SHEET_PIXELS):
            errors.append("computed sprite sheet dimensions exceed the bounded pixel budget")
            return report
        cells = []
        for position, frame in enumerate(verified):
            row, column = divmod(position, columns)
            x = column * (cell_size[0] + padding)
            y = row * (cell_size[1] + padding)
            cells.append({**frame, "column": column, "row_from_top": row,
                          "rect_from_top_left": [x, y, cell_size[0], cell_size[1]]})
        report.update(status="ready", ready_for_assembly=True,
                      request_schema=schema,
                      request_sha256=_sheet_hash(request), frames=verified, cells=cells,
                      sheet_size=[sheet_width, sheet_height])
    except (TypeError, KeyError, OSError, OverflowError) as exc:
        errors.append(str(exc))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
