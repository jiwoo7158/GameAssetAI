"""Read current Workspace Profile verbatim with provenance; never infer game rules."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from validate_workspace import read_json_object, validate_workspace


def read_profile_context(root: Path) -> dict:
    errors = validate_workspace(root)
    if errors:
        raise ValueError("; ".join(errors))
    reference = root / "config" / "active-profile.json"
    before = reference.read_bytes()
    stem = read_json_object(reference)["profile"]
    path = root / "profiles" / f"{stem}.md" if stem is not None else None
    raw = path.read_bytes() if path is not None else None
    if reference.read_bytes() != before or (path is not None and path.read_bytes() != raw):
        raise ValueError("Profile changed during read; retry rather than reuse stale context")
    return {"schema": "gameassetai.profile-context.v1", "profile": stem,
            "path": str(path.absolute()) if path is not None else None,
            "reference_sha256": hashlib.sha256(before).hexdigest(),
            "profile_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
            "markdown": raw.decode("utf-8-sig") if raw is not None else None,
            "rules": "interpret explicit applicable Markdown rules; absent fields are unknown"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    try:
        report = read_profile_context(args.workspace.expanduser().absolute())
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"Profile context unavailable: {exc}\n")
    print(json.dumps(report, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
