from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Any

from .errors import SafetyError, ValidationError
from .filesystem import atomic_write_json, is_link, read_json_object, validate_identifier
from .workspace import validate_workspace


RUN_SCHEMA = "gameassetai.output-run.v1"


def new_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


def begin_output_run(
    workspace: Path,
    *,
    game: str,
    asset_category: str,
    asset_id: str,
    run_id: str | None = None,
    request_summary: str = "",
) -> dict[str, Any]:
    validate_workspace(workspace)
    game = validate_identifier(game, "game")
    asset_category = validate_identifier(asset_category, "asset category")
    asset_id = validate_identifier(asset_id, "asset id")
    run_id = validate_identifier(run_id, "run id") if run_id else new_run_id().lower()
    output_root = workspace / "outputs"
    if is_link(output_root):
        raise SafetyError("Workspace outputs must not be a link or junction")
    run = output_root / game / asset_category / run_id
    if run.exists() or is_link(run):
        raise SafetyError(f"Output run already exists: {run}")
    run.mkdir(parents=True)
    manifest = {
        "schema": RUN_SCHEMA,
        "run_id": run_id,
        "game": game,
        "asset_category": asset_category,
        "asset_id": asset_id,
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "request_summary": request_summary,
        "artifacts": [],
        "status": "in-progress",
    }
    try:
        atomic_write_json(run / "manifest.json", manifest, replace=False)
    except BaseException:
        run.rmdir()
        raise
    return {"status": "created", "run": str(run), "manifest": manifest}


def validate_output_run(path: Path) -> dict[str, Any]:
    if is_link(path) or not path.is_dir():
        raise ValidationError(f"Output run must be a real directory: {path}")
    manifest_path = path / "manifest.json"
    if is_link(manifest_path) or not manifest_path.is_file():
        raise ValidationError("Output run is missing a real manifest.json")
    manifest = read_json_object(manifest_path)
    required = {
        "schema", "run_id", "game", "asset_category", "asset_id", "created_utc",
        "request_summary", "artifacts", "status",
    }
    if set(manifest) != required or manifest.get("schema") != RUN_SCHEMA:
        raise ValidationError("Invalid output run manifest contract")
    for field in ("run_id", "game", "asset_category", "asset_id"):
        validate_identifier(manifest[field], field)
    if not isinstance(manifest["artifacts"], list) or manifest["status"] not in {
        "in-progress", "accepted", "rejected", "complete",
    }:
        raise ValidationError("Invalid output run artifacts/status")
    return manifest
