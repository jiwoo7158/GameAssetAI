"""Offline tests for the explicit read-only Action copy plan."""
from pathlib import Path
import sys
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from plan_action_copy import plan_action_copy


def inventory():
    return {"schema": "gameassetai.animation-inventory.v1", "status": "ok", "scene": "Scene",
            "actions": [{"name": "Walk", "users": 2, "curve_count": 3}],
            "bindings": [{"owner": "Rig", "owner_type": "Object", "action": "Walk",
                          "nla_tracks": [{"name": "Base", "strips": [
                              {"name": "WalkStrip", "action": "Walk"}]}]}]}


def request():
    return {"schema": "gameassetai.action-copy-request.v1", "scene_name": "Scene",
            "source_action": "Walk", "target_action": "Walk_Copy",
            "preserve_source": True, "bind_copy": False, "set_fake_user": True}


class ActionCopyPlanTests(unittest.TestCase):
    def test_candidate_is_hash_bound_and_not_authorized(self):
        result = plan_action_copy(inventory(), request())
        self.assertEqual("candidate_for_review", result["status"])
        self.assertFalse(result["authorization"])
        self.assertEqual(64, len(result["candidate"]["request_sha256"]))
        self.assertEqual([{"owner": "Rig", "owner_type": "Object"}],
                         result["candidate"]["current_action_references"])
        self.assertEqual([{"owner": "Rig", "track": "Base", "strip": "WalkStrip"}],
                         result["candidate"]["nla_references"])

    def test_name_and_collision_fail_closed(self):
        for value in ("", " Walk", "Walk ", "가" * 86, "Walk"):
            value_request = request(); value_request["target_action"] = value
            self.assertEqual("error", plan_action_copy(inventory(), value_request)["status"])

    def test_missing_source_and_bad_inventory_fail_closed(self):
        missing = request(); missing["source_action"] = "Run"
        self.assertEqual("error", plan_action_copy(inventory(), missing)["status"])
        self.assertEqual("error", plan_action_copy({}, request())["status"])

    def test_policy_and_schema_are_explicit(self):
        for key, value in (("preserve_source", False), ("bind_copy", True),
                           ("set_fake_user", False)):
            unsafe = request(); unsafe[key] = value
            self.assertEqual("error", plan_action_copy(inventory(), unsafe)["status"])
        extra = request(); extra["rename_source"] = True
        self.assertEqual("error", plan_action_copy(inventory(), extra)["status"])
        wrong = request(); wrong["schema"] = "unknown"
        self.assertEqual("error", plan_action_copy(inventory(), wrong)["status"])


if __name__ == "__main__":
    unittest.main()
