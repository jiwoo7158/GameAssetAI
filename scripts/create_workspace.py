"""Compatibility entrypoint for safe Workspace create-or-connect."""
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["workspace", "create", *sys.argv[1:], "--template", str(ROOT / "workspace-template")]))
