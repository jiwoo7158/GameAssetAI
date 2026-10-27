"""Validate a proposed static impostor result manifest without publishing it."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat


SCHEMA = "gameassetai.2d-impostor-bundle-result.v1"
PREVIEW_SCHEMA = "gameassetai.2d-impostor-shared-framing-preview.v1"
TOP_FIELDS = frozenset(("schema", "request_sha256", "source_fingerprint",
                        "preview_fingerprint", "policy", "views", "artifacts"))
POLICY_FIELDS = frozenset(("execution_order", "publication", "on_failure",
                           "framing_mismatch"))
VIEW_FIELDS = frozenset(("position", "view_id", "plan_fingerprint"))
ARTIFACT_FIELDS = frozenset(("position", "item_id", "view_id", "pass_kind",
                             "target_file", "request_sha256", "plan_fingerprint",
                             "png_sha256", "receipt_sha256", "bytes"))
SHA256 = re.compile(r"^[0-9a-f]{64}$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


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


def _hash_json(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _hash_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _exists_or_link(path):
    try:
        path.lstat()
        return True
    except FileNotFoundError:
        return False


def validate_2d_impostor_result_manifest(manifest, request_preflight, preview):
    """Recheck a complete proposal and its PNG bytes; never write the manifest target."""
    report = {"schema": SCHEMA, "status": "error", "errors": [],
              "ready_for_manifest_publication": False, "manifest_sha256": None,
              "artifact_count": 0, "artifacts": []}
    errors = report["errors"]
    try:
        if not _exact(manifest, TOP_FIELDS, "manifest", errors):
            return report
        if manifest.get("schema") != SCHEMA:
            errors.append("schema mismatch")
        if (not isinstance(request_preflight, dict)
                or request_preflight.get("status") != "ready"
                or request_preflight.get("ready_for_shared_framing_preview") is not True
                or request_preflight.get("errors") != []):
            errors.append("a successful bundle request preflight is required")
            return report
        if (not isinstance(preview, dict) or preview.get("schema") != PREVIEW_SCHEMA
                or preview.get("status") != "planned" or preview.get("errors") != []
                or preview.get("blockers") != []):
            errors.append("a blocker-free shared-framing preview is required")
            return report
        request_hash = request_preflight.get("request_sha256")
        source_hash = preview.get("source_fingerprint")
        preview_hash = preview.get("preview_fingerprint")
        if not all(isinstance(value, str) and SHA256.fullmatch(value)
                   for value in (request_hash, source_hash, preview_hash)):
            errors.append("preflight and preview fingerprints must be lowercase SHA-256")
        if preview.get("request_sha256") != request_hash:
            errors.append("preview does not bind the request preflight")
        expected_preview_hash = _hash_json({"request_sha256": request_hash,
                                            "source_fingerprint": source_hash,
                                            "views": preview.get("views")})
        if preview_hash != expected_preview_hash:
            errors.append("preview_fingerprint does not match preview contents")
        if manifest.get("request_sha256") != request_hash:
            errors.append("manifest.request_sha256 mismatch")
        if manifest.get("source_fingerprint") != source_hash:
            errors.append("manifest.source_fingerprint mismatch")
        if manifest.get("preview_fingerprint") != preview_hash:
            errors.append("manifest.preview_fingerprint mismatch")

        expected_policy = request_preflight.get("policy")
        if _exact(manifest.get("policy"), POLICY_FIELDS, "manifest.policy", errors):
            if manifest["policy"] != expected_policy:
                errors.append("manifest.policy must match the reviewed request policy")

        preview_views = preview.get("views")
        manifest_views = manifest.get("views")
        if not isinstance(preview_views, list) or not isinstance(manifest_views, list):
            errors.append("preview.views and manifest.views must be arrays")
            preview_views, manifest_views = [], []
        if len(manifest_views) != len(preview_views):
            errors.append("manifest.views must exactly cover preview views")
        view_plans = {}
        for index, expected in enumerate(preview_views):
            if index >= len(manifest_views):
                break
            actual = manifest_views[index]
            if not _exact(actual, VIEW_FIELDS, f"manifest.views[{index}]", errors):
                continue
            plan_hash = expected.get("plan_fingerprint")
            if (actual.get("position") != index or actual.get("view_id") != expected.get("view_id")
                    or actual.get("plan_fingerprint") != plan_hash):
                errors.append(f"manifest.views[{index}] does not match preview order/binding")
            if not isinstance(plan_hash, str) or not SHA256.fullmatch(plan_hash):
                errors.append(f"preview.views[{index}] plan fingerprint is invalid")
            view_plans[expected.get("view_id")] = plan_hash

        expected_items = request_preflight.get("items")
        artifacts = manifest.get("artifacts")
        if not isinstance(expected_items, list) or not isinstance(artifacts, list):
            errors.append("request items and manifest artifacts must be arrays")
            expected_items, artifacts = [], []
        if len(artifacts) != len(expected_items):
            errors.append("manifest.artifacts must exactly cover request items")
        verified = []
        for index, expected in enumerate(expected_items):
            if index >= len(artifacts):
                break
            artifact = artifacts[index]
            label = f"manifest.artifacts[{index}]"
            if not _exact(artifact, ARTIFACT_FIELDS, label, errors):
                continue
            exact = {"position": index, "item_id": expected.get("id"),
                     "view_id": expected.get("view_id"),
                     "pass_kind": expected.get("pass_kind"),
                     "target_file": expected.get("target_file"),
                     "request_sha256": expected.get("request_sha256"),
                     "plan_fingerprint": view_plans.get(expected.get("view_id"))}
            for key, value in exact.items():
                if artifact.get(key) != value:
                    errors.append(f"{label}.{key} does not match reviewed order/binding")
            for key in ("request_sha256", "plan_fingerprint", "png_sha256", "receipt_sha256"):
                if not isinstance(artifact.get(key), str) or not SHA256.fullmatch(artifact[key]):
                    errors.append(f"{label}.{key} must be a lowercase SHA-256")
            size = artifact.get("bytes")
            if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
                errors.append(f"{label}.bytes must be a positive integer")
            path = Path(str(expected.get("target_file")))
            try:
                info = path.lstat()
                if (_is_link(path) or not stat.S_ISREG(info.st_mode)
                        or getattr(info, "st_nlink", 1) != 1 or path.suffix.lower() != ".png"):
                    errors.append(f"{label} target must be a regular PNG")
                    continue
                with path.open("rb") as stream:
                    signature = stream.read(len(PNG_SIGNATURE))
                actual_hash = _hash_file(path)
                if signature != PNG_SIGNATURE:
                    errors.append(f"{label} target is not a PNG")
                if info.st_size != size:
                    errors.append(f"{label}.bytes does not match the target")
                if actual_hash != artifact.get("png_sha256"):
                    errors.append(f"{label}.png_sha256 does not match the target")
                verified.append({"target_file": str(path), "bytes": info.st_size,
                                 "png_sha256": actual_hash})
            except (FileNotFoundError, OSError):
                errors.append(f"{label} target could not be read")

        target_text = request_preflight.get("manifest")
        try:
            target = Path(target_text)
            meta = Path(target_text + ".meta")
            if _exists_or_link(target) or _exists_or_link(meta):
                errors.append("manifest publication target or its .meta now exists")
        except (TypeError, OSError):
            errors.append("manifest publication target could not be rechecked")
        if errors:
            return report
        report.update(status="ready", ready_for_manifest_publication=True,
                      manifest_sha256=_hash_json(manifest), artifact_count=len(verified),
                      artifacts=verified, target_file=target_text,
                      limitations=["Validation does not write or publish the JSON manifest",
                                   "Child receipt hashes are bound but receipt objects are validated elsewhere"])
    except (TypeError, KeyError, OSError, OverflowError, ValueError) as exc:
        errors.append(str(exc))
    return report
