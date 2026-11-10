from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.distribution import (  # noqa: E402
    PRODUCT_SKILLS, build_product_bundle, install_product_bundle,
    update_product_bundle, validate_product_bundle, write_bundle_zip,
)
from gameassetai.errors import SafetyError  # noqa: E402


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-distribution-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"

    def build(self):
        build_product_bundle(ROOT, self.bundle)

    def test_bundle_is_self_contained_reproducible_and_executable(self):
        self.build()
        self.assertEqual("valid", validate_product_bundle(self.bundle)["status"])
        for name in PRODUCT_SKILLS:
            skill = self.bundle / "skills" / name
            self.assertTrue((skill / "runtime" / "gameassetai" / "cli.py").is_file())
            all_text = "\n".join(
                path.read_text(encoding="utf-8-sig")
                for path in skill.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".json"}
            )
            self.assertNotIn(str(ROOT), all_text)
        entry = self.bundle / "skills" / "gameassetai-workspace" / "scripts" / "gameassetai.py"
        result = subprocess.run(
            [sys.executable, "-B", str(entry), "catalog", "validate"],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"status": "valid"', result.stdout)

        archive_a, archive_b = self.root / "a.zip", self.root / "b.zip"
        first = write_bundle_zip(self.bundle, archive_a)
        second = write_bundle_zip(self.bundle, archive_b)
        self.assertEqual(first["sha256"], second["sha256"])

    def test_install_refuses_overwrite_and_update_retains_backup(self):
        self.build()
        installed = self.root / "workspace" / ".agents" / "skills"
        self.assertEqual("installed", install_product_bundle(self.bundle, installed)["status"])
        with self.assertRaises(SafetyError):
            install_product_bundle(self.bundle, installed)
        personal = installed / PRODUCT_SKILLS[0] / "personal.txt"
        personal.write_text("preserve old installation", encoding="utf-8")

        rebuilt = self.root / "rebuilt"
        build_product_bundle(ROOT, rebuilt)
        backup = self.root / "backup" / "product-0.2.0-old"
        result = update_product_bundle(rebuilt, installed, backup)
        self.assertEqual("updated", result["status"])
        self.assertEqual("preserve old installation", (backup / PRODUCT_SKILLS[0] / "personal.txt").read_text())
        self.assertFalse((installed / PRODUCT_SKILLS[0] / "personal.txt").exists())
        self.assertEqual("valid", validate_product_bundle(rebuilt)["status"])


if __name__ == "__main__":
    unittest.main()
