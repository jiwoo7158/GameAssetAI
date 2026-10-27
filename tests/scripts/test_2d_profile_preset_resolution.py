"""Fresh-hash and no-partial-merge tests for Profile-backed 2D settings."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from extract_2d_profile_preset import PRESET_SCHEMA  # noqa: E402
from resolve_2d_profile_preset import resolve_2d_profile_preset  # noqa: E402
from validate_2d_action_sequence_request import (  # noqa: E402
    SCHEMA as ACTION_SCHEMA, validate_2d_action_sequence_request)
from validate_2d_static_render_request import (  # noqa: E402
    SCHEMA as STATIC_SCHEMA, validate_2d_static_render_request)


class Profile2DPresetResolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-resolution-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        preset = {
            "schema": PRESET_SCHEMA,
            "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                     "up": [0, 0, 1], "framing_margin": 0.1},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [32, 32],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "NONE", "palette": [], "max_colors": None,
                      "outline_mode": "NONE", "outline_color": None,
                      "outline_width": 0, "shading_mode": "NONE", "value_steps": None},
            "sequence": {"playback_fps": 12.5},
            "sprite_sheet": {"padding": 2, "order": "ROW_MAJOR_TOP_LEFT"},
        }
        self.context = {"schema": "gameassetai.profile-context.v1", "profile": "TestGame",
                        "path": str(root / "TestGame.md"), "reference_sha256": "1" * 64,
                        "profile_sha256": "2" * 64,
                        "markdown": "```gameassetai-2d-preset\n" + json.dumps(preset) + "\n```\n",
                        "rules": "interpret explicit applicable Markdown rules; absent fields are unknown"}
        self.root = root

    def test_all_purposes_resolve_only_their_complete_settings(self):
        static = resolve_2d_profile_preset(self.context, "STATIC_RENDER")
        sequence = resolve_2d_profile_preset(self.context, "ACTION_SEQUENCE")
        sheet = resolve_2d_profile_preset(self.context, "SPRITE_SHEET")
        self.assertEqual("resolved", static["status"])
        self.assertEqual({"profile", "view", "lighting", "style"}, set(static["settings"]))
        self.assertEqual(12.5, sequence["settings"]["playback_fps"])
        self.assertEqual(2, sheet["settings"]["padding"])
        self.assertEqual("ROW_MAJOR_TOP_LEFT", sheet["settings"]["order"])

    def test_fresh_binding_accepts_exact_reread(self):
        preview = resolve_2d_profile_preset(self.context, "STATIC_RENDER")
        fresh = resolve_2d_profile_preset(
            json.loads(json.dumps(self.context)), "STATIC_RENDER", preview["binding"])
        self.assertEqual("resolved", fresh["status"])
        self.assertEqual(preview["settings"], fresh["settings"])

    def test_changed_reference_profile_or_preset_refuses(self):
        preview = resolve_2d_profile_preset(self.context, "ACTION_SEQUENCE")
        for key in ("reference_sha256", "profile_sha256"):
            changed = dict(self.context); changed[key] = "9" * 64
            self.assertEqual("error", resolve_2d_profile_preset(
                changed, "ACTION_SEQUENCE", preview["binding"])["status"])
        changed = dict(self.context); changed["markdown"] += "\n"
        # Markdown outside the exact block does not change the preset, but Profile provenance does.
        changed["profile_sha256"] = "8" * 64
        self.assertEqual("error", resolve_2d_profile_preset(
            changed, "ACTION_SEQUENCE", preview["binding"])["status"])
        changed = json.loads(json.dumps(self.context))
        changed["markdown"] = changed["markdown"].replace('"padding": 2', '"padding": 3')
        self.assertEqual("error", resolve_2d_profile_preset(
            changed, "ACTION_SEQUENCE", preview["binding"])["status"])

    def test_absence_never_falls_back_or_reuses_prior_binding(self):
        absent = dict(self.context); absent.update(profile=None, path=None, profile_sha256=None,
                                                   markdown=None)
        report = resolve_2d_profile_preset(absent, "STATIC_RENDER")
        self.assertEqual("absent", report["status"])
        self.assertIsNone(report["settings_source"])
        binding = resolve_2d_profile_preset(self.context, "STATIC_RENDER")["binding"]
        self.assertEqual("absent", resolve_2d_profile_preset(
            absent, "STATIC_RENDER", binding)["status"])

    def test_invalid_purpose_and_binding_shape_refuse(self):
        self.assertEqual("error", resolve_2d_profile_preset(
            self.context, "BATCH_ALL")["status"])
        self.assertEqual("error", resolve_2d_profile_preset(
            self.context, "SPRITE_SHEET", {"name": "TestGame"})["status"])

    def test_resolved_settings_form_valid_static_and_action_requests(self):
        static_settings = resolve_2d_profile_preset(
            self.context, "STATIC_RENDER")["settings"]
        static_request = {"schema": STATIC_SCHEMA, "scene_name": "Scene",
                          "object_name": "Hero", **static_settings,
                          "output": {"target_file": str(self.root / "hero.png"),
                                     "color_mode": "RGBA", "color_depth": 8,
                                     "overwrite": False}}
        static_report = validate_2d_static_render_request(static_request)
        self.assertTrue(static_report["ready_for_blender_inspection"],
                        static_report["errors"])

        sequence_settings = resolve_2d_profile_preset(
            self.context, "ACTION_SEQUENCE")["settings"]
        fps = sequence_settings.pop("playback_fps")
        action_request = {
            "schema": ACTION_SCHEMA,
            "static_template": {"schema": STATIC_SCHEMA, "scene_name": "Scene",
                                "object_name": "Hero", **sequence_settings},
            "animation": {"armature_name": "Rig", "action_name": "Walk",
                          "slot_identifier": None, "frame_start": 1, "frame_end": 3,
                          "frame_step": 1, "playback_fps": fps},
            "framing": {"bounds_policy": "ACTION_RANGE",
                        "anchor_policy": "OBJECT_ORIGIN"},
            "output": {"target_directory": str(self.root),
                       "filename_prefix": "walk_", "index_start": 0,
                       "index_padding": 4, "overwrite": False},
        }
        action_report = validate_2d_action_sequence_request(action_request)
        self.assertTrue(action_report["ready_for_blender_inspection"],
                        action_report["errors"])


if __name__ == "__main__":
    unittest.main()
