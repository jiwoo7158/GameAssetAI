"""Derive one hash-bound RGBA8 silhouette mask and publish it without overwrite."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

from quantize_rgba import encode_png_rgba8
from validate_2d_silhouette_mask_request import (
    decode_png_rgba8, read_json, validate_2d_silhouette_mask_request)


RESULT_SCHEMA = "gameassetai.2d-silhouette-mask-result.v1"


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def derive_2d_silhouette_mask(request, candidate, *, authorize=False):
    report = {"schema": RESULT_SCHEMA, "status": "error", "published": False,
              "errors": []}
    target, stage, encoded, published = None, None, None, False
    try:
        if authorize is not True:
            raise ValueError("explicit mask publication authorization is required")
        fresh = validate_2d_silhouette_mask_request(request)
        if fresh.get("status") != "candidate_for_review" or candidate != fresh:
            raise ValueError("fresh exact candidate_for_review is required")
        source, target = Path(request["source_file"]), Path(request["target_file"])
        data, width, height, pixels = decode_png_rgba8(source)
        if hashlib.sha256(data).hexdigest() != request["source_sha256"]:
            raise ValueError("source PNG changed before publication")
        rgb = tuple(round(float(value) * 255.0) for value in request["visible_rgba"][:3])
        preserve = request["alpha_policy"] == "PRESERVE_ALPHA"
        output = []
        for row in pixels:
            mapped = []
            for pixel in row:
                if pixel[3] == 0:
                    mapped.append((0, 0, 0, 0))
                else:
                    mapped.append((*rgb, pixel[3] if preserve else 255))
            output.append(mapped)
        encoded = encode_png_rgba8(output)
        stage = target.parent / (".gameassetai-mask-" + uuid.uuid4().hex + ".stage.png")
        if stage.exists() or stage.is_symlink():
            raise ValueError("owned mask stage path collided")
        with stage.open("xb") as handle:
            handle.write(encoded)
        checked, checked_width, checked_height, checked_pixels = decode_png_rgba8(stage)
        if (checked != encoded or checked_width != width or checked_height != height
                or checked_pixels != output):
            raise ValueError("mask stage readback mismatch")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("target_file or its .meta appeared before publication")
        try:
            os.link(stage, target)
        except OSError:
            try:
                published = target.exists() and os.path.samefile(stage, target)
            except OSError:
                published = False
            raise
        published = True
        target_data = target.read_bytes()
        if target_data != encoded:
            raise ValueError("published mask readback mismatch")
        visible = [(x, y, pixel) for y, row in enumerate(output)
                   for x, pixel in enumerate(row) if pixel[3] > 0]
        xs, ys = [item[0] for item in visible], [item[1] for item in visible]
        artifact = {"path": str(target), "size": len(target_data),
                    "sha256": hashlib.sha256(target_data).hexdigest(),
                    "width": width, "height": height,
                    "alpha_bounds": [min(xs), min(ys), max(xs), max(ys)],
                    "visible_pixels": len(visible),
                    "partial_alpha_pixels": sum(0 < item[2][3] < 255 for item in visible),
                    "unique_rgba": len({pixel for row in output for pixel in row})}
        receipt = {"schema": RESULT_SCHEMA, "request_sha256": fresh["request_sha256"],
                   "candidate_fingerprint": fresh["candidate_fingerprint"],
                   "source_sha256": request["source_sha256"], "artifact": artifact,
                   "alpha_policy": request["alpha_policy"]}
        receipt["receipt_sha256"] = _hash(receipt)
        report.update(status="created", published=True, artifact=artifact,
                      request_sha256=fresh["request_sha256"],
                      candidate_fingerprint=fresh["candidate_fingerprint"],
                      receipt_sha256=receipt["receipt_sha256"])
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
    finally:
        if stage is not None:
            try:
                stage.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                report["errors"].append("mask stage cleanup failed: " + str(exc))
                report["status"] = "error"
        if report["status"] != "created" and published and target is not None:
            try:
                if encoded is not None and target.read_bytes() == encoded:
                    target.unlink()
                    report["published"] = False
                else:
                    report["errors"].append(
                        "published mask changed concurrently; rollback retained it")
            except OSError as exc:
                report["errors"].append("published mask rollback failed: " + str(exc))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--expected-candidate-fingerprint", required=True)
    parser.add_argument("--authorize", action="store_true")
    args = parser.parse_args()
    try:
        request = read_json(args.request)
        candidate = validate_2d_silhouette_mask_request(request)
        if candidate.get("candidate_fingerprint") != args.expected_candidate_fingerprint:
            raise ValueError("candidate fingerprint changed before publication")
        result = derive_2d_silhouette_mask(request, candidate, authorize=args.authorize)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result = {"schema": RESULT_SCHEMA, "status": "error", "published": False,
                  "errors": [str(exc)]}
    print(json.dumps(result, sort_keys=True, ensure_ascii=True, allow_nan=False))
    return 0 if result["status"] == "created" else 1


if __name__ == "__main__":
    raise SystemExit(main())
