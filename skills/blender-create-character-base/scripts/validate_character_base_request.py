import hashlib
import json
import math


SCHEMAS = {
    "gameassetai.character-base-request.v1",
    "gameassetai.character-base-request.v2",
    "gameassetai.character-base-request.v3",
}
POSES = {"A_POSE", "T_POSE"}
MATERIAL_KEYS = ("skin", "primary", "secondary", "boots")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _number(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not low <= value <= high:
        raise ValueError(f"{label} must be in [{low}, {high}]")
    return value


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    schema = request.get("schema")
    expected = {"schema", "scene_name", "character_name", "collection_name", "object_name", "mesh_name", "pose", "proportions", "colors", "policy"}
    if schema in {"gameassetai.character-base-request.v2", "gameassetai.character-base-request.v3"}:
        expected.add("topology_mode")
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if schema not in SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(SCHEMAS)}")
    if schema.endswith(".v2") and request["topology_mode"] not in {"VOLUME_ISLANDS", "VOXEL_CONNECTED"}:
        raise ValueError("topology_mode must be VOLUME_ISLANDS or VOXEL_CONNECTED")
    if schema.endswith(".v2") and request["topology_mode"] == "VOXEL_CONNECTED":
        raise ValueError("VOXEL_CONNECTED is suspended after unintended humanoid limb/foot fusion")
    if schema.endswith(".v3") and request["topology_mode"] != "BOOLEAN_CONNECTED":
        raise ValueError("v3 topology_mode must be BOOLEAN_CONNECTED")
    for key in ("scene_name", "character_name", "collection_name", "object_name", "mesh_name"):
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    if len({request[k].casefold() for k in ("collection_name", "object_name", "mesh_name")}) != 3:
        raise ValueError("collection_name, object_name and mesh_name must be distinct")
    if request["pose"] not in POSES:
        raise ValueError(f"pose must be one of {sorted(POSES)}")

    proportions = request["proportions"]
    fields = {"height", "shoulder_width_ratio", "hip_width_ratio", "body_depth_ratio", "limb_thickness_ratio", "head_height_ratio"}
    if not isinstance(proportions, dict) or set(proportions) != fields:
        raise ValueError(f"proportions fields must be exactly {sorted(fields)}")
    proportions["height"] = _number(proportions["height"], "height", 0.5, 4.0)
    proportions["shoulder_width_ratio"] = _number(proportions["shoulder_width_ratio"], "shoulder_width_ratio", 0.18, 0.42)
    proportions["hip_width_ratio"] = _number(proportions["hip_width_ratio"], "hip_width_ratio", 0.12, 0.32)
    proportions["body_depth_ratio"] = _number(proportions["body_depth_ratio"], "body_depth_ratio", 0.08, 0.25)
    proportions["limb_thickness_ratio"] = _number(proportions["limb_thickness_ratio"], "limb_thickness_ratio", 0.025, 0.09)
    proportions["head_height_ratio"] = _number(proportions["head_height_ratio"], "head_height_ratio", 0.12, 0.22)

    colors = request["colors"]
    if not isinstance(colors, dict) or set(colors) != set(MATERIAL_KEYS):
        raise ValueError(f"colors fields must be exactly {list(MATERIAL_KEYS)}")
    for key in MATERIAL_KEYS:
        color = colors[key]
        if not isinstance(color, list) or len(color) != 4:
            raise ValueError(f"colors.{key} must be RGBA")
        colors[key] = [_number(component, f"colors.{key}", 0.0, 1.0) for component in color]
        if colors[key][3] != 1.0:
            raise ValueError("character base materials must be opaque")

    required_policy = {
        "existing_names": "REFUSE",
        "source_scene": "PRESERVE",
        "creation": "NEW_SINGLE_MESH_CHARACTER",
        "failure": "ROLL_BACK_OWNED_DATA",
        "rigging": "NOT_INCLUDED",
    }
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")

    normalized = json.loads(_canonical(request))
    return {
        "status": "ready",
        "request": normalized,
        "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest(),
    }

