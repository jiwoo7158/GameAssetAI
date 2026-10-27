"""Temporary real-Workspace Profile check. Refuses active games and concurrent edits."""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from validate_workspace import is_link, read_json_object, validate_workspace


def profile_bytes(token, side):
    budget = 10 if side == "a" else 20
    return (f"# Synthetic GameAssetAI test {token} {side}\n\n"
            f"Temporary validation fixture, not durable game rules.\n"
            f"For the explicitly inspected Cube only, max_triangles: {budget}.\n"
            "Engine, materials, UV, art style, rig and export rules are unspecified.\n").encode()


def active_bytes(state, side):
    original = json.loads(base64.b64decode(state["original"]).decode("utf-8-sig"))
    original["profile"] = f"GAI_Check_{state['token']}_{side}"
    return (json.dumps(original, ensure_ascii=False, indent=2) + "\n").encode()


def replace_owned(path, contents):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(contents)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def operate(action, workspace, manifest):
    workspace = workspace.expanduser().absolute()
    manifest = manifest.expanduser().absolute()
    if any(is_link(p) for p in (workspace, *workspace.parents, manifest, *manifest.parents)):
        raise ValueError("Linked fixture paths are not supported")
    errors = validate_workspace(workspace)
    if errors:
        raise ValueError("; ".join(errors))
    reference = workspace / "config" / "active-profile.json"
    if action == "start":
        if manifest.exists():
            raise ValueError("State already exists; restore the previous check first")
        if read_json_object(reference)["profile"] is not None:
            raise ValueError("Real active Profile selected; temporary check refuses it")
        state = {"workspace": str(workspace), "token": uuid.uuid4().hex,
                 "original": base64.b64encode(reference.read_bytes()).decode(), "side": None}
        manifest.parent.mkdir(parents=True, exist_ok=True)
        with manifest.open("x", encoding="utf-8") as handle:
            json.dump(state, handle)
        # Persist restoration evidence before any Workspace mutation.
        for side in ("a", "b"):
            path = workspace / "profiles" / f"GAI_Check_{state['token']}_{side}.md"
            with path.open("xb") as handle:
                handle.write(profile_bytes(state["token"], side))
        return state
    state = read_json_object(manifest)
    if state["workspace"] != str(workspace) or uuid.UUID(hex=state["token"]).hex != state["token"]:
        raise ValueError("Fixture ownership/path mismatch")
    original = base64.b64decode(state["original"], validate=True)
    if json.loads(original.decode("utf-8-sig"))["profile"] is not None:
        raise ValueError("Fixture original must be null")
    # Recognize either exact fixture config after interruption between config/state writes.
    expected = {original, active_bytes(state, "a"), active_bytes(state, "b")}
    if reference.read_bytes() not in expected:
        raise ValueError("Active config changed outside fixture; preserve it and stop")
    for side in ("a", "b"):
        path = workspace / "profiles" / f"GAI_Check_{state['token']}_{side}.md"
        if is_link(path) or (path.exists() and path.read_bytes() != profile_bytes(state["token"], side)):
            raise ValueError("Synthetic Profile changed outside fixture; preserve it")
    if action == "restore":
        replace_owned(reference, original)
        for side in ("a", "b"):
            (workspace / "profiles" / f"GAI_Check_{state['token']}_{side}.md").unlink(missing_ok=True)
        manifest.unlink()
        return {"restored": True, "workspace": str(workspace)}
    if action not in {"a", "b"}:
        raise ValueError("Unknown fixture action")
    replace_owned(reference, active_bytes(state, action))
    state["side"] = action
    replace_owned(manifest, json.dumps(state).encode())
    return state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("start", "a", "b", "restore"))
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--state", required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(operate(args.action, args.workspace, args.state)))
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        parser.exit(1, f"Temporary Profile check failed: {exc}\n")


if __name__ == "__main__":
    main()
