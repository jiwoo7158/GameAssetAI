"""Offline no-overwrite publication checks on test-owned temporary files."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from promote_export_artifact import promote_export_artifact


class ExportPromotionTests(unittest.TestCase):
    def test_publish_preserves_stage_and_refuses_collision(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-promotion-") as temporary:
            base = Path(temporary)
            stage = base / "stage.fbx"
            target = base / "target.fbx"
            stage.write_bytes(b"owned-stage-one")
            report = promote_export_artifact(stage, target)
            self.assertEqual("published", report["status"])
            self.assertFalse(report["overwrite_performed"])
            self.assertEqual(stage.read_bytes(), target.read_bytes())
            second = base / "second.fbx"
            second.write_bytes(b"owned-stage-two")
            with self.assertRaises(FileExistsError):
                promote_export_artifact(second, target)
            self.assertEqual(b"owned-stage-one", target.read_bytes())
            self.assertEqual(b"owned-stage-two", second.read_bytes())

    def test_invalid_sources_refuse_without_target(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-promotion-") as temporary:
            base = Path(temporary)
            stage = base / "stage.fbx"
            target = base / "target.fbx"
            stage.write_bytes(b"owned-stage")
            for source, destination in ((Path("relative.fbx"), target),
                                        (stage, Path("relative.fbx")),
                                        (stage, stage),
                                        (base / "missing.fbx", target)):
                with self.assertRaises(ValueError):
                    promote_export_artifact(source, destination)
            self.assertFalse(target.exists())

    def test_unsupported_hardlink_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="gameassetai-promotion-") as temporary:
            base = Path(temporary)
            stage = base / "stage.fbx"
            target = base / "target.fbx"
            stage.write_bytes(b"owned-stage")
            with patch("promote_export_artifact.os.link", side_effect=OSError("link unsupported")):
                with self.assertRaises(OSError):
                    promote_export_artifact(stage, target)
            self.assertFalse(target.exists())
            self.assertEqual(b"owned-stage", stage.read_bytes())


if __name__ == "__main__":
    unittest.main()
