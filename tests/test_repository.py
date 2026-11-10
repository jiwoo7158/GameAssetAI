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


if __name__ == "__main__":
    unittest.main()
