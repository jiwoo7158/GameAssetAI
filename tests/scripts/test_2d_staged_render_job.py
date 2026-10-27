import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from build_2d_staged_render_job import build_2d_staged_render_job


class StagedRenderJobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-job-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "result.png"
        self.stage = self.root / ".gameassetai-2d-test.stage.blend"
        self.job = self.root / ".gameassetai-2d-test.job.json"
        self.stage.write_bytes(b"BLENDER" + b"x" * 100)
        self.request = {"output": {"target_file": str(self.target)}}
        request_sha = hashlib.sha256(json.dumps(
            self.request, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
            allow_nan=False).encode()).hexdigest()
        fingerprints = {name: character * 64 for name, character in
                        (("source_fingerprint", "a"), ("setup_fingerprint", "b"),
                         ("output_fingerprint", "c"))}
        self.candidate = {"status": "candidate_for_review",
                          "request_sha256": request_sha, **fingerprints}
        self.framing = {"status": "planned", "request_sha256": request_sha,
                        "plan_fingerprint": "d" * 64, **fingerprints}
        data = self.stage.read_bytes()
        self.staged = {"status": "created", "request_sha256": request_sha,
                       "plan_fingerprint": "d" * 64, **fingerprints,
                       "stage_file": str(self.stage), "stage_size": len(data),
                       "stage_sha256": hashlib.sha256(data).hexdigest()}

    def test_authorization_is_required(self):
        result = build_2d_staged_render_job(
            self.request, self.candidate, self.framing, self.staged, self.job)
        self.assertEqual("error", result["status"])
        self.assertFalse(self.job.exists())

    def test_writes_exact_hash_bound_job(self):
        result = build_2d_staged_render_job(
            self.request, self.candidate, self.framing, self.staged, self.job,
            authorize=True)
        self.assertEqual("created", result["status"])
        payload = json.loads(self.job.read_text(encoding="utf-8"))
        self.assertEqual("gameassetai.2d-staged-render-job.v1", payload["schema"])
        self.assertEqual(self.staged["stage_sha256"], payload["source_stage"]["sha256"])
        self.assertEqual(hashlib.sha256(self.job.read_bytes()).hexdigest(),
                         result["job_sha256"])

    def test_collision_preserves_existing_job(self):
        self.job.write_bytes(b"existing")
        result = build_2d_staged_render_job(
            self.request, self.candidate, self.framing, self.staged, self.job,
            authorize=True)
        self.assertEqual("error", result["status"])
        self.assertEqual(b"existing", self.job.read_bytes())

    def test_changed_stage_is_refused(self):
        self.stage.write_bytes(self.stage.read_bytes() + b"changed")
        result = build_2d_staged_render_job(
            self.request, self.candidate, self.framing, self.staged, self.job,
            authorize=True)
        self.assertEqual("error", result["status"])
        self.assertFalse(self.job.exists())


if __name__ == "__main__":
    unittest.main()
