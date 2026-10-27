"""Build one authorized hash-bound job for already staged 2D child renders."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

from validate_2d_render_batch_request import validate_2d_render_batch_request


JOB_SCHEMA = "gameassetai.2d-render-batch-job.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_CHILD_FIELDS = {"id", "kind", "stage_file", "stage_sha256",
                 "job_file", "job_sha256", "helper_root"}
_HELPERS = {
    "STATIC": ("quantize_rgba.py", "build_2d_render_receipt.py",
               "render_2d_staged_source.py"),
    "ACTION_SEQUENCE": ("quantize_rgba.py", "build_2d_action_sequence_job.py",
                        "render_2d_action_sequence.py"),
}
_CHILD_JOB_SCHEMAS = {
    "STATIC": "gameassetai.2d-staged-render-job.v1",
    "ACTION_SEQUENCE": "gameassetai.2d-action-sequence-job.v1",
}


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _read_hashed(path, expected):
    if not _regular(path) or not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        raise ValueError(f"Missing, linked or invalid hash-bound file: {path}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash changed for file: {path}")
    return data


def _exact(value, fields, label):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields must be exact")


def build_2d_render_batch_job(request, preview, children, job_file, *, authorize=False):
    """Write one new batch job after revalidating all source stages, jobs and helpers."""
    report = {"schema": JOB_SCHEMA, "status": "error", "errors": [],
              "job_created": False}
    created, target = False, None
    try:
        if authorize is not True:
            raise ValueError("Explicit batch-job authorization is required")
        fresh = validate_2d_render_batch_request(request)
        if (not isinstance(preview, dict) or fresh.get("status") != "ready"
                or preview.get("status") != "ready"
                or fresh.get("batch_sha256") != preview.get("batch_sha256")
                or fresh.get("items") != preview.get("items")
                or fresh.get("outputs") != preview.get("outputs")):
            raise ValueError("Matching fresh batch preview is required")
        if not isinstance(children, list) or len(children) != len(fresh["items"]):
            raise ValueError("One staged child descriptor is required per batch item")
        target = Path(job_file)
        output_directory = Path(fresh["output_directory"])
        if (not target.is_absolute() or target.parent != output_directory
                or not target.name.startswith(".gameassetai-2d-batch-")
                or not target.name.endswith(".job.json")
                or target.exists() or target.is_symlink()):
            raise ValueError("Batch job must be a new owned hidden sibling of all outputs")
        payload_children = []
        for index, (planned, child) in enumerate(zip(fresh["items"], children)):
            _exact(child, _CHILD_FIELDS, f"children[{index}]")
            if child["id"] != planned["id"] or child["kind"] != planned["kind"]:
                raise ValueError("Child id/kind order must match the reviewed batch")
            stage, child_job = Path(child["stage_file"]), Path(child["job_file"])
            if not stage.is_absolute() or not child_job.is_absolute():
                raise ValueError("Child stage and job paths must be absolute")
            stage_data = _read_hashed(stage, child["stage_sha256"])
            job_data = _read_hashed(child_job, child["job_sha256"])
            child_payload = json.loads(job_data)
            if (not isinstance(child_payload, dict)
                    or child_payload.get("schema") != _CHILD_JOB_SCHEMAS[child["kind"]]
                    or child_payload.get("request") != request["items"][index]["request"]):
                raise ValueError("Child job schema/request does not match the batch")
            source_stage = child_payload.get("source_stage")
            if (not isinstance(source_stage, dict) or source_stage.get("path") != str(stage)
                    or source_stage.get("sha256") != child["stage_sha256"]
                    or source_stage.get("size") != len(stage_data)):
                raise ValueError("Child job source-stage binding is invalid")
            helper_root = Path(child["helper_root"])
            if not helper_root.is_absolute() or not helper_root.is_dir() or helper_root.is_symlink():
                raise ValueError("Child helper_root must be an absolute real directory")
            helper_hashes = {}
            for name in _HELPERS[child["kind"]]:
                helper = helper_root / name
                if not _regular(helper):
                    raise ValueError(f"Required batch child helper is unavailable: {name}")
                helper_hashes[name] = hashlib.sha256(helper.read_bytes()).hexdigest()
            payload_children.append({**child, "stage_size": len(stage_data),
                                     "job_size": len(job_data),
                                     "helper_sha256": helper_hashes,
                                     "outputs": planned["outputs"],
                                     "request_sha256": planned["request_sha256"]})
        if any(Path(path).exists() or Path(str(path) + ".meta").exists()
               for path in fresh["outputs"]):
            raise ValueError("A batch output or sibling .meta appeared before job creation")
        payload = {"schema": JOB_SCHEMA, "batch_request": request,
                   "batch_sha256": fresh["batch_sha256"],
                   "policy": request["policy"], "children": payload_children}
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        with target.open("xb") as stream:
            created = True
            stream.write(encoded)
        if target.read_bytes() != encoded:
            raise OSError("Batch job readback verification failed")
        report.update(status="created", job_created=True, job_file=str(target),
                      job_size=len(encoded),
                      job_sha256=hashlib.sha256(encoded).hexdigest(),
                      batch_sha256=fresh["batch_sha256"],
                      item_count=fresh["item_count"], output_count=fresh["output_count"])
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
        if created and target is not None:
            try:
                target.unlink()
            except OSError as cleanup:
                report["errors"].append("Batch job cleanup failed: " + str(cleanup))
    return report

