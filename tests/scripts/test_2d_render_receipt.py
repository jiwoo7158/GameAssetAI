"""Offline regressions for static 2D artifact receipts."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from build_2d_render_receipt import build_2d_render_receipt


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class RenderReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-2d-receipt-")
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "result.png"
        self.target.write_bytes(b"\x89PNG\r\n\x1a\nfixture")
        self.request = {"schema": "gameassetai.2d-static-render-request.v1",
                        "output": {"target_file": str(self.target)}}
        self.candidate = {"status": "candidate_for_review",
                          "request_sha256": digest(self.request),
                          "source_fingerprint": "a" * 64,
                          "setup_fingerprint": "b" * 64,
                          "output_fingerprint": digest(self.request["output"])}
        self.framing = {**self.candidate, "status": "planned",
                        "plan_fingerprint": "c" * 64}
        self.facts = {"width": 2, "height": 2, "color_depth": 8, "color_type": 6,
                      "alpha_bounds": [0, 0, 1, 1], "foreground_pixels": 4,
                      "unique_rgba": 2}

    def test_receipt_binds_all_hashes_and_file(self):
        receipt = build_2d_render_receipt(
            self.request, self.candidate, self.framing, self.facts)
        self.assertEqual(hashlib.sha256(self.target.read_bytes()).hexdigest(),
                         receipt["artifact"]["sha256"])
        self.assertEqual(64, len(receipt["receipt_sha256"]))
        self.assertEqual(self.facts["alpha_bounds"], receipt["artifact"]["alpha_bounds"])

    def test_stale_request_or_fingerprints_refuse(self):
        changed = {**self.request, "extra": True}
        with self.assertRaises(ValueError):
            build_2d_render_receipt(changed, self.candidate, self.framing, self.facts)
        stale = {**self.framing, "source_fingerprint": "d" * 64}
        with self.assertRaises(ValueError):
            build_2d_render_receipt(self.request, self.candidate, stale, self.facts)

    def test_missing_or_non_png_artifact_refuses(self):
        self.target.unlink()
        with self.assertRaises(ValueError):
            build_2d_render_receipt(self.request, self.candidate, self.framing, self.facts)
        self.target.write_bytes(b"not png")
        with self.assertRaises(ValueError):
            build_2d_render_receipt(self.request, self.candidate, self.framing, self.facts)

    def test_fact_schema_and_types_are_exact(self):
        with self.assertRaises(ValueError):
            build_2d_render_receipt(self.request, self.candidate, self.framing,
                                    {**self.facts, "unknown": 1})
        with self.assertRaises(ValueError):
            build_2d_render_receipt(self.request, self.candidate, self.framing,
                                    {**self.facts, "width": True})


if __name__ == "__main__":
    unittest.main()
