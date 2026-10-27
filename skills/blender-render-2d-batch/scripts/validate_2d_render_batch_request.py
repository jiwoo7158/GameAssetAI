"""Validate an explicit mixed static/Action 2D render batch without writing files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

from validate_2d_action_sequence_request import (
    SCHEMA as ACTION_SCHEMA,
    validate_2d_action_sequence_request,
)
from validate_2d_static_render_request import (
    SCHEMA as STATIC_SCHEMA,
    validate_2d_static_render_request,
)


SCHEMA = "gameassetai.2d-render-batch-request.v1"
MAX_BATCH_ITEMS = 64
MAX_BATCH_OUTPUTS = 2048
_TOP_FIELDS = {"schema", "items", "policy"}
_ITEM_FIELDS = {"id", "kind", "settings_source", "profile_binding", "request"}
_POLICY_FIELDS = {"execution_order", "publication", "on_failure"}
_PROFILE_FIELDS = {"name", "reference_sha256", "profile_sha256", "preset_sha256"}
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _exact(value, fields, label, errors):
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        errors.append(f"{label} must be an object with string keys")
        return False
    missing, unknown = sorted(fields - value.keys()), sorted(value.keys() - fields)
    if missing:
        errors.append(f"{label} missing fields: " + ", ".join(missing))
    if unknown:
        errors.append(f"{label} unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _path_key(value):
    return str(Path(value).resolve(strict=False)).casefold()


def validate_2d_render_batch_request(request):
    """Return an ordered, collision-checked child plan; never create or modify a file."""
    report = {"schema": SCHEMA, "status": "error", "errors": [],
              "ready_for_execution_planning": False, "batch_sha256": None,
              "item_count": 0, "output_count": 0, "items": [], "outputs": []}
    errors = report["errors"]
    try:
        if not _exact(request, _TOP_FIELDS, "request", errors):
            return report
        if request.get("schema") != SCHEMA:
            errors.append("schema mismatch")
        policy = request.get("policy")
        if _exact(policy, _POLICY_FIELDS, "policy", errors):
            if policy.get("execution_order") != "LIST_ORDER":
                errors.append("policy.execution_order must be LIST_ORDER")
            if policy.get("publication") != "ALL_OR_NOTHING":
                errors.append("policy.publication must be ALL_OR_NOTHING")
            if policy.get("on_failure") != "ROLL_BACK_BATCH_OUTPUTS":
                errors.append("policy.on_failure must be ROLL_BACK_BATCH_OUTPUTS")

        items = request.get("items")
        if not isinstance(items, list) or not 1 <= len(items) <= MAX_BATCH_ITEMS:
            errors.append(f"items must contain 1 through {MAX_BATCH_ITEMS} entries")
            items = []
        ids, output_keys, output_parents, planned_items, outputs = set(), set(), set(), [], []
        for index, item in enumerate(items):
            label = f"items[{index}]"
            if not _exact(item, _ITEM_FIELDS, label, errors):
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not _ID.fullmatch(item_id):
                errors.append(f"{label}.id must be a safe 1-64 character identifier")
            elif item_id.casefold() in ids:
                errors.append("item ids must be case-insensitively unique")
            else:
                ids.add(item_id.casefold())
            kind, child = item.get("kind"), item.get("request")
            if kind == "STATIC":
                validation = validate_2d_static_render_request(child)
                valid = validation.get("ready_for_blender_inspection") is True
                child_outputs = ([child["output"]["target_file"]] if valid else [])
                request_sha = validation.get("request_sha256")
                view = child.get("view") if isinstance(child, dict) else None
                action_name = None
            elif kind == "ACTION_SEQUENCE":
                validation = validate_2d_action_sequence_request(child)
                valid = validation.get("ready_for_blender_inspection") is True
                child_outputs = ([frame["target_file"] for frame in validation.get("frames", [])]
                                 if valid else [])
                request_sha = validation.get("request_sha256")
                template = child.get("static_template") if isinstance(child, dict) else None
                view = template.get("view") if isinstance(template, dict) else None
                animation = child.get("animation") if isinstance(child, dict) else None
                action_name = (animation.get("action_name")
                               if isinstance(animation, dict) else None)
            else:
                errors.append(f"{label}.kind must be STATIC or ACTION_SEQUENCE")
                continue
            binding = item.get("profile_binding")
            if _exact(binding, _PROFILE_FIELDS, f"{label}.profile_binding", errors):
                binding_values = [binding[key] for key in
                                  ("name", "reference_sha256", "profile_sha256",
                                   "preset_sha256")]
                child_profile = (child.get("profile") if kind == "STATIC"
                                 else child.get("static_template", {}).get("profile"))
                if item.get("settings_source") == "EXPLICIT":
                    if any(value is not None for value in binding_values):
                        errors.append(f"{label} explicit settings require a null binding")
                    if isinstance(child_profile, dict) and any(
                            value is not None for value in child_profile.values()):
                        errors.append(f"{label} explicit child Profile fields must be null")
                elif item.get("settings_source") == "ACTIVE_PROFILE_PRESET":
                    if (not isinstance(binding_values[0], str)
                            or not binding_values[0].strip()
                            or any(not isinstance(value, str) or not re.fullmatch(
                                r"[0-9a-f]{64}", value) for value in binding_values[1:])):
                        errors.append(f"{label} active Profile binding is incomplete")
                    expected_profile = {key: binding[key] for key in
                                        ("name", "reference_sha256", "profile_sha256")}
                    if child_profile != expected_profile:
                        errors.append(f"{label} child Profile provenance does not match binding")
                else:
                    errors.append(f"{label}.settings_source must be EXPLICIT or ACTIVE_PROFILE_PRESET")
            if not valid:
                child_errors = validation.get("errors", [])
                errors.append(f"{label}.request is invalid: " + "; ".join(child_errors))
                continue
            for output in child_outputs:
                key = _path_key(output)
                if key in output_keys:
                    errors.append("child output paths must be case-insensitively unique")
                else:
                    output_keys.add(key)
                    outputs.append(output)
                    output_parents.add(str(Path(output).parent.resolve(strict=False)).casefold())
            planned_items.append({"position": index, "id": item_id, "kind": kind,
                                  "request_schema": child.get("schema"),
                                  "request_sha256": request_sha,
                                  "settings_source": item.get("settings_source"),
                                  "profile_binding": binding,
                                  "output_count": len(child_outputs), "outputs": child_outputs,
                                  "view": view, "action_name": action_name})

        if len(outputs) > MAX_BATCH_OUTPUTS:
            errors.append(f"batch expands beyond {MAX_BATCH_OUTPUTS} outputs")
        if len(output_parents) > 1:
            errors.append("every batch output must share one directory")
        if errors:
            return report
        report.update(status="ready", ready_for_execution_planning=True,
                      batch_sha256=_hash(request), item_count=len(planned_items),
                      output_count=len(outputs), items=planned_items, outputs=outputs,
                      output_directory=str(Path(outputs[0]).parent),
                      child_schemas={"STATIC": STATIC_SCHEMA,
                                     "ACTION_SEQUENCE": ACTION_SCHEMA},
                      limitations=["Validation does not stage, render, publish or roll back files",
                                   "Every direction and Action remains an explicit child request"])
    except (TypeError, KeyError, OSError, OverflowError, ValueError) as exc:
        errors.append(str(exc))
    return report

