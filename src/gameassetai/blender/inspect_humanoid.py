"""Read-only explicit-mapping humanoid armature inspection for execution inside Blender."""
from __future__ import annotations

import bpy


ROLES = (
    "hips", "spine", "chest", "neck", "head",
    "upper_arm_l", "lower_arm_l", "hand_l",
    "upper_arm_r", "lower_arm_r", "hand_r",
    "upper_leg_l", "lower_leg_l", "foot_l",
    "upper_leg_r", "lower_leg_r", "foot_r",
)
REQUIRED_ROLES = tuple(role for role in ROLES if role != "chest")
PARENTS = {
    "spine": "hips", "chest": "spine", "neck": "spine", "head": "neck",
    "upper_arm_l": "spine", "lower_arm_l": "upper_arm_l", "hand_l": "lower_arm_l",
    "upper_arm_r": "spine", "lower_arm_r": "upper_arm_r", "hand_r": "lower_arm_r",
    "upper_leg_l": "hips", "lower_leg_l": "upper_leg_l", "foot_l": "lower_leg_l",
    "upper_leg_r": "hips", "lower_leg_r": "upper_leg_r", "foot_r": "lower_leg_r",
}


def _is_descendant(bone, ancestor):
    current = bone.parent
    while current is not None:
        if current == ancestor:
            return True
        current = current.parent
    return False


def inspect_humanoid(armature_name, mapping=None, scene_name=None,
                      required_roles=REQUIRED_ROLES):
    """Inspect rest-bone roles/hierarchy without operators, dependency refresh or writes."""
    report = {"schema": "gameassetai.humanoid-inspection.v1", "status": "error",
              "errors": [], "reviews": []}
    if not isinstance(armature_name, str) or not armature_name:
        report["errors"].append("armature_name must be a nonempty string")
        return report
    scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
    if scene is None:
        report["errors"].append("Scene not found")
        return report
    obj = scene.objects.get(armature_name)
    if obj is None or obj.type != "ARMATURE":
        report["errors"].append("Named Scene object is not an Armature")
        return report
    if getattr(obj.data, "is_editmode", None) is not False:
        report["errors"].append("Armature rest data is unverified in Edit Mode")
        return report
    if mapping is None:
        mapping = {}
    if not isinstance(mapping, dict):
        report["errors"].append("mapping must be an explicit role-to-bone object")
        return report
    if not isinstance(required_roles, (list, tuple)) or any(
            role not in ROLES for role in required_roles):
        report["errors"].append("required_roles contains an unsupported role")
        return report
    unknown = sorted(set(mapping) - set(ROLES))
    if unknown:
        report["errors"].append("Unsupported mapping roles: " + ", ".join(unknown))
        return report
    if any(not isinstance(name, str) or not name for name in mapping.values()):
        report["errors"].append("Mapped bone names must be nonempty strings")
        return report
    names = list(mapping.values())
    if len(names) != len(set(names)):
        report["errors"].append("One bone cannot satisfy multiple humanoid roles")
        return report

    bones = obj.data.bones
    roots = sorted(bone.name for bone in bones if bone.parent is None)
    missing_roles = sorted(set(required_roles) - set(mapping))
    missing_bones = sorted(name for name in mapping.values() if bones.get(name) is None)
    report.update({
        "blender_version": bpy.app.version_string,
        "scene": scene.name,
        "armature": obj.name,
        "datablock": obj.data.name,
        "bone_count": len(bones),
        "root_bones": roots,
        "mapping": dict(sorted(mapping.items())),
        "required_roles": list(required_roles),
        "missing_roles": missing_roles,
        "missing_bones": missing_bones,
        "hierarchy": [],
        "mapped_bones": [],
        "object_animation": bool(obj.animation_data and
                                 (obj.animation_data.action or obj.animation_data.nla_tracks)),
        "data_animation": bool(obj.data.animation_data and obj.data.animation_data.action),
    })
    if len(roots) != 1:
        report["reviews"].append(f"Armature has {len(roots)} root bones; humanoid root policy is unresolved")
    if not mapping:
        report["reviews"].append("No explicit humanoid bone mapping supplied; names were not guessed")
    if missing_roles:
        report["reviews"].append("Required humanoid roles are unmapped")
    if missing_bones:
        report["reviews"].append("Mapped bones are missing from the Armature")

    for role, name in sorted(mapping.items()):
        bone = bones.get(name)
        if bone is None:
            continue
        report["mapped_bones"].append({
            "role": role, "bone": name,
            "parent": bone.parent.name if bone.parent else None,
            "use_deform": bone.use_deform,
            "head_local": list(bone.head_local), "tail_local": list(bone.tail_local),
        })
        if not bone.use_deform:
            report["reviews"].append(f"Mapped role {role} uses non-deform bone {name}")

    hierarchy_failed = False
    for role, parent_role in PARENTS.items():
        if role not in mapping or parent_role not in mapping:
            continue
        child, parent = bones.get(mapping[role]), bones.get(mapping[parent_role])
        if child is None or parent is None:
            continue
        ok = _is_descendant(child, parent)
        report["hierarchy"].append({"role": role, "ancestor_role": parent_role, "ok": ok})
        if not ok:
            hierarchy_failed = True
    if hierarchy_failed:
        report["reviews"].append("Mapped humanoid hierarchy is inconsistent")
    if report["object_animation"] or report["data_animation"]:
        report["reviews"].append("Existing animation is preservation-sensitive")
    report["status"] = ("incomplete" if missing_roles or missing_bones or hierarchy_failed
                        else "ok")
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
