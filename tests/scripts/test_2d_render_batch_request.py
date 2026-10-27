"""Offline tests for explicit multi-direction and multi-Action batch planning."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from validate_2d_action_sequence_request import SCHEMA as ACTION_SCHEMA  # noqa: E402
from validate_2d_render_batch_request import (  # noqa: E402
    SCHEMA, validate_2d_render_batch_request)
from validate_2d_static_render_request import SCHEMA as STATIC_SCHEMA  # noqa: E402


def make_batch_fixture(root):
    profile = {"name": None, "reference_sha256": None, "profile_sha256": None}
    style = {"mode": "PIXEL", "resolution": [32, 32],
             "anti_aliasing": "DISABLED", "nearest_neighbor": True,
             "palette_mode": "NONE", "palette": [], "max_colors": None,
             "outline_mode": "NONE", "outline_color": None, "outline_width": 0,
             "shading_mode": "NONE", "value_steps": None}
    lighting = {"mode": "OWNED_NEUTRAL", "transparent_background": True}
    static = {"schema": STATIC_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
              "profile": profile,
              "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                       "up": [0, 0, 1], "framing_margin": 0.1},
              "lighting": lighting, "style": style,
              "output": {"target_file": str(root / "front.png"), "color_mode": "RGBA",
                         "color_depth": 8, "overwrite": False}}
    action = {
        "schema": ACTION_SCHEMA,
        "static_template": {"schema": STATIC_SCHEMA, "scene_name": "Scene",
                            "object_name": "Hero", "profile": profile,
                            "view": {"projection": "ORTHOGRAPHIC", "direction": [1, 0, 0],
                                     "up": [0, 0, 1], "framing_margin": 0.1},
                            "lighting": lighting, "style": style},
        "animation": {"armature_name": "Rig", "action_name": "Walk",
                      "slot_identifier": None, "frame_start": 1, "frame_end": 3,
                      "frame_step": 1, "playback_fps": 12},
        "framing": {"bounds_policy": "ACTION_RANGE", "anchor_policy": "OBJECT_ORIGIN"},
        "output": {"target_directory": str(root), "filename_prefix": "side-walk-",
                   "index_start": 0, "index_padding": 4, "overwrite": False},
    }
    request = {"schema": SCHEMA,
               "items": [{"id": "front-idle", "kind": "STATIC",
                          "settings_source": "EXPLICIT",
                          "profile_binding": {"name": None, "reference_sha256": None,
                                              "profile_sha256": None, "preset_sha256": None},
                          "request": static},
                         {"id": "side-walk", "kind": "ACTION_SEQUENCE",
                          "settings_source": "EXPLICIT",
                          "profile_binding": {"name": None, "reference_sha256": None,
                                              "profile_sha256": None, "preset_sha256": None},
                          "request": action}],
               "policy": {"execution_order": "LIST_ORDER",
                          "publication": "ALL_OR_NOTHING",
                          "on_failure": "ROLL_BACK_BATCH_OUTPUTS"}}
    return request, static, action


class Render2DBatchRequestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-2d-batch-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request, self.static, self.action = make_batch_fixture(self.root)

    def validate(self, request=None):
        return validate_2d_render_batch_request(request or self.request)

    def test_valid_mixed_batch_is_stable_ordered_and_read_only(self):
        before = list(self.root.iterdir())
        first, second = self.validate(), self.validate()
        self.assertEqual("ready", first["status"])
        self.assertEqual(first, second)
        self.assertEqual(2, first["item_count"])
        self.assertEqual(4, first["output_count"])
        self.assertEqual(["front-idle", "side-walk"],
                         [item["id"] for item in first["items"]])
        self.assertEqual(before, list(self.root.iterdir()))

    def test_each_direction_and_action_remains_explicit(self):
        report = self.validate()
        self.assertEqual([0, -1, 0], report["items"][0]["view"]["direction"])
        self.assertEqual([1, 0, 0], report["items"][1]["view"]["direction"])
        self.assertEqual("Walk", report["items"][1]["action_name"])

    def test_exact_fields_and_fixed_policy_are_required(self):
        for key, value in (("execution_order", "PARALLEL"),
                           ("publication", "PARTIAL_OK"),
                           ("on_failure", "KEEP_COMPLETED")):
            changed = copy.deepcopy(self.request); changed["policy"][key] = value
            self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["extra"] = True
        self.assertEqual("error", self.validate(changed)["status"])

    def test_ids_are_safe_and_case_insensitively_unique(self):
        changed = copy.deepcopy(self.request); changed["items"][1]["id"] = "FRONT-IDLE"
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][0]["id"] = "bad/id"
        self.assertEqual("error", self.validate(changed)["status"])

    def test_child_validation_and_kind_fail_closed(self):
        changed = copy.deepcopy(self.request); changed["items"][0]["request"]["view"][
            "direction"] = [0, 0, 0]
        self.assertEqual("error", self.validate(changed)["status"])

    def test_profile_binding_matches_the_selected_settings_source(self):
        changed = copy.deepcopy(self.request)
        binding = {"name": "PixelGame", "reference_sha256": "1" * 64,
                   "profile_sha256": "2" * 64, "preset_sha256": "3" * 64}
        changed["items"][0]["settings_source"] = "ACTIVE_PROFILE_PRESET"
        changed["items"][0]["profile_binding"] = binding
        changed["items"][0]["request"]["profile"] = {
            key: binding[key] for key in ("name", "reference_sha256", "profile_sha256")}
        self.assertEqual("ready", self.validate(changed)["status"])
        changed["items"][0]["profile_binding"]["preset_sha256"] = None
        self.assertEqual("error", self.validate(changed)["status"])
        changed = copy.deepcopy(self.request); changed["items"][0]["kind"] = "GUESSED"
        self.assertEqual("error", self.validate(changed)["status"])

    def test_cross_child_output_collision_is_refused(self):
        changed = copy.deepcopy(self.request)
        changed["items"][0]["request"]["output"]["target_file"] = str(
            self.root / "SIDE-WALK-0000.PNG")
        self.assertEqual("error", self.validate(changed)["status"])

    def test_outputs_must_share_one_directory(self):
        child = self.root / "child"; child.mkdir()
        changed = copy.deepcopy(self.request)
        changed["items"][0]["request"]["output"]["target_file"] = str(child / "front.png")
        self.assertEqual("error", self.validate(changed)["status"])

    def test_existing_output_and_total_output_budget_are_refused(self):
        (self.root / "front.png.meta").write_text("sentinel", encoding="utf-8")
        self.assertEqual("error", self.validate()["status"])
        (self.root / "front.png.meta").unlink()
        changed = copy.deepcopy(self.request)
        changed["items"][1]["request"]["animation"].update(
            frame_start=1, frame_end=2048, frame_step=1)
        self.assertEqual("error", self.validate(changed)["status"])


if __name__ == "__main__":
    unittest.main()
