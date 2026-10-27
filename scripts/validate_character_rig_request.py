import hashlib
import json
import math


SCHEMAS = {"gameassetai.character-rig-request.v1", "gameassetai.character-rig-request.v2",
           "gameassetai.character-rig-request.v3"}
LANDMARK_NAMES = {
    "root", "pelvis", "spine", "chest", "neck", "head_top",
    "shoulder.L", "elbow.L", "wrist.L", "hand_tip.L",
    "shoulder.R", "elbow.R", "wrist.R", "hand_tip.R",
    "hip.L", "knee.L", "ankle.L", "toe.L",
    "hip.R", "knee.R", "ankle.R", "toe.R",
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_request(request):
    schema = request.get("schema") if isinstance(request, dict) else None
    expected = {"schema", "scene_name", "mesh_object_name", "armature_object_name",
                "armature_data_name", "rig_name", "policy"}
    if schema == "gameassetai.character-rig-request.v3":
        expected.add("fitting")
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(SCHEMAS)}")
    for key in expected - {"schema", "policy", "fitting"}:
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    names = [request["mesh_object_name"], request["armature_object_name"], request["armature_data_name"]]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("mesh and Armature output names must be distinct")
    if schema == "gameassetai.character-rig-request.v3":
        fitting = request["fitting"]
        if not isinstance(fitting, dict) or set(fitting) != {
                "mode", "pose", "front_axis", "coordinate_space", "landmarks",
                "transition_width_ratio", "max_influences"}:
            raise ValueError("fitting fields are invalid")
        constants = {"mode": "EXPLICIT_LANDMARKS", "pose": "A_POSE", "front_axis": "-Y",
                     "coordinate_space": "OBJECT_LOCAL", "max_influences": 4}
        for key, value in constants.items():
            if fitting[key] != value:
                raise ValueError(f"fitting {key} must be {value}")
        landmarks = fitting["landmarks"]
        if not isinstance(landmarks, dict) or set(landmarks) != LANDMARK_NAMES:
            raise ValueError(f"landmark names must be exactly {sorted(LANDMARK_NAMES)}")
        for name, point in landmarks.items():
            if (not isinstance(point, list) or len(point) != 3
                    or any(isinstance(value, bool) or not isinstance(value, (int, float))
                           or not math.isfinite(value) for value in point)):
                raise ValueError(f"landmark {name} must be three finite numbers")
        width = fitting["transition_width_ratio"]
        if (isinstance(width, bool) or not isinstance(width, (int, float))
                or not math.isfinite(width) or not 0.015 <= float(width) <= 0.10):
            raise ValueError("transition_width_ratio must be finite and between 0.015 and 0.10")
        required = {"target": "EXPLICIT_HUMANOID_MESH", "existing_rig": "REFUSE",
                    "weights": "LANDMARK_ENVELOPE_V3",
                    "source_mesh": "PRESERVE_GEOMETRY_AND_UV",
                    "failure": "ROLL_BACK_RIG_CHANGES"}
    else:
        required = {
            "target": "OWNED_CHARACTER_BASE_ONLY",
            "existing_rig": "REFUSE",
            "weights": ("REGION_ASSIGNMENT_V1" if schema.endswith(".v1")
                        else "LINEAR_JOINT_BLEND_V2"),
            "source_mesh": "PRESERVE_GEOMETRY",
            "failure": "ROLL_BACK_RIG_CHANGES",
        }
    if request["policy"] != required:
        raise ValueError(f"policy must be exactly {required}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized, "request_sha256": hashlib.sha256(_canonical(normalized).encode()).hexdigest()}
