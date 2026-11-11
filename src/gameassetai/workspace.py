from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any
import uuid

from .catalog import validate_style_ids
from .errors import SafetyError, ValidationError
from .filesystem import (
    atomic_write_json,
    is_link,
    read_json_object,
    reject_linked_components,
    require_absolute_path,
    validate_identifier,
)


WORKSPACE_SCHEMA = "gameassetai.workspace.v2"
ACTIVE_PROFILE_SCHEMA = "gameassetai.active-profile.v1"
PROJECTS_SCHEMA = "gameassetai.projects.v1"
SETTINGS_SCHEMA = "gameassetai.settings.v1"
PROFILE_SCHEMA = "gameassetai.profile.v1"
REQUIRED_FILES = (
    "AGENTS.md",
    "config/workspace.json",
    "config/active-profile.json",
    "config/projects.json",
    "config/settings.json",
)
REQUIRED_DIRS = ("config", "profiles")
SAFE_ADDITIVE_TEMPLATE_FILES = ("README.md", "profiles/README.md", "notes/README.md")
CLONE_INITIALIZATION_FILES = (
    "config/active-profile.json",
    "config/projects.json",
    "config/settings.json",
    "profiles/_template.json",
    "profiles/README.md",
)
PROFILE_SETTING_SEGMENT = re.compile(r"[a-z][a-z0-9_-]*\Z")
PROFILE_MUTABLE_OBJECTS = {
    "styles", "art_direction", "asset_defaults", "rig_animation", "output_defaults",
}
PROFILE_MUTABLE_SCALARS = {"name", "description"}


def default_template_root() -> Path:
    from importlib import resources

    path = Path(str(resources.files("gameassetai").joinpath("data", "workspace-template")))
    if not path.is_dir():
        raise ValidationError("No packaged Workspace template is available; pass --template")
    return path


def _real_file(root: Path, relative: str) -> Path:
    path = root / relative
    if is_link(path) or not path.is_file():
        raise ValidationError(f"Missing or linked Workspace file: {relative}")
    if not path.read_text(encoding="utf-8-sig").strip():
        raise ValidationError(f"Empty Workspace file: {relative}")
    return path


def _validate_profile_document(profile: dict[str, Any], expected_id: str | None = None) -> None:
    required = {
        "schema", "id", "name", "description", "styles", "art_direction",
        "asset_defaults", "rig_animation", "output_defaults", "metadata",
    }
    if set(profile) != required or profile.get("schema") != PROFILE_SCHEMA:
        raise ValidationError("Profile fields or schema are invalid")
    identifier = validate_identifier(profile.get("id"), "profile id")
    if expected_id is not None and identifier != expected_id:
        raise ValidationError("Profile filename and id do not match")
    for field in ("name", "description"):
        if not isinstance(profile[field], str) or not profile[field].strip():
            raise ValidationError(f"Profile {field} must be nonempty")
    styles = profile["styles"]
    if not isinstance(styles, dict) or set(styles) != {"three_d", "two_d"}:
        raise ValidationError("Profile styles must contain three_d and two_d")
    validate_style_ids(styles["three_d"], styles["two_d"], label="Profile styles")
    for field in ("art_direction", "asset_defaults", "rig_animation", "output_defaults", "metadata"):
        if not isinstance(profile[field], dict):
            raise ValidationError(f"Profile {field} must be an object")
    output_root = profile["output_defaults"].get("root")
    if output_root is not None:
        require_absolute_path(output_root, "Profile output_defaults.root")


def validate_workspace(root: Path, *, require_profile: bool = False) -> dict[str, Any]:
    root = root.expanduser().absolute()
    reject_linked_components(root)
    if is_link(root) or not root.is_dir():
        raise ValidationError(f"Workspace must be a real directory: {root}")
    for relative in REQUIRED_DIRS:
        path = root / relative
        if is_link(path) or not path.is_dir():
            raise ValidationError(f"Missing or linked Workspace directory: {relative}")
    for relative in REQUIRED_FILES:
        _real_file(root, relative)

    marker = read_json_object(root / "config" / "workspace.json")
    if marker.get("schema") != WORKSPACE_SCHEMA:
        raise ValidationError("Unsupported Workspace schema")
    if not isinstance(marker.get("workspace_id"), str) or not marker["workspace_id"].strip():
        raise ValidationError("Workspace marker requires workspace_id")

    active = read_json_object(root / "config" / "active-profile.json")
    if set(active) != {"schema", "profile"} or active.get("schema") != ACTIVE_PROFILE_SCHEMA:
        raise ValidationError("Invalid active-profile.json contract")
    profile_id = active["profile"]
    if profile_id is None:
        if require_profile:
            raise ValidationError("No active Profile is selected")
    else:
        validate_identifier(profile_id, "active profile")
        profile_path = root / "profiles" / f"{profile_id}.json"
        if is_link(profile_path) or not profile_path.is_file():
            raise ValidationError(f"Active Profile is missing or linked: {profile_path.name}")
    for profile_path in sorted((root / "profiles").glob("*.json")):
        if is_link(profile_path) or not profile_path.is_file():
            raise ValidationError(f"Profile must be a real JSON file: {profile_path.name}")
        expected_id = None if profile_path.name.startswith("_") else profile_path.stem
        _validate_profile_document(read_json_object(profile_path), expected_id)

    projects = read_json_object(root / "config" / "projects.json")
    if set(projects) != {"schema", "games"} or projects.get("schema") != PROJECTS_SCHEMA:
        raise ValidationError("Invalid projects.json contract")
    if not isinstance(projects["games"], dict):
        raise ValidationError("projects.json games must be an object")
    for game, entry in projects["games"].items():
        validate_identifier(game, "project game id")
        if not isinstance(entry, dict) or set(entry) != {"paths"} or not isinstance(entry["paths"], dict):
            raise ValidationError(f"Project mapping {game} must contain a paths object")
        for label, value in entry["paths"].items():
            validate_identifier(label, f"project path label for {game}")
            require_absolute_path(value, f"projects.{game}.paths.{label}")

    settings = read_json_object(root / "config" / "settings.json")
    if set(settings) != {"schema", "preferences"} or settings.get("schema") != SETTINGS_SCHEMA:
        raise ValidationError("Invalid settings.json contract")
    if not isinstance(settings["preferences"], dict):
        raise ValidationError("settings.json preferences must be an object")
    output_root = settings["preferences"].get("output_root")
    if output_root is not None:
        require_absolute_path(output_root, "settings.preferences.output_root")

    return {
        "status": "valid",
        "workspace": str(root),
        "active_profile": profile_id,
        "outputs_present": (root / "outputs").is_dir() and not is_link(root / "outputs"),
    }


def detect_legacy_workspace(root: Path) -> bool:
    root = root.expanduser().absolute()
    required = (
        root / "AGENTS.md", root / "profiles", root / "config" / "active-profile.json",
        root / "config" / "projects.json",
    )
    return root.is_dir() and not is_link(root) and all(path.exists() and not is_link(path) for path in required)


def _template_files(template: Path) -> list[Path]:
    validate_workspace(template)
    files: list[Path] = []
    for path in sorted(template.rglob("*")):
        if is_link(path):
            raise SafetyError(f"Linked Workspace template component: {path}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            raise SafetyError(f"Unsupported Workspace template component: {path}")
    return files


def create_or_connect_workspace(template: Path | None, target: Path) -> dict[str, Any]:
    template = (template or default_template_root()).expanduser().resolve()
    target = target.expanduser().absolute()
    reject_linked_components(target.parent)
    resolved_target = target.resolve()
    if resolved_target == template or resolved_target in template.parents or template in resolved_target.parents:
        raise SafetyError("Workspace and template must not overlap")

    if target.exists() and any(target.iterdir()):
        try:
            report = validate_workspace(target)
        except ValidationError:
            if detect_legacy_workspace(target):
                return {
                    "status": "legacy-connected",
                    "workspace": str(target),
                    "migration_required": True,
                    "changed": [],
                }
            raise SafetyError("Existing nonempty directory is not a recognized Workspace")
        return {**report, "status": "connected", "changed": []}
    if target.exists() and not target.is_dir():
        raise SafetyError(f"Workspace target is not a directory: {target}")

    sources = _template_files(template)
    created_files: list[Path] = []
    created_dirs: list[Path] = []
    if not target.exists():
        target.mkdir(parents=True)
        created_dirs.append(target)
    try:
        for source in sources:
            relative = source.relative_to(template)
            destination = target / relative
            missing: list[Path] = []
            parent = destination.parent
            while parent != target and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            with destination.open("xb") as output:
                created_files.append(destination)
                output.write(source.read_bytes())
        atomic_write_json(
            target / "config" / "workspace.json",
            {"schema": WORKSPACE_SCHEMA, "workspace_id": f"workspace-{uuid.uuid4().hex}"},
            replace=True,
        )
        report = validate_workspace(target)
    except BaseException:
        for path in reversed(created_files):
            if path.is_file() and not is_link(path):
                path.unlink()
        for path in reversed(created_dirs):
            if path.is_dir() and not is_link(path):
                path.rmdir()
        raise
    return {**report, "status": "created", "changed": [str(p.relative_to(target)) for p in created_files]}


def initialize_distribution_workspace(root: Path) -> dict[str, Any]:
    """Initialize personal state only inside a verified ``dist/workspace`` clone."""
    from .distribution import validate_workspace_distribution

    root = root.expanduser().absolute()
    validate_workspace_distribution(root)
    git_marker = root / ".git"
    if is_link(git_marker) or not (git_marker.is_dir() or git_marker.is_file()):
        raise ValidationError(
            "workspace init-clone requires a real Git clone of the Workspace distribution"
        )
    try:
        git_check = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise ValidationError(f"workspace init-clone requires Git: {exc}") from exc
    if git_check.returncode != 0 or git_check.stdout.strip() != "true":
        raise ValidationError(
            "workspace init-clone requires a valid Git worktree for the Workspace distribution"
        )
    try:
        report = validate_workspace(root)
    except ValidationError:
        report = None
    if report is not None:
        return {**report, "status": "already-initialized", "changed": []}

    template = root / "templates" / "workspace"
    marker = root / "config" / "workspace.json"
    if is_link(marker) or (marker.exists() and not marker.is_file()):
        raise SafetyError(f"Workspace marker must be a real file: {marker}")
    marker_document = (
        read_json_object(marker)
        if marker.exists()
        else {"schema": WORKSPACE_SCHEMA, "workspace_id": f"workspace-{uuid.uuid4().hex}"}
    )

    candidate_parent = root.parent
    reject_linked_components(candidate_parent)
    with tempfile.TemporaryDirectory(
        prefix=".gameassetai-clone-init-", dir=candidate_parent,
    ) as temporary:
        candidate = Path(temporary)
        shutil.copy2(root / "AGENTS.md", candidate / "AGENTS.md")
        for directory_name in ("config", "profiles"):
            source_directory = root / directory_name
            candidate_directory = candidate / directory_name
            candidate_directory.mkdir()
            if not source_directory.exists() and not is_link(source_directory):
                continue
            if is_link(source_directory) or not source_directory.is_dir():
                raise SafetyError(
                    f"Personal Workspace path must be a real directory: {source_directory}"
                )
            for source in sorted(source_directory.rglob("*")):
                if is_link(source):
                    raise SafetyError(f"Linked personal Workspace component: {source}")
                relative = source.relative_to(source_directory)
                destination = candidate_directory / relative
                if source.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                elif source.is_file():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
                else:
                    raise SafetyError(f"Unsupported personal Workspace component: {source}")
        for relative in CLONE_INITIALIZATION_FILES:
            destination = candidate / relative
            if destination.exists() or is_link(destination):
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(template / relative, destination)
        atomic_write_json(candidate / "config" / "workspace.json", marker_document, replace=True)
        validate_workspace(candidate)

    created_files: list[Path] = []
    created_dirs: list[Path] = []
    try:
        for relative in CLONE_INITIALIZATION_FILES:
            destination = root / relative
            if destination.exists() or is_link(destination):
                continue
            missing: list[Path] = []
            parent = destination.parent
            while parent != root and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                reject_linked_components(directory.parent, stop=root)
                directory.mkdir()
                if is_link(directory) or not directory.is_dir():
                    raise SafetyError(
                        f"Personal Workspace directory was replaced during creation: {directory}"
                    )
                created_dirs.append(directory)
            reject_linked_components(destination.parent, stop=root)
            with destination.open("xb") as output:
                output.write((template / relative).read_bytes())
            created_files.append(destination)
        if not marker.exists() and not is_link(marker):
            reject_linked_components(marker.parent, stop=root)
            marker.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(marker, marker_document, replace=False)
            created_files.append(marker)
        final = validate_workspace(root)
    except BaseException:
        for path in reversed(created_files):
            if path.is_file() and not is_link(path):
                path.unlink()
        for path in reversed(created_dirs):
            if path.is_dir() and not is_link(path):
                try:
                    path.rmdir()
                except OSError:
                    pass
        raise
    return {
        **final,
        "status": "initialized",
        "changed": [str(path.relative_to(root)) for path in created_files],
    }


def update_workspace(template: Path | None, target: Path) -> dict[str, Any]:
    template = (template or default_template_root()).expanduser().resolve()
    target = target.expanduser().absolute()
    validate_workspace(template)
    validate_workspace(target)
    added: list[str] = []
    for relative in SAFE_ADDITIVE_TEMPLATE_FILES:
        source = template / relative
        destination = target / relative
        if destination.exists() or is_link(destination):
            continue
        reject_linked_components(destination.parent, stop=target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        reject_linked_components(destination.parent, stop=target)
        with destination.open("xb") as output:
            output.write(source.read_bytes())
        added.append(relative)
    return {"status": "updated" if added else "already-current", "workspace": str(target), "added": added}


def create_profile(
    workspace: Path, profile_id: str, name: str, description: str,
    *, three_d_style: str | None = None, two_d_styles: list[str] | None = None,
) -> dict[str, Any]:
    workspace = workspace.expanduser().absolute()
    validate_workspace(workspace)
    profile_id = validate_identifier(profile_id, "profile id")
    if not name.strip() or not description.strip():
        raise ValidationError("Profile name and description must be nonempty")
    document = {
        "schema": PROFILE_SCHEMA,
        "id": profile_id,
        "name": name.strip(),
        "description": description.strip(),
        "styles": {"three_d": three_d_style, "two_d": list(two_d_styles or [])},
        "art_direction": {"rules": [], "palette": []},
        "asset_defaults": {},
        "rig_animation": {},
        "output_defaults": {"formats": ["blend"]},
        "metadata": {"created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat()},
    }
    _validate_profile_document(document, profile_id)
    path = workspace / "profiles" / f"{profile_id}.json"
    atomic_write_json(path, document, replace=False)
    return {"status": "created", "profile": profile_id, "path": str(path)}


def _profile_path(workspace: Path, profile_id: str | None) -> tuple[str, Path]:
    workspace = workspace.expanduser().absolute()
    report = validate_workspace(workspace)
    identifier = profile_id if profile_id is not None else report["active_profile"]
    if identifier is None:
        raise ValidationError("No active Profile is selected; pass an explicit profile id")
    identifier = validate_identifier(identifier, "profile id")
    path = workspace / "profiles" / f"{identifier}.json"
    if is_link(path) or not path.is_file():
        raise ValidationError(f"Profile does not exist or is linked: {identifier}")
    return identifier, path


def read_profile(workspace: Path, profile_id: str | None = None) -> dict[str, Any]:
    identifier, path = _profile_path(workspace, profile_id)
    document = read_json_object(path)
    _validate_profile_document(document, identifier)
    return document


def _profile_setting_parts(setting: str, *, for_update: bool) -> list[str]:
    if not isinstance(setting, str) or not setting.strip() or setting != setting.strip():
        raise ValidationError("Profile setting must be a nonempty dot-separated path")
    parts = setting.split(".")
    if any(not PROFILE_SETTING_SEGMENT.fullmatch(part) for part in parts):
        raise ValidationError(f"Invalid Profile setting path: {setting!r}")
    if for_update:
        root = parts[0]
        if root in PROFILE_MUTABLE_SCALARS:
            if len(parts) != 1:
                raise ValidationError(f"Profile scalar {root} does not have child settings")
        elif root in PROFILE_MUTABLE_OBJECTS:
            if len(parts) < 2:
                raise ValidationError(f"Update a specific child setting under {root}")
        else:
            raise ValidationError(f"Profile setting is read-only or unknown: {root}")
    return parts


def read_profile_setting(
    workspace: Path, setting: str, *, profile_id: str | None = None,
) -> dict[str, Any]:
    identifier, _ = _profile_path(workspace, profile_id)
    value: Any = read_profile(workspace, identifier)
    for part in _profile_setting_parts(setting, for_update=False):
        if not isinstance(value, dict) or part not in value:
            raise ValidationError(f"Profile setting does not exist: {setting}")
        value = value[part]
    return {"profile": identifier, "setting": setting, "value": deepcopy(value)}


def update_profile_setting(
    workspace: Path,
    setting: str,
    value: Any,
    *,
    profile_id: str | None = None,
) -> dict[str, Any]:
    identifier, path = _profile_path(workspace, profile_id)
    current = read_profile(workspace, identifier)
    candidate = deepcopy(current)
    parts = _profile_setting_parts(setting, for_update=True)
    parent: dict[str, Any] = candidate
    for part in parts[:-1]:
        child = parent.get(part)
        if child is None:
            child = {}
            parent[part] = child
        if not isinstance(child, dict):
            raise ValidationError(f"Profile setting parent is not an object: {part}")
        parent = child
    leaf = parts[-1]
    previous = deepcopy(parent.get(leaf)) if leaf in parent else None
    existed = leaf in parent
    parent[leaf] = deepcopy(value)
    candidate["metadata"]["updated_utc"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    _validate_profile_document(candidate, identifier)
    if is_link(path):
        raise SafetyError(f"Refusing to replace linked Profile: {path}")
    atomic_write_json(path, candidate, replace=True)
    persisted = read_json_object(path)
    _validate_profile_document(persisted, identifier)
    return {
        "status": "updated",
        "profile": identifier,
        "setting": setting,
        "previous_exists": existed,
        "previous": previous,
        "value": deepcopy(value),
    }


def select_profile(workspace: Path, profile_id: str | None) -> dict[str, Any]:
    workspace = workspace.expanduser().absolute()
    validate_workspace(workspace)
    if profile_id is not None:
        profile_id = validate_identifier(profile_id, "profile id")
        path = workspace / "profiles" / f"{profile_id}.json"
        if is_link(path) or not path.is_file():
            raise ValidationError(f"Profile does not exist: {profile_id}")
        _validate_profile_document(read_json_object(path), profile_id)
    active = {"schema": ACTIVE_PROFILE_SCHEMA, "profile": profile_id}
    atomic_write_json(workspace / "config" / "active-profile.json", active, replace=True)
    validate_workspace(workspace, require_profile=profile_id is not None)
    return {"status": "selected" if profile_id else "cleared", "profile": profile_id}


def list_profiles(workspace: Path) -> list[dict[str, Any]]:
    workspace = workspace.expanduser().absolute()
    report = validate_workspace(workspace)
    result = []
    for path in sorted((workspace / "profiles").glob("*.json")):
        if path.name.startswith("_") or is_link(path):
            continue
        profile = read_json_object(path)
        _validate_profile_document(profile, path.stem)
        result.append({"id": path.stem, "name": profile["name"], "active": path.stem == report["active_profile"]})
    return result


def read_active_profile(workspace: Path) -> dict[str, Any] | None:
    workspace = workspace.expanduser().absolute()
    report = validate_workspace(workspace)
    identifier = report["active_profile"]
    if identifier is None:
        return None
    return read_json_object(workspace / "profiles" / f"{identifier}.json")


def _validate_selected_output_root(workspace: Path, value: str, label: str) -> Path:
    require_absolute_path(value, label)
    selected = Path(value).expanduser().absolute()
    reject_linked_components(selected)
    if is_link(selected) or not selected.is_dir():
        raise ValidationError(f"{label} must be an existing real directory: {selected}")
    resolved_workspace = workspace.resolve(strict=True)
    resolved_selected = selected.resolve(strict=True)
    internal = (workspace / "outputs").resolve(strict=False)
    if resolved_selected != internal:
        try:
            resolved_selected.relative_to(resolved_workspace)
        except ValueError:
            pass
        else:
            raise SafetyError(
                "An output root inside the Workspace must be exactly the disposable outputs directory"
            )
    return selected


def read_workspace_output_root(workspace: Path) -> dict[str, Any]:
    workspace = workspace.expanduser().absolute()
    report = validate_workspace(workspace)
    settings = read_json_object(workspace / "config" / "settings.json")
    workspace_value = settings["preferences"].get("output_root")
    profile_value = None
    if report["active_profile"] is not None:
        profile_value = read_profile(workspace, report["active_profile"])["output_defaults"].get("root")
    if profile_value is not None:
        effective, source = profile_value, "profile"
    elif workspace_value is not None:
        effective, source = workspace_value, "workspace-preference"
    else:
        effective, source = str(workspace / "outputs"), "workspace-internal"
    return {
        "workspace": str(workspace),
        "active_profile": report["active_profile"],
        "workspace_preference": workspace_value,
        "profile_override": profile_value,
        "effective": effective,
        "source": source,
    }


def set_workspace_output_root(workspace: Path, value: str | None) -> dict[str, Any]:
    workspace = workspace.expanduser().absolute()
    validate_workspace(workspace)
    settings_path = workspace / "config" / "settings.json"
    if is_link(settings_path):
        raise SafetyError(f"Refusing to replace linked Workspace settings: {settings_path}")
    settings = read_json_object(settings_path)
    previous = settings["preferences"].get("output_root")
    if value is None:
        settings["preferences"].pop("output_root", None)
        normalized = None
    else:
        normalized = str(_validate_selected_output_root(
            workspace, value, "Workspace output root",
        ))
        settings["preferences"]["output_root"] = normalized
    atomic_write_json(settings_path, settings, replace=True)
    validate_workspace(workspace)
    return {
        "status": "updated",
        "workspace": str(workspace),
        "previous": previous,
        "output_root": normalized,
    }


def resolve_workspace_output_root(
    workspace: Path,
    *,
    explicit_output_root: Path | None = None,
    profile_id: str | None = None,
) -> dict[str, Any]:
    workspace = workspace.expanduser().absolute()
    report = validate_workspace(workspace, require_profile=True)
    selected_profile = profile_id or report["active_profile"]
    if selected_profile != report["active_profile"]:
        raise ValidationError("Output Profile must match the active Profile")
    profile = read_profile(workspace, selected_profile)
    settings = read_json_object(workspace / "config" / "settings.json")
    if explicit_output_root is not None:
        raw_value = str(explicit_output_root)
        source = "explicit"
    elif profile["output_defaults"].get("root") is not None:
        raw_value = profile["output_defaults"]["root"]
        source = "profile"
    elif settings["preferences"].get("output_root") is not None:
        raw_value = settings["preferences"]["output_root"]
        source = "workspace-preference"
    else:
        marker = read_json_object(workspace / "config" / "workspace.json")
        return {
            "root": workspace / "outputs",
            "source": "workspace-internal",
            "kind": "workspace",
            "workspace_id": marker["workspace_id"],
        }
    selected = _validate_selected_output_root(workspace, raw_value, f"{source} output root")
    marker = read_json_object(workspace / "config" / "workspace.json")
    return {
        "root": selected,
        "source": source,
        "kind": "workspace" if selected.resolve() == (workspace / "outputs").resolve(strict=False) else "external",
        "workspace_id": marker["workspace_id"],
    }
