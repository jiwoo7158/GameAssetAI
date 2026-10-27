"""Execute a hash-bound static impostor bundle with verified rollback and manifest-last publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess
import sys

from build_2d_impostor_bundle_job import (CHILD_FIELDS, HELPERS, JOB_SCHEMA,
                                          _preview_maps)
from validate_2d_impostor_bundle_request import validate_2d_impostor_bundle_request
from validate_2d_impostor_result_manifest import (SCHEMA as RESULT_MANIFEST_SCHEMA,
                                                   validate_2d_impostor_result_manifest)


RESULT_SCHEMA = "gameassetai.2d-impostor-bundle-run-result.v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
JOB_FIELDS = {"schema", "bundle_request", "request_sha256", "preview",
              "preview_fingerprint", "policy", "children"}
BUILT_CHILD_FIELDS = CHILD_FIELDS | {"position", "view_id", "stage_size", "job_size",
                                     "helper_sha256", "target_file", "request_sha256",
                                     "plan_fingerprint"}
RENDERERS = {"COLOR": "render_2d_staged_source.py",
             "NORMAL": "render_2d_normal_pass.py",
             "DEPTH": "render_2d_depth_pass.py"}


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            and getattr(info, "st_nlink", 1) == 1)


def _data_with_hash(path, expected, size=None):
    if not _regular(path) or not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError(f"Missing, linked or invalid hash-bound file: {path}")
    data = path.read_bytes()
    if (size is not None and len(data) != size) or hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash or size changed for file: {path}")
    return data


def _default_child_runner(blender_executable, child):
    renderer = Path(child["helper_root"]) / RENDERERS[child["pass_kind"]]
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


def _verified_child(child, result):
    if result.get("status") != "created" or result.get("png_published") is not True:
        raise RuntimeError("Impostor child render did not publish successfully")
    artifact = result.get("artifact")
    if (not isinstance(artifact, dict) or artifact.get("path") != child["target_file"]
            or not isinstance(artifact.get("sha256"), str)
            or not SHA256.fullmatch(artifact["sha256"])):
        raise RuntimeError("Impostor child artifact receipt is malformed")
    data = _data_with_hash(Path(child["target_file"]), artifact["sha256"], artifact.get("size"))
    receipt = result.get("receipt_sha256")
    if not isinstance(receipt, str) or not SHA256.fullmatch(receipt):
        raise RuntimeError("Impostor child receipt SHA-256 is missing")
    return {"path": child["target_file"], "size": len(data),
            "sha256": artifact["sha256"], "receipt_sha256": receipt}


def run_2d_impostor_bundle_job(job_file, job_sha256, blender_executable, *, child_runner=None):
    report = {"schema": RESULT_SCHEMA, "status": "error", "errors": [],
              "artifacts_published": False, "manifest_published": False,
              "published_count": 0, "completed_children": 0, "artifacts": []}
    published, manifest_path, manifest_hash = [], None, None
    try:
        job_path, blender = Path(job_file), Path(blender_executable)
        payload = json.loads(_data_with_hash(job_path, job_sha256))
        if not isinstance(payload, dict) or set(payload) != JOB_FIELDS:
            raise ValueError("Bundle job fields are invalid")
        if payload.get("schema") != JOB_SCHEMA:
            raise ValueError("Bundle job schema mismatch")
        fresh = validate_2d_impostor_bundle_request(payload.get("bundle_request"))
        if (fresh.get("status") != "ready"
                or fresh.get("request_sha256") != payload.get("request_sha256")
                or payload.get("policy") != fresh.get("policy")
                or payload.get("preview_fingerprint") != payload.get("preview", {}).get("preview_fingerprint")):
            raise ValueError("Bundle request/preview changed or is no longer ready")
        plans, preview_children = _preview_maps(payload["preview"], fresh)
        children = payload.get("children")
        if not isinstance(children, list) or len(children) != fresh["item_count"]:
            raise ValueError("Bundle job child count is invalid")
        if not blender.is_absolute() or not _regular(blender):
            raise ValueError("Blender executable must be an absolute regular file")
        for index, (planned, child) in enumerate(zip(fresh["items"], children)):
            if not isinstance(child, dict) or set(child) != BUILT_CHILD_FIELDS:
                raise ValueError(f"Bundle child {index} fields are invalid")
            view = plans.get(planned["view_id"])
            if (child.get("position") != index or child.get("id") != planned["id"]
                    or child.get("pass_kind") != planned["pass_kind"]
                    or child.get("view_id") != planned["view_id"]
                    or child.get("target_file") != planned["target_file"]
                    or child.get("request_sha256") != planned["request_sha256"]
                    or view is None or child.get("plan_fingerprint") != view.get("plan_fingerprint")
                    or preview_children.get(index) is None):
                raise ValueError("Bundle child no longer matches the reviewed plan")
            _data_with_hash(Path(child["stage_file"]), child["stage_sha256"], child["stage_size"])
            _data_with_hash(Path(child["job_file"]), child["job_sha256"], child["job_size"])
            helper_root = Path(child["helper_root"])
            if not helper_root.is_absolute() or not helper_root.is_dir() or helper_root.is_symlink():
                raise ValueError("Bundle child helper root is invalid")
            expected_helpers = set(HELPERS[child["pass_kind"]])
            if not isinstance(child["helper_sha256"], dict) or set(child["helper_sha256"]) != expected_helpers:
                raise ValueError("Bundle child helper manifest is invalid")
            for name, digest in child["helper_sha256"].items():
                _data_with_hash(helper_root / name, digest)
        manifest_path = Path(fresh["manifest"])
        if any(Path(path).exists() or Path(str(path) + ".meta").exists()
               for path in [*fresh["outputs"], fresh["manifest"]]):
            raise ValueError("A bundle target or sibling .meta exists before execution")

        runner = child_runner or _default_child_runner
        artifact_rows = []
        for child in children:
            verified = _verified_child(child, runner(blender, child))
            published.append(verified)
            artifact_rows.append({"position": child["position"], "item_id": child["id"],
                                  "view_id": child["view_id"],
                                  "pass_kind": child["pass_kind"],
                                  "target_file": child["target_file"],
                                  "request_sha256": child["request_sha256"],
                                  "plan_fingerprint": child["plan_fingerprint"],
                                  "png_sha256": verified["sha256"],
                                  "receipt_sha256": verified["receipt_sha256"],
                                  "bytes": verified["size"]})
            report["completed_children"] += 1
        proposed = {"schema": RESULT_MANIFEST_SCHEMA,
                    "request_sha256": fresh["request_sha256"],
                    "source_fingerprint": payload["preview"]["source_fingerprint"],
                    "preview_fingerprint": payload["preview_fingerprint"],
                    "policy": fresh["policy"],
                    "views": [{"position": index, "view_id": view["view_id"],
                               "plan_fingerprint": view["plan_fingerprint"]}
                              for index, view in enumerate(payload["preview"]["views"])],
                    "artifacts": artifact_rows}
        validation = validate_2d_impostor_result_manifest(proposed, fresh, payload["preview"])
        if validation.get("status") != "ready":
            raise RuntimeError("Proposed result manifest failed validation: "
                               + "; ".join(validation.get("errors", [])))
        encoded = json.dumps(proposed, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        with manifest_path.open("xb") as stream:
            stream.write(encoded)
        manifest_hash = hashlib.sha256(encoded).hexdigest()
        if (manifest_hash != validation["manifest_sha256"]
                or manifest_path.read_bytes() != encoded):
            raise OSError("Published result manifest failed readback verification")
        receipt = {"schema": "gameassetai.2d-impostor-bundle-receipt.v1",
                   "request_sha256": fresh["request_sha256"],
                   "preview_fingerprint": payload["preview_fingerprint"],
                   "job_sha256": job_sha256, "manifest_sha256": manifest_hash,
                   "artifacts": artifact_rows}
        report.update(status="created", artifacts_published=True, manifest_published=True,
                      published_count=len(published), artifacts=published,
                      manifest_file=str(manifest_path), manifest_sha256=manifest_hash,
                      request_sha256=fresh["request_sha256"],
                      preview_fingerprint=payload["preview_fingerprint"],
                      job_sha256=job_sha256,
                      receipt_sha256=hashlib.sha256(json.dumps(
                          receipt, sort_keys=True, ensure_ascii=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest())
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, UnicodeError,
            json.JSONDecodeError, subprocess.SubprocessError) as exc:
        report["errors"].append(str(exc))
    finally:
        if report["status"] != "created":
            if manifest_path is not None and manifest_hash is not None:
                try:
                    if _regular(manifest_path) and hashlib.sha256(manifest_path.read_bytes()).hexdigest() == manifest_hash:
                        manifest_path.unlink()
                    elif manifest_path.exists() or manifest_path.is_symlink():
                        raise OSError("Published manifest changed before rollback")
                except OSError as cleanup:
                    report["errors"].append("Manifest rollback failed: " + str(cleanup))
                    report["manifest_published"] = True
            remaining = []
            for artifact in reversed(published):
                path = Path(artifact["path"])
                try:
                    if not _regular(path):
                        if path.exists() or path.is_symlink():
                            raise OSError("Published bundle output is no longer a regular file")
                        continue
                    if hashlib.sha256(path.read_bytes()).hexdigest() != artifact["sha256"]:
                        raise OSError("Published bundle output changed before rollback")
                    path.unlink()
                except OSError as cleanup:
                    report["errors"].append("Bundle rollback failed: " + str(cleanup))
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
    result = run_2d_impostor_bundle_job(
        args.job, args.job_sha256, args.blender_executable)
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))
    return 0 if result["status"] == "created" else 1


if __name__ == "__main__":
    raise SystemExit(main())
