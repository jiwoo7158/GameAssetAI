"""Offline regression tests for the static 3D-to-2D request contract."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from validate_2d_static_render_request import SCHEMA, validate_2d_static_render_request


class Static2DRenderRequestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-2d-request-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.request = {
            "schema": SCHEMA, "scene_name": "Scene", "object_name": "Cube",
            "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
            "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                     "up": [0, 0, 1], "framing_margin": 0.1},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [64, 64],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "NONE", "palette": [], "max_colors": None,
                      "outline_mode": "NONE", "outline_color": None,
                      "outline_width": 0, "shading_mode": "NONE",
                      "value_steps": None},
            "output": {"target_file": str(self.root / "new.png"), "color_mode": "RGBA",
                       "color_depth": 8, "overwrite": False},
        }

    def refused(self, request):
        report = validate_2d_static_render_request(request)
        self.assertFalse(report["ready_for_blender_inspection"])
        self.assertTrue(report["errors"])
        self.assertIsNone(report["request_sha256"])

    def test_valid_explicit_request_is_stable_and_read_only(self):
        before = repr(self.request)
        first = validate_2d_static_render_request(self.request)
        second = validate_2d_static_render_request(self.request)
        self.assertTrue(first["ready_for_blender_inspection"], first["errors"])
        self.assertEqual(first["request_sha256"], second["request_sha256"])
        self.assertEqual(64, len(first["request_sha256"]))
        self.assertEqual(before, repr(self.request))
        self.assertEqual([], list(self.root.iterdir()))

    def test_profile_provenance_is_all_or_nothing(self):
        profiled = {**self.request, "profile": {"name": "Example", "reference_sha256": "a" * 64,
                                                "profile_sha256": "b" * 64}}
        self.assertTrue(validate_2d_static_render_request(profiled)["ready_for_blender_inspection"])
        for profile in ({"name": "Example", "reference_sha256": None, "profile_sha256": None},
                        {"name": None, "reference_sha256": "a" * 64, "profile_sha256": "b" * 64},
                        {"name": "Example", "reference_sha256": "A" * 64,
                         "profile_sha256": "b" * 64}):
            with self.subTest(profile=profile):
                self.refused({**self.request, "profile": profile})

    def test_view_is_explicit_and_orthonormal(self):
        for view in ({**self.request["view"], "projection": "PERSPECTIVE"},
                     {**self.request["view"], "direction": [0, -2, 0]},
                     {**self.request["view"], "up": [0, -1, 0]},
                     {**self.request["view"], "framing_margin": float("nan")},
                     {**self.request["view"], "framing_margin": 1.1}):
            with self.subTest(view=view):
                self.refused({**self.request, "view": view})

    def test_style_and_palette_policies_are_explicit(self):
        fixed = {**self.request["style"], "palette_mode": "FIXED",
                 "palette": [[0, 0, 0, 1], [1, 1, 1, 1]]}
        auto = {**self.request["style"], "palette_mode": "AUTO", "max_colors": 16}
        self.assertTrue(validate_2d_static_render_request({**self.request, "style": fixed})
                        ["ready_for_blender_inspection"])
        self.assertTrue(validate_2d_static_render_request({**self.request, "style": auto})
                        ["ready_for_blender_inspection"])
        for style in ({**self.request["style"], "mode": "JRPG"},
                      {**self.request["style"], "resolution": [0, 64]},
                      {**self.request["style"], "palette_mode": "FIXED", "palette": []},
                      {**self.request["style"], "palette_mode": "AUTO", "max_colors": 1},
                      {**self.request["style"], "nearest_neighbor": 1}):
            with self.subTest(style=style):
                self.refused({**self.request, "style": style})

    def test_outline_policy_is_explicit_and_v1_remains_readable(self):
        outlined = {**self.request["style"], "outline_mode": "OUTER",
                    "outline_color": [0, 0, 0, 1], "outline_width": 1}
        self.assertTrue(validate_2d_static_render_request(
            {**self.request, "style": outlined})["ready_for_blender_inspection"])
        for style in ({**outlined, "outline_width": 2},
                      {**outlined, "outline_color": [0, 0, 0, 0.5]},
                      {**self.request["style"], "outline_color": [0, 0, 0, 1]}):
            self.refused({**self.request, "style": style})
        v2_style = {key: value for key, value in self.request["style"].items()
                    if key not in {"shading_mode", "value_steps"}}
        v2 = {**self.request, "schema": "gameassetai.2d-static-render-request.v2",
              "style": v2_style}
        self.assertTrue(validate_2d_static_render_request(v2)
                        ["ready_for_blender_inspection"])
        legacy_style = {key: value for key, value in v2_style.items()
                        if not key.startswith("outline_")}
        legacy = {**self.request, "schema": "gameassetai.2d-static-render-request.v1",
                  "style": legacy_style}
        self.assertTrue(validate_2d_static_render_request(legacy)
                        ["ready_for_blender_inspection"])

    def test_value_step_shading_is_explicit_and_legacy_v2_stays_readable(self):
        banded = {**self.request["style"], "shading_mode": "VALUE_STEPS",
                  "value_steps": 4}
        self.assertTrue(validate_2d_static_render_request(
            {**self.request, "style": banded})["ready_for_blender_inspection"])
        for style in ({**banded, "value_steps": 1},
                      {**banded, "value_steps": 33},
                      {**banded, "value_steps": True},
                      {**self.request["style"], "value_steps": 4},
                      {**banded, "shading_mode": "CEL"}):
            self.refused({**self.request, "style": style})

    def test_output_is_absolute_png_and_never_overwrites(self):
        for output in ({**self.request["output"], "target_file": "relative.png"},
                       {**self.request["output"], "target_file": str(self.root / "bad.jpg")},
                       {**self.request["output"], "target_file": str(self.root / "CON.png")},
                       {**self.request["output"], "target_file": str(self.root / "bad?.png")},
                       {**self.request["output"], "overwrite": True},
                       {**self.request["output"], "color_mode": "BW"},
                       {**self.request["output"], "color_depth": 32}):
            with self.subTest(output=output):
                self.refused({**self.request, "output": output})
        (self.root / "new.png").write_bytes(b"sentinel")
        self.refused(self.request)
        self.assertEqual(b"sentinel", (self.root / "new.png").read_bytes())

    def test_nested_missing_and_unknown_fields_refuse(self):
        missing = dict(self.request["view"])
        del missing["up"]
        unknown = {**self.request["lighting"], "game_preset": "dark"}
        self.refused({**self.request, "view": missing})
        self.refused({**self.request, "lighting": unknown})

    def test_non_object_and_nonfinite_values_refuse(self):
        self.refused(None)
        self.refused({**self.request, "style": {**self.request["style"],
                                                "palette": [[float("inf"), 0, 0, 1]],
                                                "palette_mode": "FIXED"}})


if __name__ == "__main__":
    unittest.main()
