from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.errors import SafetyError, ValidationError  # noqa: E402
from gameassetai.workspace import (  # noqa: E402
    create_or_connect_workspace, create_profile, list_profiles, read_active_profile,
    read_profile, read_profile_setting, read_workspace_output_root, select_profile,
    set_workspace_output_root, update_profile_setting,
    update_workspace, validate_workspace,
)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-workspace-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "custom-location"

    def create(self):
        return create_or_connect_workspace(ROOT / "workspace-template", self.workspace)

    def test_create_connect_profile_switch_and_persistence(self):
        self.assertEqual("created", self.create()["status"])
        marker = json.loads((self.workspace / "config" / "workspace.json").read_text())
        self.assertNotEqual("workspace-template", marker["workspace_id"])
        self.assertEqual("connected", self.create()["status"])
        create_profile(
            self.workspace, "forest-game", "Forest Game", "Persistent style context",
            three_d_style="stylized-chibi-low-poly",
        )
        select_profile(self.workspace, "forest-game")
        self.assertEqual("forest-game", validate_workspace(self.workspace, require_profile=True)["active_profile"])
        self.assertEqual("Forest Game", read_active_profile(self.workspace)["name"])
        self.assertEqual([{"id": "forest-game", "name": "Forest Game", "active": True}], list_profiles(self.workspace))
        select_profile(self.workspace, None)
        self.assertIsNone(validate_workspace(self.workspace)["active_profile"])

    def test_update_never_overwrites_personal_files(self):
        self.create()
        agents = self.workspace / "AGENTS.md"
        agents.write_text("personal workspace instructions", encoding="utf-8")
        (self.workspace / "notes" / "personal.md").write_text("keep", encoding="utf-8")
        result = update_workspace(ROOT / "workspace-template", self.workspace)
        self.assertIn(result["status"], {"already-current", "updated"})
        self.assertEqual("personal workspace instructions", agents.read_text(encoding="utf-8"))
        self.assertEqual("keep", (self.workspace / "notes" / "personal.md").read_text(encoding="utf-8"))

    def test_existing_unknown_directory_refused_and_legacy_is_read_only(self):
        self.workspace.mkdir()
        (self.workspace / "personal.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(SafetyError):
            self.create()
        self.assertEqual("keep", (self.workspace / "personal.txt").read_text())

        legacy = self.root / "legacy"
        (legacy / "config").mkdir(parents=True)
        (legacy / "profiles").mkdir()
        (legacy / "AGENTS.md").write_text("legacy", encoding="utf-8")
        (legacy / "config" / "active-profile.json").write_text('{"profile":null}', encoding="utf-8")
        (legacy / "config" / "projects.json").write_text('{"projects":{}}', encoding="utf-8")
        before = {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()}
        report = create_or_connect_workspace(ROOT / "workspace-template", legacy)
        self.assertEqual("legacy-connected", report["status"])
        self.assertTrue(report["migration_required"])
        self.assertEqual(before, {p.relative_to(legacy): p.read_bytes() for p in legacy.rglob("*") if p.is_file()})

    def test_missing_active_profile_is_refused(self):
        self.create()
        active = self.workspace / "config" / "active-profile.json"
        active.write_text('{"schema":"gameassetai.active-profile.v1","profile":"missing"}', encoding="utf-8")
        with self.assertRaises(ValidationError):
            validate_workspace(self.workspace)

    def test_profile_setting_update_is_explicit_atomic_and_preserves_other_fields(self):
        self.create()
        create_profile(
            self.workspace, "forest-game", "Forest Game", "Persistent style context",
            three_d_style="stylized-chibi-low-poly",
        )
        create_profile(self.workspace, "desert-game", "Desert Game", "Other game context")
        select_profile(self.workspace, "forest-game")

        update_profile_setting(
            self.workspace, "art_direction.palette", ["moss", "bark"],
        )
        update_profile_setting(
            self.workspace,
            "asset_defaults.character.proportions",
            {"head_ratio": "large", "silhouette": "compact"},
        )
        profile = read_profile(self.workspace)
        self.assertEqual("Persistent style context", profile["description"])
        self.assertEqual(["blend"], profile["output_defaults"]["formats"])
        self.assertEqual(["moss", "bark"], profile["art_direction"]["palette"])
        self.assertEqual(
            {"head_ratio": "large", "silhouette": "compact"},
            read_profile_setting(
                self.workspace, "asset_defaults.character.proportions",
            )["value"],
        )
        self.assertEqual({}, read_profile(self.workspace, "desert-game")["asset_defaults"])

        profile_path = self.workspace / "profiles" / "forest-game.json"
        before = profile_path.read_bytes()
        with self.assertRaises(ValidationError):
            update_profile_setting(self.workspace, "styles.two_d", "not-a-list")
        self.assertEqual(before, profile_path.read_bytes())

    def test_profile_update_requires_specific_mutable_setting(self):
        self.create()
        create_profile(self.workspace, "forest-game", "Forest Game", "Persistent context")
        select_profile(self.workspace, "forest-game")
        with self.assertRaisesRegex(ValidationError, "specific child"):
            update_profile_setting(self.workspace, "art_direction", {})
        with self.assertRaisesRegex(ValidationError, "read-only"):
            update_profile_setting(self.workspace, "schema", "other")

    def test_profile_style_ids_are_catalog_and_dimension_validated_without_data_loss(self):
        self.create()
        create_profile(
            self.workspace, "forest-game", "Forest Game", "Style validation",
            three_d_style="stylized-chibi-low-poly",
            two_d_styles=["eight-direction-pixel-sprite"],
        )
        select_profile(self.workspace, "forest-game")
        profile_path = self.workspace / "profiles" / "forest-game.json"
        before = profile_path.read_bytes()

        with self.assertRaisesRegex(ValidationError, "Unknown styles identifier"):
            update_profile_setting(self.workspace, "styles.three_d", "missing-style")
        self.assertEqual(before, profile_path.read_bytes())
        with self.assertRaisesRegex(ValidationError, "must reference a 3D style"):
            update_profile_setting(
                self.workspace, "styles.three_d", "eight-direction-pixel-sprite",
            )
        self.assertEqual(before, profile_path.read_bytes())
        with self.assertRaisesRegex(ValidationError, "only reference 2D styles"):
            update_profile_setting(
                self.workspace, "styles.two_d", ["simplified-stylized"],
            )
        self.assertEqual(before, profile_path.read_bytes())

        update_profile_setting(
            self.workspace, "art_direction.rules",
            ["Freeform user rule, not an official style id"],
        )
        profile = read_profile(self.workspace)
        self.assertEqual("stylized-chibi-low-poly", profile["styles"]["three_d"])
        self.assertEqual(
            ["eight-direction-pixel-sprite"], profile["styles"]["two_d"],
        )
        self.assertEqual(
            ["Freeform user rule, not an official style id"],
            profile["art_direction"]["rules"],
        )

    def test_profile_creation_and_loading_reject_invalid_style_ids_without_mutation(self):
        self.create()
        with self.assertRaises(ValidationError):
            create_profile(
                self.workspace, "bad-game", "Bad Game", "Unknown style",
                three_d_style="unknown-style",
            )
        self.assertFalse((self.workspace / "profiles" / "bad-game.json").exists())
        with self.assertRaisesRegex(ValidationError, "must reference a 3D style"):
            create_profile(
                self.workspace, "wrong-game", "Wrong Game", "Wrong dimension",
                three_d_style="animated-sprite-sheet",
            )
        self.assertFalse((self.workspace / "profiles" / "wrong-game.json").exists())

        create_profile(self.workspace, "forest-game", "Forest Game", "Load validation")
        path = self.workspace / "profiles" / "forest-game.json"
        document = json.loads(path.read_text(encoding="utf-8"))
        document["styles"]["two_d"] = ["faceted-angular-low-poly"]
        path.write_text(json.dumps(document), encoding="utf-8")
        corrupted = path.read_bytes()
        with self.assertRaisesRegex(ValidationError, "only reference 2D styles"):
            validate_workspace(self.workspace)
        with self.assertRaisesRegex(ValidationError, "only reference 2D styles"):
            read_profile(self.workspace, "forest-game")
        self.assertEqual(corrupted, path.read_bytes())

    def test_workspace_and_profile_output_roots_are_explicit_and_non_destructive(self):
        self.create()
        create_profile(self.workspace, "forest-game", "Forest Game", "Output root policy")
        select_profile(self.workspace, "forest-game")
        external = self.root / "external-output"
        external.mkdir()
        result = set_workspace_output_root(self.workspace, str(external))
        self.assertEqual(str(external), result["output_root"])
        self.assertEqual("workspace-preference", read_workspace_output_root(self.workspace)["source"])

        profile_path = self.workspace / "profiles" / "forest-game.json"
        before = profile_path.read_bytes()
        with self.assertRaisesRegex(ValidationError, "absolute"):
            update_profile_setting(self.workspace, "output_defaults.root", "relative-output")
        self.assertEqual(before, profile_path.read_bytes())

        external.rmdir()
        self.assertEqual("valid", validate_workspace(self.workspace)["status"])
        set_workspace_output_root(self.workspace, None)
        self.assertEqual("workspace-internal", read_workspace_output_root(self.workspace)["source"])


if __name__ == "__main__":
    unittest.main()
