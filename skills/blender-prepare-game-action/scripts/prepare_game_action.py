"""Prepare one evaluated Armature Action range as an independent game clip."""
from __future__ import annotations

import hashlib
import json
import math
import re
import uuid

import bpy
from mathutils import Quaternion, Vector


SCHEMA = "gameassetai.game-action-preparation-request.v1"
PLAN_SCHEMA = "gameassetai.game-action-preparation-plan.v1"
RESULT_SCHEMA = "gameassetai.game-action-preparation-result.v1"
_REQUEST_KEYS = {"schema", "scene_name", "armature_name", "source_action",
                 "source_slot_identifier", "target_action", "frame", "root_bone_name",
                 "sampling", "tolerances", "policy"}
_FRAME_KEYS = {"source_start", "source_end", "source_fps", "target_fps", "output_start"}
_SAMPLING_KEYS = {"mode", "key_cleanup"}
_TOLERANCE_KEYS = {"translation", "rotation_radians", "scale"}
_POLICY_KEYS = {"preserve_source", "bind_result", "set_fake_user", "failure"}
_POSE_PATH = re.compile(
    r'^pose\.bones\["((?:[^"\\]|\\.)+)"\]\.(location|rotation_euler|rotation_quaternion|rotation_axis_angle|scale)$')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False)


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _finite_number(value, label, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must be <= {maximum}")
    return value


def _exact_dict(value, keys, label, errors):
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    unknown, missing = sorted(set(value) - keys), sorted(keys - set(value))
    if unknown:
        errors.append(f"Unknown {label} fields: " + ", ".join(unknown))
    if missing:
        errors.append(f"Missing {label} fields: " + ", ".join(missing))
    return not unknown and not missing


def _bone_from_path(path):
    match = _POSE_PATH.fullmatch(path)
    if match is None:
        return None, None
    # Blender RNA paths escape quotes/backslashes like Python string literals.
    try:
        bone = json.loads('"' + match.group(1) + '"')
    except json.JSONDecodeError:
        return None, None
    return bone, match.group(2)


def _rig_static_snapshot(obj):
    return {
        "object_matrix": [[float(value) for value in row] for row in obj.matrix_world],
        "data": obj.data.name,
        "bones": [{"name": bone.name, "parent": bone.parent.name if bone.parent else None,
                   "matrix_local": [[float(value) for value in row]
                                    for row in bone.matrix_local],
                   "head": [float(value) for value in bone.head_local],
                   "tail": [float(value) for value in bone.tail_local],
                   "use_deform": bool(bone.use_deform)}
                  for bone in obj.data.bones],
    }


def _animation_state(obj):
    data = obj.animation_data
    if data is None:
        return {"exists": False, "action": None, "slot": None, "nla": [], "drivers": []}
    return {"exists": True,
            "action": data.action.name if data.action else None,
            "slot": getattr(getattr(data, "action_slot", None), "identifier", None),
            "nla": [(track.name, strip.name, strip.action.name if strip.action else None)
                    for track in data.nla_tracks for strip in track.strips],
            "drivers": [(curve.data_path, curve.array_index) for curve in data.drivers]}


def _sample_times(frame):
    intervals = ((frame["source_end"] - frame["source_start"])
                 * frame["target_fps"] / frame["source_fps"])
    rounded = round(intervals)
    if abs(intervals - rounded) > 1.0e-7:
        raise ValueError("Source range does not map to an integral target-frame interval count")
    if rounded < 1 or rounded > 10000:
        raise ValueError("Prepared clip must contain 2..10001 samples")
    return [(frame["source_start"] + index * frame["source_fps"] / frame["target_fps"],
             frame["output_start"] + index)
            for index in range(rounded + 1)]


def _validate_request(request):
    errors = []
    if not _exact_dict(request, _REQUEST_KEYS, "request", errors):
        return None, errors
    if request["schema"] != SCHEMA:
        errors.append("Unsupported request schema")
    for key in ("scene_name", "armature_name", "source_action", "source_slot_identifier",
                "target_action", "root_bone_name"):
        value = request[key]
        if not isinstance(value, str) or not value or value != value.strip():
            errors.append(f"{key} must be an exact nonempty name")
    if request["source_action"] == request["target_action"]:
        errors.append("Source and target Action names must differ")
    valid_parts = all((_exact_dict(request[key], keys, key, errors)
                       for key, keys in (("frame", _FRAME_KEYS),
                                         ("sampling", _SAMPLING_KEYS),
                                         ("tolerances", _TOLERANCE_KEYS),
                                         ("policy", _POLICY_KEYS))))
    if not valid_parts or errors:
        return None, errors
    try:
        frame = {
            "source_start": _finite_number(request["frame"]["source_start"], "source_start"),
            "source_end": _finite_number(request["frame"]["source_end"], "source_end"),
            "source_fps": _finite_number(request["frame"]["source_fps"], "source_fps", minimum=1),
            "target_fps": _finite_number(request["frame"]["target_fps"], "target_fps", minimum=1),
            "output_start": request["frame"]["output_start"],
        }
        if frame["source_end"] <= frame["source_start"]:
            errors.append("source_end must be greater than source_start")
        if (isinstance(frame["output_start"], bool)
                or frame["output_start"] not in {0, 1}):
            errors.append("output_start must be integer 0 or 1")
        tolerances = {key: _finite_number(request["tolerances"][key], key, minimum=0)
                      for key in _TOLERANCE_KEYS}
        times = _sample_times(frame) if not errors else []
    except ValueError as exc:
        errors.append(str(exc))
        return None, errors
    if request["sampling"]["mode"] != "EVALUATED_POSE":
        errors.append("sampling.mode must be EVALUATED_POSE")
    if request["sampling"]["key_cleanup"] not in {"NONE", "EXACT_REDUNDANT"}:
        errors.append("key_cleanup must be NONE or EXACT_REDUNDANT")
    policy = request["policy"]
    for key, expected in (("preserve_source", True), ("bind_result", False),
                          ("set_fake_user", True),
                          ("failure", "ROLL_BACK_NEW_DATA")):
        if policy[key] != expected:
            errors.append(f"This workflow requires policy.{key}={expected!r}")
    return ({"frame": frame, "tolerances": tolerances, "times": times}
            if not errors else None), errors


def preview_game_action_preparation(request):
    report = {"schema": PLAN_SCHEMA, "status": "error", "errors": [], "reviews": [],
              "authorization": False}
    parsed, errors = _validate_request(request) if isinstance(request, dict) else (
        None, ["Request must be an object"])
    report["errors"].extend(errors)
    if errors:
        return report
    scene = bpy.data.scenes.get(request["scene_name"])
    armature = bpy.data.objects.get(request["armature_name"])
    action = bpy.data.actions.get(request["source_action"])
    if scene is None:
        report["errors"].append("Scene not found")
    if armature is None or armature.type != "ARMATURE" or scene.objects.get(armature.name) is None:
        report["errors"].append("Named local Armature Object is not in the Scene")
    if action is None:
        report["errors"].append("Source Action not found")
    if bpy.data.actions.get(request["target_action"]) is not None:
        report["errors"].append("Target Action already exists")
    if report["errors"]:
        return report
    if armature.library or armature.data.library or armature.override_library:
        report["errors"].append("Linked or overridden Armatures are not supported")
    if armature.constraints or any(bone.constraints for bone in armature.pose.bones):
        report["errors"].append("Armature and pose constraints are not supported")
    state = _animation_state(armature)
    if state["drivers"]:
        report["errors"].append("Armature animation drivers are not supported")
    slots = list(getattr(action, "slots", ()))
    if (len(slots) != 1 or getattr(slots[0], "target_id_type", None) != "OBJECT"
            or slots[0].identifier != request["source_slot_identifier"]):
        report["errors"].append("Source Action requires the exact single Object slot")
    curves = list(_curves(action))
    animated = {}
    unsupported = []
    for curve in curves:
        bone_name, channel = _bone_from_path(curve.data_path)
        if bone_name is None:
            unsupported.append(f"{curve.data_path}[{curve.array_index}]")
            continue
        if armature.pose.bones.get(bone_name) is None:
            report["errors"].append(f"Action references missing bone: {bone_name}")
            continue
        animated.setdefault(bone_name, set()).add(channel)
        for point in curve.keyframe_points:
            if not all(math.isfinite(float(value)) for value in point.co):
                report["errors"].append("Action contains non-finite keyframe data")
                break
    if unsupported:
        report["errors"].append("Unsupported non-pose channels: " + ", ".join(unsupported))
    if not curves or not animated:
        report["errors"].append("Source Action has no supported pose transform curves")
    if armature.pose.bones.get(request["root_bone_name"]) is None:
        report["errors"].append("Explicit root bone not found")
    start, end = parsed["frame"]["source_start"], parsed["frame"]["source_end"]
    action_start, action_end = map(float, action.frame_range)
    if start < action_start - 1.0e-7 or end > action_end + 1.0e-7:
        report["errors"].append("Requested range lies outside the Action frame range")
    if report["errors"]:
        return report
    current, nla = _action_references(action)
    candidate = {
        "operation": "evaluated_pose_game_clip",
        "request_sha256": _digest(request),
        "source_content_sha256": action_content_fingerprint(action),
        "source_references_sha256": _digest({"current": current, "nla": nla}),
        "armature_static_sha256": _digest(_rig_static_snapshot(armature)),
        "source_frame_start": start, "source_frame_end": end,
        "source_fps": parsed["frame"]["source_fps"],
        "target_fps": parsed["frame"]["target_fps"],
        "output_frame_start": parsed["times"][0][1],
        "output_frame_end": parsed["times"][-1][1],
        "sample_count": len(parsed["times"]),
        "animated_bones": sorted(animated),
        "source_curve_count": len(curves),
        "source_current_references": current,
        "source_nla_references": nla,
        "armature_animation_state": state,
    }
    report.update(status="candidate_for_review", request=json.loads(_canonical(request)),
                  candidate=candidate)
    report["reviews"].extend([
        "Output is an unbound evaluated-pose bake; source curves and references remain unchanged",
        "Loop and root-motion metrics are inspection metadata, not automatic editing or approval",
    ])
    return report


def _set_frame(scene, value):
    whole = math.floor(value)
    scene.frame_set(whole, subframe=value - whole)
    bpy.context.view_layer.update()


def _pose_sample(obj, bones):
    result = {}
    for name in bones:
        location, rotation, scale = obj.pose.bones[name].matrix_basis.decompose()
        rotation.normalize()
        result[name] = {"location": location.copy(), "rotation": rotation.copy(),
                        "scale": scale.copy()}
    return result


def _quaternion_angle(left, right):
    left, right = left.normalized(), right.normalized()
    return 2.0 * math.acos(min(1.0, max(-1.0, abs(left.dot(right)))))


def _pose_error(expected, actual):
    translation = rotation = scale = 0.0
    for name in expected:
        translation = max(translation, (expected[name]["location"] - actual[name]["location"]).length)
        rotation = max(rotation, _quaternion_angle(expected[name]["rotation"],
                                                   actual[name]["rotation"]))
        scale = max(scale, (expected[name]["scale"] - actual[name]["scale"]).length)
    return {"translation": translation, "rotation_radians": rotation, "scale": scale}


def _remove_exact_redundant(action):
    removed = 0
    epsilon = 1.0e-10
    for curve in _curves(action):
        changed = True
        while changed and len(curve.keyframe_points) > 2:
            changed = False
            points = curve.keyframe_points
            for index in range(1, len(points) - 1):
                left, middle, right = points[index - 1], points[index], points[index + 1]
                span = float(right.co.x - left.co.x)
                if span <= 0:
                    continue
                factor = float(middle.co.x - left.co.x) / span
                expected = float(left.co.y) + factor * float(right.co.y - left.co.y)
                if abs(float(middle.co.y) - expected) <= epsilon:
                    points.remove(middle, fast=True)
                    removed += 1
                    changed = True
                    break
        curve.update()
    return removed


def _loop_metrics(samples, root_name, target_fps):
    first, last = samples[0], samples[-1]
    endpoint = _pose_error(first, last)
    root_delta = last[root_name]["location"] - first[root_name]["location"]
    velocity = {"translation": 0.0, "rotation_radians": 0.0, "scale": 0.0}
    if len(samples) >= 3:
        start_error = _pose_error(samples[0], samples[1])
        end_error = _pose_error(samples[-2], samples[-1])
        velocity = {key: abs(start_error[key] - end_error[key]) * target_fps
                    for key in velocity}
    return {"endpoint_pose_delta": endpoint,
            "boundary_velocity_delta_per_second": velocity,
            "root_translation_delta": [float(value) for value in root_delta],
            "seamless_loop_approved": False}


def _remove_work(scene, objects):
    for obj in objects:
        if obj is not None and bpy.data.objects.get(obj.name) == obj:
            if obj.animation_data:
                obj.animation_data_clear()
            bpy.data.objects.remove(obj, do_unlink=True)
    if scene is not None and bpy.data.scenes.get(scene.name) == scene:
        bpy.data.scenes.remove(scene)


def apply_game_action_preparation(plan, authorization=False):
    result = {"schema": RESULT_SCHEMA, "status": "error", "errors": []}
    if authorization is not True:
        result["errors"].append("Explicit authorization=true is required")
        return result
    if (not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA
            or plan.get("status") != "candidate_for_review"):
        result["errors"].append("A candidate_for_review plan is required")
        return result
    request, candidate = plan.get("request"), plan.get("candidate")
    fresh = preview_game_action_preparation(request) if isinstance(request, dict) else None
    if (not fresh or fresh.get("status") != "candidate_for_review"
            or fresh.get("candidate") != candidate):
        result["errors"].append("Game Action preparation preview is stale")
        return result
    scene = bpy.data.scenes[request["scene_name"]]
    armature = bpy.data.objects[request["armature_name"]]
    source = bpy.data.actions[request["source_action"]]
    parsed, errors = _validate_request(request)
    if errors:
        result["errors"].extend(errors)
        return result
    source_snapshot = action_content_snapshot(source)
    source_refs = _action_references(source)
    rig_snapshot = _rig_static_snapshot(armature)
    animation_snapshot = _animation_state(armature)
    context_scene = bpy.context.window.scene if bpy.context.window else bpy.context.scene
    context_frame = (context_scene.frame_current, context_scene.frame_subframe)
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    token = uuid.uuid4().hex
    work_scene = source_work = target_work = created = None
    samples = []
    try:
        work_scene = bpy.data.scenes.new("GAA_ActionCleanup_" + token)
        source_work = armature.copy()
        target_work = armature.copy()
        source_work.name = "GAA_ActionSource_" + token
        target_work.name = "GAA_ActionTarget_" + token
        source_work.animation_data_clear()
        target_work.animation_data_clear()
        work_scene.collection.objects.link(source_work)
        work_scene.collection.objects.link(target_work)
        source_work.animation_data_create().action = source
        source_work.animation_data.action_slot = source.slots[0]
        created = bpy.data.actions.new(request["target_action"])
        created.use_fake_user = True
        created["gameassetai_schema"] = SCHEMA
        created["gameassetai_source_action"] = source.name
        created["gameassetai_source_start"] = parsed["frame"]["source_start"]
        created["gameassetai_source_end"] = parsed["frame"]["source_end"]
        created["gameassetai_source_fps"] = parsed["frame"]["source_fps"]
        created["gameassetai_target_fps"] = parsed["frame"]["target_fps"]
        created["gameassetai_root_bone"] = request["root_bone_name"]
        created["gameassetai_root_motion_policy"] = "PRESERVE"
        target_work.animation_data_create().action = created
        if bpy.context.window:
            bpy.context.window.scene = work_scene
        prior_quaternions = {}
        for source_frame, output_frame in parsed["times"]:
            _set_frame(work_scene, source_frame)
            sample = _pose_sample(source_work, candidate["animated_bones"])
            for name, values in sample.items():
                quaternion = values["rotation"]
                previous = prior_quaternions.get(name)
                if previous is not None and previous.dot(quaternion) < 0.0:
                    quaternion = Quaternion(tuple(-value for value in quaternion))
                    values["rotation"] = quaternion
                prior_quaternions[name] = quaternion.copy()
                pose = target_work.pose.bones[name]
                pose.location = values["location"]
                pose.rotation_mode = "QUATERNION"
                pose.rotation_quaternion = quaternion
                pose.scale = values["scale"]
                pose.keyframe_insert("location", frame=output_frame, group=name)
                pose.keyframe_insert("rotation_quaternion", frame=output_frame, group=name)
                pose.keyframe_insert("scale", frame=output_frame, group=name)
            samples.append(sample)
        for curve in _curves(created):
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
        removed = (_remove_exact_redundant(created)
                   if request["sampling"]["key_cleanup"] == "EXACT_REDUNDANT" else 0)
        created.use_frame_range = True
        created.frame_start = candidate["output_frame_start"]
        created.frame_end = candidate["output_frame_end"]
        max_error = {"translation": 0.0, "rotation_radians": 0.0, "scale": 0.0}
        for index, (_, output_frame) in enumerate(parsed["times"]):
            _set_frame(work_scene, output_frame)
            actual = _pose_sample(target_work, candidate["animated_bones"])
            error = _pose_error(samples[index], actual)
            for key in max_error:
                max_error[key] = max(max_error[key], error[key])
        for key, limit in parsed["tolerances"].items():
            if max_error[key] > limit:
                raise RuntimeError(
                    f"Prepared pose error exceeds {key} tolerance: {max_error[key]} > {limit}")
        curves = list(_curves(created))
        if not curves or any(not curve.keyframe_points and not curve.sampled_points for curve in curves):
            raise RuntimeError("Prepared Action contains an empty F-Curve")
        if len(getattr(created, "slots", ())) != 1:
            raise RuntimeError("Prepared Action did not create exactly one Object slot")
        created.slots[0].name_display = armature.name
        loop = _loop_metrics(samples, request["root_bone_name"], parsed["frame"]["target_fps"])
        # Detach temporary references before proving source/reference preservation.
        source_work.animation_data_clear()
        target_work.animation_data_clear()
        _remove_work(work_scene, (source_work, target_work))
        work_scene = source_work = target_work = None
        if (action_content_snapshot(source) != source_snapshot
                or _action_references(source) != source_refs):
            raise RuntimeError("Source Action content or references changed")
        if (_rig_static_snapshot(armature) != rig_snapshot
                or _animation_state(armature) != animation_snapshot):
            raise RuntimeError("Armature rest or animation state changed")
        if _action_references(created) != ([], []):
            raise RuntimeError("Prepared Action was unexpectedly bound")
        result.update({
            "status": "created", "source_action": source.name,
            "source_slot_identifier": request["source_slot_identifier"],
            "target_action": created.name,
            "target_slot_identifier": created.slots[0].identifier,
            "source_frame_start": candidate["source_frame_start"],
            "source_frame_end": candidate["source_frame_end"],
            "frame_start": candidate["output_frame_start"],
            "frame_end": candidate["output_frame_end"],
            "source_fps": candidate["source_fps"], "target_fps": candidate["target_fps"],
            "sample_count": candidate["sample_count"],
            "animated_bones": candidate["animated_bones"],
            "curve_count": len(curves),
            "keyframe_count": sum(len(curve.keyframe_points) for curve in curves),
            "removed_exact_redundant_keys": removed,
            "maximum_sampled_pose_error": max_error,
            "loop_and_root_motion": loop,
            "source_preserved": True, "armature_preserved": True,
            "result_unbound": True, "result_fake_user": bool(created.use_fake_user),
            "key_cleanup": request["sampling"]["key_cleanup"],
        })
        result["receipt_sha256"] = _digest(result)
        return result
    except Exception as exc:
        _remove_work(work_scene, (source_work, target_work))
        if created is not None and bpy.data.actions.get(created.name) == created:
            bpy.data.actions.remove(created)
        result["errors"].append(str(exc))
        return result
    finally:
        if bpy.context.window and context_scene and bpy.data.scenes.get(context_scene.name):
            bpy.context.window.scene = context_scene
        if bpy.data.scenes.get(context_scene.name):
            context_scene.frame_set(context_frame[0], subframe=context_frame[1])
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in selected:
            if bpy.data.objects.get(obj.name):
                obj.select_set(True)
        if active and bpy.data.objects.get(active.name):
            bpy.context.view_layer.objects.active = active
