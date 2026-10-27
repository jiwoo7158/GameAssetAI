"""Pure validation for an explicit independent-copy static LOD generation request."""
from __future__ import annotations

import hashlib
import json
import math


SCHEMA = "gameassetai.static-lod-copy-request.v1"
FIELDS = frozenset(("schema", "scene_name", "source_object_name", "output_object_name",
                    "output_mesh_name", "operation", "policy"))
OPERATION_FIELDS = frozenset(("method", "ratio", "triangulate"))
POLICY_FIELDS = frozenset(("geometry_source", "dependency_handling", "source_mutation",
                           "output_independence", "transform", "materials", "uv_layers",
                           "authorization"))


def _exact(value, fields, label, errors):
    if not isinstance(value, dict):
        errors.append(label + " must be an object"); return False
    if any(not isinstance(key, str) for key in value):
        errors.append(label + " keys must be strings"); return False
    missing, unknown = sorted(fields - value.keys()), sorted(value.keys() - fields)
    if missing: errors.append(label + " missing fields: " + ", ".join(missing))
    if unknown: errors.append(label + " unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _name(value, label, errors):
    if not isinstance(value, str) or not value or value != value.strip():
        errors.append(label + " must be a nonempty exact name"); return None
    return value


def validate_static_lod_copy_request(request: object) -> dict:
    errors = []
    if not _exact(request, FIELDS, "request", errors):
        return {"schema": SCHEMA, "status": "error", "request_sha256": None,
                "errors": errors, "mutation_authorized": False}
    if request.get("schema") != SCHEMA: errors.append("schema mismatch")
    scene = _name(request.get("scene_name"), "scene_name", errors)
    source = _name(request.get("source_object_name"), "source_object_name", errors)
    output_object = _name(request.get("output_object_name"), "output_object_name", errors)
    output_mesh = _name(request.get("output_mesh_name"), "output_mesh_name", errors)
    if source is not None and output_object == source:
        errors.append("output_object_name must differ from source_object_name")
    if output_object is not None and output_mesh == output_object:
        errors.append("output Object and Mesh names must differ")
    operation = request.get("operation")
    if _exact(operation, OPERATION_FIELDS, "operation", errors):
        if operation["method"] != "DECIMATE_COLLAPSE":
            errors.append("operation.method must be DECIMATE_COLLAPSE")
        ratio = operation["ratio"]
        if isinstance(ratio, bool) or not isinstance(ratio, (int, float)):
            errors.append("operation.ratio must be a finite number from 0.01 through 0.99")
        else:
            try: valid = math.isfinite(float(ratio)) and 0.01 <= ratio <= 0.99
            except OverflowError: valid = False
            if not valid:
                errors.append("operation.ratio must be a finite number from 0.01 through 0.99")
        if operation["triangulate"] is not False:
            errors.append("operation.triangulate must be false in v1")
    policy = request.get("policy")
    if _exact(policy, POLICY_FIELDS, "policy", errors):
        expected = {"geometry_source":"BASE_MESH_ONLY", "dependency_handling":"REFUSE",
                    "source_mutation":"PRESERVE", "output_independence":"NEW_OBJECT_AND_MESH",
                    "transform":"COPY_EXACT", "materials":"SHARE_DATABLOCKS_READ_ONLY",
                    "uv_layers":"COPY", "authorization":"PREVIEW_THEN_EXPLICIT_APPLY"}
        for key, value in expected.items():
            if policy[key] != value: errors.append("policy." + key + " must be " + value)
    digest = None
    if not errors:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {"schema":SCHEMA, "status":"ready" if not errors else "error",
            "request_sha256":digest, "scene_name":scene, "source_object_name":source,
            "output_object_name":output_object, "output_mesh_name":output_mesh,
            "errors":errors, "mutation_authorized":False}
