from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import uuid
import zipfile
from typing import Any

from .errors import SafetyError, ValidationError
from .filesystem import canonical_json, is_link, reject_linked_components


BUNDLE_SCHEMA = "gameassetai.skill-bundle.v1"
SKILL_SCHEMA = "gameassetai.installed-skill.v1"
PRODUCT_SKILLS = (
    "gameassetai-workspace",
    "gameassetai-create-asset",
    "gameassetai-modify-asset",
    "gameassetai-output-asset",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in sorted(root.rglob("*")):
        if is_link(path):
            raise SafetyError(f"Linked bundle component: {path}")
        if path.name in {"__pycache__", ".DS_Store", "Thumbs.db"} or path.suffix in {".pyc", ".pyo"}:
            continue
        if path.is_file():
            result.append(path)
        elif not path.is_dir():
            raise SafetyError(f"Unsupported bundle component: {path}")
    return result


def _manifest(root: Path, *, exclude: set[str] | None = None) -> dict[str, str]:
    excluded = exclude or set()
    return {
        path.relative_to(root).as_posix(): _hash(path)
        for path in _files(root)
        if path.relative_to(root).as_posix() not in excluded
    }


def _copy_tree(source: Path, destination: Path, *, python_only: bool = False) -> None:
    if is_link(source) or not source.is_dir():
        raise SafetyError(f"Source must be a real directory: {source}")
    for path in _files(source):
        if python_only and path.suffix != ".py":
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as output:
            output.write(path.read_bytes())


def _validate_skill_source(path: Path, expected_name: str) -> None:
    entry = path / "SKILL.md"
    if is_link(path) or not path.is_dir() or is_link(entry) or not entry.is_file():
        raise ValidationError(f"Invalid Skill source: {path}")
    lines = entry.read_text(encoding="utf-8-sig").splitlines()
    if len(lines) < 4 or lines[0] != "---" or "---" not in lines[1:]:
        raise ValidationError(f"Skill frontmatter is missing: {path}")
    end = lines[1:].index("---") + 1
    header = lines[1:end]
    names = [line.removeprefix("name:").strip() for line in header if line.startswith("name:")]
    if names != [expected_name]:
        raise ValidationError(f"Skill name does not match directory: {path}")
    if not any(line.startswith("description:") and line.split(":", 1)[1].strip() for line in header):
        raise ValidationError(f"Skill description is missing: {path}")


def build_product_bundle(repo_root: Path, destination: Path) -> dict[str, Any]:
    repo_root = repo_root.expanduser().absolute()
    reject_linked_components(repo_root)
    repo_root = repo_root.resolve()
    destination = destination.expanduser().absolute()
    if destination.exists() or is_link(destination):
        raise SafetyError(f"Bundle destination already exists: {destination}")
    reject_linked_components(destination)
    source_runtime = repo_root / "src" / "gameassetai"
    source_catalog = repo_root / "catalog"
    source_template = repo_root / "workspace-template"
    entrypoint = repo_root / "packaging" / "skill-entrypoint.py"
    if not entrypoint.is_file() or is_link(entrypoint):
        raise ValidationError("Missing packaging/skill-entrypoint.py")
    for name in PRODUCT_SKILLS:
        _validate_skill_source(repo_root / "skills" / name, name)

    destination.parent.mkdir(parents=True, exist_ok=True)
    reject_linked_components(destination.parent)
    stage = Path(tempfile.mkdtemp(prefix=".gameassetai-bundle-", dir=destination.parent))
    try:
        skills_root = stage / "skills"
        skills_root.mkdir()
        for name in PRODUCT_SKILLS:
            source_skill = repo_root / "skills" / name
            target = skills_root / name
            target.mkdir()
            _copy_tree(source_skill, target)
            runtime = target / "runtime" / "gameassetai"
            runtime.mkdir(parents=True)
            _copy_tree(source_runtime, runtime, python_only=True)
            data = runtime / "data"
            data.mkdir()
            (data / "__init__.py").write_text("\"\"\"Packaged product data.\"\"\"\n", encoding="utf-8")
            _copy_tree(source_catalog, data / "catalog")
            _copy_tree(source_template, data / "workspace-template")
            scripts = target / "scripts"
            scripts.mkdir(exist_ok=True)
            shutil.copy2(entrypoint, scripts / "gameassetai.py")
            for python in target.rglob("*.py"):
                compile(python.read_text(encoding="utf-8-sig"), str(python), "exec")
            skill_manifest = {
                "schema": SKILL_SCHEMA,
                "skill": name,
                "runtime": "runtime/gameassetai",
                "files": _manifest(target, exclude={"manifest.json"}),
            }
            (target / "manifest.json").write_text(canonical_json(skill_manifest), encoding="utf-8")

        bundle_manifest = {
            "schema": BUNDLE_SCHEMA,
            "version": "0.2.0",
            "skills": list(PRODUCT_SKILLS),
            "files": _manifest(stage, exclude={"manifest.json"}),
        }
        (stage / "manifest.json").write_text(canonical_json(bundle_manifest), encoding="utf-8")
        stage.rename(destination)
    except BaseException:
        if stage.exists() and not is_link(stage):
            shutil.rmtree(stage)
        raise
    return {"status": "built", "bundle": str(destination), "skills": list(PRODUCT_SKILLS)}


def validate_product_bundle(bundle: Path) -> dict[str, Any]:
    bundle = bundle.expanduser().absolute()
    reject_linked_components(bundle)
    if is_link(bundle) or not bundle.is_dir():
        raise ValidationError(f"Bundle must be a real directory: {bundle}")
    manifest_path = bundle / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"Cannot read bundle manifest: {exc}") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema") != BUNDLE_SCHEMA
        or manifest.get("skills") != list(PRODUCT_SKILLS)
        or not isinstance(manifest.get("files"), dict)
    ):
        raise ValidationError("Invalid product bundle manifest")
    actual = _manifest(bundle, exclude={"manifest.json"})
    if actual != manifest["files"]:
        raise ValidationError("Product bundle hashes do not match its manifest")
    for name in PRODUCT_SKILLS:
        skill = bundle / "skills" / name
        _validate_skill_source(skill, name)
        skill_manifest = json.loads((skill / "manifest.json").read_text(encoding="utf-8-sig"))
        if (
            skill_manifest.get("schema") != SKILL_SCHEMA
            or skill_manifest.get("skill") != name
            or skill_manifest.get("files") != _manifest(skill, exclude={"manifest.json"})
        ):
            raise ValidationError(f"Installed Skill manifest mismatch: {name}")
    return {"status": "valid", "bundle": str(bundle), "skills": list(PRODUCT_SKILLS)}


def validate_installed_product(skills_dir: Path) -> dict[str, Any]:
    skills_dir = skills_dir.expanduser().absolute()
    reject_linked_components(skills_dir)
    if is_link(skills_dir) or not skills_dir.is_dir():
        raise ValidationError(f"Installed Skills root must be a real directory: {skills_dir}")
    for name in PRODUCT_SKILLS:
        skill = skills_dir / name
        _validate_skill_source(skill, name)
        manifest_path = skill / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValidationError(f"Cannot read installed Skill manifest for {name}: {exc}") from exc
        if (
            manifest.get("schema") != SKILL_SCHEMA
            or manifest.get("skill") != name
            or manifest.get("files") != _manifest(skill, exclude={"manifest.json"})
        ):
            raise ValidationError(f"Installed Skill manifest mismatch: {name}")
    return {"status": "valid", "skills_dir": str(skills_dir), "skills": list(PRODUCT_SKILLS)}


def install_product_bundle(bundle: Path, skills_dir: Path) -> dict[str, Any]:
    validate_product_bundle(bundle)
    skills_dir = skills_dir.expanduser().absolute()
    reject_linked_components(skills_dir)
    if skills_dir.exists() and not skills_dir.is_dir():
        raise SafetyError(f"Skill installation target is not a directory: {skills_dir}")
    existing = [name for name in PRODUCT_SKILLS if (skills_dir / name).exists() or is_link(skills_dir / name)]
    if existing:
        raise SafetyError(f"Refusing to overwrite installed Skills: {', '.join(existing)}")
    skills_dir.mkdir(parents=True, exist_ok=True)
    reject_linked_components(skills_dir)
    if is_link(skills_dir) or not skills_dir.is_dir():
        raise SafetyError(f"Skill installation target must be a real directory: {skills_dir}")
    stage = skills_dir / f".gameassetai-install-{uuid.uuid4().hex}"
    stage.mkdir()
    promoted: list[Path] = []
    try:
        for name in PRODUCT_SKILLS:
            _copy_tree(bundle / "skills" / name, stage / name)
        for name in PRODUCT_SKILLS:
            source = stage / name
            target = skills_dir / name
            source.rename(target)
            promoted.append(target)
        stage.rmdir()
    except BaseException:
        for target in reversed(promoted):
            if target.is_dir() and not is_link(target):
                shutil.rmtree(target)
        if stage.exists() and not is_link(stage):
            shutil.rmtree(stage)
        raise
    return {"status": "installed", "skills_dir": str(skills_dir), "skills": list(PRODUCT_SKILLS)}


def install_project_bundle(
    bundle: Path,
    workspace: Path,
    *,
    template: Path | None = None,
) -> dict[str, Any]:
    """Create/connect a Workspace before installing its project-scoped Skills."""
    from .workspace import create_or_connect_workspace, validate_workspace

    workspace = workspace.expanduser().absolute()
    workspace_result = create_or_connect_workspace(template, workspace)
    if workspace_result["status"] == "legacy-connected":
        raise ValidationError(
            "Project-scoped Skills require a current validated Workspace; migrate the legacy "
            "Workspace only after user review"
        )
    validate_workspace(workspace)
    skills_dir = workspace / ".codex" / "skills"
    install_result = install_product_bundle(bundle, skills_dir)
    installed_result = validate_installed_product(skills_dir)
    return {
        "status": "installed",
        "workspace": str(workspace),
        "workspace_status": workspace_result["status"],
        "skills_dir": str(skills_dir),
        "skills": list(PRODUCT_SKILLS),
        "steps": [
            "workspace-created-or-connected",
            "workspace-validated",
            "skills-installed",
            "installation-validated",
        ],
        "install_status": install_result["status"],
        "validation_status": installed_result["status"],
    }


def update_product_bundle(bundle: Path, skills_dir: Path, backup_root: Path) -> dict[str, Any]:
    validate_product_bundle(bundle)
    skills_dir = skills_dir.expanduser().absolute()
    backup_root = backup_root.expanduser().absolute()
    reject_linked_components(skills_dir)
    reject_linked_components(backup_root)
    if not skills_dir.is_dir():
        raise ValidationError(f"Installed Skills root must be a real directory: {skills_dir}")
    if backup_root.exists() or is_link(backup_root):
        raise SafetyError("Update backup path must not exist")
    resolved_skills = skills_dir.resolve()
    resolved_backup = backup_root.resolve()
    if (
        resolved_skills == resolved_backup
        or resolved_skills in resolved_backup.parents
        or resolved_backup in resolved_skills.parents
    ):
        raise SafetyError("Installed and backup paths must not overlap")
    for name in PRODUCT_SKILLS:
        installed = skills_dir / name
        if is_link(installed) or not installed.is_dir():
            raise ValidationError(f"Expected an existing real installed Skill: {installed}")

    expected = {name: _manifest(bundle / "skills" / name) for name in PRODUCT_SKILLS}
    current = {name: _manifest(skills_dir / name) for name in PRODUCT_SKILLS}
    if current == expected:
        return {"status": "already-aligned", "skills_dir": str(skills_dir), "backup": None}

    stage = skills_dir / f".gameassetai-update-{uuid.uuid4().hex}"
    moved_old: list[str] = []
    promoted: list[str] = []
    try:
        stage.mkdir()
        backup_root.mkdir(parents=True)
        reject_linked_components(backup_root)
        if is_link(backup_root) or not backup_root.is_dir():
            raise SafetyError(f"Update backup must be a real directory: {backup_root}")
        for name in PRODUCT_SKILLS:
            _copy_tree(bundle / "skills" / name, stage / name)
        for name in PRODUCT_SKILLS:
            (skills_dir / name).rename(backup_root / name)
            moved_old.append(name)
            (stage / name).rename(skills_dir / name)
            promoted.append(name)
        stage.rmdir()
    except BaseException:
        for name in reversed(promoted):
            current_new = skills_dir / name
            if current_new.exists() and not is_link(current_new):
                current_new.rename(stage / name)
        for name in reversed(moved_old):
            old = backup_root / name
            if old.exists() and not is_link(old):
                old.rename(skills_dir / name)
        if stage.exists() and not is_link(stage):
            shutil.rmtree(stage)
        if backup_root.exists() and not is_link(backup_root) and not any(backup_root.iterdir()):
            backup_root.rmdir()
        raise
    return {
        "status": "updated",
        "skills_dir": str(skills_dir),
        "backup": str(backup_root),
        "skills": list(PRODUCT_SKILLS),
    }


def write_bundle_zip(bundle: Path, target: Path) -> dict[str, Any]:
    validate_product_bundle(bundle)
    target = target.expanduser().absolute()
    if target.exists() or is_link(target):
        raise SafetyError(f"Archive already exists: {target}")
    reject_linked_components(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    reject_linked_components(target.parent)
    with tempfile.TemporaryFile(dir=target.parent) as staged:
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in _files(bundle):
                relative = path.relative_to(bundle).as_posix()
                info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        staged.seek(0)
        with target.open("xb") as output:
            shutil.copyfileobj(staged, output)
    return {"status": "created", "archive": str(target), "sha256": _hash(target)}
