"""Synthetic, isolated regression fixtures. Never access user game projects."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import stat
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from create_workspace import copy_workspace
from validate_repo import validate_repository
from validate_workspace import is_link, read_json_object, validate_workspace, valid_profile_stem


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repository"
        self.template = self.repo / "workspace-template"
        shutil.copytree(REPO / "workspace-template", self.template)
        self.target = self.base / "workspace"

    def create(self):
        copy_workspace(self.template, self.target, False)

    def configure(self, filename, data):
        (self.target / "config" / filename).write_text(json.dumps(data), encoding="utf-8")

    def inventory(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}

    def link(self, link, destination, directory=False):
        try:
            link.symlink_to(destination, target_is_directory=directory)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows symlink creation privilege unavailable (WinError 1314)")
            raise


class CreationTests(Fixture):
    def test_new_workspace_matches_template(self):
        before = self.inventory(self.template)
        self.create()
        self.assertEqual(before, self.inventory(self.target))
        self.assertEqual(before, self.inventory(self.template))
        self.assertEqual([], validate_workspace(self.target))

    def test_empty_existing_directory(self):
        self.target.mkdir()
        self.create()
        self.assertEqual([], validate_workspace(self.target))

    def test_parent_directories_created(self):
        self.target = self.base / "new" / "nested" / "workspace"
        self.create()
        self.assertEqual([], validate_workspace(self.target))

    def test_nonempty_target_unchanged_without_force(self):
        self.create()
        (self.target / "personal.txt").write_text("keep", encoding="utf-8")
        before = self.inventory(self.target)
        with self.assertRaisesRegex(ValueError, "not empty"):
            self.create()
        self.assertEqual(before, self.inventory(self.target))

    def test_force_merges_and_keeps_extra_files(self):
        self.create()
        (self.target / "AGENTS.md").write_text("old", encoding="utf-8")
        (self.target / "profiles" / "Personal.md").write_text("keep", encoding="utf-8")
        copy_workspace(self.template, self.target, True)
        self.assertEqual((self.template / "AGENTS.md").read_bytes(),
                         (self.target / "AGENTS.md").read_bytes())
        self.assertEqual("keep", (self.target / "profiles" / "Personal.md").read_text())

    def test_repository_overlap_rejected_with_and_without_force(self):
        before = self.inventory(self.repo)
        for target in (self.repo, self.template, self.template / "nested", self.repo / "workspace",
                       self.base):
            for force in (False, True):
                with self.subTest(target=target, force=force):
                    with self.assertRaisesRegex(ValueError, "outside"):
                        copy_workspace(self.template, target, force)
        self.assertEqual(before, self.inventory(self.repo))
        self.assertFalse((self.template / "nested").exists())

    def test_target_file_rejected(self):
        self.target.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not a directory"):
            copy_workspace(self.template, self.target, True)
        self.assertEqual("keep", self.target.read_text())

    def test_invalid_template_does_not_create_target(self):
        (self.template / "config" / "projects.json").write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Invalid workspace template"):
            self.create()
        self.assertFalse(self.target.exists())

    def test_missing_template_rejected(self):
        with self.assertRaises(ValueError):
            copy_workspace(self.repo / "absent-template", self.target, False)
        self.assertFalse(self.target.exists())

    def test_file_directory_collisions_preflight(self):
        for relative, directory in (("config", False), ("README.md", True)):
            with self.subTest(relative=relative):
                self.target.mkdir(exist_ok=True)
                path = self.target / relative
                path.mkdir() if directory else path.write_text("keep", encoding="utf-8")
                before = self.inventory(self.target)
                with self.assertRaisesRegex(ValueError, "collision"):
                    copy_workspace(self.template, self.target, True)
                self.assertEqual(before, self.inventory(self.target))
                path.rmdir() if directory else path.unlink()

    def test_linked_destination_directory_preserves_external_data(self):
        self.target.mkdir()
        external = self.base / "external"
        external.mkdir()
        (external / "projects.json").write_text("keep", encoding="utf-8")
        self.link(self.target / "config", external, True)
        before = self.inventory(external)
        with self.assertRaisesRegex(ValueError, "Linked destination"):
            copy_workspace(self.template, self.target, True)
        self.assertEqual(before, self.inventory(external))
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_linked_target_root_rejected(self):
        external = self.base / "external"
        external.mkdir()
        self.link(self.target, external, True)
        with self.assertRaisesRegex(ValueError, "symlinks or junctions"):
            copy_workspace(self.template, self.target, True)
        self.assertEqual([], list(external.iterdir()))

    def test_linked_template_extra_rejected(self):
        external = self.base / "external.txt"
        external.write_text("keep", encoding="utf-8")
        self.link(self.template / "extra.txt", external)
        with self.assertRaisesRegex(ValueError, "Unsupported template path"):
            self.create()
        self.assertFalse(self.target.exists())

    def test_hardlink_overwrite_does_not_modify_external_file(self):
        self.target.mkdir()
        external = self.base / "external.txt"
        external.write_text("keep", encoding="utf-8")
        os.link(external, self.target / "AGENTS.md")
        copy_workspace(self.template, self.target, True)
        self.assertEqual("keep", external.read_text())
        self.assertEqual((self.template / "AGENTS.md").read_bytes(),
                         (self.target / "AGENTS.md").read_bytes())

    def test_copy_failure_does_not_truncate_existing_file_or_leave_staging(self):
        self.target.mkdir()
        (self.target / "AGENTS.md").write_text("keep", encoding="utf-8")
        before = self.inventory(self.target)
        with patch("create_workspace.shutil.copy2", side_effect=OSError("simulated I/O failure")):
            with self.assertRaisesRegex(OSError, "simulated"):
                copy_workspace(self.template, self.target, True)
        self.assertEqual(before, self.inventory(self.target))

    def test_linked_destination_preflight_with_simulated_link(self):
        self.target.mkdir()
        linked_path = self.target / "config"
        real_is_link = is_link
        with patch("create_workspace.is_link", side_effect=lambda p: p == linked_path or real_is_link(p)):
            with self.assertRaisesRegex(ValueError, "Linked destination"):
                copy_workspace(self.template, self.target, True)
        self.assertEqual([], list(self.target.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_real_junction_destination_preserves_external_data(self):
        self.target.mkdir()
        external = self.base / "external"
        external.mkdir()
        (external / "projects.json").write_text("keep", encoding="utf-8")
        junction = self.target / "config"
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(external)],
                                capture_output=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        # Check precise temp paths before removing only the junction, not its target.
        self.assertTrue(junction.absolute().is_relative_to(self.base))
        self.assertTrue(external.absolute().is_relative_to(self.base))
        self.addCleanup(junction.rmdir)
        self.assertTrue(is_link(junction))
        before = self.inventory(external)
        with self.assertRaisesRegex(ValueError, "Linked destination"):
            copy_workspace(self.template, self.target, True)
        self.assertEqual(before, self.inventory(external))
        self.assertFalse((self.target / "AGENTS.md").exists())

    def test_cli_success_and_failure_from_other_cwd(self):
        script = REPO / "scripts" / "create_workspace.py"
        first = subprocess.run([sys.executable, "-B", str(script), str(self.target)],
                               cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, first.returncode, first.stderr)
        second = subprocess.run([sys.executable, "-B", str(script), str(self.target)],
                                cwd=self.base, capture_output=True, text=True)
        self.assertEqual(1, second.returncode)
        self.assertIn("not empty", second.stderr)
        self.assertNotIn("Traceback", second.stderr)


class WorkspaceTests(Fixture):
    def setUp(self):
        super().setUp()
        self.create()

    def test_null_profile_valid_but_strict_mode_fails(self):
        self.assertEqual([], validate_workspace(self.target))
        self.assertIn("No active profile selected", validate_workspace(self.target, True))

    def test_source_template_must_be_game_neutral(self):
        (self.target / "profiles" / "Game.md").write_text("# Rules", encoding="utf-8")
        self.configure("active-profile.json", {"profile": "Game"})
        self.assertEqual([], validate_workspace(self.target))
        self.assertTrue(validate_workspace(self.target, template_mode=True))
        self.configure("active-profile.json", {"profile": None})
        self.configure("projects.json", {"projects": {"Game": {"blender": "D:/Existing"}}})
        self.assertEqual([], validate_workspace(self.target))
        self.assertTrue(validate_workspace(self.target, template_mode=True))

    def test_profile_creation_switching_and_rule_reading(self):
        for name, rule in (("GameA", "Unity; props under 5k triangles"),
                           ("GameB", "Unreal; preserve existing skeleton")):
            (self.target / "profiles" / f"{name}.md").write_text(rule, encoding="utf-8")
        for name in ("GameA", "GameB", "GameA"):
            self.configure("active-profile.json", {"profile": name})
            self.assertEqual([], validate_workspace(self.target, True))
            stem = read_json_object(self.target / "config" / "active-profile.json")["profile"]
            self.assertIn("Unity" if name == "GameA" else "Unreal",
                          (self.target / "profiles" / f"{stem}.md").read_text())

    def test_invalid_profile_values(self):
        for value in ("../escape", "..\\escape", "Game.md", "Game.MD", "README", "_PROFILE_TEMPLATE",
                      "", " ", "Game.", "game/other", "CON", "NUL.name", 7, True, {}, []):
            with self.subTest(value=value):
                self.configure("active-profile.json", {"profile": value})
                self.assertTrue(validate_workspace(self.target))

    def test_unicode_profile_supported(self):
        name = "게임-하나"
        (self.target / "profiles" / f"{name}.md").write_text("# 미정", encoding="utf-8")
        self.configure("active-profile.json", {"profile": name})
        self.assertEqual([], validate_workspace(self.target, True))
        self.assertTrue(valid_profile_stem(name))

    def test_missing_empty_and_case_mismatched_profiles(self):
        self.configure("active-profile.json", {"profile": "Absent"})
        self.assertTrue(validate_workspace(self.target))
        (self.target / "profiles" / "Absent.md").write_text("", encoding="utf-8")
        self.assertTrue(validate_workspace(self.target))
        (self.target / "profiles" / "Absent.md").write_text("# Rules", encoding="utf-8")
        self.configure("active-profile.json", {"profile": "absent"})
        self.assertTrue(validate_workspace(self.target))

    def test_linked_active_profile_rejected(self):
        external = self.base / "external.md"
        external.write_text("private", encoding="utf-8")
        self.link(self.target / "profiles" / "Game.md", external)
        self.configure("active-profile.json", {"profile": "Game"})
        self.assertTrue(validate_workspace(self.target))

    def test_link_detection_for_symlinks_and_windows_reparse_points(self):
        path = self.target / "mock"
        for mode, attributes in ((stat.S_IFLNK, 0), (stat.S_IFDIR, 0x400)):
            with self.subTest(mode=mode, attributes=attributes):
                with patch.object(Path, "lstat", return_value=SimpleNamespace(
                        st_mode=mode, st_file_attributes=attributes)):
                    with patch("validate_workspace.stat.FILE_ATTRIBUTE_REPARSE_POINT", 0x400, create=True):
                        self.assertTrue(is_link(path))
        self.assertFalse(is_link(path))

    def test_linked_profile_rejected_with_simulated_link(self):
        profile = self.target / "profiles" / "Game.md"
        profile.write_text("# Rules", encoding="utf-8")
        self.configure("active-profile.json", {"profile": "Game"})
        real_is_link = is_link
        with patch("validate_workspace.is_link", side_effect=lambda p: p == profile or real_is_link(p)):
            self.assertTrue(validate_workspace(self.target))

    def test_malformed_duplicate_and_nonstandard_json(self):
        path = self.target / "config" / "active-profile.json"
        for text in ('{', '[]', '{"profile":null,"profile":"Other"}',
                     '{"profile":NaN}', '{"profile":Infinity}', '{}'):
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.assertTrue(validate_workspace(self.target))

    def test_utf8_bom_supported(self):
        (self.target / "config" / "active-profile.json").write_text(
            '{"profile":null}', encoding="utf-8-sig")
        self.assertEqual([], validate_workspace(self.target))

    def test_optional_notes_and_readmes_not_required_at_runtime(self):
        shutil.rmtree(self.target / "notes")
        (self.target / "README.md").unlink()
        (self.target / "profiles" / "README.md").unlink()
        (self.target / "profiles" / "_PROFILE_TEMPLATE.md").unlink()
        self.assertEqual([], validate_workspace(self.target))
        self.assertTrue(validate_workspace(self.target, template_mode=True))

    def test_absolute_project_mappings_are_not_accessed_or_modified(self):
        mappings = {"projects": {"Example": {"unity": "D:/Games/ExistingUnity",
                    "unreal": "E:/Existing Unreal/Game", "blender": "/existing/blender",
                    "custom": "//server/share/existing"}}}
        self.configure("projects.json", mappings)
        before = self.inventory(self.target)
        self.assertEqual([], validate_workspace(self.target))
        self.assertEqual(before, self.inventory(self.target))
        self.assertEqual(mappings, read_json_object(self.target / "config" / "projects.json"))

    def test_invalid_project_mappings(self):
        for projects in (None, [], {"Game": "D:/Game"}, {"": {}},
                         {"Game": {"unity": 2}}, {"Game": {"unity": "relative/path"}},
                         {"Game": {"unity": "D:relative"}}, {"Game": {"unity": "D:/bad\x00"}}):
            with self.subTest(projects=projects):
                self.configure("projects.json", {"projects": projects})
                self.assertTrue(validate_workspace(self.target))

    def test_missing_and_empty_required_files(self):
        (self.target / "AGENTS.md").write_text("", encoding="utf-8")
        self.assertTrue(validate_workspace(self.target))
        (self.target / "AGENTS.md").unlink()
        self.assertTrue(validate_workspace(self.target))

    def test_validator_cli_readonly_and_strict_mode(self):
        script = REPO / "scripts" / "validate_workspace.py"
        before = self.inventory(self.target)
        normal = subprocess.run([sys.executable, "-B", str(script), str(self.target)],
                                cwd=self.base, capture_output=True, text=True)
        strict = subprocess.run([sys.executable, "-B", str(script), str(self.target), "--require-profile"],
                                cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, normal.returncode, normal.stdout + normal.stderr)
        self.assertEqual(1, strict.returncode)
        self.assertEqual(before, self.inventory(self.target))


class RepositoryTests(Fixture):
    def setUp(self):
        super().setUp()
        shutil.copytree(REPO, self.repo, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".local", "tmp", ".venv"))

    def test_current_repository_valid(self):
        self.assertEqual([], validate_repository(self.repo))

    def test_missing_roadmap_detected(self):
        (self.repo / "docs" / "roadmap.md").unlink()
        self.assertTrue(validate_repository(self.repo))

    def test_directory_disguised_as_required_file_detected(self):
        path = self.repo / "README.md"
        path.unlink()
        path.mkdir()
        self.assertTrue(validate_repository(self.repo))

    def test_empty_required_file_detected(self):
        (self.repo / "docs" / "requirements.md").write_text("", encoding="utf-8")
        self.assertTrue(validate_repository(self.repo))

    def test_template_json_failure_detected(self):
        (self.template / "config" / "projects.json").write_text("[]", encoding="utf-8")
        self.assertTrue(validate_repository(self.repo))

    def test_missing_profile_template_detected(self):
        (self.template / "profiles" / "_PROFILE_TEMPLATE.md").unlink()
        self.assertTrue(validate_repository(self.repo))


if __name__ == "__main__":
    unittest.main()
