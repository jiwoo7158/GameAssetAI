"""Read-only comparison of one source skill and its deployment, not client discovery."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from package_skill import skill_files
from validate_workspace import is_link


def validate_skill_deployment(source: Path, installed: Path) -> dict:
    report = {"schema":"gameassetai.skill-deployment.v1","status":"error",
              "client_discovery":"not_verified","errors":[]}
    try:
        if source.name != installed.name:
            raise ValueError("Source and deployment directory names must match")
        if source.resolve() == installed.resolve():
            raise ValueError("Deployment must be distinct from development source")
        for root in (source,installed):
            if any(is_link(p) for p in (root,*root.parents)):
                raise ValueError("Linked source/deployment components are not supported")
        original = {p.relative_to(source).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in skill_files(source)}
        deployed = {p.relative_to(installed).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in skill_files(installed)}
        missing,extra = sorted(original.keys()-deployed.keys()), sorted(deployed.keys()-original.keys())
        changed = sorted(p for p in original.keys() & deployed.keys() if original[p]!=deployed[p])
        report.update({"source":str(source.absolute()),"installed":str(installed.absolute()),
                       "missing":missing,"extra":extra,"changed":changed,
                       "source_sha256":original,"installed_sha256":deployed,
                       "status":"aligned" if not (missing or extra or changed) else "drift"})
    except (OSError,UnicodeError,ValueError,SyntaxError) as exc:
        report["errors"].append(str(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("installed",type=Path)
    args = parser.parse_args()
    report = validate_skill_deployment(args.source.expanduser().absolute(),args.installed.expanduser().absolute())
    print(json.dumps(report,ensure_ascii=True))
    return 0 if report["status"]=="aligned" else 1


if __name__ == "__main__":
    raise SystemExit(main())
