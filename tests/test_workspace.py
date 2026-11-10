from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import SafetyError, ValidationError  # noqa: E402
from gameassetai.workspace import (  # noqa: E402
    create_or_connect_workspace, create_profile, list_profiles, read_active_profile,
    select_profile, update_workspace, validate_workspace,
)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-workspace-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "custom-location"

    def create(self):
        return create_or_connect_workspace(ROOT / "workspace-template", self.workspace)

    def test_create_connect_profile_switch_and_persistence(self):
        self.assertEqual("created", self.create()["status"])
        marker = json.loads((self.workspace / "config" / "workspace.json").read_text())
        self.assertNotEqual("workspace-template", marker["workspace_id"])
        self.assertEqual("connected", self.create()["status"])
        create_profile(
            self.workspace, "forest-game", "Forest Game", "Persistent style context",
            three_d_style="stylized-chibi-low-poly",
        )
        select_profile(self.workspace, "forest-game")
        self.assertEqual("forest-game", validate_workspace(self.workspace, require_profile=True)["active_profile"])
        self.assertEqual("Forest Game", read_active_profile(self.workspace)["name"])
        self.assertEqual([{"id": "forest-game", "name": "Forest Game", "active": True}], list_profiles(self.workspace))
        select_profile(self.workspace, None)
        self.assertIsNone(validate_workspace(self.workspace)["active_profile"])

    def test_update_never_overwrites_personal_files(self):
        self.create()
        agents = self.workspace / "AGENTS.md"
        agents.write_text("personal workspace instructions", encoding="utf-8")
        (self.workspace / "notes" / "personal.md").write_text("keep", encoding="utf-8")
        result = update_workspace(ROOT / "workspace-template", self.workspace)
        self.assertIn(result["status"], {"already-current", "updated"})
        self.assertEqual("personal workspace instructions", agents.read_text(encoding="utf-8"))
        self.assertEqual("keep", (self.workspace / "notes" / "personal.md").read_text(encoding="utf-8"))

    def test_existing_unknown_directory_refused_and_legacy_is_read_only(self):
        self.workspace.mkdir()
        (self.workspace / "personal.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(SafetyError):
            self.create()
        self.assertEqual("keep", (self.workspace / "personal.txt").read_text())

        legacy = self.root / "legacy"
        (legacy / "config").mkdir(parents=True)
        (legacy / "profiles").mkdir()
        (legacy / "AGENTS.md").write_text("legacy", encoding="utf-8")
        (legacy / "config" / "active-profile.json").write_text('{"profile":null}', encoding="utf-8")
        (legacy / "config" / "projects.json").write_text('{"projects":{}}', encoding="utf-8")
        before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        report = create_or_connect_workspace(ROOT / "workspace-template", legacy)
        self.assertEqual("legacy-connected", report["status"])
        self.assertTrue(report["migration_required"])
        self.assertEqual(before, {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()})

    def test_missing_active_profile_is_refused(self):
        self.create()
        active = self.workspace / "config" / "active-profile.json"
        active.write_text('{"schema":"gameassetai.active-profile.v1","profile":"missing"}', encoding="utf-8")
        with self.assertRaises(ValidationError):
            validate_workspace(self.workspace)


if __name__ == "__main__":
    unittest.main()
