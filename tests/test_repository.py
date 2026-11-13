from pathlib import Path
import importlib.util
import shutil
import tempfile
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

    def test_foundation_ci_excludes_generated_distribution_branch(self):
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("branches-ignore: [dist/workspace]", workflow)
        self.assertNotIn("retained-contract", workflow)

    def test_official_codex_skill_roots_are_used_by_active_runtime(self):
        distribution = (ROOT / "src" / "gameassetai" / "distribution.py").read_text(
            encoding="utf-8",
        )
        self.assertIn('workspace / ".agents" / "skills"', distribution)
        self.assertNotIn('workspace / ".codex" / "skills"', distribution)

    def test_workspace_distribution_ignore_rules_protect_local_noise_not_product_skills(self):
        rules = (ROOT / "packaging" / "workspace-distribution" / ".gitignore").read_text(
            encoding="utf-8",
        ).splitlines()
        for expected in (
            "/config/", "/profiles/", "/notes/", "/outputs/", "/AGENTS.local.md",
            "/.local/",
            "__pycache__/", "*.py[cod]", "/.venv/", "/venv/", "/env/",
            ".vscode/", ".idea/", ".DS_Store", "Thumbs.db", "desktop.ini",
            "*.blend1", "*.blend2", "*.blend@", "*.blend@*",
        ):
            self.assertIn(expected, rules)
        self.assertFalse(any(".agents" in rule for rule in rules))

    def test_isolated_legacy_remains_outside_the_active_test_suite(self):
        self.assertFalse((ROOT / "tests" / "retained_blender").exists())
        inventory = ROOT / "archive" / "legacy" / "INVENTORY.md"
        if (ROOT / "archive").exists():
            self.assertTrue(inventory.is_file())

    def test_future_blender_source_is_allowed_while_isolated_legacy_use_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-blender-boundary-") as temporary:
            checkout = Path(temporary) / "checkout"
            shutil.copytree(
                ROOT,
                checkout,
                ignore=shutil.ignore_patterns(
                    ".git", ".local", "output", "__pycache__", "*.pyc",
                ),
            )

            blender = checkout / "src" / "gameassetai" / "blender"
            blender.mkdir(parents=True, exist_ok=True)
            (blender / "__init__.py").write_text(
                '"""Approved future Blender product package fixture."""\n', encoding="utf-8",
            )
            (blender / "modeling.py").write_text(
                "def feature_name():\n    return 'future-approved-fixture'\n", encoding="utf-8",
            )
            (checkout / "src" / "gameassetai" / "future_feature.py").write_text(
                "from gameassetai.blender import modeling\n", encoding="utf-8",
            )
            addon = checkout / "blender_addon"
            addon.mkdir()
            (addon / "approved_addon.py").write_text(
                "APPROVED_ADDON_FIXTURE = True\n", encoding="utf-8",
            )

            def tracked() -> set[str]:
                return {
                    path.relative_to(checkout).as_posix()
                    for path in checkout.rglob("*") if path.is_file()
                }

            self.assertEqual([], MODULE.validate_repository(checkout, tracked_files=tracked()))

            forbidden = checkout / "src" / "gameassetai" / "forbidden_legacy_use.py"
            forbidden.write_text(
                "from archive" + ".legacy import unavailable\n", encoding="utf-8",
            )
            errors = MODULE.validate_repository(checkout, tracked_files=tracked())
            self.assertTrue(any(
                "Active Python depends on isolated legacy" in error
                and "forbidden_legacy_use.py" in error
                for error in errors
            ))
            forbidden.unlink()

            isolated_root = (
                checkout / "archive" / "legacy" / "src" / "gameassetai" / "blender"
            )
            isolated = next(isolated_root.glob("*.py"), None) if isolated_root.is_dir() else None
            if isolated is None:
                isolated_root.mkdir(parents=True, exist_ok=True)
                isolated = isolated_root / "historical_fixture.py"
                isolated.write_text("HISTORICAL_FIXTURE = True\n", encoding="utf-8")
            copied = blender / "copied_legacy.py"
            copied.write_bytes(isolated.read_bytes())
            errors = MODULE.validate_repository(checkout, tracked_files=tracked())
            self.assertTrue(any(
                "Active Python duplicates isolated legacy without adoption" in error
                and "copied_legacy.py" in error
                for error in errors
            ))

    def test_legacy_inventory_names_every_isolated_candidate(self):
        inventory = ROOT / "archive" / "legacy" / "INVENTORY.md"
        if not inventory.exists():
            return  # archive-absent product checkout is an explicitly supported validation mode
        text = inventory.read_text(encoding="utf-8")
        groups = (
            (
                "Blender Runtime candidates (70)",
                "Blender Add-on candidates",
                ROOT / "archive" / "legacy" / "src" / "gameassetai" / "blender",
            ),
            (
                "Blender Add-on candidates (14)",
                "Retained contract-test candidates",
                ROOT / "archive" / "legacy" / "blender_addon" / "gameassetai",
            ),
            (
                "Retained contract-test candidates (6)",
                "Adoption gate",
                ROOT / "archive" / "legacy" / "tests" / "retained_blender",
            ),
        )
        marker = "`"
        for heading, following, root in groups:
            section = text.split(f"## {heading}", 1)[1].split(f"## {following}", 1)[0]
            inventoried = {
                line.split(marker)[1]
                for line in section.splitlines()
                if line.startswith(f"| {marker}")
            }
            actual = {
                path.relative_to(root).as_posix()
                for path in root.rglob("*") if path.is_file()
            }
            self.assertEqual(actual, inventoried, heading)

    def test_product_version_has_one_authored_source(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        distribution = (ROOT / "src" / "gameassetai" / "distribution.py").read_text(
            encoding="utf-8",
        )
        self.assertIn('dynamic = ["version"]', pyproject)
        self.assertIn('version = {attr = "gameassetai.__version__"}', pyproject)
        self.assertIn('"version": __version__', distribution)
        self.assertNotIn('"version": "0.2.0"', distribution)


if __name__ == "__main__":
    unittest.main()
