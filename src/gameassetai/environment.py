from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from .errors import ValidationError
from .filesystem import atomic_write_json, is_link, read_json_object, reject_linked_components


LOCAL_ENVIRONMENT_SCHEMA = "gameassetai.local-environment.v1"
LOCAL_ENVIRONMENT_PATH = Path(".local") / "environment.json"
DIAGNOSTIC_PREFIX = "GAMEASSETAI_BLENDER_DIAGNOSTIC="


def _configuration_path(root: Path) -> Path:
    root = Path(root).absolute()
    if not root.exists() or not root.is_dir():
        raise ValidationError(f"Local environment root must be an existing directory: {root}")
    if is_link(root):
        raise ValidationError(f"Local environment root cannot be a linked directory: {root}")
    return root / LOCAL_ENVIRONMENT_PATH


def _validate_executable(path_value: object) -> Path:
    if not isinstance(path_value, str) or not path_value.strip() or path_value != path_value.strip():
        raise ValidationError("Blender executable must be a nonempty absolute path string")
    path = Path(path_value)
    if not path.is_absolute():
        raise ValidationError(f"Blender executable path must be absolute: {path}")
    if not path.exists() or not path.is_file():
        raise ValidationError(f"Configured Blender executable does not exist: {path}")
    reject_linked_components(path)
    return path.absolute()


def _validate_configuration(data: dict[str, Any], path: Path) -> dict[str, Any]:
    if set(data) != {"schema", "blender"}:
        raise ValidationError(f"Unexpected local environment fields in {path}")
    if data.get("schema") != LOCAL_ENVIRONMENT_SCHEMA:
        raise ValidationError(f"Unsupported local environment schema in {path}: {data.get('schema')!r}")
    blender = data.get("blender")
    if not isinstance(blender, dict) or set(blender) != {"executable"}:
        raise ValidationError(f"Local environment blender entry is invalid: {path}")
    executable = _validate_executable(blender.get("executable"))
    return {
        "schema": LOCAL_ENVIRONMENT_SCHEMA,
        "blender": {"executable": str(executable)},
    }


def configure_blender_executable(root: Path, executable: Path) -> dict[str, Any]:
    """Store one local Blender executable without placing a personal path in Git."""
    path = _configuration_path(root)
    reject_linked_components(path.parent, stop=Path(root).absolute())
    if is_link(path):
        raise ValidationError(f"Local environment configuration cannot be linked: {path}")
    if path.exists() and not path.is_file():
        raise ValidationError(f"Local environment configuration must be a file: {path}")
    validated_executable = _validate_executable(str(Path(executable).absolute()))
    data = {
        "schema": LOCAL_ENVIRONMENT_SCHEMA,
        "blender": {"executable": str(validated_executable)},
    }
    atomic_write_json(path, data, replace=path.exists())
    return {"status": "configured", "configuration": str(path), **data}


def read_local_environment(root: Path) -> dict[str, Any]:
    path = _configuration_path(root)
    if not path.exists():
        raise ValidationError(
            f"Local Blender environment is not configured: {path}. "
            "Run 'environment blender set <root> <blender-executable>'."
        )
    reject_linked_components(path)
    return _validate_configuration(read_json_object(path), path)


def _run(command: list[str], *, timeout: float) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValidationError(f"Blender diagnostic could not run: {exc}") from exc


def _diagnostic_payload(process: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    if process.returncode != 0:
        detail = (process.stderr or process.stdout).strip()
        raise ValidationError(
            f"Blender background diagnostic failed with exit code {process.returncode}: {detail}"
        )
    for line in process.stdout.splitlines():
        if line.startswith(DIAGNOSTIC_PREFIX):
            try:
                data = json.loads(line[len(DIAGNOSTIC_PREFIX):])
            except json.JSONDecodeError as exc:
                raise ValidationError(f"Blender returned invalid diagnostic JSON: {exc}") from exc
            if not isinstance(data, dict):
                break
            return data
    raise ValidationError("Blender completed without the expected GameAssetAI diagnostic record")


def validate_blender_environment(root: Path, *, timeout: float = 60.0) -> dict[str, Any]:
    """Run factory-startup diagnostics without opening or saving a user Blender file."""
    environment = read_local_environment(root)
    executable = environment["blender"]["executable"]
    expression = (
        "import bpy,json,sys;"
        f"print({DIAGNOSTIC_PREFIX!r}+json.dumps({{"
        "'background':bpy.app.background,"
        "'blender':bpy.app.version_string,"
        "'filepath':bpy.data.filepath,"
        "'python':sys.version.split()[0]"
        "},sort_keys=True))"
    )
    success = _run(
        [
            executable,
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python-expr",
            expression,
        ],
        timeout=timeout,
    )
    diagnostic = _diagnostic_payload(success)
    if diagnostic.get("background") is not True or diagnostic.get("filepath") != "":
        raise ValidationError(
            "Blender diagnostic did not use an unsaved factory-startup background session"
        )

    failure_marker = "gameassetai-diagnostic-error"
    failure = _run(
        [
            executable,
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "7",
            "--python-expr",
            f"raise RuntimeError({failure_marker!r})",
        ],
        timeout=timeout,
    )
    failure_text = f"{failure.stdout}\n{failure.stderr}"
    if failure.returncode != 7 or failure_marker not in failure_text:
        raise ValidationError(
            "Blender did not propagate the requested Python diagnostic failure (expected exit 7)"
        )
    return {
        "status": "valid",
        "configuration": str(_configuration_path(root)),
        "executable": executable,
        "diagnostic": diagnostic,
        "python_error_exit_code": failure.returncode,
    }
