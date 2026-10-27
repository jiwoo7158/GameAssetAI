import hashlib
import json


SCHEMAS = {"gameassetai.character-rig-request.v1", "gameassetai.character-rig-request.v2"}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_request(request):
    expected = {"schema", "scene_name", "mesh_object_name", "armature_object_name", "armature_data_name", "rig_name", "policy"}
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(SCHEMAS)}")
    for key in expected - {"schema", "policy"}:
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    names = [request["mesh_object_name"], request["armature_object_name"], request["armature_data_name"]]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("mesh and Armature output names must be distinct")
    required = {
        "target": "OWNED_CHARACTER_BASE_ONLY",
        "existing_rig": "REFUSE",
        "weights": ("REGION_ASSIGNMENT_V1" if request["schema"].endswith(".v1")
                    else "LINEAR_JOINT_BLEND_V2"),
        "source_mesh": "PRESERVE_GEOMETRY",
        "failure": "ROLL_BACK_RIG_CHANGES",
    }
    if request["policy"] != required:
        raise ValueError(f"policy must be exactly {required}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized, "request_sha256": hashlib.sha256(_canonical(normalized).encode()).hexdigest()}

