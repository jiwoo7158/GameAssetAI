import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from update_blender_addon import apply_update, plan_update, restore_update


def addon(root: Path, version=(0, 1, 0), value="old") -> None:
    root.mkdir(parents=True)
    (root / "__init__.py").write_text(
        f"bl_info={{'name':'GameAssetAI','version':{version!r},'blender':(5,0,0)}}\n",
        encoding="utf-8")
    (root / "module.py").write_text(f"VALUE={value!r}\n", encoding="utf-8")


class BlenderAddonUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-addon-update-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.source, self.installed = root / "source" / "gameassetai", root / "addons" / "gameassetai"
        self.backup, self.replaced = root / "backup" / "gameassetai-old", root / "backup" / "gameassetai-new"
        self.backup.parent.mkdir()
        addon(self.source, (0, 2, 0), "new")
        addon(self.installed, (0, 1, 0), "old")

    def test_update_preserves_backup_and_exact_source(self):
        plan = plan_update(self.source, self.installed, self.backup)
        result = apply_update(plan)
        self.assertEqual("updated", result["status"])
        self.assertTrue(result["restart_required"])
        self.assertIn("new", (self.installed / "module.py").read_text())
        self.assertIn("old", (self.backup / "module.py").read_text())

    def test_source_drift_after_plan_is_refused(self):
        plan = plan_update(self.source, self.installed, self.backup)
        (self.source / "module.py").write_text("VALUE='changed'\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "changed after planning"):
            apply_update(plan)
        self.assertFalse(self.backup.exists())
        self.assertIn("old", (self.installed / "module.py").read_text())

    def test_restore_retains_replaced_new_version(self):
        plan = plan_update(self.source, self.installed, self.backup)
        apply_update(plan)
        result = restore_update(plan, self.replaced)
        self.assertEqual("restored", result["status"])
        self.assertIn("old", (self.installed / "module.py").read_text())
        self.assertIn("new", (self.replaced / "module.py").read_text())

    def test_aligned_apply_is_noop(self):
        shutil.rmtree(self.installed)
        shutil.copytree(self.source, self.installed)
        plan = plan_update(self.source, self.installed, self.backup)
        result = apply_update(plan)
        self.assertEqual("already_aligned", result["status"])
        self.assertFalse(result["restart_required"])
        self.assertFalse(self.backup.exists())


if __name__ == "__main__":
    unittest.main()
