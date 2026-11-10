"""Validate the current product-focused repository layout and offline contracts."""
from __future__ import annotations

from pathlib import Path
import py_compile
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.catalog import validate_catalog  # noqa: E402
from gameassetai.distribution import PRODUCT_SKILLS  # noqa: E402
from gameassetai.filesystem import is_link  # noqa: E402
from gameassetai.workspace import validate_workspace  # noqa: E402


REQUIRED = (
    "AGENTS.md", "README.md", "LICENSE", ".gitignore", "pyproject.toml",
    "docs/product-definition.md", "docs/requirements.md", "docs/architecture.md",
    "docs/capabilities.md", "docs/workspace.md", "docs/distribution.md",
    "docs/quality.md", "docs/roadmap.md", "catalog/asset-types/core.json",
    "catalog/styles/core.json", "catalog/generation-providers/core.json",
    "src/gameassetai/cli.py", "src/gameassetai/workspace.py", "src/gameassetai/outputs.py",
    "src/gameassetai/distribution.py", "packaging/skill-entrypoint.py",
    "workspace-template/config/workspace.json",
)
FORBIDDEN_ACTIVE_DOCS = {
    "SESSION_STATE.md", "IMPLEMENTATION_MEMORY.md", "PROJECT_AUDIT.md",
    "SKILL_REUSE_AUDIT.md",
}


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        path = root / relative
        if is_link(path) or not path.is_file():
            errors.append(f"Missing or linked required file: {relative}")
    if errors:
        return errors

    skill_dirs = sorted(path.name for path in (root / "skills").iterdir() if path.is_dir())
    if skill_dirs != sorted(PRODUCT_SKILLS):
        errors.append(f"Product Skill set mismatch: {skill_dirs}")
    for name in PRODUCT_SKILLS:
        entry = root / "skills" / name / "SKILL.md"
        text = entry.read_text(encoding="utf-8-sig")
        if f"name: {name}" not in text or "description:" not in text:
            errors.append(f"Invalid Skill frontmatter: {name}")
        if (root / "skills" / name / "runtime").exists():
            errors.append(f"Generated runtime must not be committed in source Skill: {name}")

    for forbidden in FORBIDDEN_ACTIVE_DOCS:
        if any(path.name == forbidden for path in (root / "docs").rglob("*")):
            errors.append(f"Historical active-state document remains: {forbidden}")

    try:
        validate_catalog(root / "catalog")
    except Exception as exc:  # report all validation failures together
        errors.append(f"Catalog validation failed: {exc}")
    try:
        validate_workspace(root / "workspace-template")
    except Exception as exc:
        errors.append(f"Workspace template validation failed: {exc}")

    for path in sorted((root / "src").rglob("*.py")) + sorted((root / "scripts").glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"Python compile failed: {path.relative_to(root)}: {exc}")

    forbidden_fragments = ("D:/Blender/MCP_Test", "D:\\Blender\\MCP_Test", "B1-B8 is active")
    for area in ("src", "skills", "scripts", "packaging", "workspace-template", "catalog"):
        for path in (root / area).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".json", ".toml", ".yaml"}:
                if path.resolve() == Path(__file__).resolve():
                    continue
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except UnicodeError:
                    continue
                if any(fragment in text for fragment in forbidden_fragments):
                    errors.append(f"Active source contains legacy hard-coded authority/path: {path.relative_to(root)}")
    return errors


def main() -> int:
    errors = validate_repository()
    if errors:
        print("Repository validation failed.")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Repository structure, catalogs, Workspace template, Skills, and Python syntax are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
