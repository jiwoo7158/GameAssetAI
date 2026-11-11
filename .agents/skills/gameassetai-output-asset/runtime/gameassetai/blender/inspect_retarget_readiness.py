"""Read-only source/target humanoid and Action readiness inventory for retarget design."""
from __future__ import annotations

import math
import re
import bpy


_POSE_TRANSFORM = re.compile(
    r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]\.(location|rotation_euler|rotation_quaternion|rotation_axis_angle|scale)$')


def _retarget_bone_channel(data_path):
    match = _POSE_TRANSFORM.match(data_path)
    if not match:
        return None
    return (match.group(1).replace('\\"', '"').replace('\\\\', '\\'), match.group(2))


def _action_referenced_by_object(obj, action):
    data = obj.animation_data
    if data is None:
        return False
    if data.action == action:
        return True
    return any(strip.action == action for track in data.nla_tracks for strip in track.strips)


def _identity_transform(obj, tolerance=1e-6):
    return (max(abs(float(v)) for v in obj.location) <= tolerance and
            max(abs(float(v)) for v in obj.rotation_euler) <= tolerance and
            max(abs(float(v) - 1.0) for v in obj.scale) <= tolerance)


def inspect_retarget_readiness(scene_name, source_armature_name, target_armature_name,
                               source_mapping, target_mapping, source_action_name,
                               required_roles=REQUIRED_ROLES, source_slot_identifier=None):
    """Compare explicit rigs/rest bones and source Action channels without retargeting."""
    report = {"schema": "gameassetai.retarget-readiness.v1", "status": "error",
              "errors": [], "reviews": [], "retarget_candidate": False}
    scene = bpy.data.scenes.get(scene_name) if isinstance(scene_name, str) else None
    if scene is None:
        report["errors"].append("Named Scene not found")
        return report
    source = scene.objects.get(source_armature_name) if isinstance(source_armature_name, str) else None
    target = scene.objects.get(target_armature_name) if isinstance(target_armature_name, str) else None
    if source is None or target is None or source.type != "ARMATURE" or target.type != "ARMATURE":
        report["errors"].append("Source and target must be named Armature Objects in the Scene")
        return report
    if source == target:
        report["errors"].append("Source and target Armatures must be distinct")
        return report
    source_report = inspect_humanoid(source.name, source_mapping, scene.name, required_roles)
    target_report = inspect_humanoid(target.name, target_mapping, scene.name, required_roles)
    if source_report["status"] == "error" or target_report["status"] == "error":
        report["errors"].append("Source or target humanoid inspection failed")
        report.update({"source_humanoid": source_report, "target_humanoid": target_report})
        return report
    action = bpy.data.actions.get(source_action_name) if isinstance(source_action_name, str) else None
    if action is None:
        report["errors"].append("Named source Action not found")
        return report
    slots = [slot.identifier for slot in getattr(action, "slots", ())]
    if source_slot_identifier is None and len(slots) > 1:
        report["errors"].append("source_slot_identifier is required for a multi-slot Action")
        return report
    if source_slot_identifier is not None and source_slot_identifier not in slots:
        report["errors"].append("Named source Action slot not found")
        return report
    slot_identifier = source_slot_identifier if source_slot_identifier is not None else (
        slots[0] if slots else None)

    source_reverse = {bone: role for role, bone in source_mapping.items()}
    role_channels = {}
    unmapped_bones = set()
    non_bone_channels = []
    for curve, slot in _curves_with_slots(action):
        if slot_identifier is not None and slot not in {None, slot_identifier}:
            continue
        parsed = _retarget_bone_channel(curve.data_path)
        if parsed is None:
            non_bone_channels.append({"data_path": curve.data_path,
                                      "array_index": curve.array_index, "slot": slot})
            continue
        bone_name, property_name = parsed
        role = source_reverse.get(bone_name)
        if role is None:
            unmapped_bones.add(bone_name)
            continue
        role_channels.setdefault(role, set()).add(property_name)

    metrics = []
    zero_length_roles = []
    common_roles = sorted(set(source_mapping) & set(target_mapping))
    for role in common_roles:
        source_bone = source.data.bones.get(source_mapping[role])
        target_bone = target.data.bones.get(target_mapping[role])
        if source_bone is None or target_bone is None:
            continue
        source_vector = source_bone.tail_local - source_bone.head_local
        target_vector = target_bone.tail_local - target_bone.head_local
        source_length, target_length = float(source_vector.length), float(target_vector.length)
        if source_length <= 1e-12 or target_length <= 1e-12:
            zero_length_roles.append(role)
            direction_dot = None
            ratio = None
        else:
            direction_dot = float(source_vector.normalized().dot(target_vector.normalized()))
            ratio = target_length / source_length
        metrics.append({"role": role, "source_bone": source_bone.name,
                        "target_bone": target_bone.name,
                        "source_length": source_length, "target_length": target_length,
                        "target_to_source_length_ratio": ratio,
                        "armature_space_direction_dot": direction_dot})

    source_bound = _action_referenced_by_object(source, action)
    target_animation = bool(target.animation_data and
                            (target.animation_data.action or target.animation_data.nla_tracks))
    mapped_animated_roles = sorted(role_channels)
    complete = source_report["status"] == "ok" and target_report["status"] == "ok"
    candidate = complete and source_bound and bool(mapped_animated_roles) and not zero_length_roles
    report.update({"status": "ok" if complete else "incomplete",
                   "blender_version": bpy.app.version_string, "scene": scene.name,
                   "source_armature": source.name, "target_armature": target.name,
                   "source_humanoid": source_report, "target_humanoid": target_report,
                   "source_action": action.name, "source_slot_identifier": slot_identifier,
                   "source_action_referenced_by_source": source_bound,
                   "mapped_animated_roles": mapped_animated_roles,
                   "role_transform_channels": {role: sorted(values)
                                               for role, values in sorted(role_channels.items())},
                   "unmapped_animated_bones": sorted(unmapped_bones),
                   "non_bone_channels": non_bone_channels,
                   "role_rest_metrics": metrics, "zero_length_roles": zero_length_roles,
                   "source_transform": {"location": list(source.location),
                                        "rotation_euler": list(source.rotation_euler),
                                        "scale": list(source.scale)},
                   "target_transform": {"location": list(target.location),
                                        "rotation_euler": list(target.rotation_euler),
                                        "scale": list(target.scale)},
                   "target_has_animation": target_animation,
                   "retarget_candidate": candidate})
    if not source_bound:
        report["reviews"].append("The named source Action is not currently referenced by the source Armature")
    if not mapped_animated_roles:
        report["reviews"].append("The source Action has no transform channels on explicitly mapped humanoid bones")
    if unmapped_bones:
        report["reviews"].append("The source Action also animates bones outside the explicit humanoid mapping")
    if zero_length_roles:
        report["reviews"].append("At least one mapped rest bone has near-zero length")
    if not _identity_transform(source) or not _identity_transform(target):
        report["reviews"].append("Source or target Armature Object has non-identity transform")
    if target_animation:
        report["reviews"].append("Target Armature already has preservation-sensitive animation")
    report["reviews"].append(
        "Armature-space rest length/direction metrics do not certify rest-pose alignment, bone roll, axes, constraints, weights or retarget quality")
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
