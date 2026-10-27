"""Offline tests for explicit existing static-collider candidate requests."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_static_collider_request import (  # noqa: E402
    SCHEMA, validate_static_collider_request)


def fixture():
    return {"schema": SCHEMA, "scene_name": "Scene", "render_object_name": "RenderMesh",
            "colliders": [
                {"id": "body", "object_name": "UCX_Body",
                 "collider_kind": "CONVEX_MESH_CANDIDATE",
                 "convexity_tolerance_ratio": 0.0001},
                {"id": "ground", "object_name": "CollisionGround",
                 "collider_kind": "STATIC_TRIANGLE_MESH",
                 "convexity_tolerance_ratio": None}],
            "geometry_source": "BASE_MESH", "coordinate_space": "WORLD",
            "policy": {"object_selection": "EXPLICIT_ONLY",
                       "modifier_evaluation": "BASE_MESH_ONLY", "mutation": "READ_ONLY"}}


class StaticColliderRequestTests(unittest.TestCase):
    def validate(self, request=None):
        return validate_static_collider_request(request if request is not None else fixture())

    def test_exact_request_is_stable_ordered_and_read_only(self):
        request = fixture(); before = copy.deepcopy(request)
        first, second = self.validate(request), self.validate(request)
        self.assertEqual("ready", first["status"])
        self.assertEqual(first, second)
        self.assertEqual(before, request)
        self.assertEqual(["body", "ground"], [item["id"] for item in first["colliders"]])
        self.assertFalse(first["mutation_authorized"])

    def test_exact_fields_schema_and_fixed_policy_are_required(self):
        for mutate in (
                lambda r: r.pop("coordinate_space"),
                lambda r: r.update(extra=True),
                lambda r: r.update(schema="old"),
                lambda r: r.update(geometry_source="EVALUATED"),
                lambda r: r.update(coordinate_space="LOCAL"),
                lambda r: r["policy"].update(object_selection="DISCOVER"),
                lambda r: r["policy"].update(modifier_evaluation="EVALUATED"),
                lambda r: r["policy"].update(mutation="ALLOW")):
            request = fixture(); mutate(request)
            self.assertEqual("error", self.validate(request)["status"])

    def test_names_ids_counts_and_kinds_are_explicit_unique_and_bounded(self):
        changes = []
        request = fixture(); request["colliders"] = []; changes.append(request)
        request = fixture(); request["colliders"] *= 17; changes.append(request)
        request = fixture(); request["colliders"][1]["id"] = "BODY"; changes.append(request)
        request = fixture(); request["colliders"][1]["object_name"] = "ucx_body"; changes.append(request)
        request = fixture(); request["colliders"][0]["object_name"] = "RenderMesh"; changes.append(request)
        request = fixture(); request["colliders"][0]["id"] = "bad id"; changes.append(request)
        request = fixture(); request["colliders"][0]["collider_kind"] = "BOX"; changes.append(request)
        for request in changes:
            self.assertEqual("error", self.validate(request)["status"])

    def test_convex_tolerance_is_relative_bounded_and_kind_specific(self):
        values = (None, -0.1, 0.02, True, float("nan"), float("inf"), "0.1")
        for value in values:
            request = fixture(); request["colliders"][0]["convexity_tolerance_ratio"] = value
            self.assertEqual("error", self.validate(request)["status"])
        request = fixture(); request["colliders"][1]["convexity_tolerance_ratio"] = 0.0
        self.assertEqual("error", self.validate(request)["status"])
        request = fixture(); request["colliders"][0]["convexity_tolerance_ratio"] = 0.0
        self.assertEqual("ready", self.validate(request)["status"])

    def test_non_objects_and_nested_unknown_fields_refuse_without_hash(self):
        for request in (None, [], {3: "bad"}):
            report = validate_static_collider_request(request)
            self.assertEqual("error", report["status"])
            self.assertIsNone(report["request_sha256"])
        request = fixture(); request["colliders"][0]["guess"] = True
        report = self.validate(request)
        self.assertEqual("error", report["status"])
        self.assertIsNone(report["request_sha256"])


if __name__ == "__main__":
    unittest.main()
