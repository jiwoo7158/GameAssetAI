"""Create a collision-safe hash-bound Object-ID render job."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat


OBJECT_ID_JOB_SCHEMA = "gameassetai.2d-object-id-job.v1"


def _id_job_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _id_job_regular(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)


def build_2d_object_id_job(request, candidate, framing, source_stage, job_file, *, authorize=False):
    report = {"schema": OBJECT_ID_JOB_SCHEMA, "status": "error", "errors": [],
              "job_created": False, "png_published": False}
    job = None
    created = False
    try:
        if authorize is not True:
            raise ValueError("Explicit Object-ID job authorization is required")
        request_sha = _id_job_hash(request)
        if (candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != request_sha
                or framing.get("status") != "planned" or framing.get("request_sha256") != request_sha
                or source_stage.get("status") != "created"
                or source_stage.get("request_sha256") != request_sha):
            raise ValueError("Reviewed request/candidate/framing/stage chain is required")
        for key in ("source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            value = candidate.get(key)
            if (not isinstance(value, str) or len(value) != 64
                    or framing.get(key) != value or source_stage.get(key) != value):
                raise ValueError("Candidate, framing and source-stage fingerprints must match")
        if source_stage.get("plan_fingerprint") != framing.get("plan_fingerprint"):
            raise ValueError("Framing plan fingerprint must match source stage")
        target, stage, job = (Path(request["output"]["target_file"]),
                              Path(source_stage["stage_file"]), Path(job_file))
        if (stage.parent != target.parent or job.parent != target.parent
                or not stage.name.startswith(".gameassetai-object-id-")
                or not stage.name.endswith(".stage.blend")
                or not job.name.startswith(".gameassetai-object-id-")
                or not job.name.endswith(".job.json")):
            raise ValueError("Stage and job must be owned hidden files beside the target")
        if job.exists() or job.is_symlink():
            raise ValueError("Object-ID job already exists")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta appeared before job creation")
        if not _id_job_regular(stage):
            raise ValueError("Source stage must be a regular file")
        stage_data = stage.read_bytes()
        if (len(stage_data) != source_stage.get("stage_size")
                or hashlib.sha256(stage_data).hexdigest() != source_stage.get("stage_sha256")):
            raise ValueError("Source stage changed before job creation")
        payload = {"schema": OBJECT_ID_JOB_SCHEMA, "request": request,
                   "candidate": candidate, "framing": framing,
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
