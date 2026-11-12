from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.environment import (  # noqa: E402
    DIAGNOSTIC_PREFIX,
    configure_blender_executable,
    read_local_environment,
    validate_blender_environment,
)
from gameassetai.errors import ValidationError  # noqa: E402


class LocalBlenderEnvironmentTests(unittest.TestCase):
    def test_configuration_is_local_atomic_and_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / ("blender.exe" if __import__("os").name == "nt" else "blender")
            executable.write_bytes(b"placeholder")

            configured = configure_blender_executable(root, executable)
            loaded = read_local_environment(root)

            self.assertEqual(configured["status"], "configured")
            self.assertEqual(loaded["blender"]["executable"], str(executable.absolute()))
            self.assertTrue((root / ".local" / "environment.json").is_file())

    def test_missing_or_invalid_executable_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValidationError, "not configured"):
                read_local_environment(root)
            with self.assertRaisesRegex(ValidationError, "does not exist"):
                configure_blender_executable(root, root / "missing-blender")

    def test_diagnostic_checks_factory_session_and_python_error_propagation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / ("blender.exe" if __import__("os").name == "nt" else "blender")
            executable.write_bytes(b"placeholder")
            configure_blender_executable(root, executable)
            payload = {
                "background": True,
                "blender": "5.2.4 LTS",
                "filepath": "",
                "python": "3.13.13",
            }
            success = subprocess.CompletedProcess(
                [], 0, stdout=DIAGNOSTIC_PREFIX + json.dumps(payload) + "\n", stderr="",
            )
            failure = subprocess.CompletedProcess(
                [], 7, stdout="", stderr="RuntimeError: gameassetai-diagnostic-error",
            )
            with mock.patch("gameassetai.environment.subprocess.run", side_effect=[success, failure]):
                result = validate_blender_environment(root)

            self.assertEqual(result["diagnostic"], payload)
            self.assertEqual(result["python_error_exit_code"], 7)

    def test_failed_reconfiguration_preserves_existing_setting(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / ("blender.exe" if __import__("os").name == "nt" else "blender")
            executable.write_bytes(b"placeholder")
            configure_blender_executable(root, executable)
            before = (root / ".local" / "environment.json").read_bytes()

            with self.assertRaises(ValidationError):
                configure_blender_executable(root, root / "missing")

            self.assertEqual((root / ".local" / "environment.json").read_bytes(), before)

    def test_configuration_refuses_non_file_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executable = root / ("blender.exe" if __import__("os").name == "nt" else "blender")
            executable.write_bytes(b"placeholder")
            destination = root / ".local" / "environment.json"
            destination.mkdir(parents=True)

            with self.assertRaisesRegex(ValidationError, "must be a file"):
                configure_blender_executable(root, executable)

            self.assertTrue(destination.is_dir())


if __name__ == "__main__":
    unittest.main()
