"""Read-only Blender Action, binding, NLA and explicit root-motion channel inventory."""
from __future__ import annotations

import re
import bpy


_POSE_BONE = re.compile(r'^pose\.bones\["((?:[^"\\]|\\.)*)"\]')


def _curves(action):
    result = list(getattr(action, "fcurves", ()))
    for layer in getattr(action, "layers", ()):
        for strip in getattr(layer, "strips", ()):
            for bag in getattr(strip, "channelbags", ()):
                result.extend(bag.fcurves)
    seen = set()
    return [curve for curve in result if not (curve.as_pointer() in seen or seen.add(curve.as_pointer()))]


def _binding(owner):
    data = getattr(owner, "animation_data", None)
    if data is None:
        return None
    slot = getattr(data, "action_slot", None)
    return {
        "owner": owner.name,
        "owner_type": type(owner).__name__,
        "action": data.action.name if data.action else None,
        "slot": getattr(slot, "identifier", None),
        "drivers": len(data.drivers),
        "nla_tracks": [{
            "name": track.name, "mute": track.mute,
            "strips": [{"name": strip.name, "action": strip.action.name if strip.action else None,
                        "frame_start": float(strip.frame_start), "frame_end": float(strip.frame_end),
                        "scale": float(strip.scale), "repeat": float(strip.repeat)}
                       for strip in track.strips],
        } for track in data.nla_tracks],
    }


def inspect_animation(scene_name=None, object_name=None, root_bone_names=None):
    """Inventory stored animation without frame changes, graph evaluation, operators or writes."""
    report = {"schema": "gameassetai.animation-inventory.v1", "status": "error",
              "errors": [], "reviews": []}
    scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
    if scene is None:
        report["errors"].append("Scene not found")
        return report
    if object_name is not None:
        if not isinstance(object_name, str) or scene.objects.get(object_name) is None:
            report["errors"].append("Named object not found in Scene")
            return report
        targets = [scene.objects[object_name]]
    else:
        targets = sorted(scene.objects, key=lambda item: item.name)
    if root_bone_names is None:
        root_bone_names = []
    if (not isinstance(root_bone_names, (list, tuple))
            or any(not isinstance(name, str) or not name for name in root_bone_names)
            or len(set(root_bone_names)) != len(root_bone_names)):
        report["errors"].append("root_bone_names must be a unique list of nonempty strings")
        return report

    bindings = []
    owners = list(targets)
    for obj in targets:
        if obj.data is not None:
            owners.append(obj.data)
        if obj.type == "MESH" and obj.data.shape_keys is not None:
            owners.append(obj.data.shape_keys)
    for owner in owners:
        value = _binding(owner)
        if value is not None:
            bindings.append(value)

    actions = []
    root_channels = []
    roots = set(root_bone_names)
    for action in sorted(bpy.data.actions, key=lambda item: item.name):
        curves = _curves(action)
        channels = []
        for curve in curves:
            points = list(curve.keyframe_points)
            channel = {"data_path": curve.data_path, "array_index": curve.array_index,
                       "keyframes": len(points),
                       "frame_min": min((float(p.co.x) for p in points), default=None),
                       "frame_max": max((float(p.co.x) for p in points), default=None),
                       "cyclic": any(mod.type == "CYCLES" for mod in curve.modifiers)}
            channels.append(channel)
            match = _POSE_BONE.match(curve.data_path)
            bone = (match.group(1).replace('\\"', '"').replace('\\\\', '\\')
                    if match else None)
            if ((curve.data_path == "location" and object_name is not None)
                    or (bone in roots and curve.data_path.endswith(".location"))):
                root_channels.append({"action": action.name, **channel,
                                      "bone": bone, "object_channel": bone is None})
        actions.append({"name": action.name, "users": action.users,
                        "frame_range": [float(value) for value in action.frame_range],
                        "slots": [{"identifier": slot.identifier,
                                   "target_id_type": getattr(slot, "target_id_type", None)}
                                  for slot in getattr(action, "slots", ())],
                        "curve_count": len(curves),
                        "keyframe_count": sum(item["keyframes"] for item in channels),
                        "channels": channels})
    report.update({"blender_version": bpy.app.version_string, "scene": scene.name,
                   "targets": [item.name for item in targets], "actions": actions,
                   "bindings": bindings, "root_bone_names": list(root_bone_names),
                   "root_motion_channels": root_channels})
    if not root_bone_names:
        report["reviews"].append("Root-bone mapping was not supplied; bone root motion was not inferred")
    if not actions:
        report["reviews"].append("No Actions exist in the Blender file")
    report["status"] = "ok"
    return report
