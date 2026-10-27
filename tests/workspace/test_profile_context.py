import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from read_profile_context import read_profile_context
from profile_check_fixture import active_bytes, operate


class ProfileContextTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="gameassetai-profile-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.workspace = self.base / "workspace"
        shutil.copytree(REPO / "workspace-template", self.workspace)
        self.state = self.base / "state.json"

    def test_null_is_unknown_not_defaults(self):
        context = read_profile_context(self.workspace)
        self.assertIsNone(context["profile"])
        self.assertIsNone(context["markdown"])

    def test_switch_reads_new_profile_and_restores_exact_original(self):
        reference = self.workspace / "config" / "active-profile.json"
        original = reference.read_bytes()
        names = sorted(p.name for p in (self.workspace / "profiles").iterdir())
        operate("start",self.workspace,self.state)
        operate("a",self.workspace,self.state)
        a = read_profile_context(self.workspace)
        operate("b",self.workspace,self.state)
        b = read_profile_context(self.workspace)
        self.assertIn("max_triangles: 10",a["markdown"])
        self.assertIn("max_triangles: 20",b["markdown"])
        self.assertNotEqual(a["profile_sha256"],b["profile_sha256"])
        operate("restore",self.workspace,self.state)
        self.assertEqual(original,reference.read_bytes())
        self.assertEqual(names,sorted(p.name for p in (self.workspace / "profiles").iterdir()))
        self.assertFalse(self.state.exists())

    def test_real_active_game_refused(self):
        (self.workspace/"profiles"/"Game.md").write_text("real game rules")
        (self.workspace/"config"/"active-profile.json").write_text('{"profile":"Game"}')
        with self.assertRaises(ValueError):
            operate("start",self.workspace,self.state)
        self.assertFalse(self.state.exists())

    def test_concurrent_personal_change_preserved(self):
        operate("start",self.workspace,self.state)
        reference=self.workspace/"config"/"active-profile.json"
        reference.write_text('{"profile":null,"personal":"new"}')
        with self.assertRaises(ValueError):
            operate("restore",self.workspace,self.state)
        self.assertEqual("new",json.loads(reference.read_text())["personal"])

    def test_missing_profile_fails_instead_of_stale_context(self):
        (self.workspace/"config"/"active-profile.json").write_text('{"profile":"missing"}')
        with self.assertRaises(ValueError):
            read_profile_context(self.workspace)

    def test_fixture_start_never_overwrites_previous_manifest(self):
        operate("start",self.workspace,self.state)
        original=self.state.read_bytes()
        with self.assertRaises(ValueError):
            operate("start",self.workspace,self.state)
        self.assertEqual(original,self.state.read_bytes())

    def test_interrupted_switch_can_restore_recognized_fixture_config(self):
        reference=self.workspace/"config"/"active-profile.json"
        original=reference.read_bytes()
        state=operate("start",self.workspace,self.state)
        reference.write_bytes(active_bytes(state,"a"))
        operate("restore",self.workspace,self.state)
        self.assertEqual(original,reference.read_bytes())
