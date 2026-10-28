import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tests" / "blender_addon"))
from record_real_mixamo_visual_review import CHECKS, record_review


class RealMixamoVisualReviewTests(unittest.TestCase):
    def setUp(self):
        (REPO / ".local").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-visual-review-",
                                                dir=REPO / ".local")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.images = {}
        for key in ("1-front", "1-side"):
            path = self.root / f"{key}.png"; path.write_bytes(b"png-" + key.encode())
            self.images[key] = str(path)
        self.report = self.root / "validation.json"
        self.report.write_text(json.dumps({
            "status": "structural_pass_visual_review_required",
            "source_fbx_sha256": "a" * 64, "images": self.images,
        }), encoding="utf-8")
        self.output = self.root / "review.json"
        self.findings = tuple(f"{key}=accepted" for key in CHECKS)
        self.image_args = tuple(f"{key}={path}" for key, path in self.images.items())

    def test_explicit_review_records_reviewer_time_and_image_hashes(self):
        result = record_review(report_path=self.report, output=self.output,
                               reviewer="Codex visual inspection",
                               reviewed_at="2026-10-28T12:00:00+09:00",
                               decision="accepted", images=self.image_args,
                               findings=self.findings, notes="Compared source and target")
        self.assertEqual("accepted", result["status"])
        self.assertEqual(2, len(result["reviewed_images"]))
        self.assertTrue(all(item["sha256"] for item in result["reviewed_images"]))

    def test_acceptance_refuses_missing_images_or_findings(self):
        with self.assertRaises(ValueError):
            record_review(report_path=self.report, output=self.output, reviewer="reviewer",
                          reviewed_at="2026-10-28T12:00:00Z", decision="accepted",
                          images=self.image_args[:1], findings=self.findings)
        with self.assertRaises(ValueError):
            record_review(report_path=self.report, output=self.output, reviewer="reviewer",
                          reviewed_at="2026-10-28T12:00:00Z", decision="accepted",
                          images=self.image_args, findings=self.findings[:1])

    def test_no_implicit_reviewer_or_timezone(self):
        for reviewer, reviewed_at in (("", "2026-10-28T12:00:00Z"),
                                      ("reviewer", "2026-10-28T12:00:00")):
            with self.assertRaises(ValueError):
                record_review(report_path=self.report, output=self.output, reviewer=reviewer,
                              reviewed_at=reviewed_at, decision="accepted",
                              images=self.image_args, findings=self.findings)


if __name__ == "__main__":
    unittest.main()
