"""Build one authorized hash-bound job for staged static impostor pass children."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

from validate_2d_impostor_bundle_request import validate_2d_impostor_bundle_request


JOB_SCHEMA = "gameassetai.2d-impostor-bundle-job.v1"
PREVIEW_SCHEMA = "gameassetai.2d-impostor-shared-framing-preview.v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
CHILD_FIELDS = {"id", "pass_kind", "stage_file", "stage_sha256",
                "job_file", "job_sha256", "helper_root"}
HELPERS = {
    "COLOR": ("quantize_rgba.py", "build_2d_render_receipt.py",
              "render_2d_staged_source.py"),
    "NORMAL": ("quantize_rgba.py", "build_2d_render_receipt.py",
               "render_2d_normal_pass.py"),
    "DEPTH": ("quantize_rgba.py", "build_2d_render_receipt.py",
              "render_2d_depth_pass.py"),
}
JOB_SCHEMAS = {"COLOR": "gameassetai.2d-staged-render-job.v1",
               "NORMAL": "gameassetai.2d-normal-pass-job.v1",
               "DEPTH": "gameassetai.2d-depth-pass-job.v1"}


def _hash_json(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)
            and getattr(info, "st_nlink", 1) == 1)


def _read_hashed(path, expected):
    if not _regular(path) or not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError(f"Missing, linked or invalid hash-bound file: {path}")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Hash changed for file: {path}")
    return data


def _preview_maps(preview, fresh):
    if (not isinstance(preview, dict) or preview.get("schema") != PREVIEW_SCHEMA
            or preview.get("status") != "planned" or preview.get("errors") != []
            or preview.get("blockers") != []
            or preview.get("request_sha256") != fresh.get("request_sha256")):
        raise ValueError("Matching blocker-free shared-framing preview is required")
    expected_hash = _hash_json({"request_sha256": fresh["request_sha256"],
                                "source_fingerprint": preview.get("source_fingerprint"),
                                "views": preview.get("views")})
    if preview.get("preview_fingerprint") != expected_hash:
        raise ValueError("Shared-framing preview hash changed")
    source_hash = preview.get("source_fingerprint")
    if not isinstance(source_hash, str) or not SHA256.fullmatch(source_hash):
        raise ValueError("Shared-framing source fingerprint is invalid")
    view_list, child_list = preview.get("views"), preview.get("children")
    if not isinstance(view_list, list) or not isinstance(child_list, list):
        raise ValueError("Shared-framing view/child collections are invalid")
    plans, children = {}, {}
    for entry in view_list:
        if (not isinstance(entry, dict)
                or set(entry) != {"view_id", "plan", "plan_fingerprint", "children"}
                or not isinstance(entry.get("view_id"), str)
                or not isinstance(entry.get("plan"), dict)
                or entry.get("plan_fingerprint") != _hash_json(entry.get("plan"))
                or entry["view_id"] in plans):
            raise ValueError("Shared-framing view entry is malformed")
        plans[entry["view_id"]] = entry
    for entry in child_list:
        if (not isinstance(entry, dict)
                or set(entry) != {"position", "id", "view_id", "pass_kind",
                                  "request_sha256", "candidate_schema", "candidate_status",
                                  "source_fingerprint", "setup_fingerprint",
                                  "output_fingerprint"}
                or not isinstance(entry.get("position"), int)
                or entry["position"] in children
                or entry.get("candidate_status") != "candidate_for_review"
                or any(not isinstance(entry.get(key), str) or not SHA256.fullmatch(entry[key])
                       for key in ("request_sha256", "source_fingerprint",
                                   "setup_fingerprint", "output_fingerprint"))):
            raise ValueError("Shared-framing child entry is malformed")
        children[entry["position"]] = entry
    if len(plans) != fresh["view_count"] or len(children) != fresh["item_count"]:
        raise ValueError("Shared-framing preview coverage is incomplete")
    for view_id, view in plans.items():
        expected = [{**child, "shared_plan_fingerprint": view["plan_fingerprint"]}
                    for child in child_list if child["view_id"] == view_id]
        if view["children"] != expected:
            raise ValueError("Shared-framing per-view child bindings are malformed")
    return plans, children


def _shared_plan_from_child(plan):
    if not isinstance(plan, dict):
        raise ValueError("Child framing plan must be an object")
    normalized = dict(plan)
    normalized.pop("camera_frame", None)  # Static COLOR stores this redundant derived field.
    return normalized


def build_2d_impostor_bundle_job(request, preview, children, job_file, *, authorize=False):
    report = {"schema": JOB_SCHEMA, "status": "error", "errors": [],
              "job_created": False}
    target, created = None, False
    try:
        if authorize is not True:
            raise ValueError("Explicit impostor bundle-job authorization is required")
        fresh = validate_2d_impostor_bundle_request(request)
        if fresh.get("status") != "ready":
            raise ValueError("A currently valid impostor bundle request is required")
        plans, preview_children = _preview_maps(preview, fresh)
        if not isinstance(children, list) or len(children) != fresh["item_count"]:
            raise ValueError("One staged child descriptor is required per bundle item")
        output_dir = Path(fresh["outputs"][0]).parent
        target = Path(job_file)
        if (not target.is_absolute() or target.parent != output_dir
                or not target.name.startswith(".gameassetai-impostor-bundle-")
                or not target.name.endswith(".job.json")
                or target.exists() or target.is_symlink()):
            raise ValueError("Bundle job must be a new owned hidden sibling of all outputs")
        payload_children = []
        for index, (planned, descriptor) in enumerate(zip(fresh["items"], children)):
            if not isinstance(descriptor, dict) or set(descriptor) != CHILD_FIELDS:
                raise ValueError(f"children[{index}] fields must be exact")
            if (descriptor["id"] != planned["id"]
                    or descriptor["pass_kind"] != planned["pass_kind"]):
                raise ValueError("Child id/pass order must match the reviewed bundle")
            stage, child_job = Path(descriptor["stage_file"]), Path(descriptor["job_file"])
            stage_data = _read_hashed(stage, descriptor["stage_sha256"])
            job_data = _read_hashed(child_job, descriptor["job_sha256"])
            payload = json.loads(job_data)
            if (not isinstance(payload, dict)
                    or payload.get("schema") != JOB_SCHEMAS[planned["pass_kind"]]
                    or payload.get("request") != request["items"][index]["request"]):
                raise ValueError("Child job schema/request does not match the bundle")
            source_stage = payload.get("source_stage")
            if (not isinstance(source_stage, dict) or source_stage.get("path") != str(stage)
                    or source_stage.get("sha256") != descriptor["stage_sha256"]
                    or source_stage.get("size") != len(stage_data)):
                raise ValueError("Child job source-stage binding is invalid")
            candidate, framing = payload.get("candidate"), payload.get("framing")
            preview_child, view = preview_children.get(index), plans.get(planned["view_id"])
            if (not isinstance(candidate, dict) or not isinstance(framing, dict)
                    or preview_child is None or view is None
                    or candidate.get("request_sha256") != planned["request_sha256"]
                    or framing.get("request_sha256") != planned["request_sha256"]
                    or framing.get("plan_fingerprint") != _hash_json(framing.get("plan"))
                    or _shared_plan_from_child(framing.get("plan")) != view.get("plan")):
                raise ValueError("Child job does not bind the shared framing plan")
            for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
                if (candidate.get(key) != preview_child.get(key)
                        or framing.get(key) != preview_child.get(key)):
                    raise ValueError("Child candidate/framing fingerprints changed")
            helper_root = Path(descriptor["helper_root"])
            if not helper_root.is_absolute() or not helper_root.is_dir() or helper_root.is_symlink():
                raise ValueError("Child helper_root must be an absolute real directory")
            helper_hashes = {}
            for name in HELPERS[planned["pass_kind"]]:
                helper = helper_root / name
                if not _regular(helper):
                    raise ValueError(f"Required child helper is unavailable: {name}")
                helper_hashes[name] = hashlib.sha256(helper.read_bytes()).hexdigest()
            payload_children.append({**descriptor, "position": index,
                                     "view_id": planned["view_id"],
                                     "stage_size": len(stage_data), "job_size": len(job_data),
                                     "helper_sha256": helper_hashes,
                                     "target_file": planned["target_file"],
                                     "request_sha256": planned["request_sha256"],
                                     "plan_fingerprint": view["plan_fingerprint"]})
        all_targets = [*fresh["outputs"], fresh["manifest"]]
        if any(Path(path).exists() or Path(str(path) + ".meta").exists()
               for path in all_targets):
            raise ValueError("A bundle output, manifest or sibling .meta appeared")
        payload = {"schema": JOB_SCHEMA, "bundle_request": request,
                   "request_sha256": fresh["request_sha256"], "preview": preview,
                   "preview_fingerprint": preview["preview_fingerprint"],
                   "policy": request["policy"], "children": payload_children}
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        with target.open("xb") as stream:
            created = True
            stream.write(encoded)
        if target.read_bytes() != encoded:
            raise OSError("Bundle job readback verification failed")
        report.update(status="created", job_created=True, job_file=str(target),
                      job_size=len(encoded), job_sha256=hashlib.sha256(encoded).hexdigest(),
                      request_sha256=fresh["request_sha256"],
                      preview_fingerprint=preview["preview_fingerprint"],
                      child_count=len(payload_children), output_count=len(fresh["outputs"]))
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
        if created and target is not None:
            try:
                target.unlink()
            except OSError as cleanup:
                report["errors"].append("Bundle job cleanup failed: " + str(cleanup))
    return report
