from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any
import uuid

from .errors import SafetyError, ValidationError
from .filesystem import (
    atomic_write_json,
    is_link,
    read_json_object,
    reject_linked_components,
    require_absolute_path,
    validate_identifier,
)
from .workspace import validate_workspace


LOCATION_SCHEMA = "gameassetai.external-tools-location.v1"
REPOSITORY_SCHEMA = "gameassetai.tools-repository.v1"
TOOL_SCHEMA = "gameassetai.external-tool.v1"
STATUS_SCHEMA = "gameassetai.external-tool-status.v1"
LOCATION_PATH = Path(".local") / "external-tools.json"
REPOSITORY_MARKER = ".gameassetai-tools.json"
TOOLS_DIRECTORY = "tools"
DEFAULT_TOOLS_DIRECTORY = "GameAssetAI-Tools"

TOOL_KINDS = {
    "blender-addon",
    "mcp-server",
    "git-project",
    "python-package",
    "ai-model",
    "system-cli",
    "external-api",
    "other",
}
INSTALL_METHODS = {
    "blender-managed",
    "git-clone",
    "download",
    "python-package",
    "mcp-package",
    "system-installer",
    "existing",
    "api",
    "other",
}
INSTALLATION_STATES = {"not-checked", "found", "not-found"}
ACTIVATION_STATES = {"not-checked", "active", "inactive", "not-applicable"}
COMPATIBILITY_STATES = {"not-checked", "compatible", "incompatible"}
EXECUTION_STATES = {"not-tested", "passed", "failed"}
FUNCTIONALITY_STATES = {"not-tested", "passed", "failed"}
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _validate_timestamp(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{label} must be a timezone-aware ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{label} must be a timezone-aware ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValidationError(f"{label} must include a timezone")
    return value


def _text(value: object, label: str, *, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or CONTROL_CHARACTERS.search(value)
    ):
        raise ValidationError(
            f"{label} must be a nonempty trimmed string of at most {maximum} characters"
        )
    return value


def _optional_text(value: object, label: str, *, maximum: int) -> str | None:
    if value is None:
        return None
    return _text(value, label, maximum=maximum)


def _metadata_path(value: object, label: str) -> str | None:
    if value is None:
        return None
    normalized = require_absolute_path(value, label)
    path = Path(normalized).absolute()
    reject_linked_components(path)
    return str(path)


def _validate_tool_id(value: object) -> str:
    identifier = validate_identifier(value, "tool id")
    if len(identifier) > 80:
        raise ValidationError("tool id must be at most 80 characters")
    return identifier


def _validate_repository_marker(document: dict[str, Any], path: Path) -> dict[str, Any]:
    if set(document) != {"schema", "repository_id", "created_utc"}:
        raise ValidationError(f"Tools repository marker fields are invalid: {path}")
    if document.get("schema") != REPOSITORY_SCHEMA:
        raise ValidationError(f"Unsupported Tools repository schema: {path}")
    validate_identifier(document.get("repository_id"), "Tools repository id")
    _validate_timestamp(document.get("created_utc"), "Tools repository created_utc")
    return document


def _validate_registration(document: dict[str, Any], expected_id: str) -> dict[str, Any]:
    required = {
        "schema", "id", "name", "kind", "source", "installation", "modification",
        "capabilities", "metadata",
    }
    if set(document) != required or document.get("schema") != TOOL_SCHEMA:
        raise ValidationError(f"Tool registration fields or schema are invalid: {expected_id}")
    identifier = _validate_tool_id(document.get("id"))
    if identifier != expected_id:
        raise ValidationError("Tool directory and registered id do not match")
    _text(document.get("name"), "tool name", maximum=200)
    if document.get("kind") not in TOOL_KINDS:
        raise ValidationError(f"Unsupported tool kind: {document.get('kind')!r}")

    source = document.get("source")
    if not isinstance(source, dict) or set(source) != {"origin", "license"}:
        raise ValidationError("Tool source must contain origin and license")
    _text(source.get("origin"), "tool source origin", maximum=2048)
    _optional_text(source.get("license"), "tool source license", maximum=200)

    installation = document.get("installation")
    installation_fields = {
        "method", "location", "identifier", "version", "revision", "environment",
    }
    if not isinstance(installation, dict) or set(installation) != installation_fields:
        raise ValidationError("Tool installation contract is invalid")
    if installation.get("method") not in INSTALL_METHODS:
        raise ValidationError(f"Unsupported installation method: {installation.get('method')!r}")
    location = _metadata_path(installation.get("location"), "tool installation.location")
    external_identifier = _optional_text(
        installation.get("identifier"), "tool installation.identifier", maximum=300,
    )
    if location is None and external_identifier is None:
        raise ValidationError("Tool installation requires a location or external identifier")
    _optional_text(installation.get("version"), "tool installation.version", maximum=200)
    _optional_text(installation.get("revision"), "tool installation.revision", maximum=200)
    _metadata_path(installation.get("environment"), "tool installation.environment")

    modification = document.get("modification")
    if not isinstance(modification, dict) or set(modification) != {
        "modified", "upstream_revision", "notes",
    }:
        raise ValidationError("Tool modification contract is invalid")
    if not isinstance(modification.get("modified"), bool):
        raise ValidationError("Tool modification.modified must be a boolean")
    upstream = _optional_text(
        modification.get("upstream_revision"),
        "tool modification.upstream_revision",
        maximum=200,
    )
    if modification["modified"] and upstream is None:
        raise ValidationError("A modified tool requires its upstream revision")
    _optional_text(modification.get("notes"), "tool modification.notes", maximum=1000)

    capabilities = document.get("capabilities")
    if not isinstance(capabilities, list):
        raise ValidationError("Tool capabilities must be a list")
    if len(capabilities) > 100:
        raise ValidationError("Tool capabilities may contain at most 100 identifiers")
    normalized_capabilities = [
        validate_identifier(value, "tool capability") for value in capabilities
    ]
    if len(set(normalized_capabilities)) != len(normalized_capabilities):
        raise ValidationError("Tool capabilities must not contain duplicates")

    metadata = document.get("metadata")
    if not isinstance(metadata, dict) or set(metadata) != {"created_utc"}:
        raise ValidationError("Tool metadata must contain only created_utc")
    _validate_timestamp(metadata.get("created_utc"), "tool metadata.created_utc")
    return document


def _validate_status(document: dict[str, Any], expected_id: str) -> dict[str, Any]:
    required = {
        "schema", "tool_id", "checked_utc", "target", "installation", "activation",
        "compatibility", "execution", "functionality", "failure",
    }
    if set(document) != required or document.get("schema") != STATUS_SCHEMA:
        raise ValidationError(f"Tool status fields or schema are invalid: {expected_id}")
    if _validate_tool_id(document.get("tool_id")) != expected_id:
        raise ValidationError("Tool status id does not match its directory")
    _validate_timestamp(document.get("checked_utc"), "tool status.checked_utc")
    _text(document.get("target"), "tool status.target", maximum=500)
    if document.get("installation") not in INSTALLATION_STATES:
        raise ValidationError("Tool status.installation is invalid")
    if document.get("activation") not in ACTIVATION_STATES:
        raise ValidationError("Tool status.activation is invalid")
    if document.get("compatibility") not in COMPATIBILITY_STATES:
        raise ValidationError("Tool status.compatibility is invalid")
    if document.get("execution") not in EXECUTION_STATES:
        raise ValidationError("Tool status.execution is invalid")
    if document.get("functionality") not in FUNCTIONALITY_STATES:
        raise ValidationError("Tool status.functionality is invalid")
    _optional_text(document.get("failure"), "tool status.failure", maximum=2000)

    inspected = (
        document["installation"] != "not-checked"
        or document["activation"] != "not-checked"
        or document["compatibility"] != "not-checked"
        or document["execution"] != "not-tested"
        or document["functionality"] != "not-tested"
    )
    if not inspected:
        raise ValidationError("Tool status requires at least one actual inspection result")
    if document["activation"] == "active" and document["installation"] != "found":
        raise ValidationError("An active tool must have been found")
    if document["compatibility"] == "compatible" and document["installation"] != "found":
        raise ValidationError("A compatible tool must have been found")
    if document["execution"] == "passed" and document["installation"] != "found":
        raise ValidationError("Execution cannot pass unless the installation was found")
    if document["functionality"] == "passed" and document["execution"] != "passed":
        raise ValidationError("Functionality cannot pass unless execution passed")
    has_failed_check = (
        document["installation"] == "not-found"
        or document["activation"] == "inactive"
        or document["compatibility"] == "incompatible"
        or document["execution"] == "failed"
        or document["functionality"] == "failed"
    )
    if has_failed_check and document["failure"] is None:
        raise ValidationError("A failed tool inspection requires a failure reason")
    if not has_failed_check and document["failure"] is not None:
        raise ValidationError("A failure reason requires a failed tool inspection result")
    return document


def _normalize_tools_root(workspace: Path, value: Path, label: str) -> Path:
    require_absolute_path(str(value), label)
    root = value.absolute()
    reject_linked_components(root)
    resolved_workspace = workspace.resolve(strict=True)
    resolved_root = root.resolve(strict=False)
    if (
        resolved_root == resolved_workspace
        or resolved_root in resolved_workspace.parents
        or resolved_workspace in resolved_root.parents
    ):
        raise SafetyError("Tools repository and Workspace must not overlap")
    return root


def validate_tools_repository(tools_root: Path) -> dict[str, Any]:
    root = tools_root.absolute()
    reject_linked_components(root)
    if is_link(root) or not root.is_dir():
        raise ValidationError(f"Tools repository must be a real directory: {root}")
    marker_path = root / REPOSITORY_MARKER
    tools_path = root / TOOLS_DIRECTORY
    if is_link(marker_path) or not marker_path.is_file():
        raise ValidationError(f"Missing or linked Tools repository marker: {marker_path}")
    if is_link(tools_path) or not tools_path.is_dir():
        raise ValidationError(f"Missing or linked Tools directory: {tools_path}")
    marker = _validate_repository_marker(read_json_object(marker_path), marker_path)

    registered: list[str] = []
    unregistered: list[str] = []
    statuses = 0
    for directory in sorted(tools_path.iterdir(), key=lambda path: path.name):
        if is_link(directory) or not directory.is_dir():
            raise ValidationError(f"Tools entries must be real directories: {directory}")
        identifier = _validate_tool_id(directory.name)
        tool_path = directory / "tool.json"
        status_path = directory / "status.json"
        if tool_path.exists() or is_link(tool_path):
            if is_link(tool_path) or not tool_path.is_file():
                raise ValidationError(f"Tool registration must be a real file: {tool_path}")
            _validate_registration(read_json_object(tool_path), identifier)
            registered.append(identifier)
        else:
            unregistered.append(identifier)
        if status_path.exists() or is_link(status_path):
            if identifier not in registered:
                raise ValidationError(f"Unregistered tool has a status file: {identifier}")
            if is_link(status_path) or not status_path.is_file():
                raise ValidationError(f"Tool status must be a real file: {status_path}")
            _validate_status(read_json_object(status_path), identifier)
            statuses += 1
    return {
        "status": "valid",
        "tools_root": str(root),
        "repository_id": marker["repository_id"],
        "registered_tools": registered,
        "unregistered_directories": unregistered,
        "status_records": statuses,
    }


def _location_path(workspace: Path) -> tuple[Path, Path]:
    workspace = workspace.absolute()
    validate_workspace(workspace)
    return workspace, workspace / LOCATION_PATH


def _read_location_document(workspace: Path) -> tuple[Path, dict[str, Any] | None]:
    workspace, path = _location_path(workspace)
    if not path.exists() and not is_link(path):
        return path, None
    if is_link(path) or not path.is_file():
        raise ValidationError(f"External-tools location must be a real file: {path}")
    document = read_json_object(path)
    if set(document) != {"schema", "tools_root"} or document.get("schema") != LOCATION_SCHEMA:
        raise ValidationError(f"External-tools location contract is invalid: {path}")
    value = require_absolute_path(document.get("tools_root"), "external tools_root")
    root = _normalize_tools_root(workspace, Path(value), "external tools_root")
    return path, {"schema": LOCATION_SCHEMA, "tools_root": str(root)}


def read_tools_connection(workspace: Path) -> dict[str, Any]:
    path, document = _read_location_document(workspace)
    if document is None:
        return {
            "status": "not-connected",
            "workspace": str(workspace.absolute()),
            "configuration": str(path),
            "tools_root": None,
        }
    root = Path(document["tools_root"])
    if not root.exists():
        return {
            "status": "missing",
            "workspace": str(workspace.absolute()),
            "configuration": str(path),
            "tools_root": str(root),
        }
    report = validate_tools_repository(root)
    return {
        **report,
        "status": "connected",
        "workspace": str(workspace.absolute()),
        "configuration": str(path),
    }


def connect_tools_repository(workspace: Path, tools_root: Path) -> dict[str, Any]:
    workspace = workspace.absolute()
    validate_workspace(workspace)
    root = _normalize_tools_root(workspace, tools_root, "Tools repository path")
    report = validate_tools_repository(root)
    path, current = _read_location_document(workspace)
    if current is not None and current["tools_root"] == str(root):
        return {
            **report,
            "status": "already-connected",
            "workspace": str(workspace),
            "configuration": str(path),
        }
    if is_link(path) or (path.exists() and not path.is_file()):
        raise SafetyError(f"Refusing to replace non-file external-tools location: {path}")
    previous = None if current is None else current["tools_root"]
    atomic_write_json(
        path,
        {"schema": LOCATION_SCHEMA, "tools_root": str(root)},
        replace=path.exists(),
    )
    return {
        **report,
        "status": "connected",
        "workspace": str(workspace),
        "configuration": str(path),
        "previous_tools_root": previous,
    }


def initialize_tools_repository(
    workspace: Path, tools_root: Path | None = None,
) -> dict[str, Any]:
    workspace = workspace.absolute()
    validate_workspace(workspace)
    selected = tools_root if tools_root is not None else workspace.parent / DEFAULT_TOOLS_DIRECTORY
    root = _normalize_tools_root(workspace, selected, "Tools repository path")
    if root.exists() or is_link(root):
        if is_link(root) or not root.is_dir():
            raise SafetyError(f"Tools repository target must be a real directory: {root}")
        if any(root.iterdir()):
            report = validate_tools_repository(root)
            connection = connect_tools_repository(workspace, root)
            return {
                **report,
                **connection,
                "status": "connected",
                "repository_status": "existing",
            }

    root_created = False
    tools_created = False
    marker_created = False
    try:
        if not root.exists():
            root.mkdir()
            root_created = True
        tools_path = root / TOOLS_DIRECTORY
        tools_path.mkdir()
        tools_created = True
        marker = root / REPOSITORY_MARKER
        atomic_write_json(
            marker,
            {
                "schema": REPOSITORY_SCHEMA,
                "repository_id": f"tools-{uuid.uuid4().hex}",
                "created_utc": _utc_now(),
            },
            replace=False,
        )
        marker_created = True
        report = validate_tools_repository(root)
        connection = connect_tools_repository(workspace, root)
    except BaseException:
        if marker_created and (root / REPOSITORY_MARKER).is_file() and not is_link(root / REPOSITORY_MARKER):
            (root / REPOSITORY_MARKER).unlink()
        if tools_created and (root / TOOLS_DIRECTORY).is_dir() and not is_link(root / TOOLS_DIRECTORY):
            try:
                (root / TOOLS_DIRECTORY).rmdir()
            except OSError:
                pass
        if root_created and root.is_dir() and not is_link(root):
            try:
                root.rmdir()
            except OSError:
                pass
        raise
    return {
        **report,
        **connection,
        "status": "initialized",
        "repository_status": "created",
    }


def _connected_tools_root(workspace: Path) -> Path:
    connection = read_tools_connection(workspace)
    if connection["status"] == "not-connected":
        raise ValidationError("No GameAssetAI-Tools repository is connected")
    if connection["status"] == "missing":
        raise ValidationError(
            f"Connected GameAssetAI-Tools repository is missing: {connection['tools_root']}"
        )
    return Path(connection["tools_root"])


def validate_connected_tools_repository(workspace: Path) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    return validate_tools_repository(root)


def _tool_directory(root: Path, tool_id: str) -> Path:
    identifier = _validate_tool_id(tool_id)
    directory = root / TOOLS_DIRECTORY / identifier
    reject_linked_components(directory, stop=root / TOOLS_DIRECTORY)
    return directory


def read_tool_status(workspace: Path, tool_id: str) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    validate_tools_repository(root)
    directory = _tool_directory(root, tool_id)
    tool_path = directory / "tool.json"
    if is_link(tool_path) or not tool_path.is_file():
        raise ValidationError(f"Tool is not registered: {tool_id}")
    status_path = directory / "status.json"
    if not status_path.exists() and not is_link(status_path):
        return {
            "tool_id": tool_id,
            "inspection_status": "not-inspected",
            "status_record": None,
        }
    if is_link(status_path) or not status_path.is_file():
        raise ValidationError(f"Tool status must be a real file: {status_path}")
    status = _validate_status(read_json_object(status_path), tool_id)
    return {
        "tool_id": tool_id,
        "inspection_status": "recorded",
        "status_record": status,
    }


def read_tool_registration(workspace: Path, tool_id: str) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    validate_tools_repository(root)
    directory = _tool_directory(root, tool_id)
    tool_path = directory / "tool.json"
    if is_link(tool_path) or not tool_path.is_file():
        raise ValidationError(f"Tool is not registered: {tool_id}")
    tool = _validate_registration(read_json_object(tool_path), tool_id)
    return {
        "tool": tool,
        "inspection": read_tool_status(workspace, tool_id),
        "directory": str(directory),
    }


def list_registered_tools(workspace: Path) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    report = validate_tools_repository(root)
    tools = []
    for identifier in report["registered_tools"]:
        registration = read_tool_registration(workspace, identifier)
        tools.append({
            "id": identifier,
            "name": registration["tool"]["name"],
            "kind": registration["tool"]["kind"],
            "inspection_status": registration["inspection"]["inspection_status"],
        })
    return {"tools_root": str(root), "tools": tools}


def register_tool(
    workspace: Path,
    tool_id: str,
    *,
    name: str,
    kind: str,
    source: str,
    install_method: str,
    location: str | None = None,
    external_identifier: str | None = None,
    version: str | None = None,
    revision: str | None = None,
    environment: str | None = None,
    license_name: str | None = None,
    modified: bool = False,
    upstream_revision: str | None = None,
    modification_notes: str | None = None,
    capabilities: list[str] | None = None,
) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    validate_tools_repository(root)
    identifier = _validate_tool_id(tool_id)
    directory = _tool_directory(root, identifier)
    created_directory = False
    if directory.exists() or is_link(directory):
        if is_link(directory) or not directory.is_dir():
            raise SafetyError(f"Tool path must be a real directory: {directory}")
    else:
        directory.mkdir()
        created_directory = True
    tool_path = directory / "tool.json"
    status_path = directory / "status.json"
    if tool_path.exists() or is_link(tool_path):
        raise SafetyError(f"Tool id is already registered: {identifier}")
    if status_path.exists() or is_link(status_path):
        raise SafetyError(f"Unregistered tool has an unexpected status file: {identifier}")
    document = {
        "schema": TOOL_SCHEMA,
        "id": identifier,
        "name": name,
        "kind": kind,
        "source": {"origin": source, "license": license_name},
        "installation": {
            "method": install_method,
            "location": location,
            "identifier": external_identifier,
            "version": version,
            "revision": revision,
            "environment": environment,
        },
        "modification": {
            "modified": modified,
            "upstream_revision": upstream_revision,
            "notes": modification_notes,
        },
        "capabilities": list(capabilities or []),
        "metadata": {"created_utc": _utc_now()},
    }
    try:
        _validate_registration(document, identifier)
        atomic_write_json(tool_path, document, replace=False)
        validate_tools_repository(root)
    except BaseException:
        if created_directory and directory.is_dir() and not is_link(directory):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    return {
        "status": "registered",
        "tools_root": str(root),
        "tool": document,
        "inspection_status": "not-inspected",
    }


def record_tool_status(
    workspace: Path,
    tool_id: str,
    *,
    target: str,
    installation: str = "not-checked",
    activation: str = "not-checked",
    compatibility: str = "not-checked",
    execution: str = "not-tested",
    functionality: str = "not-tested",
    failure: str | None = None,
) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    validate_tools_repository(root)
    identifier = _validate_tool_id(tool_id)
    directory = _tool_directory(root, identifier)
    if is_link(directory / "tool.json") or not (directory / "tool.json").is_file():
        raise ValidationError(f"Tool is not registered: {identifier}")
    status_path = directory / "status.json"
    if is_link(status_path) or (status_path.exists() and not status_path.is_file()):
        raise SafetyError(f"Tool status path must be a real file: {status_path}")
    document = {
        "schema": STATUS_SCHEMA,
        "tool_id": identifier,
        "checked_utc": _utc_now(),
        "target": target,
        "installation": installation,
        "activation": activation,
        "compatibility": compatibility,
        "execution": execution,
        "functionality": functionality,
        "failure": failure,
    }
    _validate_status(document, identifier)
    atomic_write_json(status_path, document, replace=status_path.exists())
    validate_tools_repository(root)
    return {"status": "recorded", "tools_root": str(root), "status_record": document}


def unregister_tool(workspace: Path, tool_id: str) -> dict[str, Any]:
    root = _connected_tools_root(workspace)
    validate_tools_repository(root)
    identifier = _validate_tool_id(tool_id)
    directory = _tool_directory(root, identifier)
    tool_path = directory / "tool.json"
    status_path = directory / "status.json"
    if is_link(tool_path) or not tool_path.is_file():
        raise ValidationError(f"Tool is not registered: {identifier}")
    if status_path.exists() or is_link(status_path):
        if is_link(status_path) or not status_path.is_file():
            raise SafetyError(f"Tool status path must be a real file: {status_path}")
        status_path.unlink()
    tool_path.unlink()
    preserved = sorted(path.name for path in directory.iterdir())
    validate_tools_repository(root)
    return {
        "status": "unregistered",
        "tool_id": identifier,
        "directory": str(directory),
        "preserved": preserved,
    }
