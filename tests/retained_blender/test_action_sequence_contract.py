"""Offline regressions for the Action PNG-sequence request contract."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "gameassetai" / "blender"))
from validate_2d_action_sequence_request import (
    SCHEMA, validate_2d_action_sequence_request,
)
from validate_2d_static_render_request import SCHEMA as STATIC_SCHEMA


class Action2DSequenceRequestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-2d-sequence-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.request = {
            "schema": SCHEMA,
            "static_template": {
                "schema": STATIC_SCHEMA, "scene_name": "Scene", "object_name": "Hero",
                "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
                "style": {"mode": "PIXEL", "resolution": [32, 32],
                          "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                          "palette_mode": "AUTO", "palette": [], "max_colors": 4,
                          "outline_mode": "OUTER", "outline_color": [0, 0, 0, 1],
                          "outline_width": 1, "shading_mode": "VALUE_STEPS",
                          "value_steps": 4}},
            "animation": {"armature_name": "Rig", "action_name": "Walk",
                          "slot_identifier": None, "frame_start": 1, "frame_end": 5,
                          "frame_step": 2, "playback_fps": 12},
            "framing": {"bounds_policy": "ACTION_RANGE", "anchor_policy": "OBJECT_ORIGIN"},
            "output": {"target_directory": str(self.root), "filename_prefix": "walk_",
                       "index_start": 0, "index_padding": 4, "overwrite": False},
        }

    def refused(self, request):
        result = validate_2d_action_sequence_request(request)
        self.assertFalse(result["ready_for_blender_inspection"])
        self.assertTrue(result["errors"])
        self.assertIsNone(result["request_sha256"])
        self.assertEqual([], result["frames"])

    def test_valid_request_is_stable_read_only_and_maps_frames(self):
        first = validate_2d_action_sequence_request(self.request)
        second = validate_2d_action_sequence_request(self.request)
        self.assertTrue(first["ready_for_blender_inspection"], first["errors"])
        self.assertEqual(first, second)
        self.assertEqual([1, 3, 5], [frame["source_frame"] for frame in first["frames"]])
        self.assertEqual(["walk_0000.png", "walk_0001.png", "walk_0002.png"],
                         [Path(frame["target_file"]).name for frame in first["frames"]])
        self.assertEqual([], list(self.root.iterdir()))

    def test_frame_range_is_exact_bounded_and_integer(self):
        for animation in ({**self.request["animation"], "frame_end": 4},
                          {**self.request["animation"], "frame_step": 0},
                          {**self.request["animation"], "frame_start": 6},
                          {**self.request["animation"], "frame_start": 1.5},
                          {**self.request["animation"], "frame_end": 4097,
                           "frame_step": 2}):
            with self.subTest(animation=animation):
                self.refused({**self.request, "animation": animation})

    def test_names_slot_and_fps_are_explicit(self):
        for animation in ({**self.request["animation"], "armature_name": ""},
                          {**self.request["animation"], "slot_identifier": " slot"},
                          {**self.request["animation"], "playback_fps": 0},
                          {**self.request["animation"], "playback_fps": float("nan")}):
            with self.subTest(animation=animation):
                self.refused({**self.request, "animation": animation})

    def test_framing_policy_is_narrow_and_explicit(self):
        for framing in ({**self.request["framing"], "bounds_policy": "PER_FRAME"},
                        {**self.request["framing"], "anchor_policy": "GUESSED_ROOT"}):
            self.refused({**self.request, "framing": framing})

    def test_output_policy_and_collisions_refuse(self):
        for output in ({**self.request["output"], "target_directory": "relative"},
                       {**self.request["output"], "filename_prefix": "bad?"},
                       {**self.request["output"], "index_start": -1},
                       {**self.request["output"], "index_padding": 0},
                       {**self.request["output"], "overwrite": True}):
            with self.subTest(output=output):
                self.refused({**self.request, "output": output})
        (self.root / "walk_0001.png.meta").write_text("sentinel", encoding="utf-8")
        self.refused(self.request)

    def test_static_template_uses_current_static_contract(self):
        bad_style = {**self.request["static_template"]["style"], "value_steps": 1}
        bad_template = {**self.request["static_template"], "style": bad_style}
        self.refused({**self.request, "static_template": bad_template})
        legacy = {**self.request["static_template"],
                  "schema": "gameassetai.2d-static-render-request.v2"}
        self.refused({**self.request, "static_template": legacy})

    def test_missing_and_unknown_fields_refuse(self):
        missing = dict(self.request["animation"])
        del missing["action_name"]
        self.refused({**self.request, "animation": missing})
        self.refused({**self.request, "output": {**self.request["output"],
                                                  "game_preset": "dark"}})


if __name__ == "__main__":
    unittest.main()
# Retained focused contract regression after the product restructure.
