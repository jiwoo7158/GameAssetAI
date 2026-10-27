"""Offline success and rollback tests for the 2D batch coordinator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "tests" / "scripts"))
from build_2d_render_batch_job import build_2d_render_batch_job  # noqa: E402
from run_2d_render_batch import run_2d_render_batch_job  # noqa: E402
from test_2d_render_batch_request import make_batch_fixture  # noqa: E402
from validate_2d_render_batch_request import validate_2d_render_batch_request  # noqa: E402


class Render2DBatchRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-batch-run-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, _, _ = make_batch_fixture(self.root)
        self.preview = validate_2d_render_batch_request(self.request)
        self.children = []
        for index, item in enumerate(self.request["items"]):
            stage = self.root / f"child-{index}.stage.blend"
            stage.write_bytes(f"stage-{index}".encode())
            stage_sha = hashlib.sha256(stage.read_bytes()).hexdigest()
            job = self.root / f"child-{index}.job.json"
            child_payload = {"schema": ("gameassetai.2d-staged-render-job.v1"
                                         if item["kind"] == "STATIC"
                                         else "gameassetai.2d-action-sequence-job.v1"),
                             "request": item["request"],
                             "source_stage": {"path": str(stage),
                                              "size": stage.stat().st_size,
                                              "sha256": stage_sha}}
            job.write_text(json.dumps(child_payload, sort_keys=True, separators=(",", ":")),
                           encoding="utf-8")
            self.children.append({"id": item["id"], "kind": item["kind"],
                                  "stage_file": str(stage), "stage_sha256": stage_sha,
                                  "job_file": str(job),
                                  "job_sha256": hashlib.sha256(job.read_bytes()).hexdigest(),
                                  "helper_root": str(REPO / "scripts")})
        self.job = self.root / ".gameassetai-2d-batch-run.job.json"
        built = build_2d_render_batch_job(self.request, self.preview, self.children,
                                          str(self.job), authorize=True)
        self.assertEqual("created", built["status"], built["errors"])
        self.job_sha = built["job_sha256"]

    @staticmethod
    def _write_artifact(path, token):
        data = b"\x89PNG\r\n\x1a\n" + token.encode()
        Path(path).write_bytes(data)
        return {"path": path, "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}

    def _success_runner(self, _blender, child):
        artifacts = [self._write_artifact(path, child["id"]) for path in child["outputs"]]
        if child["kind"] == "STATIC":
            return {"status": "created", "png_published": True,
                    "artifact": artifacts[0], "receipt_sha256": "a" * 64}
        return {"status": "created", "pngs_published": True,
                "published_count": len(artifacts), "artifacts": artifacts,
                "receipt_sha256": "b" * 64}

    def execute(self, runner):
        return run_2d_render_batch_job(self.job, self.job_sha, sys.executable,
                                       child_runner=runner)

    def test_success_verifies_all_outputs_and_receipt(self):
        result = self.execute(self._success_runner)
        self.assertEqual("created", result["status"], result["errors"])
        self.assertEqual(4, result["published_count"])
        self.assertEqual(2, result["completed_children"])
        self.assertTrue(all(Path(path).is_file() for path in self.preview["outputs"]))
        self.assertEqual(64, len(result["receipt_sha256"]))

    def test_later_child_failure_rolls_back_prior_child(self):
        calls = []

        def runner(blender, child):
            calls.append(child["id"])
            if len(calls) == 2:
                return {"status": "error", "pngs_published": False, "errors": ["synthetic"]}
            return self._success_runner(blender, child)

        result = self.execute(runner)
        self.assertEqual("error", result["status"])
        self.assertEqual(0, result["published_count"])
        self.assertFalse(Path(self.preview["outputs"][0]).exists())

    def test_changed_prior_output_is_not_deleted_during_rollback(self):
        calls = []

        def runner(blender, child):
            calls.append(child["id"])
            if len(calls) == 2:
                Path(self.preview["outputs"][0]).write_bytes(b"user-change")
                raise RuntimeError("synthetic second-child failure")
            return self._success_runner(blender, child)

        result = self.execute(runner)
        self.assertEqual("error", result["status"])
        self.assertEqual(1, result["published_count"])
        self.assertEqual(b"user-change", Path(self.preview["outputs"][0]).read_bytes())
        self.assertTrue(any("changed before rollback" in error for error in result["errors"]))

    def test_job_stage_helper_and_preexisting_target_drift_refuse(self):
        Path(self.children[0]["stage_file"]).write_bytes(b"changed")
        self.assertEqual("error", self.execute(self._success_runner)["status"])
        self.assertFalse(any(Path(path).exists() for path in self.preview["outputs"]))


if __name__ == "__main__":
    unittest.main()
