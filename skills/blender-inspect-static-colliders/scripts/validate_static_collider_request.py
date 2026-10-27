"""Pure validation for an explicit existing static-collider candidate request."""
from __future__ import annotations

import hashlib
import json
import math
import re


SCHEMA = "gameassetai.static-collider-candidate-request.v1"
FIELDS = frozenset(("schema", "scene_name", "render_object_name", "colliders",
                    "geometry_source", "coordinate_space", "policy"))
COLLIDER_FIELDS = frozenset(("id", "object_name", "collider_kind",
                             "convexity_tolerance_ratio"))
POLICY_FIELDS = frozenset(("object_selection", "modifier_evaluation", "mutation"))
KINDS = frozenset(("STATIC_TRIANGLE_MESH", "CONVEX_MESH_CANDIDATE"))
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _exact(value, fields, label, errors):
    if not isinstance(value, dict):
        errors.append(label + " must be an object")
        return False
    if any(not isinstance(key, str) for key in value):
        errors.append(label + " keys must be strings")
        return False
    missing = sorted(fields - value.keys())
    unknown = sorted(value.keys() - fields)
    if missing:
        errors.append(label + " missing fields: " + ", ".join(missing))
    if unknown:
        errors.append(label + " unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _name(value, label, errors):
    if not isinstance(value, str) or not value or value != value.strip():
        errors.append(label + " must be a nonempty exact name")
        return None
    return value


def _ratio(value, label, errors):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(label + " must be a finite number from 0 through 0.01")
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        number = math.nan
    if not math.isfinite(number) or not 0.0 <= number <= 0.01:
        errors.append(label + " must be a finite number from 0 through 0.01")
        return None
    return number


def validate_static_collider_request(request: object) -> dict:
    """Return a deterministic read-only preflight report."""
    errors = []
    if not _exact(request, FIELDS, "request", errors):
        return {"schema": SCHEMA, "status": "error", "request_sha256": None,
                "collider_count": None, "errors": errors, "mutation_authorized": False}
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    scene_name = _name(request.get("scene_name"), "scene_name", errors)
    render_name = _name(request.get("render_object_name"), "render_object_name", errors)
    if request.get("geometry_source") != "BASE_MESH":
        errors.append("geometry_source must be BASE_MESH")
    if request.get("coordinate_space") != "WORLD":
        errors.append("coordinate_space must be WORLD")
    policy = request.get("policy")
    if _exact(policy, POLICY_FIELDS, "policy", errors):
        if policy["object_selection"] != "EXPLICIT_ONLY":
            errors.append("policy.object_selection must be EXPLICIT_ONLY")
        if policy["modifier_evaluation"] != "BASE_MESH_ONLY":
            errors.append("policy.modifier_evaluation must be BASE_MESH_ONLY")
        if policy["mutation"] != "READ_ONLY":
            errors.append("policy.mutation must be READ_ONLY")

    items = request.get("colliders")
    if not isinstance(items, list) or isinstance(items, (str, bytes)):
        errors.append("colliders must be an array")
        items = []
    elif not 1 <= len(items) <= 32:
        errors.append("colliders must contain 1 through 32 items")
    ids, names = set(), set()
    normalized = []
    for index, item in enumerate(items):
        label = f"colliders[{index}]"
        if not _exact(item, COLLIDER_FIELDS, label, errors):
            continue
        identifier = item["id"]
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(label + ".id must be a safe 1-64 character identifier")
        elif identifier.casefold() in ids:
            errors.append(label + ".id must be case-insensitively unique")
        else:
            ids.add(identifier.casefold())
        object_name = _name(item["object_name"], label + ".object_name", errors)
        if object_name is not None:
            if object_name == render_name:
                errors.append(label + ".object_name must differ from render_object_name")
            if object_name.casefold() in names:
                errors.append(label + ".object_name must be case-insensitively unique")
            names.add(object_name.casefold())
        kind = item["collider_kind"]
        if kind not in KINDS:
            errors.append(label + ".collider_kind is unsupported")
        tolerance = item["convexity_tolerance_ratio"]
        if kind == "CONVEX_MESH_CANDIDATE":
            tolerance = _ratio(tolerance, label + ".convexity_tolerance_ratio", errors)
        elif tolerance is not None:
            errors.append(label + ".convexity_tolerance_ratio must be null for STATIC_TRIANGLE_MESH")
        normalized.append({"position": index, "id": identifier,
                           "object_name": object_name, "collider_kind": kind,
                           "convexity_tolerance_ratio": tolerance})

    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, "status": "ready" if not errors else "error",
            "request_sha256": digest, "scene_name": scene_name,
            "render_object_name": render_name, "collider_count": len(items),
            "colliders": normalized if not errors else None,
            "errors": errors, "mutation_authorized": False}
