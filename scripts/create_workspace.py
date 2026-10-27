from __future__ import annotations

import argparse
import shutil
import os
import tempfile
from pathlib import Path

from validate_workspace import is_link, validate_workspace


def copy_workspace(template: Path, target: Path, force: bool) -> None:
    if is_link(template) or is_link(target):
        raise ValueError("Template and target must not be symlinks or junctions")
    template = template.resolve()
    target = target.expanduser().resolve()
    repo_root = template.parent
    if target == repo_root or repo_root in target.parents or target in repo_root.parents:
        raise ValueError("Workspace target must be outside, and not contain, the development repository")
    errors = validate_workspace(template, template_mode=True)
    if errors:
        raise ValueError("Invalid workspace template: " + "; ".join(errors))
    if target.exists() and not target.is_dir():
        raise ValueError(f"Target is not a directory: {target}")
    if target.exists() and any(target.iterdir()) and not force:
        raise ValueError(
            f"Target is not empty: {target}\n"
            "Choose an empty/new folder or pass --force."
        )

    # Snapshot and preflight all paths before making any target changes.
    sources = []
    pending = [template]
    while pending:
        for src in sorted(pending.pop().iterdir()):
            if is_link(src) or not (src.is_file() or src.is_dir()):
                raise ValueError(f"Unsupported template path: {src}")
            sources.append(src)
            if src.is_dir():
                pending.append(src)
    for src in sources:
        dst = target / src.relative_to(template)
        for path in (dst, *dst.parents):
            if path == target.parent:
                break
            if is_link(path):
                raise ValueError(f"Linked destination path is not supported: {path}")
        if dst.exists() and src.is_dir() != dst.is_dir():
            raise ValueError(f"File/directory collision: {dst}")

    target.mkdir(parents=True, exist_ok=True)
    for src in sources:
        relative = src.relative_to(template)
        dst = target / relative

        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and not force:
                continue
            # Replace rather than truncate: existing hard links are not modified.
            with tempfile.NamedTemporaryFile(dir=dst.parent, delete=False) as handle:
                staged = Path(handle.name)
            try:
                shutil.copy2(src, staged)
                os.replace(staged, dst)
            finally:
                if staged.exists():
                    staged.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a GameAssetAI-Workspace from the repository template."
    )
    parser.add_argument("target", help="Destination workspace directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow copying into an existing directory and overwrite template files",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    template = repo_root / "workspace-template"
    target = Path(args.target).expanduser()
    try:
        copy_workspace(template, target, args.force)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Workspace creation failed: {exc}\n")
    print(f"Created GameAssetAI workspace: {target.resolve()}")
    print("Open this folder in Codex for normal Blender asset work.")


if __name__ == "__main__":
    main()
