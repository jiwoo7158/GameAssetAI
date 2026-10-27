"""Offline tests for one optional exact 2D preset embedded in Profile Markdown."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from extract_2d_profile_preset import (  # noqa: E402
    PRESET_SCHEMA, extract_2d_profile_preset)


class Profile2DPresetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-profile-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.preset = {
            "schema": PRESET_SCHEMA,
            "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                     "up": [0, 0, 1], "framing_margin": 0.1},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [32, 32],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "NONE", "palette": [], "max_colors": None,
                      "outline_mode": "NONE", "outline_color": None,
                      "outline_width": 0, "shading_mode": "NONE", "value_steps": None},
            "sequence": {"playback_fps": 12},
            "sprite_sheet": {"padding": 1, "order": "ROW_MAJOR_TOP_LEFT"},
        }

    def context(self, markdown=None, active=True):
        return {"schema": "gameassetai.profile-context.v1",
                "profile": "TestGame" if active else None,
                "path": str(self.root / "TestGame.md") if active else None,
                "reference_sha256": "1" * 64,
                "profile_sha256": "2" * 64 if active else None,
                "markdown": markdown if active else None,
                "rules": "interpret explicit applicable Markdown rules; absent fields are unknown"}

    def block(self, preset=None):
        return "# Profile\n\n```gameassetai-2d-preset\n" + json.dumps(
            preset or self.preset) + "\n```\n"

    def test_null_and_unconfigured_profiles_are_absent(self):
        self.assertEqual("absent", extract_2d_profile_preset(
            self.context(active=False))["status"])
        report = extract_2d_profile_preset(self.context("# Profile\n"))
        self.assertEqual("absent", report["status"])
        self.assertEqual("no_explicit_2d_preset", report["reason"])

    def test_exact_preset_is_ready_and_hash_bound(self):
        report = extract_2d_profile_preset(self.context(self.block()))
        self.assertEqual("ready", report["status"], report)
        self.assertTrue(report["preset_available"])
        self.assertEqual(self.preset, report["preset"])
        self.assertEqual(64, len(report["preset_sha256"]))
        self.assertEqual([], list(self.root.iterdir()))

    def test_duplicate_malformed_and_unknown_fields_refuse(self):
        self.assertEqual("error", extract_2d_profile_preset(
            self.context(self.block() + self.block()))["status"])
        self.assertEqual("error", extract_2d_profile_preset(
            self.context("```gameassetai-2d-preset\n{bad}\n```"))["status"])
        changed = {**self.preset, "unknown": True}
        self.assertEqual("error", extract_2d_profile_preset(
            self.context(self.block(changed)))["status"])

    def test_static_style_and_convenience_fields_are_strict(self):
        changed = json.loads(json.dumps(self.preset))
        changed["style"]["resolution"] = [0, 32]
        self.assertEqual("error", extract_2d_profile_preset(
            self.context(self.block(changed)))["status"])
        changed = json.loads(json.dumps(self.preset))
        changed["sequence"]["playback_fps"] = 0
        self.assertEqual("error", extract_2d_profile_preset(
            self.context(self.block(changed)))["status"])
        changed = json.loads(json.dumps(self.preset))
        changed["sprite_sheet"]["order"] = "GUESSED"
        self.assertEqual("error", extract_2d_profile_preset(
            self.context(self.block(changed)))["status"])

    def test_context_provenance_is_required(self):
        context = self.context(self.block())
        context["profile_sha256"] = None
        self.assertEqual("error", extract_2d_profile_preset(context)["status"])
        context = self.context(self.block())
        context["schema"] = "wrong"
        self.assertEqual("error", extract_2d_profile_preset(context)["status"])


if __name__ == "__main__":
    unittest.main()
