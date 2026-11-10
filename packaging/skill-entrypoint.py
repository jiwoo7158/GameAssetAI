"""Self-contained entrypoint copied into each installed GameAssetAI Skill."""
from pathlib import Path
import sys


RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
if not RUNTIME.is_dir():
    raise SystemExit(f"Bundled GameAssetAI runtime is missing: {RUNTIME}")
sys.path.insert(0, str(RUNTIME))

from gameassetai.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
