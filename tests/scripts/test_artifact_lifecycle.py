import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from artifact_lifecycle import create_run, finalize_run, verify_run, cleanup_runs


class ArtifactLifecycleTests(unittest.TestCase):
    def setUp(self):
        (REPO / ".local").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-artifacts-",
                                                dir=REPO / ".local")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "runs"
        self.external = self.base / "source.fbx"
        self.external.write_bytes(b"external-input")
        patcher = patch("artifact_lifecycle._git_identity",
                        return_value={"commit": "a" * 40, "dirty": False})
        patcher.start(); self.addCleanup(patcher.stop)
        protection = patch("artifact_lifecycle._automatic_protected_ancestor", return_value=None)
        protection.start(); self.addCleanup(protection.stop)

    def create(self):
        result = create_run(root=self.root, milestone="M3", case="fixture", purpose="test",
                            skill="example", skill_version="1", repo=REPO,
                            inputs=(f"EXTERNAL_INPUT:{self.external}::fixture source::CC0::regenerate",))
        return Path(result["run_directory"])

    def test_create_finalize_verify_and_cleanup(self):
        run = self.create()
        manifest = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("CC0", manifest["inputs"][0]["license"])
        self.assertEqual("regenerate", manifest["inputs"][0]["reacquisition"])
        (run / "validation.json").write_text("{}", encoding="utf-8")
        result = finalize_run(run=run, status="rejected", preservation="TEMPORARY_RUN",
                              reproduction="python test.py",
                              artifacts=("TEMPORARY_RUN:validation.json",),
                              deletion_eligible=True)
        self.assertEqual("pass", result["status"])
        dry = cleanup_runs(root=self.root, runs=(run,))
        self.assertEqual("dry-run", dry["mode"]); self.assertTrue(run.exists())
        applied = cleanup_runs(root=self.root, runs=(run,), apply=True)
        self.assertEqual("apply", applied["mode"]); self.assertFalse(run.exists())

    def test_cleanup_refuses_accepted_or_unmarked_run(self):
        run = self.create()
        with self.assertRaises(ValueError):
            cleanup_runs(root=self.root, runs=(run,))

    def test_cleanup_refuses_protected_intersection(self):
        run = self.create(); (run / "validation.json").write_text("{}")
        finalize_run(run=run, status="rejected", preservation="TEMPORARY_RUN",
                     reproduction="command", artifacts=("TEMPORARY_RUN:validation.json",),
                     deletion_eligible=True)
        with self.assertRaises(ValueError):
            cleanup_runs(root=self.root, runs=(run,), protected=(run.parent,))

    def test_cleanup_refuses_automatic_repository_or_workspace_boundary(self):
        run = self.create(); (run / "validation.json").write_text("{}")
        finalize_run(run=run, status="rejected", preservation="TEMPORARY_RUN",
                     reproduction="command", artifacts=("TEMPORARY_RUN:validation.json",),
                     deletion_eligible=True)
        with patch("artifact_lifecycle._automatic_protected_ancestor", return_value=run.parent):
            with self.assertRaises(ValueError):
                cleanup_runs(root=self.root, runs=(run,))

    def test_verify_detects_changed_artifact_and_external_input(self):
        run = self.create(); artifact = run / "validation.json"; artifact.write_text("{}")
        finalize_run(run=run, status="pass", preservation="ACCEPTED_EVIDENCE",
                     reproduction="command", artifacts=("ACCEPTED_EVIDENCE:validation.json",))
        artifact.write_text("changed")
        self.assertEqual("failed", verify_run(run)["status"])
        artifact.write_text("{}")
        self.external.write_bytes(b"changed")
        self.assertEqual("failed", verify_run(run)["status"])

    def test_finalize_refuses_unregistered_output(self):
        run = self.create()
        (run / "validation.json").write_text("{}")
        (run / "previews" / "frame.png").write_bytes(b"png")
        with self.assertRaises(ValueError):
            finalize_run(run=run, status="pass", preservation="TEMPORARY_RUN",
                         reproduction="command",
                         artifacts=("TEMPORARY_RUN:validation.json",),
                         deletion_eligible=True)

    def test_cleanup_refuses_link(self):
        run = self.create()
        (run / "validation.json").write_text("{}")
        finalize_run(run=run, status="rejected", preservation="TEMPORARY_RUN",
                     reproduction="command", artifacts=("TEMPORARY_RUN:validation.json",),
                     deletion_eligible=True)
        link = run / "escape"
        try:
            link.symlink_to(self.external)
        except OSError:
            self.skipTest("links are not permitted in this environment")
        with self.assertRaises(ValueError):
            cleanup_runs(root=self.root, runs=(run,))


if __name__ == "__main__":
    unittest.main()
