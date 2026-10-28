from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_unity_lodgroup_request import SCHEMA, validate_unity_lodgroup_request


def valid_request():
    return {"schema": SCHEMA,
            "project_path": r"C:\GameAssetAIFixture\UnityProject",
            "prefab_asset_path": "Assets/Blender/Tree.prefab",
            "levels": [
                {"level_index": 0, "renderer_paths": ["LOD0"],
                 "screen_relative_transition_height": 0.6},
                {"level_index": 1, "renderer_paths": ["LOD1"],
                 "screen_relative_transition_height": 0.3},
                {"level_index": 2, "renderer_paths": ["LOD2"],
                 "screen_relative_transition_height": 0.1}],
            "fade": {"fade_mode": "NONE", "animate_cross_fading": False},
            "policy": {"target_selection": "EXPLICIT_ONLY",
                       "mutation": "PREVIEW_THEN_EXPLICIT_APPLY",
                       "existing_lod_group": "REFUSE"}}


class UnityLodGroupRequestTests(unittest.TestCase):
    def test_valid_request_is_stable_and_read_only(self):
        request = valid_request(); before = copy.deepcopy(request)
        one = validate_unity_lodgroup_request(request); two = validate_unity_lodgroup_request(request)
        self.assertEqual("ready", one["status"]); self.assertEqual(one, two)
        self.assertEqual(before, request); self.assertFalse(one["mutation_authorized"])

    def test_levels_indices_paths_and_heights_are_explicit(self):
        for change in (lambda r: r["levels"].__setitem__(1, dict(r["levels"][1], level_index=3)),
                       lambda r: r["levels"][1].__setitem__("renderer_paths", ["LOD0"]),
                       lambda r: r["levels"][1].__setitem__("renderer_paths", ["/LOD1"]),
                       lambda r: r["levels"][1].__setitem__("screen_relative_transition_height", .7)):
            request = valid_request(); change(request)
            self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])

    def test_paths_must_be_absolute_project_and_normalized_prefab(self):
        for key, value in (("project_path", "relative/project"),
                           ("prefab_asset_path", r"Assets\Blender\Tree.prefab"),
                           ("prefab_asset_path", "Packages/Tree.prefab")):
            request = valid_request(); request[key] = value
            self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])

    def test_fade_and_policy_are_fixed(self):
        request = valid_request(); request["fade"]["fade_mode"] = "CROSS_FADE"
        self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])
        request = valid_request(); request["policy"]["existing_lod_group"] = "REPLACE"
        self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])

    def test_missing_unknown_and_nonfinite_values_refuse(self):
        request = valid_request(); del request["levels"]
        self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])
        request = valid_request(); request["extra"] = True
        self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])
        request = valid_request(); request["levels"][0]["screen_relative_transition_height"] = float("nan")
        self.assertEqual("error", validate_unity_lodgroup_request(request)["status"])


if __name__ == "__main__": unittest.main()
