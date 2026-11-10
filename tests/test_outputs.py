from pathlib import Path
import shutil
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.outputs import begin_output_run, validate_output_run  # noqa: E402
from gameassetai.workspace import create_or_connect_workspace, create_profile, select_profile, validate_workspace  # noqa: E402


class OutputIndependenceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
