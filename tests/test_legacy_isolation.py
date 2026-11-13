from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHILD_FLAG = "GAMEASSETAI_ARCHIVE_ABSENT_CHILD"


class LegacyIsolationTests(unittest.TestCase):
    def test_product_checkout_passes_without_the_complete_archive(self) -> None:
        if os.environ.get(CHILD_FLAG) == "1":
            return
        with tempfile.TemporaryDirectory(prefix="gameassetai-without-legacy-") as temp:
            checkout = Path(temp) / "checkout"
            shutil.copytree(
                ROOT,
                checkout,
                ignore=shutil.ignore_patterns(
                    ".git", "archive", ".local", "output", "__pycache__", "*.pyc",
                ),
            )
            self.assertFalse((checkout / "archive").exists())
            for command in (
                ["git", "init", "-b", "archive-absent"],
                ["git", "add", "-A"],
            ):
                result = subprocess.run(
                    command, cwd=checkout, capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(0, result.returncode, result.stderr)

            environment = os.environ.copy()
            environment[CHILD_FLAG] = "1"
            commands = (
                [sys.executable, "-B", "scripts/validate_repo.py"],
                [
                    sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests",
                    "-p", "test_*.py", "-v",
                ],
            )
            for command in commands:
                result = subprocess.run(
                    command,
                    cwd=checkout,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                self.assertEqual(
                    0,
                    result.returncode,
                    f"archive-absent command failed: {command}\n{result.stdout}\n{result.stderr}",
                )


if __name__ == "__main__":
    unittest.main()
