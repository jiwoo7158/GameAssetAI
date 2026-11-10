"""Execute one hash-bound 2D batch job with verified all-or-nothing rollback."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

from validate_2d_render_batch_request import validate_2d_render_batch_request


RESULT_SCHEMA = "gameassetai.2d-render-batch-result.v1"
JOB_SCHEMA = "gameassetai.2d-render-batch-job.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_JOB_FIELDS = {"schema", "batch_request", "batch_sha256", "policy", "children"}
_CHILD_FIELDS = {"id", "kind", "stage_file", "stage_sha256", "job_file", "job_sha256",
                 "helper_root", "stage_size", "job_size", "helper_sha256", "outputs",
                 "request_sha256"}
_RENDERERS = {"STATIC": "render_2d_staged_source.py",
              "ACTION_SEQUENCE": "render_2d_action_sequence.py"}


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def _data_with_hash(path, expected, size=None):
    if not _regular(path) or not isinstance(expected, str) or not _SHA256.fullmatch(expected):
        raise ValueError(f"Missing, linked or invalid hash-bound file: {path}")
    data = path.read_bytes()
    if (size is not None and len(data) != size) or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash or size changed for file: {path}")
    return data


def _default_child_runner(blender_executable, child):
    renderer = Path(child["helper_root"]) / _RENDERERS[child["kind"]]
    command = [str(blender_executable), "--background", child["stage_file"],
               "--python", str(renderer), "--", "--job", child["job_file"],
               "--job-sha256", child["job_sha256"],
               "--helper-root", child["helper_root"]]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    lines = [line for line in completed.stdout.splitlines()
             if line.startswith("GAMEASSETAI_RESULT=")]
    if completed.returncode or len(lines) != 1:
        detail = (completed.stderr or completed.stdout)[-1000:].replace("\r", " ").replace("\n", " ")
        raise RuntimeError("Child Blender render failed or returned no unique result "
                           f"(exit {completed.returncode}): {detail}")
    return json.loads(lines[0].split("=", 1)[1])


def _verified_artifacts(child, result):
    if child["kind"] == "STATIC":
        if result.get("status") != "created" or result.get("png_published") is not True:
            raise RuntimeError("Static child render did not publish successfully")
        artifacts = [result.get("artifact")]
    else:
        if (result.get("status") != "created" or result.get("pngs_published") is not True
                or result.get("published_count") != len(child["outputs"])):
            raise RuntimeError("Action-sequence child render did not publish completely")
        artifacts = result.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(child["outputs"]):
        raise RuntimeError("Child artifact count does not match the batch job")
    verified = []
    for expected, artifact in zip(child["outputs"], artifacts):
        if (not isinstance(artifact, dict) or artifact.get("path") != expected
                or not isinstance(artifact.get("sha256"), str)
                or not _SHA256.fullmatch(artifact["sha256"])):
            raise RuntimeError("Child artifact receipt is malformed or reordered")
        data = _data_with_hash(Path(expected), artifact["sha256"], artifact.get("size"))
        verified.append({"path": expected, "size": len(data),
                         "sha256": artifact["sha256"], "child_id": child["id"]})
    receipt = result.get("receipt_sha256")
    if not isinstance(receipt, str) or not _SHA256.fullmatch(receipt):
        raise RuntimeError("Child receipt SHA-256 is missing")
    return verified, receipt


def run_2d_render_batch_job(job_file, job_sha256, blender_executable, *, child_runner=None):
    """Run validated children in list order and roll back verified prior outputs on failure."""
    report = {"schema": RESULT_SCHEMA, "status": "error", "errors": [],
              "artifacts_published": False, "published_count": 0,
              "completed_children": 0, "artifacts": [], "child_receipts": []}
    published = []
    try:
        job_path, blender = Path(job_file), Path(blender_executable)
        job_data = _data_with_hash(job_path, job_sha256)
        payload = json.loads(job_data)
        if not isinstance(payload, dict) or set(payload) != _JOB_FIELDS:
            raise ValueError("Batch job fields are invalid")
        if payload.get("schema") != JOB_SCHEMA:
            raise ValueError("Batch job schema mismatch")
        fresh = validate_2d_render_batch_request(payload.get("batch_request"))
        if (fresh.get("status") != "ready"
                or fresh.get("batch_sha256") != payload.get("batch_sha256")
                or payload.get("policy") != payload["batch_request"].get("policy")):
            raise ValueError("Batch request changed or is no longer ready")
        children = payload.get("children")
        if not isinstance(children, list) or len(children) != len(fresh["items"]):
            raise ValueError("Batch job child count is invalid")
        if not blender.is_absolute() or not _regular(blender):
            raise ValueError("Blender executable must be an absolute regular file")
        for index, (planned, child) in enumerate(zip(fresh["items"], children)):
            if not isinstance(child, dict) or set(child) != _CHILD_FIELDS:
                raise ValueError(f"Batch child {index} fields are invalid")
            if (child.get("id") != planned["id"] or child.get("kind") != planned["kind"]
                    or child.get("outputs") != planned["outputs"]
                    or child.get("request_sha256") != planned["request_sha256"]):
                raise ValueError("Batch child no longer matches the reviewed plan")
            _data_with_hash(Path(child["stage_file"]), child["stage_sha256"],
                            child["stage_size"])
            _data_with_hash(Path(child["job_file"]), child["job_sha256"], child["job_size"])
            helper_root = Path(child["helper_root"])
            if not helper_root.is_absolute() or not helper_root.is_dir() or helper_root.is_symlink():
                raise ValueError("Batch child helper root is invalid")
            if (not isinstance(child["helper_sha256"], dict)
                    or _RENDERERS[child["kind"]] not in child["helper_sha256"]):
                raise ValueError("Batch child helper manifest is invalid")
            for name, digest in child["helper_sha256"].items():
                _data_with_hash(helper_root / name, digest)
        if any(Path(path).exists() or Path(str(path) + ".meta").exists()
               for path in fresh["outputs"]):
            raise ValueError("A batch target or sibling .meta exists before execution")

        runner = child_runner or _default_child_runner
        for child in children:
            result = runner(blender, child)
            artifacts, receipt = _verified_artifacts(child, result)
            published.extend(artifacts)
            report["child_receipts"].append({"id": child["id"], "sha256": receipt})
            report["completed_children"] += 1
        receipt = {"schema": "gameassetai.2d-render-batch-receipt.v1",
                   "batch_sha256": fresh["batch_sha256"],
                   "job_sha256": job_sha256, "artifacts": published,
                   "child_receipts": report["child_receipts"]}
        receipt_data = json.dumps(receipt, sort_keys=True, ensure_ascii=True,
                                  separators=(",", ":"), allow_nan=False).encode("utf-8")
        report.update(status="created", artifacts_published=True,
                      published_count=len(published), artifacts=published,
                      batch_sha256=fresh["batch_sha256"], job_sha256=job_sha256,
                      receipt_sha256=hashlib.sha256(receipt_data).hexdigest())
    except (ValueError, TypeError, KeyError, OSError, RuntimeError,
            UnicodeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report["errors"].append(str(exc))
    finally:
        if report["status"] != "created":
            remaining = []
            for artifact in reversed(published):
                path = Path(artifact["path"])
                try:
                    if not _regular(path):
                        if path.exists() or path.is_symlink():
                            raise OSError("Published batch output is no longer a regular file")
                        continue
                    if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                        raise OSError("Published batch output changed before rollback")
                    path.unlink()
                except OSError as cleanup:
                    report["errors"].append("Batch rollback failed: " + str(cleanup))
                    remaining.append(artifact)
            report["artifacts_published"] = bool(remaining)
            report["published_count"] = len(remaining)
            report["artifacts"] = list(reversed(remaining))
    return report


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--job-sha256", required=True)
    parser.add_argument("--blender-executable", required=True)
    args = parser.parse_args(tail)
    result = run_2d_render_batch_job(args.job, args.job_sha256, args.blender_executable)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "created" else 1


if __name__ == "__main__":
    raise SystemExit(main())
# Retained bounded Blender capability; product support remains evidence-scoped.
