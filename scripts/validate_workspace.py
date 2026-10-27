"""Read-only validation of the workspace contract; no Blender dependency."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat


TEMPLATE_FILES = (
    "AGENTS.md", "README.md", "profiles/README.md",
    "profiles/_PROFILE_TEMPLATE.md", "config/projects.json",
    "config/active-profile.json", "notes/README.md",
)
WORKSPACE_FILES = ("AGENTS.md", "config/projects.json", "config/active-profile.json")
WORKSPACE_DIRS = ("profiles", "config")


def is_link(path: Path) -> bool:
    """Reject symlinks and Windows reparse points, including junctions."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def read_json_object(path: Path) -> dict:
    def unique_keys(pairs: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"Non-standard JSON constant: {value}")

    data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys,
                      parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object")
    return data


def valid_profile_stem(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if value.startswith(".") or value.endswith(".") or value.lower().endswith(".md"):
        return False
    if re.search(r'[\x00-\x1f/\\:*?"<>|]', value):
        return False
    if value.casefold() in {"readme", "_profile_template"}:
        return False
    # Portable filenames: also reject Windows device names (including extensions).
    base = value.split(".", 1)[0].upper()
    return base not in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)]}


def validate_workspace(root: Path, require_profile: bool = False,
                       template_mode: bool = False) -> list[str]:
    errors = []
    if is_link(root):
        return ["Workspace root must not be a symlink or junction"]
    for relative in (*WORKSPACE_DIRS, "notes") if template_mode else WORKSPACE_DIRS:
        path = root / relative
        if is_link(path) or not path.is_dir():
            errors.append(f"Expected a real directory: {relative}")
    for relative in TEMPLATE_FILES if template_mode else WORKSPACE_FILES:
        path = root / relative
        # Never read through a linked workspace component.
        parents = path.relative_to(root).parents
        if is_link(path) or any(is_link(root / p) for p in parents):
            errors.append(f"Linked workspace path is not supported: {relative}")
            continue
        if not path.is_file():
            errors.append(f"Missing or non-file path: {relative}")
            continue
        try:
            if not path.read_text(encoding="utf-8-sig").strip():
                errors.append(f"Empty file: {relative}")
        except (OSError, UnicodeError) as exc:
            errors.append(f"Cannot read {relative}: {exc}")
    if errors:
        return errors

    for filename in ("active-profile.json", "projects.json"):
        try:
            data = read_json_object(root / "config" / filename)
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"Invalid config/{filename}: {exc}")
            continue
        if filename == "active-profile.json":
            if template_mode and data.get("profile") is not None:
                errors.append("Source template must have profile set to null")
            if "profile" not in data:
                errors.append("active-profile.json must contain profile")
            elif data["profile"] is None:
                if require_profile:
                    errors.append("No active profile selected")
            elif not valid_profile_stem(data["profile"]):
                errors.append("profile must be a non-reserved filename stem, without paths or .md")
            else:
                profile = root / "profiles" / f"{data['profile']}.md"
                try:
                    exact_names = {p.name for p in (root / "profiles").iterdir()}
                    if is_link(profile) or not profile.is_file() or profile.name not in exact_names:
                        errors.append(f"Active profile missing, linked, or case mismatch: {profile.name}")
                    elif not profile.read_text(encoding="utf-8-sig").strip():
                        errors.append(f"Active profile is empty: {profile.name}")
                except (OSError, UnicodeError) as exc:
                    errors.append(f"Cannot read active profile: {exc}")
        else:
            projects = data.get("projects")
            if not isinstance(projects, dict):
                errors.append("projects.json must contain a projects object")
                continue
            if template_mode and projects:
                errors.append("Source template must have empty project mappings")
            for name, mappings in projects.items():
                if not name.strip() or not isinstance(mappings, dict):
                    errors.append(f"Project {name!r} must be a named object of path mappings")
                    continue
                for label, value in mappings.items():
                    if (not label.strip() or not isinstance(value, str) or not value.strip()
                            or re.search(r"[\x00-\x1f]", value)):
                        errors.append(f"Project {name!r}/{label!r} must contain a nonempty path string")
                    elif not (PureWindowsPath(value).is_absolute() or PurePosixPath(value).is_absolute()):
                        errors.append(f"Project {name!r}/{label!r} must use an absolute path")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--require-profile", action="store_true",
                        help="Fail if no active game profile has been selected")
    args = parser.parse_args()
    root = args.workspace.expanduser().absolute()
    try:
        errors = validate_workspace(root, args.require_profile)
    except OSError as exc:
        errors = [str(exc)]
    if errors:
        print("Workspace validation failed.")
        for error in errors:
            print(f"  {error}")
        return 1
    print("Workspace structure and configuration OK.")
    print("External project paths are not accessed; game rules are not inferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
