"""Plan, atomically update, or restore a local Blender Add-on installation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from inspect_blender_addon_installation import _files, _manifest, inspect_installation
from validate_workspace import is_link


SCHEMA = "gameassetai.blender-addon-update.v1"
FIELDS = frozenset(("schema", "status", "source", "installed", "backup",
                    "source_sha256", "installed_sha256", "source_info", "installed_info"))


def _separate(*paths: Path) -> None:
    resolved = [path.resolve() for path in paths]
    for index, left in enumerate(resolved):
        for right in resolved[index + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError("Source, installation and recovery paths must not overlap")


def plan_update(source: Path, installed: Path, backup: Path) -> dict:
    source, installed, backup = (path.expanduser().absolute()
                                 for path in (source, installed, backup))
    if backup.exists() or is_link(backup) or not backup.parent.is_dir():
        raise ValueError("Backup must be a new path under an existing real directory")
    _separate(source, installed, backup)
    report = inspect_installation(source, installed)
    if report["status"] == "not_installed":
        raise ValueError("This updater requires an existing installation")
    return {
        "schema": SCHEMA,
        "status": "already_aligned" if report["status"] == "aligned" else "update_needed",
        "source": str(source),
        "installed": str(installed),
        "backup": str(backup),
        "source_sha256": report["source_sha256"],
        "installed_sha256": report["installed_sha256"],
        "source_info": report["source_info"],
        "installed_info": report["installed_info"],
    }


def _check_plan(plan: dict) -> None:
    if (not isinstance(plan, dict) or set(plan) != FIELDS or plan.get("schema") != SCHEMA
            or plan.get("status") not in {"already_aligned", "update_needed"}):
        raise ValueError("Invalid Add-on update plan")


def _stage_path(installed: Path, plan: dict) -> Path:
    digest = hashlib.sha256(json.dumps(
        plan, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]
    return installed.with_name(f".{installed.name}.gameassetai-stage-{digest}")


def _write_tree(source: Path, target: Path) -> None:
    target.mkdir()
    try:
        for path in _files(source):
            output = target / path.relative_to(source)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("xb") as handle:
                handle.write(path.read_bytes())
    except BaseException:
        _remove_tree(target)
        raise


def _remove_tree(root: Path) -> None:
    if not root.is_dir() or is_link(root):
        raise OSError(f"Refusing to remove an unverified tree: {root}")
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if is_link(path):
            raise OSError(f"Refusing linked staged component: {path}")
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    root.rmdir()


def apply_update(plan: dict) -> dict:
    _check_plan(plan)
    source, installed, backup = (Path(plan[key]) for key in ("source", "installed", "backup"))
    fresh = plan_update(source, installed, backup)
    if fresh != plan:
        raise ValueError("Add-on source or installation changed after planning")
    if plan["status"] == "already_aligned":
        return {"schema": SCHEMA, "status": "already_aligned", "installed": str(installed),
                "restart_required": False}
    stage = _stage_path(installed, plan)
    if stage.exists() or is_link(stage):
        raise ValueError("Deterministic Add-on stage already exists")
    _write_tree(source, stage)
    if _manifest(stage) != plan["source_sha256"]:
        _remove_tree(stage)
        raise OSError("Staged Add-on manifest mismatch")
    old_moved = new_moved = False
    try:
        installed.rename(backup)
        old_moved = True
        stage.rename(installed)
        new_moved = True
        if _manifest(installed) != plan["source_sha256"]:
            raise OSError("Installed Add-on verification failed")
    except BaseException:
        if new_moved and installed.exists() and not stage.exists():
            installed.rename(stage)
        if old_moved and backup.exists() and not installed.exists():
            backup.rename(installed)
        if stage.exists():
            _remove_tree(stage)
        raise
    return {"schema": SCHEMA, "status": "updated", "installed": str(installed),
            "backup": str(backup), "restart_required": True,
            "source_sha256": plan["source_sha256"]}


def restore_update(plan: dict, replaced: Path) -> dict:
    _check_plan(plan)
    installed, backup = Path(plan["installed"]), Path(plan["backup"])
    replaced = replaced.expanduser().absolute()
    _separate(Path(plan["source"]), installed, backup, replaced)
    if replaced.exists() or is_link(replaced) or not replaced.parent.is_dir():
        raise ValueError("Replaced-version path must be new under an existing directory")
    if _manifest(installed) != plan["source_sha256"]:
        raise ValueError("Current installation no longer matches the updated version")
    if _manifest(backup) != plan["installed_sha256"]:
        raise ValueError("Backup no longer matches the previous version")
    installed.rename(replaced)
    try:
        backup.rename(installed)
    except BaseException:
        replaced.rename(installed)
        raise
    return {"schema": SCHEMA, "status": "restored", "installed": str(installed),
            "replaced": str(replaced), "restart_required": True}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"),
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("Non-standard JSON constant: " + value)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    planned = commands.add_parser("plan")
    planned.add_argument("source", type=Path)
    planned.add_argument("installed", type=Path)
    planned.add_argument("--backup", required=True, type=Path)
    applied = commands.add_parser("apply")
    applied.add_argument("plan", type=Path)
    restored = commands.add_parser("restore")
    restored.add_argument("plan", type=Path)
    restored.add_argument("--replaced", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = plan_update(args.source, args.installed, args.backup)
        elif args.command == "apply":
            result = apply_update(_read(args.plan))
        else:
            result = restore_update(_read(args.plan), args.replaced)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"Blender Add-on update failed: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
