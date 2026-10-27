"""Pure validation for an explicit existing static LOD-chain inspection request."""
from __future__ import annotations

import hashlib
import json


SCHEMA = "gameassetai.static-lod-chain-request.v1"
FIELDS = frozenset(("schema", "scene_name", "levels", "geometry_source",
                    "coordinate_space", "policy"))
LEVEL_FIELDS = frozenset(("level_index", "object_name"))
POLICY_FIELDS = frozenset(("object_selection", "modifier_evaluation", "mutation",
                           "transform_alignment", "triangle_order"))


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


def validate_static_lod_chain_request(request: object) -> dict:
    """Return a stable no-write preflight report."""
    errors = []
    if not _exact(request, FIELDS, "request", errors):
        return {"schema": SCHEMA, "status": "error", "request_sha256": None,
                "level_count": None, "levels": None, "errors": errors,
                "mutation_authorized": False}
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    scene_name = _name(request.get("scene_name"), "scene_name", errors)
    if request.get("geometry_source") != "BASE_MESH":
        errors.append("geometry_source must be BASE_MESH")
    if request.get("coordinate_space") != "WORLD":
        errors.append("coordinate_space must be WORLD")
    policy = request.get("policy")
    if _exact(policy, POLICY_FIELDS, "policy", errors):
        expected = {"object_selection": "EXPLICIT_ONLY",
                    "modifier_evaluation": "BASE_MESH_ONLY", "mutation": "READ_ONLY",
                    "transform_alignment": "EXACT_WORLD_MATRIX",
                    "triangle_order": "STRICTLY_DECREASING"}
        for key, value in expected.items():
            if policy[key] != value:
                errors.append("policy." + key + " must be " + value)

    levels = request.get("levels")
    if not isinstance(levels, list) or isinstance(levels, (str, bytes)):
        errors.append("levels must be an array")
        levels = []
    elif not 2 <= len(levels) <= 8:
        errors.append("levels must contain 2 through 8 items")
    names, normalized, indices = set(), [], []
    for position, level in enumerate(levels):
        label = f"levels[{position}]"
        if not _exact(level, LEVEL_FIELDS, label, errors):
            continue
        index = level["level_index"]
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index <= 7:
            errors.append(label + ".level_index must be an integer from 0 through 7")
        else:
            indices.append(index)
            if index != position:
                errors.append(label + ".level_index must equal its contiguous list position")
        name = _name(level["object_name"], label + ".object_name", errors)
        if name is not None:
            folded = name.casefold()
            if folded in names:
                errors.append(label + ".object_name must be case-insensitively unique")
            names.add(folded)
        normalized.append({"position": position, "level_index": index, "object_name": name})
    if len(indices) != len(set(indices)):
        errors.append("level_index values must be unique")

    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, "status": "ready" if not errors else "error",
            "request_sha256": digest, "scene_name": scene_name,
            "level_count": len(levels), "levels": normalized if not errors else None,
            "errors": errors, "mutation_authorized": False}
