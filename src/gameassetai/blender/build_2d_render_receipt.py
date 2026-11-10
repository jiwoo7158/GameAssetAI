"""Build a read-only, hash-bound receipt for one published static 2D PNG."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat


RECEIPT_SCHEMA = "gameassetai.2d-static-render-receipt.v1"
FACT_FIELDS = frozenset(("width", "height", "color_depth", "color_type",
                         "alpha_bounds", "foreground_pixels", "unique_rgba"))


def _receipt_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_2d_render_receipt(request, candidate, framing, artifact_facts):
    """Inspect the exact published PNG and return provenance; never write a receipt file."""
    if not all(isinstance(value, dict) for value in
               (request, candidate, framing, artifact_facts)):
        raise ValueError("request, candidate, framing and artifact_facts must be objects")
    if set(artifact_facts) != FACT_FIELDS:
        raise ValueError("artifact_facts fields must be exact")
    request_hash = _receipt_hash(request)
    if (candidate.get("status") != "candidate_for_review"
            or candidate.get("request_sha256") != request_hash
            or framing.get("status") != "planned"
            or framing.get("request_sha256") != request_hash):
        raise ValueError("reviewed request/candidate/framing chain is required")
    for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
        if (not isinstance(candidate.get(key), str) or len(candidate[key]) != 64
                or framing.get(key) != candidate[key]):
            raise ValueError("candidate and framing fingerprints must match")
    if candidate["output_fingerprint"] != _receipt_hash(request.get("output")):
        raise ValueError("output contract changed since candidate inspection")
    target = Path(request["output"]["target_file"])
    try:
        info = target.lstat()
    except FileNotFoundError as exc:
        raise ValueError("published artifact does not exist") from exc
    if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)
            or target.suffix.lower() != ".png"):
        raise ValueError("published artifact must be a regular PNG file")
    for key in ("width", "height", "color_depth", "color_type",
                "foreground_pixels", "unique_rgba"):
        if isinstance(artifact_facts[key], bool) or not isinstance(artifact_facts[key], int):
            raise ValueError("artifact integer facts are invalid")
    bounds = artifact_facts["alpha_bounds"]
    if (not isinstance(bounds, list) or len(bounds) != 4
            or any(isinstance(value, bool) or not isinstance(value, int) for value in bounds)):
        raise ValueError("alpha_bounds must contain four integers")
    data = target.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("published artifact is not a PNG")
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "request_sha256": request_hash,
        "source_fingerprint": candidate["source_fingerprint"],
        "setup_fingerprint": candidate["setup_fingerprint"],
        "output_fingerprint": candidate["output_fingerprint"],
        "plan_fingerprint": framing.get("plan_fingerprint"),
        "artifact": {"path": str(target), "size": len(data),
                     "sha256": hashlib.sha256(data).hexdigest(), **artifact_facts},
    }
    receipt["receipt_sha256"] = _receipt_hash(receipt)
    return receipt
# Retained bounded Blender capability; product support remains evidence-scoped.
