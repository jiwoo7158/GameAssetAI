"""Plan, apply, or restore one hash-bound local Skill update without deleting either version."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from package_skill import skill_files
from validate_workspace import is_link


SCHEMA = "gameassetai.skill-update.v1"
PLAN_FIELDS = frozenset(("schema", "status", "source", "installed", "backup",
                         "source_sha256", "installed_sha256", "client_discovery"))


def _manifest(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in skill_files(root)}


def _staged_manifest(root: Path) -> dict[str, str]:
    if not root.is_dir() or is_link(root):
        raise ValueError("Staged Skill must be a real directory")
    result = {}
    for path in root.rglob("*"):
        if is_link(path):
            raise ValueError("Linked staged components are not supported")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise ValueError("Staged Skill contains a non-file component")
    return result


def _linked_component(path: Path) -> bool:
    return any(is_link(item) for item in (path, *path.parents))


def _separate(*paths: Path) -> None:
    resolved = [path.resolve() for path in paths]
    for index, left in enumerate(resolved):
        for right in resolved[index + 1:]:
            if left == right or left in right.parents or right in left.parents:
                raise ValueError("Source, installation and recovery paths must not overlap")


def _validate_roots(source: Path, installed: Path, backup: Path) -> None:
    if source.name != installed.name:
        raise ValueError("Source and installed Skill directory names must match")
    if not source.is_dir() or not installed.is_dir():
        raise ValueError("Source and installed Skill directories must already exist")
    if backup.exists() or is_link(backup):
        raise ValueError("Backup path must not already exist")
    if not backup.parent.is_dir():
        raise ValueError("Backup parent must already exist")
    for path in (source, installed, backup.parent):
        if _linked_component(path):
            raise ValueError(f"Linked path components are not supported: {path}")
    _separate(source, installed, backup)


def plan_update(source: Path, installed: Path, backup: Path) -> dict:
    source = source.expanduser().absolute()
    installed = installed.expanduser().absolute()
    backup = backup.expanduser().absolute()
    _validate_roots(source, installed, backup)
    source_hashes = _manifest(source)
    installed_hashes = _manifest(installed)
    return {
        "schema": SCHEMA,
        "status": "already_aligned" if source_hashes == installed_hashes else "update_needed",
        "source": str(source),
        "installed": str(installed),
        "backup": str(backup),
        "source_sha256": source_hashes,
        "installed_sha256": installed_hashes,
        "client_discovery": "not_verified",
    }


def _read_plan(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate plan key: " + key)
            result[key] = value
        return result
    data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("Non-standard JSON constant: " + value)))
    if not isinstance(data, dict) or set(data) != PLAN_FIELDS:
        raise ValueError("Update plan fields do not match the schema")
    if data.get("schema") != SCHEMA or data.get("status") not in {
            "update_needed", "already_aligned"}:
        raise ValueError("Update plan schema/status is invalid")
    if data.get("client_discovery") != "not_verified":
        raise ValueError("Update plan client_discovery must remain not_verified")
    for key in ("source_sha256", "installed_sha256"):
        value = data.get(key)
        if (not isinstance(value, dict) or not value
                or any(not isinstance(name, str) or not isinstance(digest, str)
                       or len(digest) != 64
                       or any(ch not in "0123456789abcdef" for ch in digest)
                       for name, digest in value.items())):
            raise ValueError(f"Update plan {key} is invalid")
    return data


def _stage_path(installed: Path, plan: dict, label: str) -> Path:
    canonical = json.dumps(plan, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    token = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return installed.with_name(f".{installed.name}.gameassetai-{label}-{token}")


def _write_snapshot(root: Path, snapshot: dict[str, bytes]) -> None:
    root.mkdir()
    created_files: list[Path] = []
    created_dirs = [root]
    try:
        for relative, contents in snapshot.items():
            output = root.joinpath(*relative.split("/"))
            missing = []
            parent = output.parent
            while parent != root and not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                created_dirs.append(directory)
            with output.open("xb") as handle:
                created_files.append(output)
                handle.write(contents)
            if output.read_bytes() != contents:
                raise OSError(f"Staged byte verification failed: {relative}")
    except BaseException:
        for output in reversed(created_files):
            if output.is_file() and not is_link(output):
                output.unlink()
        for directory in reversed(created_dirs):
            if directory.is_dir() and not is_link(directory):
                directory.rmdir()
        raise


def _remove_snapshot(root: Path, manifest: dict[str, str]) -> None:
    if not root.is_dir() or is_link(root) or _staged_manifest(root) != manifest:
        raise OSError("Refusing cleanup because the owned staged tree changed")
    files = [root.joinpath(*relative.split("/")) for relative in manifest]
    for path in files:
        path.unlink()
    directories = sorted({parent for path in files for parent in path.parents
                          if parent != root and root in parent.parents},
                         key=lambda item: len(item.parts), reverse=True)
    for directory in directories:
        directory.rmdir()
    root.rmdir()


def apply_update(plan: dict) -> dict:
    if set(plan) != PLAN_FIELDS or plan.get("schema") != SCHEMA:
        raise ValueError("Invalid update plan")
    source, installed, backup = map(lambda key: Path(plan[key]),
                                    ("source", "installed", "backup"))
    _validate_roots(source, installed, backup)
    if _manifest(source) != plan["source_sha256"]:
        raise ValueError("Source changed after update planning")
    if _manifest(installed) != plan["installed_sha256"]:
        raise ValueError("Installed Skill changed after update planning")
    if plan["status"] == "already_aligned":
        return {"schema": SCHEMA, "status": "already_aligned",
                "installed": str(installed), "client_discovery": "not_verified"}
    if plan["status"] != "update_needed":
        raise ValueError("Update plan is not applicable")
    snapshot = {p.relative_to(source).as_posix(): p.read_bytes()
                for p in skill_files(source)}
    stage = _stage_path(installed, plan, "stage")
    if stage.exists() or is_link(stage):
        raise ValueError("Deterministic update stage already exists")
    _write_snapshot(stage, snapshot)
    if _staged_manifest(stage) != plan["source_sha256"]:
        _remove_snapshot(stage, plan["source_sha256"])
        raise OSError("Staged Skill manifest mismatch")
    old_moved = False
    new_moved = False
    try:
        installed.rename(backup)
        old_moved = True
        stage.rename(installed)
        new_moved = True
        if _manifest(installed) != plan["source_sha256"]:
            raise OSError("Installed Skill verification failed after promotion")
    except BaseException:
        if new_moved and installed.exists() and not stage.exists():
            installed.rename(stage)
        if old_moved and backup.exists() and not installed.exists():
            backup.rename(installed)
        if stage.exists():
            _remove_snapshot(stage, plan["source_sha256"])
        raise
    return {"schema": SCHEMA, "status": "updated", "installed": str(installed),
            "backup": str(backup), "source_sha256": plan["source_sha256"],
            "previous_sha256": plan["installed_sha256"],
            "client_discovery": "not_verified"}


def restore_update(plan: dict, replaced: Path) -> dict:
    if set(plan) != PLAN_FIELDS or plan.get("schema") != SCHEMA:
        raise ValueError("Invalid update plan")
    installed, backup = Path(plan["installed"]), Path(plan["backup"])
    replaced = replaced.expanduser().absolute()
    if not installed.is_dir() or not backup.is_dir() or replaced.exists() or is_link(replaced):
        raise ValueError("Installed/backup/replaced recovery paths are not in the required state")
    if not replaced.parent.is_dir() or _linked_component(replaced.parent):
        raise ValueError("Replaced-version parent must be an existing real directory")
    _separate(Path(plan["source"]), installed, backup, replaced)
    if _manifest(installed) != plan["source_sha256"]:
        raise ValueError("Current installation no longer matches the planned new version")
    if _manifest(backup) != plan["installed_sha256"]:
        raise ValueError("Backup no longer matches the planned previous version")
    current_moved = False
    backup_moved = False
    try:
        installed.rename(replaced)
        current_moved = True
        backup.rename(installed)
        backup_moved = True
        if _manifest(installed) != plan["installed_sha256"]:
            raise OSError("Restored Skill verification failed")
    except BaseException:
        if backup_moved and installed.exists() and not backup.exists():
            installed.rename(backup)
        if current_moved and replaced.exists() and not installed.exists():
            replaced.rename(installed)
        raise
    return {"schema": SCHEMA, "status": "restored", "installed": str(installed),
            "replaced": str(replaced), "installed_sha256": plan["installed_sha256"],
            "client_discovery": "not_verified"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("source", type=Path)
    plan_parser.add_argument("installed", type=Path)
    plan_parser.add_argument("--backup", required=True, type=Path)
    apply_parser = commands.add_parser("apply")
    apply_parser.add_argument("plan", type=Path)
    restore_parser = commands.add_parser("restore")
    restore_parser.add_argument("plan", type=Path)
    restore_parser.add_argument("--replaced", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = plan_update(args.source, args.installed, args.backup)
        else:
            plan = _read_plan(args.plan.expanduser().absolute())
            result = (apply_update(plan) if args.command == "apply"
                      else restore_update(plan, args.replaced))
    except (OSError, UnicodeError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Skill update failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
