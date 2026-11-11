from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import tempfile
from typing import Any

from .errors import SafetyError, ValidationError


PORTABLE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
WINDOWS_DEVICES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def is_link(path: Path) -> bool:
    """Return true for symlinks and Windows reparse points, including junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def reject_linked_components(path: Path, *, stop: Path | None = None) -> None:
    current = path.absolute()
    boundary = stop.absolute() if stop else None
    while True:
        if is_link(current):
            raise SafetyError(f"Linked path component is not supported: {current}")
        if current.parent == current or current == boundary:
            return
        current = current.parent


def read_json_object(path: Path) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValidationError(f"Non-standard JSON constant in {path}: {value}")

    try:
        data = json.loads(
            path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=unique,
            parse_constant=reject_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read JSON object {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"Expected a JSON object: {path}")
    return data


def canonical_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write_json(path: Path, data: object, *, replace: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    reject_linked_components(path.parent)
    if not replace and (path.exists() or is_link(path)):
        raise SafetyError(f"Refusing to overwrite existing file: {path}")
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False,
    )
    staged = Path(handle.name)
    try:
        with handle:
            handle.write(canonical_json(data))
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            os.replace(staged, path)
        else:
            # Same-directory hard-link publication is atomic and fails if another writer
            # claimed the destination. Unlinking the stage keeps the published inode intact.
            os.link(staged, path)
            staged.unlink()
    finally:
        staged.unlink(missing_ok=True)


def validate_identifier(value: object, label: str = "identifier") -> str:
    if not isinstance(value, str) or not PORTABLE_ID.fullmatch(value):
        raise ValidationError(
            f"{label} must be a lowercase portable slug (letters, digits, hyphens): {value!r}"
        )
    if value.split(".", 1)[0].upper() in WINDOWS_DEVICES:
        raise ValidationError(f"{label} is a reserved device name: {value!r}")
    return value


def require_absolute_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValidationError(f"{label} must be a nonempty absolute path string")
    if re.search(r"[\x00-\x1f]", value):
        raise ValidationError(f"{label} contains control characters")
    from pathlib import PurePosixPath, PureWindowsPath

    if not (PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()):
        raise ValidationError(f"{label} must be absolute: {value}")
    return value
