"""Validate the current product-focused repository layout and offline contracts."""
from __future__ import annotations

import hashlib
from pathlib import Path
import py_compile
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.catalog import validate_catalog  # noqa: E402
from gameassetai.distribution import PRODUCT_SKILLS  # noqa: E402
from gameassetai import __version__  # noqa: E402
from gameassetai.filesystem import is_link  # noqa: E402
from gameassetai.workspace import validate_workspace  # noqa: E402


REQUIRED = (
    "AGENTS.md", "README.md", "LICENSE", ".gitignore", "pyproject.toml",
    "docs/product-definition.md", "docs/requirements.md", "docs/architecture.md",
    "docs/capabilities.md", "docs/workspace.md", "docs/distribution.md",
    "docs/quality.md", "docs/roadmap.md", "catalog/asset-types/core.json",
    "catalog/styles/core.json", "catalog/generation-providers/core.json",
    "src/gameassetai/cli.py", "src/gameassetai/workspace.py", "src/gameassetai/outputs.py",
    "src/gameassetai/distribution.py", "src/gameassetai/environment.py",
    "packaging/skill-entrypoint.py",
    "packaging/workspace-distribution/README.md",
    "packaging/workspace-distribution/.gitattributes",
    "packaging/workspace-distribution/.gitignore",
    "workspace-template/config/workspace.json", ".github/workflows/ci.yml",
    ".github/workflows/publish-workspace.yml",
)
FORBIDDEN_ACTIVE_DOCS = {
    "SESSION_STATE.md", "IMPLEMENTATION_MEMORY.md", "PROJECT_AUDIT.md",
    "SKILL_REUSE_AUDIT.md",
}
ISOLATED_LEGACY_CODE_ROOTS = (
    "archive/legacy/src/gameassetai/blender",
    "archive/legacy/blender_addon/gameassetai",
    "archive/legacy/tests/retained_blender",
)
ACTIVE_PYTHON_ROOTS = ("src", "scripts", "tests", "packaging", "blender_addon")
PRODUCT_PYTHON_ROOTS = {"src", "scripts", "packaging", "blender_addon"}
LEGACY_REFERENCE_FRAGMENTS = ("archive/legacy", "archive\\legacy", "archive.legacy")
LEGACY_PATH_EXPRESSIONS = (
    re.compile(r'''["']archive["']\s*\)?\s*/\s*["']legacy["']'''),
    re.compile(r'''["']archive["']\s*,\s*["']legacy["']'''),
    re.compile(r'''["']archive["']\s*\)?\s*\.joinpath\(\s*["']legacy["']'''),
)


def _references_isolated_legacy(source: str) -> bool:
    return any(fragment in source for fragment in LEGACY_REFERENCE_FRAGMENTS) or any(
        pattern.search(source) for pattern in LEGACY_PATH_EXPRESSIONS
    )


def _git_tracked_files(root: Path) -> tuple[set[str] | None, str | None]:
    if not (root / ".git").exists():
        return None, None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return None, f"Cannot inspect Git tracked files: {exc}"
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        return None, f"Cannot inspect Git tracked files: {message or result.returncode}"
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0") if item
    }, None


def validate_repository(
    root: Path = ROOT, *, tracked_files: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    if tracked_files is None:
        tracked_files, git_error = _git_tracked_files(root)
        if git_error:
            errors.append(git_error)
    for relative in REQUIRED:
        path = root / relative
        if is_link(path) or not path.is_file():
            errors.append(f"Missing or linked required file: {relative}")
        elif tracked_files is not None and relative not in tracked_files:
            errors.append(f"Required product source is not tracked by Git: {relative}")
    if errors:
        return errors

    skill_dirs = sorted(path.name for path in (root / "skills").iterdir() if path.is_dir())
    if skill_dirs != sorted(PRODUCT_SKILLS):
        errors.append(f"Product Skill set mismatch: {skill_dirs}")
    for name in PRODUCT_SKILLS:
        entry = root / "skills" / name / "SKILL.md"
        relative_entry = entry.relative_to(root).as_posix()
        if tracked_files is not None and relative_entry not in tracked_files:
            errors.append(f"Required Skill source is not tracked by Git: {relative_entry}")
        if is_link(entry) or not entry.is_file():
            errors.append(f"Missing or linked Skill entrypoint: {relative_entry}")
            continue
        text = entry.read_text(encoding="utf-8-sig")
        if f"name: {name}" not in text or "description:" not in text:
            errors.append(f"Invalid Skill frontmatter: {name}")
        if (root / "skills" / name / "runtime").exists():
            errors.append(f"Generated runtime must not be committed in source Skill: {name}")

    ignore_lines = {
        line.strip() for line in (root / ".gitignore").read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    if "/output/" not in ignore_lines:
        errors.append("Development experiment root must be ignored with the anchored /output/ rule")
    if tracked_files is not None:
        tracked_output = sorted(path for path in tracked_files if path.startswith("output/"))
        if tracked_output:
            errors.append(f"Development experiment output is Git-tracked: {tracked_output}")

    retained_legacy_tests = root / "tests" / "retained_blender"
    if retained_legacy_tests.exists() or is_link(retained_legacy_tests):
        errors.append("Unverified retained Blender tests remain in the active test suite")
    if tracked_files is not None:
        retained_legacy = sorted(
            path for path in tracked_files if path.startswith("tests/retained_blender/")
        )
        if retained_legacy:
            errors.append(f"Unverified retained Blender tests are tracked: {retained_legacy}")

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8-sig")
    if 'dynamic = ["version"]' not in pyproject:
        errors.append("pyproject.toml must obtain the product version dynamically")
    if 'version = {attr = "gameassetai.__version__"}' not in pyproject:
        errors.append("pyproject.toml must use gameassetai.__version__ as the version source")
    for line in pyproject.splitlines():
        if line.strip().startswith("version = ") and "attr =" not in line:
            errors.append("pyproject.toml contains a second authored product version")
    if not __version__ or not all(part.isdigit() for part in __version__.split(".")):
        errors.append(f"Invalid canonical product version: {__version__!r}")

    distribution_ignore = {
        line.strip()
        for line in (root / "packaging" / "workspace-distribution" / ".gitignore")
        .read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    required_personal_ignores = {
        "/config/", "/profiles/", "/notes/", "/outputs/", "/AGENTS.local.md", "/.local/",
    }
    if not required_personal_ignores.issubset(distribution_ignore):
        errors.append("Workspace distribution .gitignore does not protect every personal path")

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

    active_python: list[Path] = []
    for relative in ACTIVE_PYTHON_ROOTS:
        directory = root / relative
        if directory.is_dir() and not is_link(directory):
            active_python.extend(path for path in directory.rglob("*.py") if path.is_file())
    active_python = sorted(set(active_python))

    isolated_hashes: dict[str, list[str]] = {}
    for relative in ISOLATED_LEGACY_CODE_ROOTS:
        directory = root / relative
        if not directory.is_dir() or is_link(directory):
            continue
        for path in sorted(directory.rglob("*.py")):
            if path.is_file() and not is_link(path):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                isolated_hashes.setdefault(digest, []).append(path.relative_to(root).as_posix())

    for path in active_python:
        relative_path = path.relative_to(root).as_posix()
        try:
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            errors.append(f"Python compile failed: {path.relative_to(root)}: {exc}")
        try:
            source = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        top_level = relative_path.split("/", 1)[0]
        if (
            top_level in PRODUCT_PYTHON_ROOTS
            and relative_path != "scripts/validate_repo.py"
            and _references_isolated_legacy(source)
        ):
            errors.append(f"Active Python depends on isolated legacy: {path.relative_to(root)}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in isolated_hashes:
            errors.append(
                "Active Python duplicates isolated legacy without adoption: "
                f"{path.relative_to(root)} matches {isolated_hashes[digest]}"
            )

    forbidden_fragments = ("D:/Blender/MCP_Test", "D:\\Blender\\MCP_Test", "B1-B8 is active")
    for area in ("src", "skills", "scripts", "packaging", "workspace-template", "catalog"):
        for path in (root / area).rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".md", ".json", ".toml", ".yaml"}:
                if path.relative_to(root).as_posix() == "scripts/validate_repo.py":
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
