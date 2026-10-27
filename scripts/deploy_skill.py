"""Copy one tested source skill to an explicit local discovery directory, without overwrite."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from package_skill import skill_files
from validate_workspace import is_link


def deploy_skill(skill: Path, skills_dir: Path) -> dict:
    files = skill_files(skill)
    destination = skills_dir.expanduser().absolute() / skill.name
    source = skill.resolve()
    resolved = destination.resolve()
    if resolved == source or source in resolved.parents or resolved in source.parents:
        raise ValueError("Source and deployment must not overlap")
    for path in (destination, *destination.parents):
        if is_link(path):
            raise ValueError(f"Linked deployment path is not supported: {path}")
    if destination.exists():
        raise ValueError("Deployment already exists; no overwrite/update is permitted")
    # Read all sources before creating deployment. No concurrent source/destination edits.
    snapshot = {p.relative_to(skill): p.read_bytes() for p in files}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()  # Exclusive claim; a concurrent existing destination is rejected.
    owned_files, owned_dirs = [], [destination]
    try:
        for relative, contents in snapshot.items():
            output = destination / relative
            for directory in reversed(output.parent.relative_to(destination).parents):
                child = destination / directory
                if child != destination and not child.exists():
                    child.mkdir()
                    owned_dirs.append(child)
            if output.parent != destination and not output.parent.exists():
                output.parent.mkdir()
                owned_dirs.append(output.parent)
            with output.open("xb") as handle:
                owned_files.append(output)
                handle.write(contents)
            if output.read_bytes() != contents:
                raise OSError(f"Deployment byte verification failed: {relative}")
    except Exception:
        # Only paths created by this invocation; never recursively delete a destination.
        for path in reversed(owned_files):
            path.unlink()
        for path in reversed(owned_dirs):
            path.rmdir()
        raise
    return {"destination": str(destination), "client_discovery": "not_verified",
            "source_sha256": {p.as_posix(): hashlib.sha256(b).hexdigest() for p, b in snapshot.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    parser.add_argument("--skills-dir", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = deploy_skill(args.skill.expanduser(), args.skills_dir)
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        parser.exit(1, f"Skill deployment failed: {exc}\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
