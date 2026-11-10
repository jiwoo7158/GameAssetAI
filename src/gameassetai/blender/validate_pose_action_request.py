import hashlib
import json
import math


SCHEMAS = {
    "gameassetai.pose-action-request.v1": "ROTATION_EULER_XYZ_ONLY",
    "gameassetai.pose-action-request.v2": "ROTATION_EULER_XYZ_AND_LOCATION",
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def validate_request(request):
    expected = {"schema", "scene_name", "armature_object_name", "action_name", "frame_start", "frame_end", "fps", "front_axis", "keyframes", "policy"}
    if not isinstance(request, dict) or set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(SCHEMAS)}")
    schema = request["schema"]
    for key in ("scene_name", "armature_object_name", "action_name"):
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    for key in ("frame_start", "frame_end", "fps"):
        if isinstance(request[key], bool) or not isinstance(request[key], int):
            raise ValueError(f"{key} must be an integer")
    if request["frame_start"] < 0 or request["frame_end"] <= request["frame_start"] or not 1 <= request["fps"] <= 240:
        raise ValueError("invalid frame range or fps")
    if request["front_axis"] not in {"-Y", "+Y", "-X", "+X"}:
        raise ValueError("front_axis must be one horizontal signed axis")
    keyframes = request["keyframes"]
    if not isinstance(keyframes, list) or not 2 <= len(keyframes) <= 256:
        raise ValueError("keyframes must contain 2 to 256 entries")
    frames = []
    bone_set = None
    for index, item in enumerate(keyframes):
        expected_item = {"frame", "rotations_degrees"}
        if schema.endswith(".v2"):
            expected_item.add("locations_local")
        if not isinstance(item, dict) or set(item) != expected_item:
            raise ValueError(f"keyframes[{index}] has invalid fields")
        frame = item["frame"]
        if isinstance(frame, bool) or not isinstance(frame, int) or not request["frame_start"] <= frame <= request["frame_end"]:
            raise ValueError("keyframe frame is outside the request range")
        frames.append(frame)
        rotations = item["rotations_degrees"]
        if not isinstance(rotations, dict) or not rotations:
            raise ValueError("rotations_degrees must be a non-empty object")
        current = set(rotations)
        if bone_set is None: bone_set = current
        if current != bone_set:
            raise ValueError("every keyframe must provide the same complete animated bone set")
        for bone, rotation in rotations.items():
            if not isinstance(bone, str) or not bone or not isinstance(rotation, list) or len(rotation) != 3:
                raise ValueError("bone rotations must be named XYZ triples")
            for value in rotation:
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 360:
                    raise ValueError("rotation degrees must be finite and within [-360, 360]")
        if schema.endswith(".v2"):
            locations = item["locations_local"]
            if not isinstance(locations, dict) or not locations:
                raise ValueError("locations_local must be a non-empty object")
            if index == 0:
                location_bone_set = set(locations)
            elif set(locations) != location_bone_set:
                raise ValueError("every keyframe must provide the same complete location bone set")
            for bone, location in locations.items():
                if not isinstance(bone, str) or not bone or not isinstance(location, list) or len(location) != 3:
                    raise ValueError("bone locations must be named local XYZ triples")
                for value in location:
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > 10:
                        raise ValueError("local locations must be finite and within [-10, 10] metres")
    if frames != sorted(set(frames)) or frames[0] != request["frame_start"] or frames[-1] != request["frame_end"]:
        raise ValueError("keyframe frames must be unique, sorted, and include both range endpoints")
    required = {"existing_action": "REFUSE", "current_action": "REQUIRE_EMPTY", "channels": SCHEMAS[schema], "interpolation": "BEZIER_AUTO_CLAMPED", "mutation": "CREATE_AND_BIND"}
    if request["policy"] != required:
        raise ValueError(f"policy must be exactly {required}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized, "animated_bones": sorted(bone_set), "location_bones": sorted(location_bone_set) if schema.endswith(".v2") else [], "request_sha256": hashlib.sha256(_canonical(normalized).encode()).hexdigest()}
# Retained bounded Blender contract; product support remains capability-scoped.
