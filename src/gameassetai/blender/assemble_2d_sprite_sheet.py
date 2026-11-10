"""Assemble verified RGBA8 PNG frames into one collision-safe sprite sheet and metadata."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import uuid
import zlib

from quantize_rgba import encode_png_rgba8
from validate_2d_sprite_sheet_request import (
    SPRITE_SHEET_SCHEMA,
    _sheet_hash,
    validate_2d_sprite_sheet_request,
)


SPRITE_SHEET_RESULT_SCHEMA = "gameassetai.2d-sprite-sheet-result.v1"


def _decode_sheet_rgba8(path):
    data = path.read_bytes()
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    chunks, position, interlace = [], 8, None
    while position < len(data):
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        payload = data[position + 8:position + 8 + length]
        position += 12 + length
        if kind == b"IHDR":
            interlace = payload[12]
        elif kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            break
    if depth != 8 or color_type != 6 or interlace != 0:
        raise ValueError("Sprite-sheet inputs must be non-interlaced RGBA8")
    raw = zlib.decompress(b"".join(chunks))
    stride, previous, offset, rows = width * 4, bytearray(width * 4), 0, []

    def paeth(a, b, c):
        estimate = a + b - c
        values = (a, b, c)
        return values[min(range(3), key=lambda index: abs(estimate - values[index]))]

    for _ in range(height):
        filter_type = raw[offset]
        encoded = raw[offset + 1:offset + 1 + stride]
        offset += 1 + stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            predictors = {0: 0, 1: left, 2: above, 3: (left + above) // 2,
                          4: paeth(left, above, upper_left)}
            if filter_type not in predictors:
                raise ValueError("Unsupported PNG row filter")
            row[index] = (value + predictors[filter_type]) & 255
        rows.append([tuple(row[index:index + 4]) for index in range(0, stride, 4)])
        previous = row
    return data, rows


def assemble_2d_sprite_sheet(request, preview, *, authorize=False):
    """Publish the sheet and metadata only after both owned stages are complete."""
    report = {"schema": SPRITE_SHEET_RESULT_SCHEMA, "status": "error", "errors": [],
              "artifacts_published": False, "published_count": 0}
    stages, published = [], []
    try:
        if authorize is not True:
            raise ValueError("Explicit sprite-sheet assembly authorization is required")
        fresh = validate_2d_sprite_sheet_request(request)
        if (not isinstance(preview, dict) or fresh.get("status") != "ready"
                or preview.get("status") != "ready"
                or fresh.get("request_sha256") != preview.get("request_sha256")
                or fresh.get("frames") != preview.get("frames")
                or fresh.get("cells") != preview.get("cells")):
            raise ValueError("Matching fresh sprite-sheet preview is required")
        target = Path(request["output"]["target_file"])
        metadata_target = Path(request["output"]["metadata_file"])
        token = uuid.uuid4().hex
        png_stage = target.parent / (".gameassetai-spritesheet-" + token + ".png.stage")
        json_stage = target.parent / (".gameassetai-spritesheet-" + token + ".json.stage")
        stages = [png_stage, json_stage]
        if any(path.exists() or path.is_symlink() for path in stages):
            raise ValueError("Owned sprite-sheet stage path already exists")

        sheet_width, sheet_height = fresh["sheet_size"]
        transparent = (0, 0, 0, 0)
        sheet = [[transparent for _ in range(sheet_width)] for _ in range(sheet_height)]
        metadata_cells = []
        for cell in fresh["cells"]:
            source_data, pixels = _decode_sheet_rgba8(Path(cell["path"]))
            if hashlib.sha256(source_data).hexdigest() != cell["sha256"]:
                raise ValueError("A sprite-sheet input changed after preview")
            x, y, width, height = cell["rect_from_top_left"]
            for row in range(height):
                sheet[y + row][x:x + width] = pixels[row]
            anchor = cell["anchor_pixel_from_bottom_left"]
            metadata_cells.append({
                "source_frame": cell["source_frame"],
                "sequence_index": cell["sequence_index"],
                "source_path": cell["path"], "source_sha256": cell["sha256"],
                "column": cell["column"], "row_from_top": cell["row_from_top"],
                "rect_from_top_left": cell["rect_from_top_left"],
                "anchor_in_cell_from_bottom_left": anchor,
                "anchor_in_sheet_from_bottom_left": [
                    x + float(anchor[0]), sheet_height - y - height + float(anchor[1])],
            })
        png_data = encode_png_rgba8(sheet)
        sheet_sha = hashlib.sha256(png_data).hexdigest()
        is_v2 = request.get("schema") == SPRITE_SHEET_SCHEMA
        metadata = {
            "schema": ("gameassetai.2d-sprite-sheet-metadata.v2" if is_v2
                       else "gameassetai.2d-sprite-sheet-metadata.v1"),
            "request_sha256": fresh["request_sha256"],
            "image": {"path": str(target), "width": sheet_width,
                      "height": sheet_height, "color_mode": "RGBA",
                      "color_depth": 8, "sha256": sheet_sha},
            "layout": request["layout"], "cells": metadata_cells,
        }
        if is_v2:
            metadata["profile"] = request["profile"]
        metadata_data = json.dumps(metadata, sort_keys=True, ensure_ascii=True,
                                   separators=(",", ":"), allow_nan=False).encode("utf-8")
        png_stage.write_bytes(png_data)
        json_stage.write_bytes(metadata_data)
        if (hashlib.sha256(png_stage.read_bytes()).hexdigest() != sheet_sha
                or json.loads(json_stage.read_text(encoding="utf-8")) != metadata):
            raise RuntimeError("Sprite-sheet stage verification failed")
        if any(path.exists() or Path(str(path) + ".meta").exists()
               for path in (target, metadata_target)):
            raise ValueError("A sprite-sheet target appeared before publication")
        for stage, destination in ((png_stage, target), (json_stage, metadata_target)):
            os.link(stage, destination)
            published.append(destination)
        receipt = {"schema": "gameassetai.2d-sprite-sheet-receipt.v1",
                   "request_sha256": fresh["request_sha256"],
                   "sheet_sha256": sheet_sha,
                   "metadata_sha256": hashlib.sha256(metadata_data).hexdigest(),
                   "frame_count": len(metadata_cells)}
        receipt_sha = _sheet_hash(receipt)
        report.update(status="created", artifacts_published=True, published_count=2,
                      request_sha256=fresh["request_sha256"], sheet_size=fresh["sheet_size"],
                      frame_count=len(metadata_cells), target_file=str(target),
                      metadata_file=str(metadata_target), sheet_sha256=sheet_sha,
                      metadata_sha256=receipt["metadata_sha256"],
                      receipt_sha256=receipt_sha, cells=metadata_cells)
    except (ValueError, TypeError, KeyError, OSError, RuntimeError,
            json.JSONDecodeError, struct.error, zlib.error) as exc:
        report["errors"].append(str(exc))
    finally:
        for path in stages:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                report["errors"].append("Sprite-sheet stage cleanup failed: " + str(cleanup))
                report["status"] = "error"
        if report["status"] != "created":
            for path in reversed(published):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                except OSError as cleanup:
                    report["errors"].append("Sprite-sheet publication rollback failed: " + str(cleanup))
            report["artifacts_published"] = False
            report["published_count"] = sum(path.exists() for path in published)
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
