import hashlib
import json
import math


SCHEMA = "gameassetai.character-joint-weight-copy-request.v1"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def validate_request(request):
    expected = {"schema", "scene_name", "source_object_name", "armature_object_name",
                "output_object_name", "output_mesh_name", "adjustment", "policy"}
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    for key in expected - {"schema", "adjustment", "policy"}:
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    names = [request[key] for key in ("source_object_name", "armature_object_name",
                                      "output_object_name", "output_mesh_name")]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("source, Armature and output names must be distinct")
    adjustment = request["adjustment"]
    if not isinstance(adjustment, dict) or set(adjustment) != {
            "joint", "side", "transition_width_ratio"}:
        raise ValueError("adjustment fields are invalid")
    if adjustment["joint"] not in {"SHOULDER", "HIP"}:
        raise ValueError("joint must be SHOULDER or HIP")
    if adjustment["side"] not in {"LEFT", "RIGHT", "BOTH"}:
        raise ValueError("side must be LEFT, RIGHT or BOTH")
    width = adjustment["transition_width_ratio"]
    if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width):
        raise ValueError("transition_width_ratio must be finite")
    if not 0.01 <= float(width) <= 0.08:
        raise ValueError("transition_width_ratio must be between 0.01 and 0.08")
    required = {
        "target": "OWNED_CHARACTER_RIG_ONLY",
        "source_mutation": "PRESERVE",
        "output": "NEW_OBJECT_AND_MESH",
        "geometry": "PRESERVE_EXACT",
        "armature": "SHARE_EXISTING",
        "other_weights": "PRESERVE",
        "normalization": "TARGET_PAIR_TO_EXISTING_SUM",
        "authorization": "PREVIEW_THEN_EXPLICIT_APPLY",
    }
    if request["policy"] != required:
        raise ValueError(f"policy must be exactly {required}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized,
            "request_sha256": hashlib.sha256(_canonical(normalized).encode()).hexdigest()}
