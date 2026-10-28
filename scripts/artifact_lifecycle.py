"""Create, verify and safely clean GameAssetAI development artifact runs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import uuid


SCHEMA = "gameassetai.artifact-run.v1"
CLASSES = {"ACCEPTED_EVIDENCE", "TEMPORARY_RUN", "EXTERNAL_INPUT"}
SAFE_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_link(path: Path) -> bool:
    junction = getattr(path, "is_junction", None)
    return path.is_symlink() or bool(junction and junction())


def _real_directory(path: Path, *, create=False) -> Path:
    path = path.expanduser().absolute()
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if _is_link(path) or not path.is_dir():
        raise ValueError(f"Expected a real directory: {path}")
    return path.resolve(strict=True)


def _automatic_protected_ancestor(path: Path) -> Path | None:
    for candidate in (path, *path.parents):
        if (candidate / ".git").is_dir():
            return candidate
        if ((candidate / ".agents" / "skills").is_dir()
                and (candidate / "config").is_dir()):
            return candidate
    return None


def _git_identity(repo: Path) -> dict:
    repo = _real_directory(repo)
    try:
        commit = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True,
            capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"], check=True,
            capture_output=True, text=True).stdout.strip())
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ValueError(f"Repository identity unavailable: {repo}") from exc
    return {"commit": commit, "dirty": dirty}


def _parse_input(spec: str) -> dict:
    parts = spec.split("::")
    if len(parts) > 4:
        raise ValueError("Input metadata accepts source, license and reacquisition fields")
    try:
        kind, text = parts[0].split(":", 1)
    except ValueError as exc:
        raise ValueError("Input must be CLASS:absolute-path") from exc
    if kind != "EXTERNAL_INPUT":
        raise ValueError("Only EXTERNAL_INPUT may point outside the run")
    path = Path(text).expanduser().absolute()
    if _is_link(path) or not path.is_file():
        raise ValueError(f"Input must be an existing regular non-link file: {path}")
    path = path.resolve(strict=True)
    metadata = parts[1:] + [None] * (3 - len(parts[1:]))
    return {"classification": kind, "path": str(path), "bytes": path.stat().st_size,
            "sha256": _sha256(path), "source": metadata[0] or None,
            "license": metadata[1] or None, "reacquisition": metadata[2] or None}


def create_run(*, root: Path, milestone: str, case: str, purpose: str, skill: str,
               skill_version: str, repo: Path, inputs=(), now=None) -> dict:
    if not SAFE_TOKEN.fullmatch(milestone) or not SAFE_TOKEN.fullmatch(case):
        raise ValueError("milestone and case must be portable 1-64 character tokens")
    requested_root = root.expanduser().absolute()
    protected = _automatic_protected_ancestor(requested_root)
    if protected is not None:
        raise ValueError(f"Artifact root may not be inside Repository/Workspace: {protected}")
    root = _real_directory(requested_root, create=True)
    protected = _automatic_protected_ancestor(root)
    if protected is not None:
        raise ValueError(f"Artifact root may not be inside Repository/Workspace: {protected}")
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{case}-{uuid.uuid4().hex[:8]}"
    run = root / milestone / run_id
    if run.exists() or _is_link(run):
        raise FileExistsError(run)
    run.mkdir(parents=True)
    try:
        (run / "previews").mkdir()
        (run / "logs").mkdir()
        identity = _git_identity(repo)
        manifest = {
            "schema": SCHEMA, "run_id": run_id, "milestone": milestone,
            "case": case, "purpose": purpose,
            "skill": {"name": skill, "version": skill_version},
            "repository": {"commit": identity["commit"], "dirty": identity["dirty"]},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "inputs": [_parse_input(item) for item in inputs], "artifacts": [],
            "validation": {"status": "pending"}, "preservation": "TEMPORARY_RUN",
            "reproduction": None, "deletion_eligible": False,
        }
        manifest["manifest_sha256"] = hashlib.sha256(_canonical(manifest).encode()).hexdigest()
        (run / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    except Exception:
        shutil.rmtree(run)
        raise
    return {"run_directory": str(run), "manifest": str(run / "manifest.json")}


def _load_run(run: Path) -> tuple[Path, dict]:
    run = _real_directory(run)
    manifest_path = run / "manifest.json"
    if _is_link(manifest_path) or not manifest_path.is_file():
        raise ValueError("Run has no real manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or manifest.get("run_id") != run.name:
        raise ValueError("Run manifest identity is invalid")
    return run, manifest


def finalize_run(*, run: Path, status: str, preservation: str, reproduction: str,
                 artifacts: tuple[str, ...], deletion_eligible=False) -> dict:
    run, manifest = _load_run(run)
    if preservation not in {"ACCEPTED_EVIDENCE", "TEMPORARY_RUN"}:
        raise ValueError("Run preservation must be ACCEPTED_EVIDENCE or TEMPORARY_RUN")
    rows = []
    for spec in artifacts:
        try:
            classification, relative = spec.split(":", 1)
        except ValueError as exc:
            raise ValueError("Artifact must be CLASS:relative-path") from exc
        if classification not in {"ACCEPTED_EVIDENCE", "TEMPORARY_RUN"}:
            raise ValueError("Artifact classification is invalid")
        candidate = run / Path(relative)
        if _is_link(candidate) or not candidate.is_file():
            raise ValueError(f"Artifact must be a regular non-link file: {relative}")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(run):
            raise ValueError("Artifact escaped its run directory")
        rows.append({"classification": classification,
                     "path": resolved.relative_to(run).as_posix(),
                     "bytes": resolved.stat().st_size, "sha256": _sha256(resolved)})
    registered = {row["path"] for row in rows}
    actual = set()
    for base, dirs, files in os.walk(run, followlinks=False):
        for name in dirs + files:
            item = Path(base) / name
            if _is_link(item):
                raise ValueError(f"Run contains an unowned link: {item}")
        for name in files:
            item = Path(base) / name
            relative = item.relative_to(run).as_posix()
            if relative != "manifest.json":
                actual.add(relative)
    if registered != actual:
        missing = sorted(actual - registered)
        stale = sorted(registered - actual)
        raise ValueError(f"Artifact registration must be exact; unregistered={missing}, stale={stale}")
    manifest.update(artifacts=rows, validation={"status": status},
                    preservation=preservation, reproduction=reproduction,
                    deletion_eligible=bool(deletion_eligible))
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = hashlib.sha256(_canonical(manifest).encode()).hexdigest()
    (run / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return verify_run(run)


def verify_run(run: Path) -> dict:
    run, manifest = _load_run(run)
    failures = []
    saved = manifest.pop("manifest_sha256", None)
    actual_manifest_hash = hashlib.sha256(_canonical(manifest).encode()).hexdigest()
    manifest["manifest_sha256"] = saved
    if saved != actual_manifest_hash:
        failures.append("manifest hash mismatch")
    for row in manifest.get("inputs", []):
        path = Path(row.get("path", ""))
        if _is_link(path) or not path.is_file() or _sha256(path) != row.get("sha256"):
            failures.append(f"input unavailable or changed: {path}")
    for row in manifest.get("artifacts", []):
        path = run / row.get("path", "")
        if (_is_link(path) or not path.is_file() or not path.resolve().is_relative_to(run)
                or _sha256(path) != row.get("sha256")):
            failures.append(f"artifact unavailable or changed: {row.get('path')}")
    return {"status": "pass" if not failures else "failed", "run_directory": str(run),
            "failures": failures, "artifact_count": len(manifest.get("artifacts", []))}


def cleanup_runs(*, root: Path, runs: tuple[Path, ...], apply=False,
                 protected: tuple[Path, ...] = ()) -> dict:
    root = _real_directory(root)
    protected_paths = [path.expanduser().absolute().resolve(strict=True) for path in protected]
    selected = []
    for candidate in runs:
        run, manifest = _load_run(candidate)
        automatic = _automatic_protected_ancestor(run)
        if automatic is not None:
            raise ValueError(f"Cleanup target is inside Repository/Workspace: {automatic}")
        if not run.is_relative_to(root) or run == root:
            raise ValueError(f"Cleanup target is outside the exact artifact root: {run}")
        if any(run == item or run.is_relative_to(item) or item.is_relative_to(run)
               for item in protected_paths):
            raise ValueError(f"Cleanup target intersects a protected path: {run}")
        if manifest.get("preservation") != "TEMPORARY_RUN" or not manifest.get("deletion_eligible"):
            raise ValueError(f"Run is not explicitly deletion-eligible: {run}")
        verification = verify_run(run)
        if verification["status"] != "pass":
            raise ValueError(f"Run verification failed before cleanup: {verification['failures']}")
        for base, dirs, files in os.walk(run, followlinks=False):
            for name in dirs + files:
                if _is_link(Path(base) / name):
                    raise ValueError(f"Cleanup target contains a link: {Path(base) / name}")
        size = sum((Path(base) / name).stat().st_size
                   for base, _, files in os.walk(run) for name in files)
        selected.append((run, size))
    if apply:
        for run, _ in selected:
            shutil.rmtree(run)
    return {"mode": "apply" if apply else "dry-run", "count": len(selected),
            "bytes": sum(size for _, size in selected),
            "targets": [str(run) for run, _ in selected]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--root", required=True, type=Path)
    create.add_argument("--milestone", required=True); create.add_argument("--case", required=True)
    create.add_argument("--purpose", required=True); create.add_argument("--skill", required=True)
    create.add_argument("--skill-version", required=True); create.add_argument("--repo", required=True, type=Path)
    create.add_argument("--input", action="append", default=[])
    finish = commands.add_parser("finalize")
    finish.add_argument("--run", required=True, type=Path); finish.add_argument("--status", required=True)
    finish.add_argument("--preservation", required=True); finish.add_argument("--reproduction", required=True)
    finish.add_argument("--artifact", action="append", default=[])
    finish.add_argument("--deletion-eligible", action="store_true")
    verify = commands.add_parser("verify"); verify.add_argument("--run", required=True, type=Path)
    clean = commands.add_parser("cleanup"); clean.add_argument("--root", required=True, type=Path)
    clean.add_argument("--run", required=True, action="append", type=Path)
    clean.add_argument("--protect", action="append", default=[], type=Path)
    clean.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "create":
            result = create_run(root=args.root, milestone=args.milestone, case=args.case,
                                purpose=args.purpose, skill=args.skill,
                                skill_version=args.skill_version, repo=args.repo, inputs=args.input)
        elif args.command == "finalize":
            result = finalize_run(run=args.run, status=args.status,
                                  preservation=args.preservation,
                                  reproduction=args.reproduction,
                                  artifacts=tuple(args.artifact),
                                  deletion_eligible=args.deletion_eligible)
        elif args.command == "verify":
            result = verify_run(args.run)
        else:
            result = cleanup_runs(root=args.root, runs=tuple(args.run), apply=args.apply,
                                  protected=tuple(args.protect))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"Artifact lifecycle failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
