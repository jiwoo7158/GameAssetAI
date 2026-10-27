"""Build a portable source ZIP, not client installation or a production release."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from validate_workspace import is_link


SKILL_CONTRACT = "gameassetai.skill-contract.v1"
CONTRACT_FIELDS = ("requirements", "evidence", "external-dependencies")
CONTRACT_SECTIONS = (
    "Requirements and responsibility",
    "Implementation basis and dependencies",
    "Workflow",
    "Preservation",
    "Validation and completion",
    "Boundary",
)
EVIDENCE_LEVELS = {"tested", "representative", "accepted", "engine-proven"}


def _validate_opted_in_contract(lines: list[str], header: list[str]) -> None:
    metadata = {}
    for line in header:
        stripped = line.strip()
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            metadata[key] = value.strip()
    if metadata.get("contract") != SKILL_CONTRACT:
        return
    missing = [field for field in CONTRACT_FIELDS if not metadata.get(field)]
    if missing:
        raise ValueError(f"{SKILL_CONTRACT} missing metadata: {', '.join(missing)}")
    if metadata["evidence"] not in EVIDENCE_LEVELS:
        raise ValueError(f"Invalid evidence level: {metadata['evidence']}")
    headings = {line.removeprefix("## ").strip() for line in lines if line.startswith("## ")}
    missing_sections = [section for section in CONTRACT_SECTIONS if section not in headings]
    if missing_sections:
        raise ValueError(f"{SKILL_CONTRACT} missing sections: {', '.join(missing_sections)}")


def skill_files(skill: Path) -> list[Path]:
    if is_link(skill) or not skill.is_dir():
        raise ValueError("Skill source must be a real directory")
    entry = skill / "SKILL.md"
    if is_link(entry) or not entry.is_file():
        raise ValueError("Missing real SKILL.md")
    lines = entry.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise ValueError("Missing skill frontmatter")
    header = lines[1:lines[1:].index("---") + 1]
    names = [line.removeprefix("name:").strip() for line in header if line.startswith("name:")]
    if names != [skill.name] or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill.name) or len(skill.name) >= 64:
        raise ValueError("Skill name must match the directory and use a literal lowercase slug")
    if not any(line.startswith("description:") and line.removeprefix("description:").strip() for line in header):
        raise ValueError("Missing description")
    _validate_opted_in_contract(lines, header)
    files = []
    pending = [skill]
    while pending:
        for path in sorted(pending.pop().iterdir()):
            if is_link(path):
                raise ValueError(f"Linked skill resource: {path}")
            if path.name in {"__pycache__", ".git", ".DS_Store", "Thumbs.db"} or path.suffix in {".pyc", ".pyo"}:
                continue
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                if path.suffix == ".py":
                    compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
                files.append(path)
            else:
                raise ValueError(f"Unsupported skill resource: {path}")
    return sorted(files)


def package_skill(skill: Path, target: Path) -> dict:
    files = skill_files(skill)
    source = skill.resolve()
    target = target.expanduser().absolute()
    resolved_target = target.resolve()
    if resolved_target == source or source in resolved_target.parents:
        raise ValueError("Archive must be outside the skill source")
    if target.exists() or is_link(target):
        raise ValueError("Archive already exists; no overwrite is permitted")
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryFile(dir=target.parent) as staged:
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                name = f"{skill.name}/{path.relative_to(skill).as_posix()}"
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        staged.seek(0)
        created = False
        try:
            with target.open("xb") as output:
                created = True
                shutil.copyfileobj(staged, output)
        except Exception:
            if created:
                target.unlink()  # Exact new file owned by this invocation, never existing data.
            raise
    return {"archive": str(target), "file_count": len(files),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = package_skill(args.skill.expanduser(), args.output)
    except (OSError, UnicodeError, ValueError, SyntaxError) as exc:
        parser.exit(1, f"Skill packaging failed: {exc}\n")
    print(__import__("json").dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
