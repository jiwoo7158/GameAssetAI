from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import SafetyError, ValidationError  # noqa: E402
from gameassetai.external_tools import (  # noqa: E402
    connect_tools_repository,
    initialize_tools_repository,
    list_registered_tools,
    read_tool_registration,
    read_tool_status,
    read_tools_connection,
    record_tool_status,
    register_tool,
    unregister_tool,
    validate_connected_tools_repository,
    validate_tools_repository,
)
from gameassetai.workspace import (  # noqa: E402
    create_or_connect_workspace,
    create_profile,
    validate_workspace,
)


class ExternalToolsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-external-tools-")
        self.addCleanup(self.temporary.cleanup)
        self.parent = Path(self.temporary.name)
        self.workspace = self.parent / "GameAssetAI-Workspace"
        create_or_connect_workspace(ROOT / "workspace-template", self.workspace)

    def test_default_repository_is_created_only_by_explicit_initialization(self) -> None:
        default_root = self.parent / "GameAssetAI-Tools"
        self.assertFalse(default_root.exists())
        self.assertFalse((self.workspace / ".local" / "external-tools.json").exists())
        self.assertEqual("valid", validate_workspace(self.workspace)["status"])
        self.assertEqual("not-connected", read_tools_connection(self.workspace)["status"])

        result = initialize_tools_repository(self.workspace)

        self.assertEqual("initialized", result["status"])
        self.assertEqual("created", result["repository_status"])
        self.assertEqual(str(default_root), result["tools_root"])
        marker = default_root / ".gameassetai-tools.json"
        self.assertTrue(marker.is_file())
        self.assertTrue((default_root / "tools").is_dir())
        self.assertNotIn("registered_tools", json.loads(marker.read_text(encoding="utf-8")))
        self.assertEqual("connected", read_tools_connection(self.workspace)["status"])
        self.assertEqual([], list_registered_tools(self.workspace)["tools"])

    def test_custom_root_requires_absolute_path_and_unknown_directory_is_preserved(self) -> None:
        with self.assertRaisesRegex(ValidationError, "must be absolute"):
            initialize_tools_repository(self.workspace, Path("relative-tools"))

        unknown = self.parent / "existing-user-folder"
        unknown.mkdir()
        personal = unknown / "personal.txt"
        personal.write_text("do not overwrite", encoding="utf-8")
        with self.assertRaises(ValidationError):
            initialize_tools_repository(self.workspace, unknown)
        self.assertEqual("do not overwrite", personal.read_text(encoding="utf-8"))
        self.assertEqual([personal], list(unknown.iterdir()))
        self.assertEqual("not-connected", read_tools_connection(self.workspace)["status"])

        selected = self.parent / "Custom-Tools"
        result = initialize_tools_repository(self.workspace, selected)
        self.assertEqual(str(selected), result["tools_root"])
        self.assertEqual("valid", validate_connected_tools_repository(self.workspace)["status"])

    def test_moved_repository_is_not_recreated_and_can_be_reconnected(self) -> None:
        original = self.parent / "Original-Tools"
        moved = self.parent / "Moved-Tools"
        initialize_tools_repository(self.workspace, original)
        original.rename(moved)

        connection = read_tools_connection(self.workspace)
        self.assertEqual("missing", connection["status"])
        self.assertEqual(str(original), connection["tools_root"])
        self.assertEqual("valid", validate_workspace(self.workspace)["status"])
        self.assertFalse(original.exists())
        with self.assertRaisesRegex(ValidationError, "missing"):
            list_registered_tools(self.workspace)

        reconnected = connect_tools_repository(self.workspace, moved)
        self.assertEqual("connected", reconnected["status"])
        self.assertEqual(str(original), reconnected["previous_tools_root"])
        self.assertEqual(str(moved), read_tools_connection(self.workspace)["tools_root"])
        self.assertFalse(original.exists())

    def test_registration_status_and_unregister_preserve_payload(self) -> None:
        tools_root = self.parent / "GameAssetAI-Tools"
        initialize_tools_repository(self.workspace, tools_root)
        payload = tools_root / "tools" / "sample-cli" / "source"
        payload.mkdir(parents=True)
        payload_file = payload / "README.txt"
        payload_file.write_text("user-owned external source", encoding="utf-8")

        registration = register_tool(
            self.workspace,
            "sample-cli",
            name="Sample CLI",
            kind="system-cli",
            source="https://example.invalid/sample-cli",
            license_name="Example-License",
            install_method="existing",
            location=str(payload),
            external_identifier="sample-cli",
            version="1.0.0",
            capabilities=["mesh-inspection"],
        )
        self.assertEqual("registered", registration["status"])
        self.assertEqual("not-inspected", registration["inspection_status"])
        self.assertNotIn("status.json", [path.name for path in payload.parent.iterdir()])
        listed = list_registered_tools(self.workspace)["tools"]
        self.assertEqual("not-inspected", listed[0]["inspection_status"])
        self.assertEqual("not-inspected", read_tool_status(self.workspace, "sample-cli")["inspection_status"])
        with self.assertRaisesRegex(SafetyError, "already registered"):
            register_tool(
                self.workspace,
                "sample-cli",
                name="Duplicate",
                kind="system-cli",
                source="https://example.invalid/duplicate",
                install_method="existing",
                external_identifier="sample-cli",
            )

        with self.assertRaisesRegex(ValidationError, "Functionality cannot pass"):
            record_tool_status(
                self.workspace,
                "sample-cli",
                target="synthetic inspection fixture",
                installation="found",
                functionality="passed",
            )
        self.assertFalse((payload.parent / "status.json").exists())

        with self.assertRaisesRegex(ValidationError, "failure reason"):
            record_tool_status(
                self.workspace,
                "sample-cli",
                target="missing installation fixture",
                installation="not-found",
            )
        self.assertFalse((payload.parent / "status.json").exists())

        recorded = record_tool_status(
            self.workspace,
            "sample-cli",
            target="synthetic inspection fixture",
            installation="found",
            activation="not-applicable",
            compatibility="compatible",
            execution="passed",
            functionality="passed",
        )
        self.assertEqual("recorded", recorded["status"])
        self.assertEqual(
            "recorded", read_tool_registration(self.workspace, "sample-cli")["inspection"]["inspection_status"],
        )
        before = (payload.parent / "status.json").read_bytes()
        with self.assertRaisesRegex(ValidationError, "Execution cannot pass"):
            record_tool_status(
                self.workspace,
                "sample-cli",
                target="invalid follow-up",
                installation="not-found",
                execution="passed",
            )
        self.assertEqual(before, (payload.parent / "status.json").read_bytes())

        removed = unregister_tool(self.workspace, "sample-cli")
        self.assertEqual("unregistered", removed["status"])
        self.assertTrue(payload_file.is_file())
        self.assertFalse((payload.parent / "tool.json").exists())
        self.assertFalse((payload.parent / "status.json").exists())
        self.assertEqual([], list_registered_tools(self.workspace)["tools"])
        validated = validate_tools_repository(tools_root)
        self.assertEqual(["sample-cli"], validated["unregistered_directories"])

    def test_invalid_registration_does_not_leave_management_files(self) -> None:
        tools_root = self.parent / "GameAssetAI-Tools"
        initialize_tools_repository(self.workspace, tools_root)
        with self.assertRaisesRegex(ValidationError, "upstream revision"):
            register_tool(
                self.workspace,
                "modified-tool",
                name="Modified Tool",
                kind="git-project",
                source="https://example.invalid/modified",
                install_method="git-clone",
                location=str(tools_root / "tools" / "modified-tool" / "source"),
                modified=True,
            )
        self.assertFalse((tools_root / "tools" / "modified-tool" / "tool.json").exists())
        self.assertEqual([], list_registered_tools(self.workspace)["tools"])

    def test_missing_tools_tree_does_not_break_workspace_or_profiles(self) -> None:
        tools_root = self.parent / "GameAssetAI-Tools"
        initialize_tools_repository(self.workspace, tools_root)
        shutil.rmtree(tools_root)
        self.assertEqual("missing", read_tools_connection(self.workspace)["status"])
        self.assertEqual("valid", validate_workspace(self.workspace)["status"])
        created = create_profile(self.workspace, "game-one", "Game One", "Still independent")
        self.assertEqual("created", created["status"])
        self.assertFalse(tools_root.exists())

    def test_linked_repository_is_rejected_without_changing_connection(self) -> None:
        real = self.parent / "Real-Tools"
        initialize_tools_repository(self.workspace, real)
        linked = self.parent / "Linked-Tools"
        try:
            linked.symlink_to(real, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")
        with self.assertRaises(SafetyError):
            connect_tools_repository(self.workspace, linked)
        self.assertEqual(str(real), read_tools_connection(self.workspace)["tools_root"])

    @unittest.skipUnless(os.name == "nt", "Windows Junction behavior")
    def test_windows_junction_repository_is_rejected(self) -> None:
        real = self.parent / "Real-Tools"
        initialize_tools_repository(self.workspace, real)
        junction = self.parent / "Junction-Tools"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(real)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.skipTest(f"Cannot create Windows Junction: {result.stderr or result.stdout}")
        try:
            with self.assertRaises(SafetyError):
                connect_tools_repository(self.workspace, junction)
            self.assertEqual(str(real), read_tools_connection(self.workspace)["tools_root"])
        finally:
            os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
