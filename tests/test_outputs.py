from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.outputs import begin_output_run, validate_output_run  # noqa: E402
from gameassetai.errors import SafetyError  # noqa: E402
from gameassetai.workspace import create_or_connect_workspace, create_profile, select_profile, validate_workspace  # noqa: E402


class OutputIndependenceTests(unittest.TestCase):
    def create_workspace(self, root: Path) -> Path:
        workspace = root / "workspace"
        create_or_connect_workspace(ROOT / "workspace-template", workspace)
        create_profile(workspace, "game-one", "Game One", "Output safety test")
        select_profile(workspace, "game-one")
        return workspace

    def test_outputs_can_be_deleted_without_system_damage(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-output-") as temporary:
            workspace = Path(temporary) / "workspace"
            create_or_connect_workspace(ROOT / "workspace-template", workspace)
            create_profile(workspace, "game-one", "Game One", "Output independence test")
            select_profile(workspace, "game-one")
            first = begin_output_run(
                workspace, game="game-one", asset_category="weapon", asset_id="sword",
                run_id="run-one", request_summary="first output",
            )
            self.assertEqual("run-one", validate_output_run(Path(first["run"]))["run_id"])
            shutil.rmtree(workspace / "outputs")
            self.assertEqual("game-one", validate_workspace(workspace, require_profile=True)["active_profile"])
            self.assertTrue((workspace / "profiles" / "game-one.json").is_file())
            second = begin_output_run(
                workspace, game="game-one", asset_category="weapon", asset_id="sword",
                run_id="run-two",
            )
            self.assertTrue(Path(second["run"]).is_dir())

    def test_existing_run_collision_preserves_existing_manifest(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-output-collision-") as temporary:
            workspace = self.create_workspace(Path(temporary))
            created = begin_output_run(
                workspace, game="game-one", asset_category="weapon", asset_id="sword",
                run_id="same-run", request_summary="keep this",
            )
            manifest = Path(created["run"]) / "manifest.json"
            before = manifest.read_bytes()
            with self.assertRaises(SafetyError):
                begin_output_run(
                    workspace, game="game-one", asset_category="weapon", asset_id="axe",
                    run_id="same-run",
                )
            self.assertEqual(before, manifest.read_bytes())

    def test_linked_intermediate_output_directory_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-output-link-") as temporary:
            root = Path(temporary)
            workspace = self.create_workspace(root)
            output_root = workspace / "outputs"
            output_root.mkdir()
            external = root / "external"
            external.mkdir()
            link = output_root / "game-one"
            try:
                link.symlink_to(external, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"Directory symlinks are unavailable: {exc}")
            with self.assertRaises(SafetyError):
                begin_output_run(
                    workspace, game="game-one", asset_category="weapon", asset_id="sword",
                    run_id="blocked-run",
                )
            self.assertEqual([], list(external.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_junction_intermediate_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-output-junction-") as temporary:
            root = Path(temporary)
            workspace = self.create_workspace(root)
            output_root = workspace / "outputs"
            output_root.mkdir()
            external = root / "external"
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
                    begin_output_run(
                        workspace, game="game-one", asset_category="weapon", asset_id="sword",
                        run_id="blocked-run",
                    )
                self.assertEqual([], list(external.iterdir()))
            finally:
                if junction.exists():
                    os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
