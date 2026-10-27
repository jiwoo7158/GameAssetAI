import hashlib
import json
import math
from pathlib import Path


SCHEMA = "gameassetai.humanoid-animation-import-request.v1"
ROLES = {
    "hips", "spine", "chest", "neck", "head",
    "upper_arm_l", "lower_arm_l", "hand_l", "upper_arm_r", "lower_arm_r", "hand_r",
    "upper_leg_l", "lower_leg_l", "foot_l", "upper_leg_r", "lower_leg_r", "foot_r",
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def validate_request(request):
    expected = {"schema", "scene_name", "source_fbx", "target", "source_mapping",
                "target_mapping", "frame", "root_motion", "policy"}
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] != SCHEMA:
        raise ValueError(f"schema must be {SCHEMA}")
    if not isinstance(request["scene_name"], str) or not request["scene_name"].strip():
        raise ValueError("scene_name must be a non-empty exact string")
    source = request["source_fbx"]
    if not isinstance(source, dict) or set(source) != {
            "path", "sha256", "format", "expected_armature_name", "expected_action_name",
            "mixamo_prefix"}:
        raise ValueError("source_fbx fields are invalid")
    path = Path(source["path"])
    if not path.is_absolute() or path.suffix.lower() != ".fbx":
        raise ValueError("source_fbx path must be an absolute .fbx path")
    if not isinstance(source["sha256"], str) or len(source["sha256"]) != 64 or any(
            char not in "0123456789abcdef" for char in source["sha256"]):
        raise ValueError("source_fbx sha256 must be an exact lowercase SHA-256")
    if source["format"] != "FBX" or not isinstance(source["mixamo_prefix"], str):
        raise ValueError("source_fbx format/prefix is invalid")
    for key in ("expected_armature_name", "expected_action_name"):
        if source[key] is not None and (not isinstance(source[key], str) or not source[key].strip()):
            raise ValueError(f"{key} must be a non-empty exact string or null")
    target = request["target"]
    if not isinstance(target, dict) or set(target) != {
            "armature_name", "mesh_object_name", "result_action_name", "import_collection_name"}:
        raise ValueError("target fields are invalid")
    for key, value in target.items():
        if not isinstance(value, str) or not value.strip() or len(value.encode("utf-8")) > 255:
            raise ValueError(f"target {key} must be a non-empty Blender name")
    for key in ("source_mapping", "target_mapping"):
        mapping = request[key]
        if not isinstance(mapping, dict) or set(mapping) != ROLES:
            raise ValueError(f"{key} roles must be exactly {sorted(ROLES)}")
        if any(not isinstance(name, str) or not name.strip() for name in mapping.values()):
            raise ValueError(f"{key} bone names must be non-empty strings")
        if len(set(mapping.values())) != len(mapping):
            raise ValueError(f"{key} cannot map one bone to multiple roles")
    frame = request["frame"]
    if not isinstance(frame, dict) or set(frame) != {"start", "end", "step", "fps"}:
        raise ValueError("frame fields are invalid")
    if any(isinstance(frame[key], bool) or not isinstance(frame[key], int)
           for key in ("start", "end", "step", "fps")):
        raise ValueError("frame values must be integers")
    if frame["end"] < frame["start"] or frame["step"] != 1 or frame["end"] - frame["start"] > 2000:
        raise ValueError("frame range must be inclusive, step 1 and at most 2001 frames")
    if not 1 <= frame["fps"] <= 240:
        raise ValueError("fps must be between 1 and 240")
    root = request["root_motion"]
    if not isinstance(root, dict) or set(root) != {"policy", "axis_mask", "translation_scale"}:
        raise ValueError("root_motion fields are invalid")
    if root["policy"] not in {"IN_PLACE", "TRANSFER"}:
        raise ValueError("root_motion policy must be IN_PLACE or TRANSFER")
    if not isinstance(root["axis_mask"], list) or len(root["axis_mask"]) != 3 or any(
            type(value) is not bool for value in root["axis_mask"]):
        raise ValueError("root_motion axis_mask must contain three booleans")
    scale = root["translation_scale"]
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(scale):
        raise ValueError("root_motion translation_scale must be finite")
    if root["policy"] == "IN_PLACE" and (any(root["axis_mask"]) or float(scale) != 1.0):
        raise ValueError("IN_PLACE requires a disabled axis mask and scale 1")
    if root["policy"] == "TRANSFER" and (not any(root["axis_mask"]) or not 0 < float(scale) <= 1000):
        raise ValueError("TRANSFER requires an enabled axis and scale in (0,1000]")
    required_policy = {"source_import": "KEEP_OWNED_COLLECTION",
                       "target_animation": "EMPTY_ONLY",
                       "result_action": "NEW_BOUND_ACTION", "preserve_sources": True,
                       "overwrite": False, "failure": "ROLL_BACK_NEW_DATA"}
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized,
            "request_sha256": hashlib.sha256(_canonical(normalized).encode()).hexdigest()}
