from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import os
from pathlib import Path, PurePosixPath
import re
import time
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
from .workspace import read_profile, resolve_workspace_output_root, validate_workspace


EXPERIMENT_SCHEMA = "gameassetai.experiment.v1"
TASK_SCHEMA = "gameassetai.output-task.v3"
LEGACY_TASK_SCHEMA = "gameassetai.output-task.v2"
LEGACY_RUN_SCHEMA = "gameassetai.output-run.v1"
TASK_NAME = re.compile(r"(?P<number>[0-9]{3,})-(?P<purpose>[a-z0-9]+(?:-[a-z0-9]+)*)\Z")
TASK_STATUSES = {"in-progress", "accepted", "rejected", "complete"}
TASK_TRANSITIONS = {
    "in-progress": {"complete", "accepted", "rejected"},
    "complete": {"accepted", "rejected"},
    "accepted": set(),
    "rejected": set(),
}
ARTIFACT_KINDS = {
    "model": ("models", {".blend"}),
    "preview": ("previews", {".jpg", ".jpeg", ".png", ".webp"}),
    "sprite": ("sprites", {".png"}),
    "export": ("exports", {".fbx", ".glb", ".gltf", ".obj"}),
}
ARTIFACT_FILENAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*(?:\.[a-z0-9]+)+\Z")
GENERIC_ARTIFACT_STEMS = {"test", "final", "new", "output", "render", "file", "image", "model"}
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
    output_root: Path | None = None,
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
        if output_root is not None:
            raise ValidationError("development output uses the Repository output root")
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
        workspace_id: str | None = None
        output_root_kind = "repository"
        output_root_source = "repository"
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
        resolved_output = resolve_workspace_output_root(
            workspace,
            explicit_output_root=output_root,
            profile_id=game_id,
        )
        if resolved_output["kind"] == "workspace":
            parent, created = _ensure_real_directories(
                workspace, ("outputs", game_id, category, asset_id),
            )
        else:
            parent, created = _ensure_real_directories(
                resolved_output["root"], (game_id, category, asset_id),
            )
        owner_id = game_id
        game_value = game_id
        experiment_value = None
        workspace_id = resolved_output["workspace_id"]
        output_root_kind = resolved_output["kind"]
        output_root_source = resolved_output["source"]

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
        "workspace_id": workspace_id,
        "output_root_kind": output_root_kind,
        "output_root_source": output_root_source,
        "created_utc": _utc_now(),
        "reservations": [],
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
    if len(path.parts) != 2 or path.parts[0] not in {
        specification[0] for specification in ARTIFACT_KINDS.values()
    }:
        raise ValidationError("Artifact paths must use one official task artifact directory")
    _validate_artifact_filename(path.parts[1], expected_directory=path.parts[0])
    return value


def _validate_artifact_filename(value: object, *, expected_directory: str) -> str:
    if not isinstance(value, str) or not ARTIFACT_FILENAME.fullmatch(value):
        raise ValidationError(
            "Artifact filename must be a lowercase descriptive name with an extension"
        )
    stem = Path(value).stem
    if stem in GENERIC_ARTIFACT_STEMS or re.fullmatch(
        r"(?:test|final|new|output|render|file|image|model)[0-9]+", stem,
    ):
        raise ValidationError("Artifact filename must describe the asset or file role")
    suffix = Path(value).suffix
    allowed = next(
        extensions
        for directory, extensions in ARTIFACT_KINDS.values()
        if directory == expected_directory
    )
    if suffix not in allowed:
        raise ValidationError(
            f"Artifact extension {suffix!r} is not allowed under {expected_directory}/"
        )
    return value


def _validate_review_evidence_files(
    task: Path,
    evidence: list[object],
    registered_artifacts: list[str],
) -> list[str]:
    if not evidence:
        raise ValidationError("Review evidence must name one or more registered artifacts")
    validated: list[str] = []
    seen: set[str] = set()
    for value in evidence:
        relative = _validate_artifact_path(value)
        if relative in seen:
            raise ValidationError("Review evidence paths must not contain duplicates")
        seen.add(relative)
        if relative not in registered_artifacts:
            raise ValidationError("Review evidence must name one or more registered artifacts")
        artifact = task / PurePosixPath(relative)
        _assert_within(artifact, task, "Review evidence path")
        reject_linked_components(artifact, stop=task)
        if is_link(artifact) or not artifact.is_file():
            raise ValidationError(
                f"Review evidence must be an existing real file at review time: {relative}"
            )
        try:
            size = artifact.stat().st_size
        except OSError as exc:
            raise ValidationError(f"Cannot inspect review evidence: {relative}") from exc
        if size <= 0:
            raise ValidationError(f"Review evidence must not be empty: {relative}")
        validated.append(relative)
    return validated


def _validate_task_manifest(manifest: dict[str, Any]) -> None:
    required = {
        "schema", "storage", "task_id", "task_number", "purpose", "experiment_id", "game_id",
        "asset_category", "asset_id", "workspace_id", "output_root_kind",
        "output_root_source", "created_utc", "reservations", "artifacts", "status", "review",
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
        if (
            manifest.get("workspace_id") is not None
            or manifest.get("output_root_kind") != "repository"
            or manifest.get("output_root_source") != "repository"
        ):
            raise ValidationError("Development task has invalid output-root metadata")
    else:
        validate_identifier(manifest.get("game_id"), "game id")
        if manifest.get("experiment_id") is not None:
            raise ValidationError("Workspace task cannot contain an experiment id")
        if not isinstance(manifest.get("workspace_id"), str) or not manifest["workspace_id"].strip():
            raise ValidationError("Workspace task requires a workspace_id")
        if manifest.get("output_root_kind") not in {"workspace", "external"}:
            raise ValidationError("Workspace task has an invalid output_root_kind")
        if manifest.get("output_root_source") not in {
            "workspace-internal", "workspace-preference", "profile", "explicit",
        }:
            raise ValidationError("Workspace task has an invalid output_root_source")
    if not isinstance(manifest.get("created_utc"), str) or not manifest["created_utc"]:
        raise ValidationError("Output task created_utc must be a nonempty string")
    reservations = manifest.get("reservations")
    if not isinstance(reservations, list):
        raise ValidationError("Output task reservations must be a list")
    if len(reservations) != len(set(reservations)):
        raise ValidationError("Output task reservations must not contain duplicates")
    for reservation in reservations:
        _validate_artifact_path(reservation)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise ValidationError("Output task artifacts must be a list")
    if len(artifacts) != len(set(artifacts)):
        raise ValidationError("Output task artifacts must not contain duplicates")
    for artifact in artifacts:
        _validate_artifact_path(artifact)
    if set(reservations).intersection(artifacts):
        raise ValidationError("Reserved and registered artifact paths must not overlap")
    if manifest.get("status") not in TASK_STATUSES:
        raise ValidationError("Invalid output task status")
    review = manifest.get("review")
    if manifest["status"] in {"accepted", "rejected"}:
        if not isinstance(review, dict) or set(review) != {
            "decision", "summary", "evidence", "reviewed_utc",
        }:
            raise ValidationError("Accepted/rejected tasks require the official review contract")
        if review["decision"] != manifest["status"]:
            raise ValidationError("Task review decision must match task status")
        _nonempty_text(review["summary"], "review summary")
        if (
            not isinstance(review["evidence"], list)
            or not review["evidence"]
            or any(value not in artifacts for value in review["evidence"])
        ):
            raise ValidationError("Review evidence must name registered task artifacts")
        if not isinstance(review["reviewed_utc"], str) or not review["reviewed_utc"]:
            raise ValidationError("Task review requires reviewed_utc")
    elif review is not None:
        raise ValidationError("In-progress/complete tasks must not carry an acceptance review")


def validate_output_task(
    path: Path,
    catalog_root: Path | None = None,
    *,
    workspace: Path | None = None,
) -> dict[str, Any]:
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
        if manifest["output_root_kind"] == "workspace":
            if len(path.parents) < 5 or path.parents[3].name != "outputs":
                raise ValidationError("Workspace-internal task is not under the fixed outputs directory")
            inferred_workspace = path.parents[4]
            if workspace is not None and workspace.expanduser().absolute() != inferred_workspace:
                raise ValidationError("Explicit Workspace does not own this internal output task")
            workspace = inferred_workspace
        elif workspace is None:
            raise ValidationError("External output validation requires the owning Workspace path")
        workspace = workspace.expanduser().absolute()
        validate_workspace(workspace)
        marker = read_json_object(workspace / "config" / "workspace.json")
        if marker["workspace_id"] != manifest["workspace_id"]:
            raise ValidationError("Output task belongs to a different Workspace")
        read_profile(workspace, manifest["game_id"])
    return manifest


def continue_output_task(
    path: Path,
    catalog_root: Path | None = None,
    *,
    workspace: Path | None = None,
) -> dict[str, Any]:
    manifest = validate_output_path(path, catalog_root, workspace=workspace)
    if manifest.get("schema") != TASK_SCHEMA:
        raise SafetyError("Legacy output manifests are read-only; allocate a new numbered task")
    if manifest["status"] != "in-progress":
        raise SafetyError("Completed, accepted, or rejected work requires a new numbered task")
    task = path.expanduser().absolute()
    for relative in manifest["artifacts"]:
        artifact = task / PurePosixPath(relative)
        _assert_within(artifact, task, "Artifact path")
        if is_link(artifact) or not artifact.exists():
            raise ValidationError(f"Cannot continue because a recorded artifact is missing or linked: {relative}")
    return {"status": "continued", "task": str(task), "manifest": manifest}


@contextmanager
def _manifest_update_lock(task: Path) -> Iterable[None]:
    lock = task / ".gameassetai-manifest.lock"
    descriptor: int | None = None
    for _ in range(200):
        try:
            descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
            except BaseException:
                os.close(descriptor)
                descriptor = None
                lock.unlink(missing_ok=True)
                raise
            break
        except FileExistsError:
            time.sleep(0.01)
    if descriptor is None:
        raise SafetyError(f"Output task manifest is busy: {task}")
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def plan_artifact_path(
    path: Path,
    *,
    kind: str,
    filename: str,
    workspace: Path | None = None,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    if kind not in ARTIFACT_KINDS:
        raise ValidationError(f"Artifact kind must be one of {', '.join(sorted(ARTIFACT_KINDS))}")
    directory, _ = ARTIFACT_KINDS[kind]
    filename = _validate_artifact_filename(filename, expected_directory=directory)
    task = path.expanduser().absolute()
    validate_output_task(task, catalog_root, workspace=workspace)
    created: list[Path] = []
    with _manifest_update_lock(task):
        manifest = validate_output_task(task, catalog_root, workspace=workspace)
        if manifest["status"] != "in-progress":
            raise SafetyError("Artifact paths can be planned only for an in-progress task")
        artifact_directory, created = _ensure_real_directories(task, (directory,))
        artifact = artifact_directory / filename
        _assert_within(artifact, task, "Artifact path")
        reject_linked_components(artifact, stop=task)
        if artifact.exists() or is_link(artifact):
            raise SafetyError(f"Refusing to overwrite an existing artifact: {artifact}")
        relative = artifact.relative_to(task).as_posix()
        if relative in manifest["artifacts"]:
            raise SafetyError(f"Artifact path is already registered: {relative}")
        if relative in manifest["reservations"]:
            raise SafetyError(f"Artifact path is already reserved: {relative}")
        manifest["reservations"].append(relative)
        try:
            _validate_task_manifest(manifest)
            atomic_write_json(task / "manifest.json", manifest, replace=True)
        except BaseException:
            _cleanup_empty(created)
            raise
    return {
        "status": "planned",
        "task": str(task),
        "kind": kind,
        "artifact": str(artifact),
        "relative_path": relative,
    }


def register_output_artifact(
    path: Path,
    artifact: Path,
    *,
    workspace: Path | None = None,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    task = path.expanduser().absolute()
    validate_output_task(task, catalog_root, workspace=workspace)
    with _manifest_update_lock(task):
        manifest = validate_output_task(task, catalog_root, workspace=workspace)
        if manifest["status"] != "in-progress":
            raise SafetyError("Artifacts can be registered only while a task is in progress")
        candidate = artifact.expanduser()
        candidate = candidate if candidate.is_absolute() else task / candidate
        candidate = candidate.absolute()
        _assert_within(candidate, task, "Artifact path")
        reject_linked_components(candidate, stop=task)
        if is_link(candidate) or not candidate.is_file():
            raise ValidationError(f"Registered artifact must be an existing real file: {candidate}")
        if candidate.stat().st_size <= 0:
            raise ValidationError(f"Registered artifact must not be empty: {candidate}")
        relative = candidate.relative_to(task).as_posix()
        _validate_artifact_path(relative)
        if relative in manifest["artifacts"]:
            raise SafetyError(f"Artifact is already registered: {relative}")
        if relative not in manifest["reservations"]:
            raise SafetyError(f"Artifact path was not reserved through the Runtime: {relative}")
        manifest["reservations"].remove(relative)
        manifest["artifacts"].append(relative)
        _validate_task_manifest(manifest)
        atomic_write_json(task / "manifest.json", manifest, replace=True)
    return {
        "status": "registered",
        "task": str(task),
        "artifact": relative,
        "artifacts": list(manifest["artifacts"]),
    }


def release_artifact_reservation(
    path: Path,
    reservation: str,
    *,
    workspace: Path | None = None,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    relative = _validate_artifact_path(reservation)
    task = path.expanduser().absolute()
    validate_output_task(task, catalog_root, workspace=workspace)
    with _manifest_update_lock(task):
        manifest = validate_output_task(task, catalog_root, workspace=workspace)
        if manifest["status"] != "in-progress":
            raise SafetyError("Reservations can be released only while a task is in progress")
        if relative not in manifest["reservations"]:
            raise SafetyError(f"Artifact path is not reserved: {relative}")
        artifact = task / PurePosixPath(relative)
        _assert_within(artifact, task, "Artifact path")
        reject_linked_components(artifact, stop=task)
        if artifact.exists() or is_link(artifact):
            raise SafetyError(
                "A published artifact exists at the reserved path; register it instead of "
                f"releasing the reservation: {relative}"
            )
        manifest["reservations"].remove(relative)
        _validate_task_manifest(manifest)
        atomic_write_json(task / "manifest.json", manifest, replace=True)
    directory = artifact.parent
    if directory.parent == task and directory.is_dir() and not is_link(directory):
        try:
            directory.rmdir()
        except OSError:
            pass
    return {
        "status": "released",
        "task": str(task),
        "artifact": relative,
        "reservations": list(manifest["reservations"]),
    }


def update_output_task_status(
    path: Path,
    status: str,
    *,
    review_summary: str | None = None,
    review_evidence: list[str] | None = None,
    workspace: Path | None = None,
    catalog_root: Path | None = None,
) -> dict[str, Any]:
    if status not in TASK_STATUSES:
        raise ValidationError(f"Task status must be one of {', '.join(sorted(TASK_STATUSES))}")
    task = path.expanduser().absolute()
    validate_output_task(task, catalog_root, workspace=workspace)
    with _manifest_update_lock(task):
        manifest = validate_output_task(task, catalog_root, workspace=workspace)
        current = manifest["status"]
        if status not in TASK_TRANSITIONS[current]:
            raise SafetyError(f"Task status cannot transition from {current} to {status}")
        if manifest["reservations"]:
            raise SafetyError("Task status cannot change while artifact reservations remain")
        if status in {"accepted", "rejected"}:
            summary = _nonempty_text(review_summary, "review summary")
            evidence = _validate_review_evidence_files(
                task, list(review_evidence or []), manifest["artifacts"],
            )
            manifest["review"] = {
                "decision": status,
                "summary": summary,
                "evidence": evidence,
                "reviewed_utc": _utc_now(),
            }
        elif review_summary is not None or review_evidence:
            raise ValidationError("Complete status does not accept quality-review evidence")
        manifest["status"] = status
        _validate_task_manifest(manifest)
        atomic_write_json(task / "manifest.json", manifest, replace=True)
    return {
        "status": "updated",
        "task": str(task),
        "previous": current,
        "task_status": status,
        "review": manifest["review"],
    }


def _validate_legacy_output_task(path: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema", "storage", "task_id", "task_number", "purpose", "experiment_id", "game_id",
        "asset_category", "asset_id", "created_utc", "artifacts", "status", "review",
    }
    if set(manifest) != required or manifest.get("schema") != LEGACY_TASK_SCHEMA:
        raise ValidationError("Invalid legacy output task contract")
    number = manifest.get("task_number")
    purpose = _descriptive_identifier(
        manifest.get("purpose"), "task purpose", GENERIC_TASK_PURPOSES,
    )
    if (
        not isinstance(number, int)
        or isinstance(number, bool)
        or number < 1
        or manifest.get("task_id") != f"{number:03d}-{purpose}"
        or path.name != manifest.get("task_id")
    ):
        raise ValidationError("Invalid legacy output task identity")
    if manifest.get("storage") not in {"development", "workspace"}:
        raise ValidationError("Invalid legacy output task storage")
    validate_identifier(manifest.get("asset_category"), "asset category")
    _descriptive_identifier(manifest.get("asset_id"), "asset id", set())
    if path.parent.name != manifest["asset_id"] or path.parent.parent.name != manifest["asset_category"]:
        raise ValidationError("Legacy output task path does not match its asset identity")
    if manifest["storage"] == "development":
        owner = _descriptive_identifier(
            manifest.get("experiment_id"), "experiment id", GENERIC_EXPERIMENT_IDS,
        )
        if manifest.get("game_id") is not None:
            raise ValidationError("Legacy development task cannot contain a game id")
    else:
        owner = validate_identifier(manifest.get("game_id"), "game id")
        if manifest.get("experiment_id") is not None:
            raise ValidationError("Legacy Workspace task cannot contain an experiment id")
    if path.parent.parent.parent.name != owner:
        raise ValidationError("Legacy output task owner directory does not match its manifest")
    if not isinstance(manifest.get("artifacts"), list) or manifest.get("status") not in TASK_STATUSES:
        raise ValidationError("Invalid legacy output task artifacts/status")
    for artifact in manifest["artifacts"]:
        if not isinstance(artifact, str) or not artifact or "\\" in artifact:
            raise ValidationError("Invalid legacy artifact path")
        relative = PurePosixPath(artifact)
        if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
            raise ValidationError("Legacy artifact path escapes its task")
    return manifest


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


def validate_output_path(
    path: Path,
    catalog_root: Path | None = None,
    *,
    workspace: Path | None = None,
) -> dict[str, Any]:
    path = path.expanduser().absolute()
    reject_linked_components(path)
    if is_link(path) or not path.is_dir():
        raise ValidationError(f"Output path must be a real directory: {path}")
    manifest_path = path / "manifest.json"
    if is_link(manifest_path) or not manifest_path.is_file():
        raise ValidationError("Output path is missing a real manifest.json")
    manifest = read_json_object(manifest_path)
    if manifest.get("schema") == TASK_SCHEMA:
        return validate_output_task(path, catalog_root, workspace=workspace)
    if manifest.get("schema") == LEGACY_TASK_SCHEMA:
        return _validate_legacy_output_task(path, manifest)
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
