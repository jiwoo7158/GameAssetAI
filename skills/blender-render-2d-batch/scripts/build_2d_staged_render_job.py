"""Write one collision-safe, hash-bound job for an isolated Blender render process."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat


JOB_SCHEMA = "gameassetai.2d-staged-render-job.v1"


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _regular_file(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def build_2d_staged_render_job(request, candidate, framing, source_stage,
                               job_file, *, authorize=False):
    """Create a new owned job JSON; never render, overwrite, or alter Blender."""
    report = {"schema": JOB_SCHEMA, "status": "error", "errors": [],
              "job_created": False, "png_published": False}
    job = None
    created = False
    try:
        if authorize is not True:
            raise ValueError("Explicit render-job authorization is required")
        if not all(isinstance(value, dict) for value in
                   (request, candidate, framing, source_stage)):
            raise ValueError("request, candidate, framing and source_stage must be objects")
        request_sha = _hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned"
                or framing.get("request_sha256") != request_sha
                or source_stage.get("status") != "created"
                or source_stage.get("request_sha256") != request_sha):
            raise ValueError("Reviewed request/candidate/framing/stage chain is required")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            value = candidate.get(key)
            if (not isinstance(value, str) or len(value) != 64
                    or framing.get(key) != value or source_stage.get(key) != value):
                raise ValueError("Candidate, framing and source-stage fingerprints must match")
        plan_sha = framing.get("plan_fingerprint")
        if (not isinstance(plan_sha, str) or len(plan_sha) != 64
                or source_stage.get("plan_fingerprint") != plan_sha):
            raise ValueError("Framing plan fingerprint must match source stage")

        target = Path(request["output"]["target_file"])
        stage = Path(source_stage["stage_file"])
        job = Path(job_file)
        if (not target.is_absolute() or not stage.is_absolute() or not job.is_absolute()
                or stage.parent != target.parent or job.parent != target.parent
                or not stage.name.startswith(".gameassetai-2d-")
                or not stage.name.endswith(".stage.blend")
                or not job.name.startswith(".gameassetai-2d-")
                or not job.name.endswith(".job.json")):
            raise ValueError("Stage and job must be owned hidden files beside the target")
        if job.exists() or job.is_symlink():
            raise ValueError("Render job already exists")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta appeared before job creation")
        if not _regular_file(stage):
            raise ValueError("Source stage must be a regular file")
        stage_data = stage.read_bytes()
        if (len(stage_data) != source_stage.get("stage_size")
                or hashlib.sha256(stage_data).hexdigest() != source_stage.get("stage_sha256")):
            raise ValueError("Source stage changed before job creation")

        payload = {"schema": JOB_SCHEMA, "request": request, "candidate": candidate,
                   "framing": framing,
                   "source_stage": {"path": str(stage), "size": len(stage_data),
                                    "sha256": hashlib.sha256(stage_data).hexdigest()}}
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")
        with job.open("xb") as stream:
            created = True
            stream.write(encoded)
        report.update(status="created", job_created=True, job_file=str(job),
                      job_size=len(encoded), job_sha256=hashlib.sha256(encoded).hexdigest(),
                      request_sha256=request_sha, source_stage_sha256=payload["source_stage"]["sha256"])
    except (ValueError, TypeError, KeyError, OSError) as exc:
        report["errors"].append(str(exc))
        if created and job is not None:
            try:
                job.unlink()
            except OSError as cleanup:
                report["errors"].append("job cleanup failed: " + str(cleanup))
    return report

