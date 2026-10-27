"""Offline tests for the authorized hash-bound 2D batch job."""
from __future__ import annotations

import copy
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
from test_2d_render_batch_request import make_batch_fixture  # noqa: E402
from validate_2d_render_batch_request import validate_2d_render_batch_request  # noqa: E402


class Render2DBatchJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-batch-job-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, _, _ = make_batch_fixture(self.root)
        self.preview = validate_2d_render_batch_request(self.request)
        self.children = []
        for index, item in enumerate(self.request["items"]):
            kind = item["kind"]
            stage = self.root / f"child-{index}.stage.blend"
            stage.write_bytes(("stage-" + str(index)).encode())
            stage_sha = hashlib.sha256(stage.read_bytes()).hexdigest()
            job = self.root / f"child-{index}.job.json"
            payload = {"schema": ("gameassetai.2d-staged-render-job.v1" if kind == "STATIC"
                                  else "gameassetai.2d-action-sequence-job.v1"),
                       "request": item["request"],
                       "source_stage": {"path": str(stage), "size": stage.stat().st_size,
                                        "sha256": stage_sha}}
            job.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")),
                           encoding="utf-8")
            self.children.append({"id": item["id"], "kind": kind,
                                  "stage_file": str(stage), "stage_sha256": stage_sha,
                                  "job_file": str(job),
                                  "job_sha256": hashlib.sha256(job.read_bytes()).hexdigest(),
                                  "helper_root": str(REPO / "scripts")})
        self.job = self.root / ".gameassetai-2d-batch-test.job.json"

    def build(self, authorize=True):
        return build_2d_render_batch_job(self.request, self.preview, self.children,
                                         str(self.job), authorize=authorize)

    def test_authorized_job_binds_every_child_and_helpers(self):
        result = self.build()
        self.assertEqual("created", result["status"], result["errors"])
        payload = json.loads(self.job.read_text(encoding="utf-8"))
        self.assertEqual(self.preview["batch_sha256"], payload["batch_sha256"])
        self.assertEqual(2, len(payload["children"]))
        self.assertIn("render_2d_staged_source.py",
                      payload["children"][0]["helper_sha256"])
        self.assertIn("render_2d_action_sequence.py",
                      payload["children"][1]["helper_sha256"])

    def test_authorization_stale_preview_and_collision_refuse(self):
        self.assertEqual("error", self.build(authorize=False)["status"])
        stale = copy.deepcopy(self.preview); stale["batch_sha256"] = "0" * 64
        self.assertEqual("error", build_2d_render_batch_job(
            self.request, stale, self.children, str(self.job), authorize=True)["status"])
        self.job.write_text("sentinel", encoding="utf-8")
        self.assertEqual("error", self.build()["status"])
        self.assertEqual("sentinel", self.job.read_text(encoding="utf-8"))

    def test_changed_stage_job_request_or_helper_refuses(self):
        changed = copy.deepcopy(self.children)
        Path(changed[0]["stage_file"]).write_bytes(b"changed")
        self.assertEqual("error", build_2d_render_batch_job(
            self.request, self.preview, changed, str(self.job), authorize=True)["status"])
        self.setUp()
        changed = copy.deepcopy(self.children); changed[0]["job_sha256"] = "0" * 64
        self.assertEqual("error", build_2d_render_batch_job(
            self.request, self.preview, changed, str(self.job), authorize=True)["status"])
        changed = copy.deepcopy(self.children); changed[0]["helper_root"] = str(self.root)
        self.assertEqual("error", build_2d_render_batch_job(
            self.request, self.preview, changed, str(self.job), authorize=True)["status"])

    def test_target_appearing_after_preview_refuses_without_job(self):
        Path(self.preview["outputs"][0]).write_bytes(b"collision")
        result = self.build()
        self.assertEqual("error", result["status"])
        self.assertFalse(self.job.exists())


if __name__ == "__main__":
    unittest.main()
