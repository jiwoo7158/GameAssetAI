"""Offline tests for exact existing static LOD-chain requests."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_static_lod_chain_request import (  # noqa: E402
    SCHEMA, validate_static_lod_chain_request)


def fixture():
    return {"schema": SCHEMA, "scene_name": "Scene",
            "levels": [{"level_index": 0, "object_name": "Hero_LOD0"},
                       {"level_index": 1, "object_name": "Hero_LOD1"},
                       {"level_index": 2, "object_name": "Hero_LOD2"}],
            "geometry_source": "BASE_MESH", "coordinate_space": "WORLD",
            "policy": {"object_selection": "EXPLICIT_ONLY",
                       "modifier_evaluation": "BASE_MESH_ONLY", "mutation": "READ_ONLY",
                       "transform_alignment": "EXACT_WORLD_MATRIX",
                       "triangle_order": "STRICTLY_DECREASING"}}


class StaticLodChainRequestTests(unittest.TestCase):
    def test_exact_request_is_stable_ordered_and_read_only(self):
        request = fixture(); before = copy.deepcopy(request)
        first = validate_static_lod_chain_request(request)
        second = validate_static_lod_chain_request(request)
        self.assertEqual("ready", first["status"])
        self.assertEqual(first, second); self.assertEqual(before, request)
        self.assertEqual([0, 1, 2], [item["level_index"] for item in first["levels"]])
        self.assertFalse(first["mutation_authorized"])

    def test_counts_indices_names_and_order_are_exact(self):
        invalid = []
        request = fixture(); request["levels"] = request["levels"][:1]; invalid.append(request)
        request = fixture(); request["levels"] *= 3; invalid.append(request)
        request = fixture(); request["levels"][1]["level_index"] = 2; invalid.append(request)
        request = fixture(); request["levels"][1]["level_index"] = True; invalid.append(request)
        request = fixture(); request["levels"][1]["object_name"] = "hero_lod0"; invalid.append(request)
        request = fixture(); request["levels"][0]["object_name"] = " "; invalid.append(request)
        for request in invalid:
            self.assertEqual("error", validate_static_lod_chain_request(request)["status"])

    def test_fixed_scope_and_policies_refuse_inference_or_generation(self):
        for key, value in (("object_selection", "DISCOVER_BY_NAME"),
                           ("modifier_evaluation", "EVALUATED"),
                           ("mutation", "GENERATE"),
                           ("transform_alignment", "APPROXIMATE"),
                           ("triangle_order", "REPORT_ONLY")):
            request = fixture(); request["policy"][key] = value
            self.assertEqual("error", validate_static_lod_chain_request(request)["status"])
        for key, value in (("geometry_source", "EVALUATED"),
                           ("coordinate_space", "LOCAL"), ("schema", "old")):
            request = fixture(); request[key] = value
            self.assertEqual("error", validate_static_lod_chain_request(request)["status"])

    def test_missing_unknown_and_nonobjects_refuse_without_hash(self):
        requests = [None, [], {3: "bad"}]
        request = fixture(); request.pop("levels"); requests.append(request)
        request = fixture(); request["discover"] = True; requests.append(request)
        request = fixture(); request["levels"][0]["ratio"] = 1.0; requests.append(request)
        for request in requests:
            report = validate_static_lod_chain_request(request)
            self.assertEqual("error", report["status"])
            self.assertIsNone(report["request_sha256"])


if __name__ == "__main__":
    unittest.main()
