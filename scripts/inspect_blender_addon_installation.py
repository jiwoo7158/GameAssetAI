"""Read-only, hash-based inspection of a GameAssetAI Blender Add-on installation."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

from validate_workspace import is_link


SCHEMA = "gameassetai.blender-addon-installation.v1"


def _files(root: Path) -> list[Path]:
    if not root.is_dir() or is_link(root):
        raise ValueError(f"Add-on path must be a real directory: {root}")
    result = []
    for path in root.rglob("*"):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if is_link(path):
            raise ValueError(f"Linked Add-on components are not supported: {path}")
        if path.is_file():
            result.append(path)
        elif not path.is_dir():
            raise ValueError(f"Unsupported Add-on component: {path}")
    return sorted(result)


def _manifest(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in _files(root)
    }


def _bl_info(root: Path) -> dict:
    init = root / "__init__.py"
    if not init.is_file() or is_link(init):
        raise ValueError("Add-on __init__.py is missing or linked")
    tree = ast.parse(init.read_text(encoding="utf-8-sig"), filename=str(init))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets):
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict):
                break
            version = value.get("version")
            blender = value.get("blender")
            if (not isinstance(version, tuple) or len(version) != 3
                    or any(not isinstance(item, int) or item < 0 for item in version)):
                raise ValueError("bl_info.version must be a three-integer tuple")
            if (not isinstance(blender, tuple) or len(blender) != 3
                    or any(not isinstance(item, int) or item < 0 for item in blender)):
                raise ValueError("bl_info.blender must be a three-integer tuple")
            return {"name": value.get("name"), "version": list(version), "blender": list(blender)}
    raise ValueError("A literal bl_info dictionary was not found")


def _version(text: str) -> list[int]:
    parts = text.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        raise ValueError("Blender version must use MAJOR.MINOR.PATCH")
    return [int(part) for part in parts]


def inspect_installation(source: Path, installed: Path, blender_version: str | None = None) -> dict:
    source = source.expanduser().absolute()
    installed = installed.expanduser().absolute()
    source_info = _bl_info(source)
    source_hashes = _manifest(source)
    actual_blender = _version(blender_version) if blender_version else None
    compatible = actual_blender is None or actual_blender >= source_info["blender"]
    result = {
        "schema": SCHEMA,
        "source": str(source),
        "installed": str(installed),
        "source_info": source_info,
        "installed_info": None,
        "blender_version": actual_blender,
        "blender_compatible": compatible,
        "missing": [],
        "extra": [],
        "changed": [],
        "source_sha256": source_hashes,
        "installed_sha256": {},
    }
    if not installed.exists():
        result["status"] = "not_installed"
        result["missing"] = sorted(source_hashes)
        return result
    installed_info = _bl_info(installed)
    installed_hashes = _manifest(installed)
    source_names, installed_names = set(source_hashes), set(installed_hashes)
    result.update({
        "installed_info": installed_info,
        "installed_sha256": installed_hashes,
        "missing": sorted(source_names - installed_names),
        "extra": sorted(installed_names - source_names),
        "changed": sorted(name for name in source_names & installed_names
                          if source_hashes[name] != installed_hashes[name]),
    })
    result["status"] = "aligned" if not any(
        result[key] for key in ("missing", "extra", "changed")) else "update_needed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("installed", type=Path)
    parser.add_argument("--blender-version")
    args = parser.parse_args()
    try:
        result = inspect_installation(args.source, args.installed, args.blender_version)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "aligned" and result["blender_compatible"] else 1
    except (OSError, SyntaxError, ValueError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "error", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
