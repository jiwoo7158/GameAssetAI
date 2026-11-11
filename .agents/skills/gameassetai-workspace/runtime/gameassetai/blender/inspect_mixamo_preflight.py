"""Read-only detection and preparation review for an existing Mixamo-style Armature."""
from __future__ import annotations

import math
import bpy


MIXAMO_SUFFIXES = {
    "hips": "Hips", "spine": "Spine", "chest": "Spine2", "neck": "Neck", "head": "Head",
    "upper_arm_l": "LeftArm", "lower_arm_l": "LeftForeArm", "hand_l": "LeftHand",
    "upper_arm_r": "RightArm", "lower_arm_r": "RightForeArm", "hand_r": "RightHand",
    "upper_leg_l": "LeftUpLeg", "lower_leg_l": "LeftLeg", "foot_l": "LeftFoot",
    "upper_leg_r": "RightUpLeg", "lower_leg_r": "RightLeg", "foot_r": "RightFoot",
}
OPTIONAL_SUFFIXES = ("Spine1", "LeftShoulder", "RightShoulder", "LeftToeBase", "RightToeBase")


def _candidate_prefixes(names):
    suffix = MIXAMO_SUFFIXES["hips"]
    return sorted({name[:-len(suffix)] for name in names if name.endswith(suffix)})


def inspect_mixamo_preflight(armature_name, scene_name=None, expected_prefix=None):
    """Detect one exact Mixamo naming signature and report preservation-sensitive state."""
    report = {"schema": "gameassetai.mixamo-preflight.v1", "status": "error",
              "errors": [], "reviews": []}
    scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
    if scene is None:
        report["errors"].append("Scene not found")
        return report
    obj = scene.objects.get(armature_name) if isinstance(armature_name, str) else None
    if obj is None or obj.type != "ARMATURE":
        report["errors"].append("Named Scene object is not an Armature")
        return report
    if getattr(obj.data, "is_editmode", None) is not False:
        report["errors"].append("Armature rest data is unverified in Edit Mode")
        return report
    if expected_prefix is not None and (not isinstance(expected_prefix, str)
                                        or expected_prefix != expected_prefix.strip()):
        report["errors"].append("expected_prefix must be an exact string or None")
        return report
    names = {bone.name for bone in obj.data.bones}
    prefixes = [expected_prefix] if expected_prefix is not None else _candidate_prefixes(names)
    candidates = []
    for prefix in prefixes:
        mapping = {role: prefix + suffix for role, suffix in MIXAMO_SUFFIXES.items()}
        missing = sorted(name for name in mapping.values() if name not in names)
        if not missing:
            candidates.append({"prefix": prefix, "mapping": mapping})
    report.update({"blender_version": bpy.app.version_string, "scene": scene.name,
                   "armature": obj.name, "candidate_prefixes": [item["prefix"] for item in candidates],
                   "mapping": {}, "humanoid": None, "bound_meshes": [],
                   "armature_transform": {"location": list(obj.location),
                                          "rotation": list(obj.rotation_euler),
                                          "scale": list(obj.scale)}})
    if len(candidates) != 1:
        report["status"] = "incomplete"
        report["reviews"].append("No unique complete Mixamo naming signature was found")
        return report
    candidate = candidates[0]
    report["mapping"] = candidate["mapping"]
    report["humanoid"] = inspect_humanoid(obj.name, candidate["mapping"], scene.name)
    prefix = candidate["prefix"]
    report["optional_bones"] = sorted(prefix + suffix for suffix in OPTIONAL_SUFFIXES
                                       if prefix + suffix in names)
    for mesh_obj in sorted((item for item in scene.objects if item.type == "MESH"),
                           key=lambda item: item.name):
        modifiers = [mod for mod in mesh_obj.modifiers
                     if mod.type == "ARMATURE" and mod.object == obj]
        if not modifiers:
            continue
        groups = {group.name for group in mesh_obj.vertex_groups}
        report["bound_meshes"].append({
            "object": mesh_obj.name,
            "modifier_count": len(modifiers),
            "missing_mapped_vertex_groups": sorted(set(candidate["mapping"].values()) - groups),
            "shape_keys": bool(mesh_obj.data.shape_keys),
        })
    if not report["bound_meshes"]:
        report["reviews"].append("No Scene Mesh has an Armature modifier targeting this rig")
    if any(item["missing_mapped_vertex_groups"] for item in report["bound_meshes"]):
        report["reviews"].append("A bound Mesh lacks one or more mapped bone vertex groups")
    values = (*obj.location, *obj.rotation_euler, *obj.scale)
    if not all(math.isfinite(value) for value in values):
        report["errors"].append("Armature transform contains non-finite values")
        report["status"] = "error"
        return report
    if (any(abs(value) > 1e-6 for value in (*obj.location, *obj.rotation_euler))
            or any(abs(value - 1.0) > 1e-6 for value in obj.scale)):
        report["reviews"].append("Armature Object transform is not identity")
    if obj.animation_data and (obj.animation_data.action or obj.animation_data.nla_tracks):
        report["reviews"].append("Existing rig animation must be preserved")
    report["reviews"].append("T/A pose, bone axes, skin quality and Mixamo upload are not certified")
    report["status"] = "ok" if report["humanoid"]["status"] == "ok" else "incomplete"
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
