"""Build a read-only, explicit plan for copying one stored Blender Action."""
from __future__ import annotations

import hashlib
import json


SCHEMA = "gameassetai.action-copy-request.v1"
_EXPECTED_KEYS = {"schema", "scene_name", "source_action", "target_action", "preserve_source",
                  "bind_copy", "set_fake_user"}


def _digest(value):
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def plan_action_copy(inventory, request):
    """Validate one non-destructive copy request against an animation inventory."""
    report = {"schema": "gameassetai.action-copy-plan.v1", "status": "error",
              "errors": [], "reviews": [], "authorization": False}
    if not isinstance(inventory, dict) or inventory.get("schema") != "gameassetai.animation-inventory.v1":
        report["errors"].append("A supported animation inventory is required")
        return report
    if inventory.get("status") != "ok":
        report["errors"].append("Animation inventory did not complete successfully")
        return report
    if not isinstance(request, dict):
        report["errors"].append("Request must be an object")
        return report
    unknown = sorted(set(request) - _EXPECTED_KEYS)
    missing = sorted(_EXPECTED_KEYS - set(request))
    if unknown or missing:
        if unknown:
            report["errors"].append("Unknown request fields: " + ", ".join(unknown))
        if missing:
            report["errors"].append("Missing request fields: " + ", ".join(missing))
        return report
    if request["schema"] != SCHEMA:
        report["errors"].append("Unsupported request schema")
        return report
    scene_name = request["scene_name"]
    source, target = request["source_action"], request["target_action"]
    if not isinstance(scene_name, str) or not scene_name or scene_name != scene_name.strip():
        report["errors"].append("scene_name must be an exact nonempty name without outer whitespace")
    elif inventory.get("scene") != scene_name:
        report["errors"].append("Request Scene does not match the inventory")
    if not isinstance(source, str) or not source or source != source.strip():
        report["errors"].append("source_action must be an exact nonempty name without outer whitespace")
    if not isinstance(target, str) or not target or target != target.strip():
        report["errors"].append("target_action must be an exact nonempty name without outer whitespace")
    elif len(target.encode("utf-8")) > 255:
        report["errors"].append("target_action exceeds Blender's observed 255-byte UTF-8 ID-name limit")
    if source == target:
        report["errors"].append("Source and target Action names must differ")
    for key in ("preserve_source", "bind_copy", "set_fake_user"):
        if type(request[key]) is not bool:
            report["errors"].append(f"{key} must be boolean")
    if request["preserve_source"] is not True:
        report["errors"].append("This workflow requires preserve_source=true")
    if request["bind_copy"] is not False:
        report["errors"].append("This bounded workflow requires bind_copy=false")
    if request["set_fake_user"] is not True:
        report["errors"].append("An unbound copy requires set_fake_user=true for persistence")
    if report["errors"]:
        return report

    actions = inventory.get("actions")
    bindings = inventory.get("bindings")
    if not isinstance(actions, list) or not isinstance(bindings, list):
        report["errors"].append("Inventory Actions/bindings are missing")
        return report
    matches = [item for item in actions if isinstance(item, dict) and item.get("name") == source]
    if len(matches) != 1:
        report["errors"].append("Source Action must resolve exactly once in the inventory")
        return report
    if any(isinstance(item, dict) and item.get("name") == target for item in actions):
        report["errors"].append("Target Action name already exists")
        return report

    current_refs = []
    nla_refs = []
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        if binding.get("action") == source:
            current_refs.append({"owner": binding.get("owner"),
                                 "owner_type": binding.get("owner_type")})
        for track in binding.get("nla_tracks", []):
            for strip in track.get("strips", []):
                if strip.get("action") == source:
                    nla_refs.append({"owner": binding.get("owner"),
                                     "track": track.get("name"),
                                     "strip": strip.get("name")})
    action = matches[0]
    candidate = {"operation": "copy_action_unbound", "scene_name": scene_name,
                 "source_action": source,
                 "target_action": target, "preserve_source": True,
                 "bind_copy": False, "set_fake_user": True,
                 "source_inventory_sha256": _digest(action),
                 "current_action_references": current_refs,
                 "nla_references": nla_refs}
    candidate["request_sha256"] = _digest(request)
    report.update({"status": "candidate_for_review", "request": dict(request),
                   "candidate": candidate})
    report["reviews"].append(
        "The plan creates one unbound persistent copy; all existing Action and NLA references remain unchanged")
    report["reviews"].append(
        "This inventory-bound plan is not authorization and is not a complete content fingerprint for apply")
    return report
