import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from record_visual_review import record_review  # noqa: E402


class VisualReviewTests(unittest.TestCase):
    def test_review_binds_every_image_and_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "view.png"
            image.write_bytes(b"image")
            report = root / "validation.json"
            report.write_text(json.dumps({
                "status": "structural_pass_visual_review_required",
                "images": {"view": str(image)},
                "required_visual_checks": ["recognizable"],
            }), encoding="utf-8")
            result = record_review(
                report_path=report, output=root / "review.json", reviewer="Codex",
                reviewed_at="2026-11-02T12:00:00+09:00", decision="accepted",
                findings={"recognizable": "accepted"},
            )
            self.assertEqual("accepted", result["status"])
            self.assertEqual(64, len(result["reviewed_images"][0]["sha256"]))

    def test_incomplete_findings_do_not_accept(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            image = root / "view.png"
            image.write_bytes(b"image")
            report = root / "validation.json"
            report.write_text(json.dumps({
                "status": "structural_pass_visual_review_required",
                "images": {"view": str(image)},
                "required_visual_checks": ["recognizable", "usable"],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "every required"):
                record_review(
                    report_path=report, output=root / "review.json", reviewer="Codex",
                    reviewed_at="2026-11-02T12:00:00+09:00", decision="accepted",
                    findings={"recognizable": "accepted"},
                )


if __name__ == "__main__":
    unittest.main()
