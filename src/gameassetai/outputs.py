from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import re
from typing import Any, Iterable

from .catalog import asset_categories
from .errors import SafetyError, ValidationError
from .filesystem import (
    atomic_write_json,
    is_link,
    read_json_object,
    reject_linked_components,
    validate_identifier,
)
from .workspace import read_profile, validate_workspace


EXPERIMENT_SCHEMA = "gameassetai.experiment.v1"
TASK_SCHEMA = "gameassetai.output-task.v2"
LEGACY_RUN_SCHEMA = "gameassetai.output-run.v1"
TASK_NAME = re.compile(r"(?P<number>[0-9]{3,})-(?P<purpose>[a-z0-9]+(?:-[a-z0-9]+)*)\Z")
TASK_STATUSES = {"in-progress", "accepted", "rejected", "complete"}
GENERIC_EXPERIMENT_IDS = {"test", "experiment", "new-test", "try-again"}
GENERIC_TASK_PURPOSES = {"test", "final", "new", "backup", "output", "run", "task", "try-again"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _nonempty_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label} must be a nonempty string")
    return value.strip()


def _descriptive_identifier(value: object, label: str, forbidden: set[str]) -> str:
    identifier = validate_identifier(value, label)
    generic = identifier in forbidden or any(
        re.fullmatch(rf"{re.escape(prefix)}-[0-9]+", identifier)
        for prefix in forbidden
    )
    if not any(character.isalpha() for character in identifier) or generic:
        raise ValidationError(f"{label} must describe its purpose; generic or numeric ids are not allowed")
    return identifier


def _validate_repository(root: Path) -> Path:
    root = root.expanduser().absolute()
    reject_linked_components(root)
    if is_link(root) or not root.is_dir():
        raise ValidationError(f"Development Repository must be a real directory: {root}")
    required = (root / "AGENTS.md", root / "catalog", root / "src" / "gameassetai")
    if not required[0].is_file() or not required[1].is_dir() or not required[2].is_dir():
        raise ValidationError(f"Not a recognized GameAssetAI development Repository: {root}")
    return root


def _assert_within(path: Path, boundary: Path, label: str) -> None:
    try:
        path.resolve(strict=False).relative_to(boundary.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise SafetyError(f"{label} escapes its storage root: {path}") from exc


def _ensure_real_directories(boundary: Path, parts: Iterable[str]) -> tuple[Path, list[Path]]:
    current = boundary
    created: list[Path] = []
    for part in parts:
        current = current / part
        _assert_within(current, boundary, "Output path")
        reject_linked_components(current, stop=boundary)
        if current.exists() or is_link(current):
            if is_link(current) or not current.is_dir():
                raise SafetyError(f"Output path component must be a real directory: {current}")
            continue
        try:
            current.mkdir()
            created.append(current)
        except FileExistsError:
            pass
        if is_link(current) or not current.is_dir():
            raise SafetyError(f"Output path component was replaced during creation: {current}")
    return current, created


def _cleanup_empty(paths: Iterable[Path]) -> None:
    for path in reversed(list(paths)):
        if path.is_dir() and not is_link(path):
            try:
                path.rmdir()
            except OSError:
                pass


def _validate_category(category: object, catalog_root: Path | None) -> str:
    identifier = validate_identifier(category, "asset category")
    allowed = asset_categories(catalog_root)
    if identifier not in allowed:
        raise ValidationError(
            f"asset category must be one of {', '.join(sorted(allowed))}: {identifier}"
        )
    return identifier


def _validate_experiment_document(document: dict[str, Any], expected_id: str | None = None) -> None:
    required = {
        "schema", "experiment_id", "purpose", "question", "evaluation_criteria",
        "scope", "description", "created_utc",
    }
    if set(document) != required or document.get("schema") != EXPERIMENT_SCHEMA:
        raise ValidationError("Invalid experiment.json contract")
    identifier = _descriptive_identifier(
        document.get("experiment_id"), "experiment id", GENERIC_EXPERIMENT_IDS,
    )
    if expected_id is not None and identifier != expected_id:
        raise ValidationError("Experiment directory and experiment_id do not match")
    _nonempty_text(document.get("purpose"), "experiment purpose")
    _nonempty_text(document.get("question"), "experiment question")
    criteria = document.get("evaluation_criteria")
    if not isinstance(criteria, list) or not criteria or not all(
        isinstance(value, str) and value.strip() for value in criteria
    ):
        raise ValidationError("experiment evaluation_criteria must be a nonempty string list")
    for field in ("scope", "description", "created_utc"):
        if not isinstance(document.get(field), str):
            raise ValidationError(f"experiment {field} must be a string")


def create_experiment(
    repository: Path,
    experiment_id: str,
    *,
    purpose: str,
    question: str,
    evaluation_criteria: list[str],
    scope: str = "",
    description: str = "",
) -> dict[str, Any]:
    repository = _validate_repository(repository)
    experiment_id = _descriptive_identifier(
        experiment_id, "experiment id", GENERIC_EXPERIMENT_IDS,
    )
    document = {
        "schema": EXPERIMENT_SCHEMA,
        "experiment_id": experiment_id,
        "purpose": _nonempty_text(purpose, "experiment purpose"),
        "question": _nonempty_text(question, "experiment question"),
        "evaluation_criteria": list(evaluation_criteria),
        "scope": scope,
        "description": description,
        "created_utc": _utc_now(),
    }
    _validate_experiment_document(document, experiment_id)
    experiments, created = _ensure_real_directories(repository, ("output", "experiments"))
    experiment = experiments / experiment_id
    _assert_within(experiment, repository, "Experiment path")
    reject_linked_components(experiment, stop=repository)
    if experiment.exists() or is_link(experiment):
        raise SafetyError(
            f"Experiment already exists; inspect and explicitly reuse it instead: {experiment}"
        )
    try:
        experiment.mkdir()
    except FileExistsError as exc:
        raise SafetyError(f"Experiment was claimed concurrently: {experiment}") from exc
    try:
        atomic_write_json(experiment / "experiment.json", document, replace=False)
    except BaseException:
        if experiment.is_dir() and not is_link(experiment):
            experiment.rmdir()
        _cleanup_empty(created)
        raise
    return {"status": "created", "experiment": str(experiment), "metadata": document}


def validate_experiment(path: Path) -> dict[str, Any]:
    path = path.expanduser().absolute()
    reject_linked_components(path)
    if is_link(path) or not path.is_dir():
        raise ValidationError(f"Experiment must be a real directory: {path}")
    metadata_path = path / "experiment.json"
    if is_link(metadata_path) or not metadata_path.is_file():
        raise ValidationError("Experiment is missing a real experiment.json")
    document = read_json_object(metadata_path)
    _validate_experiment_document(document, path.name)
    return document


def list_experiments(repository: Path) -> list[dict[str, Any]]:
    repository = _validate_repository(repository)
    experiments = repository / "output" / "experiments"
    if not experiments.exists() and not is_link(experiments):
        return []
    reject_linked_components(experiments, stop=repository)
    if is_link(experiments) or not experiments.is_dir():
        raise SafetyError(f"Experiment root must be a real directory: {experiments}")
    result: list[dict[str, Any]] = []
    for path in sorted(experiments.iterdir()):
        if is_link(path) or not path.is_dir():
            raise SafetyError(f"Experiment root contains an unsupported entry: {path}")
        try:
            document = validate_experiment(path)
        except ValidationError as exc:
            result.append({"experiment_id": path.name, "status": "unidentified", "error": str(exc)})
        else:
            result.append({**document, "status": "identified"})
    return result


def _task_numbers(asset_root: Path) -> list[int]:
    numbers: list[int] = []
    for path in asset_root.iterdir():
        if is_link(path):
            raise SafetyError(f"Linked task entry is not supported: {path}")
        if not path.is_dir():
            raise SafetyError(f"Files must be stored inside a numbered task directory: {path}")
        match = TASK_NAME.fullmatch(path.name)
        if match is None:
            raise SafetyError(f"Unrecognized task directory in asset output: {path}")
        numbers.append(int(match.group("number")))
    return numbers


def _allocate_task_directory(asset_root: Path, purpose: str) -> tuple[Path, int]:
    for _ in range(1000):
        numbers = _task_numbers(asset_root)
        number = max(numbers, default=0) + 1
        task = asset_root / f"{number:03d}-{purpose}"
        try:
            task.mkdir()
        except FileExistsError:
            continue
        if is_link(task) or not task.is_dir():
            raise SafetyError(f"Allocated task path is not a real directory: {task}")
        return task, number
    raise SafetyError("Could not allocate a task number after concurrent collisions")


def begin_output_task(
    storage: str,
    root: Path,
    *,
    asset_category: str,
    asset_id: str,
    purpose: str,
    experiment_id: str | None = None,
    game_id: str | None = None,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    if storage not in {"development", "workspace"}:
        raise ValidationError("storage must be development or workspace")
    asset_id = _descriptive_identifier(asset_id, "asset id", set())
    purpose = _descriptive_identifier(purpose, "task purpose", GENERIC_TASK_PURPOSES)
    created: list[Path] = []

    if storage == "development":
        if game_id is not None:
            raise ValidationError("development output does not accept a game id")
        if experiment_id is None:
            raise ValidationError(
                "development output requires an explicit existing experiment id; list or create "
                "an experiment instead of guessing"
            )
        repository = _validate_repository(root)
        experiment_id = _descriptive_identifier(
            experiment_id, "experiment id", GENERIC_EXPERIMENT_IDS,
        )
        experiment = repository / "output" / "experiments" / experiment_id
        validate_experiment(experiment)
        category = _validate_category(asset_category, catalog_root or repository / "catalog")
        owner_root = experiment
        owner_id = experiment_id
        parent, created = _ensure_real_directories(owner_root, (category, asset_id))
        game_value: str | None = None
        experiment_value: str | None = experiment_id
    else:
        if experiment_id is not None:
            raise ValidationError("Workspace output does not accept an experiment id")
        workspace = root.expanduser().absolute()
        report = validate_workspace(workspace, require_profile=True)
        active = report["active_profile"]
        if game_id is not None:
            game_id = validate_identifier(game_id, "game id")
            if game_id != active:
                raise ValidationError(
                    f"game id must match the active Profile ({active}); select the intended Profile first"
                )
        else:
            game_id = active
        category = _validate_category(asset_category, catalog_root)
        parent, created = _ensure_real_directories(
            workspace, ("outputs", game_id, category, asset_id),
        )
        owner_id = game_id
        game_value = game_id
        experiment_value = None

    task, number = _allocate_task_directory(parent, purpose)
    manifest = {
        "schema": TASK_SCHEMA,
        "storage": storage,
        "task_id": task.name,
        "task_number": number,
        "purpose": purpose,
        "experiment_id": experiment_value,
        "game_id": game_value,
        "asset_category": category,
        "asset_id": asset_id,
        "created_utc": _utc_now(),
        "artifacts": [],
        "status": "in-progress",
        "review": None,
    }
    try:
        _validate_task_manifest(manifest)
        atomic_write_json(task / "manifest.json", manifest, replace=False)
    except BaseException:
        if task.is_dir() and not is_link(task):
            task.rmdir()
        _cleanup_empty(created)
        raise
    return {
        "status": "created",
        "storage": storage,
        "owner_id": owner_id,
        "task": str(task),
        "manifest": manifest,
    }


def _validate_artifact_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValidationError("Artifact paths must be nonempty POSIX paths relative to the task")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValidationError(f"Artifact path escapes or is not normalized: {value!r}")
    return value


def _validate_task_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schema", "storage", "task_id", "task_number", "purpose", "experiment_id", "game_id",
        "asset_category", "asset_id", "created_utc", "artifacts", "status", "review",
    }
    if set(manifest) != required or manifest.get("schema") != TASK_SCHEMA:
        raise ValidationError("Invalid output task manifest contract")
    storage = manifest.get("storage")
    if storage not in {"development", "workspace"}:
        raise ValidationError("Invalid output task storage")
    number = manifest.get("task_number")
    if not isinstance(number, int) or isinstance(number, bool) or number < 1:
        raise ValidationError("Invalid output task number")
    purpose = _descriptive_identifier(
        manifest.get("purpose"), "task purpose", GENERIC_TASK_PURPOSES,
    )
    if manifest.get("task_id") != f"{number:03d}-{purpose}":
        raise ValidationError("Output task id does not match its number and purpose")
    validate_identifier(manifest.get("asset_category"), "asset category")
    _descriptive_identifier(manifest.get("asset_id"), "asset id", set())
    if storage == "development":
        _descriptive_identifier(
            manifest.get("experiment_id"), "experiment id", GENERIC_EXPERIMENT_IDS,
        )
        if manifest.get("game_id") is not None:
            raise ValidationError("Development task cannot contain a game id")
    else:
        validate_identifier(manifest.get("game_id"), "game id")
        if manifest.get("experiment_id") is not None:
            raise ValidationError("Workspace task cannot contain an experiment id")
    if not isinstance(manifest.get("created_utc"), str) or not manifest["created_utc"]:
        raise ValidationError("Output task created_utc must be a nonempty string")
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValidationError("Output task artifacts must be a list")
    for artifact in artifacts:
        _validate_artifact_path(artifact)
    if manifest.get("status") not in TASK_STATUSES:
        raise ValidationError("Invalid output task status")
    if manifest.get("review") is not None and not isinstance(manifest["review"], dict):
        raise ValidationError("Output task review must be null or an object")


def validate_output_task(path: Path, catalog_root: Path | None = None) -> dict[str, Any]:
    path = path.expanduser().absolute()
    reject_linked_components(path)
    if is_link(path) or not path.is_dir():
        raise ValidationError(f"Output task must be a real directory: {path}")
    manifest_path = path / "manifest.json"
    if is_link(manifest_path) or not manifest_path.is_file():
        raise ValidationError("Output task is missing a real manifest.json")
    manifest = read_json_object(manifest_path)
    _validate_task_manifest(manifest)
    if path.name != manifest["task_id"]:
        raise ValidationError("Output task directory and task_id do not match")
    if path.parent.name != manifest["asset_id"]:
        raise ValidationError("Output task parent and asset_id do not match")
    if path.parent.parent.name != manifest["asset_category"]:
        raise ValidationError("Output task category directory and manifest do not match")
    _validate_category(manifest["asset_category"], catalog_root)
    owner = manifest["experiment_id"] if manifest["storage"] == "development" else manifest["game_id"]
    if path.parent.parent.parent.name != owner:
        raise ValidationError("Output task owner directory and manifest do not match")
    if manifest["storage"] == "development":
        if len(path.parents) < 6:
            raise ValidationError("Development task path is too shallow")
        if (
            path.parents[3].name != "experiments"
            or path.parents[4].name != "output"
        ):
            raise ValidationError("Development task is not under output/experiments")
        repository = _validate_repository(path.parents[5])
        validate_experiment(
            repository / "output" / "experiments" / manifest["experiment_id"],
        )
    else:
        if len(path.parents) < 5:
            raise ValidationError("Workspace task path is too shallow")
        if path.parents[3].name != "outputs":
            raise ValidationError("Workspace task is not under the fixed outputs directory")
        workspace = path.parents[4]
        validate_workspace(workspace)
        read_profile(workspace, manifest["game_id"])
    return manifest


def continue_output_task(path: Path, catalog_root: Path | None = None) -> dict[str, Any]:
    manifest = validate_output_task(path, catalog_root)
    if manifest["status"] != "in-progress":
        raise SafetyError("Completed, accepted, or rejected work requires a new numbered task")
    task = path.expanduser().absolute()
    for relative in manifest["artifacts"]:
        artifact = task / PurePosixPath(relative)
        _assert_within(artifact, task, "Artifact path")
        if is_link(artifact) or not artifact.exists():
            raise ValidationError(f"Cannot continue because a recorded artifact is missing or linked: {relative}")
    return {"status": "continued", "task": str(task), "manifest": manifest}


def _validate_legacy_output_run(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "run_id", "game", "asset_category", "asset_id", "created_utc",
        "request_summary", "artifacts", "status",
    }
    if set(manifest) != required or manifest.get("schema") != LEGACY_RUN_SCHEMA:
        raise ValidationError("Invalid legacy output run manifest contract")
    for field in ("run_id", "game", "asset_category", "asset_id"):
        validate_identifier(manifest[field], field)
    if path.name != manifest["run_id"]:
        raise ValidationError("Legacy output directory and run_id do not match")
    if not isinstance(manifest["artifacts"], list) or manifest["status"] not in TASK_STATUSES:
        raise ValidationError("Invalid legacy output run artifacts/status")
    return manifest


def validate_output_path(path: Path, catalog_root: Path | None = None) -> dict[str, Any]:
    path = path.expanduser().absolute()
    reject_linked_components(path)
    if is_link(path) or not path.is_dir():
        raise ValidationError(f"Output path must be a real directory: {path}")
    manifest_path = path / "manifest.json"
    if is_link(manifest_path) or not manifest_path.is_file():
        raise ValidationError("Output path is missing a real manifest.json")
    manifest = read_json_object(manifest_path)
    if manifest.get("schema") == TASK_SCHEMA:
        return validate_output_task(path, catalog_root)
    if manifest.get("schema") == LEGACY_RUN_SCHEMA:
        return _validate_legacy_output_run(path, manifest)
    raise ValidationError(f"Unsupported output manifest schema: {manifest.get('schema')}")


def validate_output_run(path: Path) -> dict[str, Any]:
    """Read-only compatibility validator for old callers; new allocation uses output tasks."""
    return validate_output_path(path)


def begin_output_run(*args: object, **kwargs: object) -> dict[str, Any]:
    """Refuse legacy date/run allocation while keeping a clear compatibility error."""
    raise ValidationError(
        "Legacy output-run creation is disabled; use begin_output_task with an explicit storage, "
        "asset id, and purpose"
    )
