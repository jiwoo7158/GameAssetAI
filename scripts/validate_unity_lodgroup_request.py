"""Pure validation for an explicit prefab LODGroup configuration request."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import PurePosixPath, PureWindowsPath


SCHEMA = "gameassetai.unity-lodgroup-request.v1"
FIELDS = frozenset(("schema", "project_path", "prefab_asset_path", "levels", "fade", "policy"))
LEVEL_FIELDS = frozenset(("level_index", "renderer_paths", "screen_relative_transition_height"))
FADE_FIELDS = frozenset(("fade_mode", "animate_cross_fading"))
POLICY_FIELDS = frozenset(("target_selection", "mutation", "existing_lod_group"))


def _exact(value, fields, label, errors):
    if not isinstance(value, dict):
        errors.append(label + " must be an object"); return False
    missing = sorted(fields - value.keys()); unknown = sorted(value.keys() - fields)
    if missing: errors.append(label + " missing fields: " + ", ".join(missing))
    if unknown: errors.append(label + " unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _exact_text(value, label, errors):
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        errors.append(label + " must be a nonempty exact string"); return None
    return value


def validate_unity_lodgroup_request(request: object) -> dict:
    errors = []
    if not _exact(request, FIELDS, "request", errors):
        return {"schema": SCHEMA, "status": "error", "request_sha256": None,
                "errors": errors, "mutation_authorized": False}
    if request.get("schema") != SCHEMA: errors.append("schema mismatch")
    project = _exact_text(request.get("project_path"), "project_path", errors)
    if project is not None and not (PureWindowsPath(project).is_absolute()
                                    or PurePosixPath(project).is_absolute()):
        errors.append("project_path must be absolute")
    prefab = _exact_text(request.get("prefab_asset_path"), "prefab_asset_path", errors)
    if prefab is not None and ("\\" in prefab or not prefab.startswith("Assets/")
                               or not prefab.endswith(".prefab") or ".." in prefab.split("/")):
        errors.append("prefab_asset_path must be a normalized Assets/... .prefab path")
    levels = request.get("levels")
    if not isinstance(levels, list) or not 1 <= len(levels) <= 8:
        errors.append("levels must contain 1 through 8 entries"); levels = []
    seen_paths = set(); previous_height = 1.0
    for position, level in enumerate(levels):
        label = "levels[" + str(position) + "]"
        if not _exact(level, LEVEL_FIELDS, label, errors): continue
        if isinstance(level["level_index"], bool) or level["level_index"] != position:
            errors.append(label + ".level_index must equal its zero-based list position")
        paths = level["renderer_paths"]
        if not isinstance(paths, list) or not 1 <= len(paths) <= 32:
            errors.append(label + ".renderer_paths must contain 1 through 32 paths")
        else:
            local = set()
            for index, path in enumerate(paths):
                exact = _exact_text(path, label + ".renderer_paths[" + str(index) + "]", errors)
                if exact is None: continue
                invalid = (exact.startswith("/") or exact.endswith("/") or "\\" in exact
                           or any(part in ("", ".", "..") for part in exact.split("/")))
                if invalid: errors.append(label + ".renderer_paths must be normalized relative paths")
                folded = exact.casefold()
                if folded in local or folded in seen_paths:
                    errors.append("renderer paths must be unique across all levels")
                local.add(folded); seen_paths.add(folded)
        height = level["screen_relative_transition_height"]
        if isinstance(height, bool) or not isinstance(height, (int, float)):
            errors.append(label + ".screen_relative_transition_height must be finite in (0,1)")
        else:
            value = float(height)
            if not math.isfinite(value) or not 0.0 < value < 1.0:
                errors.append(label + ".screen_relative_transition_height must be finite in (0,1)")
            elif value >= previous_height:
                errors.append("transition heights must be strictly decreasing")
            previous_height = value
    fade = request.get("fade")
    if _exact(fade, FADE_FIELDS, "fade", errors):
        if fade["fade_mode"] != "NONE": errors.append("fade.fade_mode must be NONE in v1")
        if fade["animate_cross_fading"] is not False:
            errors.append("fade.animate_cross_fading must be false in v1")
    policy = request.get("policy")
    if _exact(policy, POLICY_FIELDS, "policy", errors):
        expected = {"target_selection": "EXPLICIT_ONLY",
                    "mutation": "PREVIEW_THEN_EXPLICIT_APPLY",
                    "existing_lod_group": "REFUSE"}
        for key, value in expected.items():
            if policy[key] != value: errors.append("policy." + key + " must be " + value)
    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema": SCHEMA, "status": "ready" if not errors else "error",
            "request_sha256": digest, "project_path": project,
            "prefab_asset_path": prefab, "level_count": len(levels),
            "errors": errors, "mutation_authorized": False}
