"""Offline contract and publication tests for explicit silhouette masks."""
from pathlib import Path
import hashlib
import sys
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from derive_2d_silhouette_mask import derive_2d_silhouette_mask  # noqa: E402
from quantize_rgba import encode_png_rgba8  # noqa: E402
from validate_2d_silhouette_mask_request import (  # noqa: E402
    SCHEMA, decode_png_rgba8, validate_2d_silhouette_mask_request)


class SilhouetteMaskTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-mask-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.png"
        self.source.write_bytes(encode_png_rgba8([
            [(0, 0, 0, 0), (10, 20, 30, 1), (20, 30, 40, 128)],
            [(30, 40, 50, 255), (0, 0, 0, 0), (1, 2, 3, 200)]]))
        self.request = {
            "schema": SCHEMA, "source_file": str(self.source),
            "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            "target_file": str(self.root / "mask.png"),
            "visible_rgba": [1, 0.5, 0, 1], "alpha_policy": "BINARY_NONZERO",
            "overwrite": False}

    def candidate(self, request=None):
        return validate_2d_silhouette_mask_request(request or self.request)

    def test_candidate_is_read_only_hash_bound_and_reports_source(self):
        before = self.source.read_bytes(); candidate = self.candidate()
        self.assertEqual("candidate_for_review", candidate["status"])
        self.assertEqual((3, 2), (candidate["source"]["width"], candidate["source"]["height"]))
        self.assertEqual(4, candidate["source"]["visible_pixels"])
        self.assertEqual(3, candidate["source"]["partial_alpha_pixels"])
        self.assertEqual(before, self.source.read_bytes())
        self.assertFalse(Path(self.request["target_file"]).exists())

    def test_binary_mask_publishes_exact_new_rgba8_and_receipt(self):
        result = derive_2d_silhouette_mask(self.request, self.candidate(), authorize=True)
        self.assertEqual("created", result["status"])
        data, width, height, pixels = decode_png_rgba8(self.request["target_file"])
        self.assertEqual((3, 2), (width, height))
        self.assertEqual([[(0, 0, 0, 0), (255, 128, 0, 255), (255, 128, 0, 255)],
                          [(255, 128, 0, 255), (0, 0, 0, 0), (255, 128, 0, 255)]], pixels)
        self.assertEqual(hashlib.sha256(data).hexdigest(), result["artifact"]["sha256"])
        self.assertEqual(0, result["artifact"]["partial_alpha_pixels"])
        self.assertEqual(64, len(result["receipt_sha256"]))
        self.assertFalse(list(self.root.glob(".gameassetai-mask-*.stage.png")))

    def test_preserve_alpha_keeps_every_source_alpha(self):
        request = {**self.request, "target_file": str(self.root / "preserve.png"),
                   "alpha_policy": "PRESERVE_ALPHA", "visible_rgba": [1, 1, 1, 1]}
        result = derive_2d_silhouette_mask(request, self.candidate(request), authorize=True)
        self.assertEqual("created", result["status"])
        pixels = decode_png_rgba8(request["target_file"])[3]
        self.assertEqual([[0, 1, 128], [255, 0, 200]],
                         [[pixel[3] for pixel in row] for row in pixels])
        self.assertEqual(3, result["artifact"]["partial_alpha_pixels"])

    def test_authorization_staleness_collision_and_policy_refuse(self):
        candidate = self.candidate()
        self.assertEqual("error", derive_2d_silhouette_mask(
            self.request, candidate, authorize=False)["status"])
        self.source.write_bytes(self.source.read_bytes() + b"drift")
        self.assertEqual("error", derive_2d_silhouette_mask(
            self.request, candidate, authorize=True)["status"])
        self.source.write_bytes(encode_png_rgba8([[(1, 2, 3, 255)]]))
        changed = {**self.request,
                   "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}
        Path(changed["target_file"]).write_bytes(b"sentinel")
        report = validate_2d_silhouette_mask_request(changed)
        self.assertEqual("blocked", report["status"])
        self.assertEqual(b"sentinel", Path(changed["target_file"]).read_bytes())
        invalid = {**changed, "target_file": str(self.root / "new.png"),
                   "alpha_policy": "THRESHOLD"}
        self.assertEqual("blocked", validate_2d_silhouette_mask_request(invalid)["status"])

    def test_publication_failure_rolls_back_and_cleans_stage(self):
        real_link = __import__("os").link
        def fail_after_link(source, target):
            real_link(source, target)
            raise OSError("injected publication failure")
        with mock.patch("derive_2d_silhouette_mask.os.link", side_effect=fail_after_link):
            result = derive_2d_silhouette_mask(
                self.request, self.candidate(), authorize=True)
        self.assertEqual("error", result["status"])
        self.assertFalse(Path(self.request["target_file"]).exists())
        self.assertFalse(list(self.root.glob(".gameassetai-mask-*.stage.png")))

    def test_concurrently_changed_published_mask_is_retained(self):
        real_link = __import__("os").link
        target = Path(self.request["target_file"])
        def change_after_link(source, destination):
            real_link(source, destination)
            target.write_bytes(b"concurrent-owner")
            raise OSError("injected concurrent change")
        with mock.patch("derive_2d_silhouette_mask.os.link", side_effect=change_after_link):
            result = derive_2d_silhouette_mask(
                self.request, self.candidate(), authorize=True)
        self.assertEqual("error", result["status"])
        self.assertEqual(b"concurrent-owner", target.read_bytes())
        self.assertTrue(any("changed concurrently" in error for error in result["errors"]))
        self.assertFalse(list(self.root.glob(".gameassetai-mask-*.stage.png")))


if __name__ == "__main__":
    unittest.main()
