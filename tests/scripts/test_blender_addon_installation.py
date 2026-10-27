import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from inspect_blender_addon_installation import inspect_installation


class BlenderAddonInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-addon-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "gameassetai"
        self.installed = self.root / "addons" / "gameassetai"
        self.source.mkdir()
        (self.source / "__init__.py").write_text(
            "bl_info={'name':'GameAssetAI','version':(0,1,5),'blender':(5,0,0)}\n",
            encoding="utf-8")
        (self.source / "module.py").write_text("VALUE=1\n", encoding="utf-8")

    def test_missing_installation_is_reported(self):
        result = inspect_installation(self.source, self.installed, "5.0.1")
        self.assertEqual("not_installed", result["status"])
        self.assertEqual(["__init__.py", "module.py"], result["missing"])

    def test_aligned_installation_and_versions(self):
        shutil.copytree(self.source, self.installed)
        result = inspect_installation(self.source, self.installed, "5.0.1")
        self.assertEqual("aligned", result["status"])
        self.assertTrue(result["blender_compatible"])
        self.assertEqual([0, 1, 5], result["installed_info"]["version"])

    def test_update_needed_reports_file_differences(self):
        shutil.copytree(self.source, self.installed)
        (self.installed / "module.py").write_text("VALUE=2\n", encoding="utf-8")
        (self.installed / "extra.py").write_text("EXTRA=True\n", encoding="utf-8")
        result = inspect_installation(self.source, self.installed)
        self.assertEqual("update_needed", result["status"])
        self.assertEqual(["module.py"], result["changed"])
        self.assertEqual(["extra.py"], result["extra"])

    def test_missing_metadata_is_refused(self):
        shutil.copytree(self.source, self.installed)
        (self.installed / "__init__.py").unlink()
        with self.assertRaisesRegex(ValueError, "__init__.py is missing"):
            inspect_installation(self.source, self.installed)

    def test_incompatible_blender_is_reported(self):
        shutil.copytree(self.source, self.installed)
        result = inspect_installation(self.source, self.installed, "4.3.2")
        self.assertEqual("aligned", result["status"])
        self.assertFalse(result["blender_compatible"])


if __name__ == "__main__":
    unittest.main()
