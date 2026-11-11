from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_repo", ROOT / "scripts" / "validate_repo.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RepositoryTests(unittest.TestCase):
    def test_current_repository_contract(self):
        self.assertEqual([], MODULE.validate_repository(ROOT))

    def test_missing_tracked_workspace_skill_is_reported(self):
        tracked, error = MODULE._git_tracked_files(ROOT)
        self.assertIsNone(error)
        self.assertIsNotNone(tracked)
        tracked = set(tracked)
        tracked.discard("skills/gameassetai-workspace/SKILL.md")
        errors = MODULE.validate_repository(ROOT, tracked_files=tracked)
        self.assertIn(
            "Required Skill source is not tracked by Git: skills/gameassetai-workspace/SKILL.md",
            errors,
        )

    def test_missing_tracked_distribution_workflow_is_reported(self):
        tracked, error = MODULE._git_tracked_files(ROOT)
        self.assertIsNone(error)
        self.assertIsNotNone(tracked)
        tracked = set(tracked)
        tracked.discard(".github/workflows/publish-workspace.yml")
        errors = MODULE.validate_repository(ROOT, tracked_files=tracked)
        self.assertIn(
            "Required product source is not tracked by Git: "
            ".github/workflows/publish-workspace.yml",
            errors,
        )

    def test_distribution_workflow_is_master_only_and_never_force_pushes(self):
        workflow = (ROOT / ".github" / "workflows" / "publish-workspace.yml").read_text(
            encoding="utf-8",
        )
        self.assertIn("branches: [master]", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("HEAD:refs/heads/dist/workspace", workflow)
        self.assertNotIn("--force", workflow)
        self.assertNotIn("force-with-lease", workflow)

    def test_official_codex_skill_roots_are_used_by_active_runtime(self):
        distribution = (ROOT / "src" / "gameassetai" / "distribution.py").read_text(
            encoding="utf-8",
        )
        self.assertIn('workspace / ".agents" / "skills"', distribution)
        self.assertNotIn('workspace / ".codex" / "skills"', distribution)


if __name__ == "__main__":
    unittest.main()
