from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import SafetyError, ValidationError  # noqa: E402
from gameassetai.outputs import (  # noqa: E402
    begin_output_task, continue_output_task, create_experiment, list_experiments,
    validate_experiment, validate_output_path, validate_output_task,
)
from gameassetai.workspace import (  # noqa: E402
    create_or_connect_workspace, create_profile, select_profile, validate_workspace,
)


class OutputManagementTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-output-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = self.root / "repository"
        (self.repository / "src" / "gameassetai").mkdir(parents=True)
        (self.repository / "AGENTS.md").write_text("test repository", encoding="utf-8")
        shutil.copytree(ROOT / "catalog", self.repository / "catalog")
        self.workspace = self.root / "workspace"
        create_or_connect_workspace(ROOT / "workspace-template", self.workspace)
        create_profile(self.workspace, "game-one", "Game One", "Output management test")
        select_profile(self.workspace, "game-one")

    def create_experiment(self, identifier: str = "chibi-character-quality") -> Path:
        result = create_experiment(
            self.repository,
            identifier,
            purpose="Validate the target visual quality",
            question="Does the method satisfy the named quality criteria?",
            evaluation_criteria=["readable silhouette", "coherent proportions"],
            scope="Storage-contract fixture only; no Blender execution",
        )
        return Path(result["experiment"])

    def begin_development(
        self,
        *,
        experiment: str = "chibi-character-quality",
        category: str = "character",
        asset: str = "chibi-adventurer",
        purpose: str = "initial-model",
    ) -> Path:
        return Path(begin_output_task(
            "development",
            self.repository,
            experiment_id=experiment,
            asset_category=category,
            asset_id=asset,
            purpose=purpose,
        )["task"])

    def begin_workspace(
        self,
        *,
        category: str = "equipment-prop",
        asset: str = "bronze-sword",
        purpose: str = "initial-model",
        game: str | None = None,
    ) -> Path:
        return Path(begin_output_task(
            "workspace",
            self.workspace,
            game_id=game,
            asset_category=category,
            asset_id=asset,
            purpose=purpose,
        )["task"])

    def test_development_requires_explicit_identified_experiment(self):
        self.assertEqual([], list_experiments(self.repository))
        self.assertFalse((self.repository / "output").exists())
        with self.assertRaisesRegex(ValidationError, "explicit existing experiment"):
            begin_output_task(
                "development", self.repository, asset_category="character",
                asset_id="chibi-adventurer", purpose="initial-model",
            )
        self.assertFalse((self.repository / "output").exists())

        experiment = self.create_experiment()
        self.assertEqual("chibi-character-quality", validate_experiment(experiment)["experiment_id"])
        task = self.begin_development()
        self.assertEqual(
            self.repository / "output" / "experiments" / "chibi-character-quality"
            / "character" / "chibi-adventurer" / "001-initial-model",
            task,
        )
        self.assertEqual({"manifest.json"}, {path.name for path in task.iterdir()})

    def test_experiment_reuse_and_new_experiment_are_explicit(self):
        first_experiment = self.create_experiment()
        first = self.begin_development(purpose="initial-model")
        second = self.begin_development(purpose="silhouette-refinement")
        self.assertEqual("001-initial-model", first.name)
        self.assertEqual("002-silhouette-refinement", second.name)
        with self.assertRaisesRegex(SafetyError, "explicitly reuse"):
            self.create_experiment()

        second_experiment = self.create_experiment("sprite-readability")
        other = self.begin_development(
            experiment="sprite-readability", purpose="front-pixel-readability",
        )
        self.assertEqual("001-front-pixel-readability", other.name)
        self.assertNotEqual(first_experiment, second_experiment)
        self.assertEqual(2, len(list_experiments(self.repository)))

    def test_unidentified_existing_experiment_is_reported_and_not_reused(self):
        unidentified = self.repository / "output" / "experiments" / "unclear-goal"
        unidentified.mkdir(parents=True)
        report = list_experiments(self.repository)
        self.assertEqual("unidentified", report[0]["status"])
        with self.assertRaisesRegex(ValidationError, "experiment.json"):
            self.begin_development(experiment="unclear-goal")
        self.assertEqual([], list(unidentified.iterdir()))

    def test_same_experiment_separates_assets_and_same_asset_can_exist_in_other_experiment(self):
        self.create_experiment()
        adventurer = self.begin_development(asset="chibi-adventurer")
        knight = self.begin_development(asset="chibi-knight")
        self.create_experiment("sprite-readability")
        sprite = self.begin_development(
            experiment="sprite-readability", asset="chibi-adventurer",
            purpose="front-pixel-readability",
        )
        self.assertEqual("001-initial-model", adventurer.name)
        self.assertEqual("001-initial-model", knight.name)
        self.assertEqual("chibi-adventurer", sprite.parent.name)
        self.assertNotEqual(adventurer.parents[2], sprite.parents[2])

    def test_catalog_categories_and_descriptive_ids_are_enforced(self):
        self.create_experiment()
        with self.assertRaisesRegex(ValidationError, "asset category must be one of"):
            self.begin_development(category="weapon")
        with self.assertRaisesRegex(ValidationError, "describe its purpose"):
            self.begin_development(purpose="test")
        with self.assertRaisesRegex(ValidationError, "lowercase portable slug"):
            self.begin_development(asset="../outside")
        with self.assertRaisesRegex(ValidationError, "describe its purpose"):
            create_experiment(
                self.repository, "experiment", purpose="purpose", question="question",
                evaluation_criteria=["criterion"],
            )
        with self.assertRaisesRegex(ValidationError, "describe its purpose"):
            create_experiment(
                self.repository, "experiment-001", purpose="purpose", question="question",
                evaluation_criteria=["criterion"],
            )

    def test_numbering_uses_current_max_and_resets_only_when_all_tasks_are_deleted(self):
        self.create_experiment()
        first = self.begin_development(purpose="initial-model")
        second = self.begin_development(purpose="proportion-refinement")
        third = self.begin_development(purpose="material-refinement")
        shutil.rmtree(second)
        fourth = self.begin_development(purpose="silhouette-refinement")
        self.assertEqual("004-silhouette-refinement", fourth.name)

        for path in (first, third, fourth):
            shutil.rmtree(path)
        reset = self.begin_development(purpose="new-independent-result")
        self.assertEqual("001-new-independent-result", reset.name)

    def test_concurrent_allocation_uses_unique_sequential_numbers(self):
        self.create_experiment()

        def allocate(_: int) -> str:
            return self.begin_development(purpose="parallel-comparison").name

        with ThreadPoolExecutor(max_workers=8) as executor:
            names = list(executor.map(allocate, range(8)))
        self.assertEqual(8, len(set(names)))
        self.assertEqual(
            list(range(1, 9)),
            sorted(int(name.split("-", 1)[0]) for name in names),
        )

    def test_workspace_uses_active_profile_game_asset_and_numbered_task(self):
        first = self.begin_workspace()
        second = self.begin_workspace(purpose="blade-refinement", game="game-one")
        environment = self.begin_workspace(
            category="environment", asset="stone-pillar", purpose="initial-model",
        )
        self.assertEqual(
            self.workspace / "outputs" / "game-one" / "equipment-prop" / "bronze-sword"
            / "001-initial-model",
            first,
        )
        self.assertEqual("002-blade-refinement", second.name)
        self.assertEqual("001-initial-model", environment.name)
        with self.assertRaisesRegex(ValidationError, "active Profile"):
            self.begin_workspace(game="other-game")

    def test_deleting_output_trees_preserves_profiles_and_allows_independent_restart(self):
        self.create_experiment()
        self.begin_development()
        self.begin_workspace()
        shutil.rmtree(self.repository / "output")
        shutil.rmtree(self.workspace / "outputs")
        self.assertEqual([], list_experiments(self.repository))
        self.assertEqual(
            "game-one", validate_workspace(self.workspace, require_profile=True)["active_profile"],
        )

        self.create_experiment("static-model-revision")
        development = self.begin_development(
            experiment="static-model-revision", category="equipment-prop",
            asset="bronze-sword", purpose="blade-refinement",
        )
        workspace = self.begin_workspace(purpose="new-independent-result")
        self.assertEqual("001-blade-refinement", development.name)
        self.assertEqual("001-new-independent-result", workspace.name)

    def test_moved_or_deleted_in_progress_task_fails_only_that_continuation(self):
        task = self.begin_workspace()
        moved = self.root / "user-archive" / task.name
        moved.parent.mkdir()
        task.rename(moved)
        with self.assertRaises(ValidationError):
            continue_output_task(task)
        with self.assertRaises(ValidationError):
            validate_output_task(moved)
        replacement = self.begin_workspace(purpose="new-independent-result")
        self.assertEqual("001-new-independent-result", replacement.name)

    def test_completed_task_cannot_be_reused_for_overwrite(self):
        task = self.begin_workspace()
        manifest_path = task / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = "complete"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        before = manifest_path.read_bytes()
        with self.assertRaisesRegex(SafetyError, "requires a new numbered task"):
            continue_output_task(task)
        self.assertEqual(before, manifest_path.read_bytes())
        next_task = self.begin_workspace(purpose="post-review-refinement")
        self.assertEqual("002-post-review-refinement", next_task.name)

    def test_legacy_output_is_read_only_and_new_structure_does_not_move_it(self):
        legacy = self.workspace / "outputs" / "game-one" / "weapon" / "old-run"
        legacy.mkdir(parents=True)
        manifest = {
            "schema": "gameassetai.output-run.v1",
            "run_id": "old-run",
            "game": "game-one",
            "asset_category": "weapon",
            "asset_id": "bronze-sword",
            "created_utc": "2026-11-10T00:00:00+00:00",
            "request_summary": "legacy",
            "artifacts": [],
            "status": "complete",
        }
        manifest_path = legacy / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        before = manifest_path.read_bytes()
        self.assertEqual("old-run", validate_output_path(legacy)["run_id"])
        current = self.begin_workspace()
        self.assertTrue(current.is_dir())
        self.assertEqual(before, manifest_path.read_bytes())
        self.assertTrue(legacy.is_dir())

    def test_linked_intermediate_output_directory_is_refused(self):
        output_root = self.workspace / "outputs"
        output_root.mkdir()
        external = self.root / "external"
        external.mkdir()
        link = output_root / "game-one"
        try:
            link.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")
        with self.assertRaises(SafetyError):
            self.begin_workspace()
        self.assertEqual([], list(external.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_intermediate_is_refused(self):
        output_root = self.workspace / "outputs"
        output_root.mkdir()
        external = self.root / "external"
        external.mkdir()
        junction = output_root / "game-one"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.skipTest(f"Cannot create a test junction: {result.stderr or result.stdout}")
        try:
            with self.assertRaises(SafetyError):
                self.begin_workspace()
            self.assertEqual([], list(external.iterdir()))
        finally:
            if junction.exists():
                os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
