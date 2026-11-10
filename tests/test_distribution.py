from pathlib import Path
import json
import os
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

        workspace = self.root / "installed-workspace"
        commands = (
            ["workspace", "create", str(workspace)],
            [
                "profile", "create", str(workspace), "game-one", "--name", "Game One",
                "--description", "Installed runtime smoke test",
            ],
            ["profile", "select", str(workspace), "game-one"],
            [
                "profile", "set", str(workspace), "art_direction.palette",
                "--value-json", '["moss", "bark"]',
            ],
            ["profile", "get", str(workspace), "art_direction.palette"],
        )
        last = None
        for arguments in commands:
            last = subprocess.run(
                [sys.executable, "-B", str(entry), *arguments],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, last.returncode, last.stderr)
        self.assertEqual(["moss", "bark"], json.loads(last.stdout)["value"])

        archive_a, archive_b = self.root / "a.zip", self.root / "b.zip"
        first = write_bundle_zip(self.bundle, archive_a)
        second = write_bundle_zip(self.bundle, archive_b)
        self.assertEqual(first["sha256"], second["sha256"])

    def test_install_refuses_overwrite_and_update_retains_backup(self):
        self.build()
        installed = self.root / "workspace" / ".codex" / "skills"
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

    def test_install_refuses_linked_target_component(self):
        self.build()
        external = self.root / "external-skills"
        external.mkdir()
        linked = self.root / "linked-parent"
        try:
            linked.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")
        with self.assertRaises(SafetyError):
            install_product_bundle(self.bundle, linked / "skills")
        self.assertEqual([], list(external.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_install_refuses_windows_junction_component(self):
        self.build()
        external = self.root / "external-skills"
        external.mkdir()
        junction = self.root / "linked-parent"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.skipTest(f"Cannot create a test junction: {result.stderr or result.stdout}")
        try:
            with self.assertRaises(SafetyError):
                install_product_bundle(self.bundle, junction / "skills")
            self.assertEqual([], list(external.iterdir()))
        finally:
            if junction.exists():
                os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
