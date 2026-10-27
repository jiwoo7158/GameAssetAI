"""Validate one explicit RGBA8 silhouette-mask derivation request without writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import stat
import struct
import zlib


SCHEMA = "gameassetai.2d-silhouette-mask-request.v1"
FIELDS = frozenset(("schema", "source_file", "source_sha256", "target_file",
                    "visible_rgba", "alpha_policy", "overwrite"))
ALPHA_POLICIES = frozenset(("BINARY_NONZERO", "PRESERVE_ALPHA"))


def _is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not _is_link(path)


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("non-standard JSON constant: " + value)))


def decode_png_rgba8(path):
    """Return (bytes, width, height, top-to-bottom RGBA8 rows)."""
    path = Path(path)
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("source must be a PNG")
    width, height, depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29])
    if (width < 1 or height < 1 or width * height > 268435456 or depth != 8
            or color_type != 6 or compression or filtering or interlace):
        raise ValueError("source must be bounded non-interlaced RGBA8 PNG")
    chunks, position = [], 8
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("PNG chunk is truncated")
        length = struct.unpack(">I", data[position:position + 4])[0]
        kind = data[position + 4:position + 8]
        end = position + 12 + length
        if end > len(data):
            raise ValueError("PNG chunk is truncated")
        payload = data[position + 8:position + 8 + length]
        position = end
        if kind == b"IDAT":
            chunks.append(payload)
        elif kind == b"IEND":
            break
    try:
        raw = zlib.decompress(b"".join(chunks))
    except zlib.error as exc:
        raise ValueError("PNG pixel stream is invalid") from exc
    stride, expected = width * 4, height * (width * 4 + 1)
    if len(raw) != expected:
        raise ValueError("PNG pixel stream size is invalid")
    rows, previous, offset = [], bytearray(stride), 0

    def paeth(a, b, c):
        estimate = a + b - c
        values = (a, b, c)
        return values[min(range(3), key=lambda index: abs(estimate - values[index]))]

    for _ in range(height):
        filter_type = raw[offset]
        encoded = raw[offset + 1:offset + 1 + stride]
        offset += 1 + stride
        if filter_type not in {0, 1, 2, 3, 4}:
            raise ValueError("PNG row filter is unsupported")
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            predictors = (0, left, above, (left + above) // 2,
                          paeth(left, above, upper_left))
            row[index] = (value + predictors[filter_type]) & 255
        rows.append([tuple(row[index:index + 4]) for index in range(0, stride, 4)])
        previous = row
    return data, width, height, rows


def validate_2d_silhouette_mask_request(request):
    errors, facts = [], None
    if not isinstance(request, dict):
        return {"schema": SCHEMA, "status": "blocked", "request_sha256": None,
                "source": None, "errors": ["request must be an object"]}
    missing, unknown = FIELDS - request.keys(), request.keys() - FIELDS
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("unknown fields: " + ", ".join(sorted(unknown)))
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    if request.get("alpha_policy") not in ALPHA_POLICIES:
        errors.append("alpha_policy must be BINARY_NONZERO or PRESERVE_ALPHA")
    color = request.get("visible_rgba")
    if (not isinstance(color, list) or len(color) != 4
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not 0.0 <= float(value) <= 1.0 for value in color)
            or (isinstance(color, list) and len(color) == 4 and float(color[3]) != 1.0)):
        errors.append("visible_rgba must be one opaque normalized RGBA color")
    if request.get("overwrite") is not False:
        errors.append("overwrite must be false")
    digest = request.get("source_sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)):
        errors.append("source_sha256 must be lowercase SHA-256")

    paths = {}
    for key in ("source_file", "target_file"):
        value = request.get(key)
        if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
            errors.append(key + " must be a nonempty exact absolute path")
            continue
        path = Path(value)
        paths[key] = path
        if not path.is_absolute() or path.suffix.lower() != ".png" or ".." in path.parts:
            errors.append(key + " must be an absolute .png path")
            continue
        try:
            if not path.parent.is_dir() or any(_is_link(item) for item in
                                                (path.parent, *path.parent.parents)):
                errors.append(key + " parent must be an existing real directory")
        except OSError:
            errors.append(key + " path could not be inspected")
    source, target = paths.get("source_file"), paths.get("target_file")
    if source is not None:
        try:
            if not _regular(source):
                errors.append("source_file must be an existing non-linked regular PNG")
            else:
                data, width, height, rows = decode_png_rgba8(source)
                actual = hashlib.sha256(data).hexdigest()
                if isinstance(digest, str) and actual != digest:
                    errors.append("source SHA-256 mismatch")
                visible = sum(pixel[3] > 0 for row in rows for pixel in row)
                if visible == 0:
                    errors.append("source PNG has no visible pixels")
                facts = {"path": str(source), "size": len(data), "sha256": actual,
                         "width": width, "height": height,
                         "visible_pixels": visible,
                         "partial_alpha_pixels": sum(0 < pixel[3] < 255
                                                     for row in rows for pixel in row)}
        except (OSError, ValueError, struct.error) as exc:
            errors.append("source PNG inspection failed: " + str(exc))
    if target is not None:
        try:
            if (_is_link(target) or target.exists()
                    or _is_link(Path(str(target) + ".meta"))
                    or Path(str(target) + ".meta").exists()):
                errors.append("target_file or its .meta already exists")
        except OSError:
            errors.append("target_file could not be inspected")
    if source is not None and target is not None and str(source).casefold() == str(target).casefold():
        errors.append("source_file and target_file must differ")
    request_sha = None if errors else _hash(request)
    result = {"schema": SCHEMA,
              "status": "candidate_for_review" if not errors else "blocked",
              "request_sha256": request_sha, "source": facts, "errors": errors}
    if not errors:
        result["candidate_fingerprint"] = _hash(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        result = validate_2d_silhouette_mask_request(read_json(args.request))
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {"schema": SCHEMA, "status": "blocked", "request_sha256": None,
                  "source": None, "errors": [str(exc)]}
    print(json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0 if result["status"] == "candidate_for_review" else 1


if __name__ == "__main__":
    raise SystemExit(main())
