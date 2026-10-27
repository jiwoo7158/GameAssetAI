import hashlib
import json
import math

import bpy

from validate_character_joint_weight_copy_request import validate_request


CHARACTER_OWNER_KEY = "gameassetai_character_owner"
RIG_OWNER_KEY = "gameassetai_rig_owner"


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _group_weight(obj, vertex, name):
    group = obj.vertex_groups.get(name)
    if group is None:
        return 0.0
    for item in vertex.groups:
        if item.group == group.index:
            return float(item.weight)
    return 0.0


def _source_facts(obj, arm):
    return {
        "object_name": obj.name,
        "mesh_name": obj.data.name,
        "armature_object_name": arm.name,
        "vertex_count": len(obj.data.vertices),
        "edge_count": len(obj.data.edges),
        "polygon_count": len(obj.data.polygons),
        "geometry": [[float(x) for x in vertex.co] for vertex in obj.data.vertices],
        "groups": {group.name: [[vertex.index, _group_weight(obj, vertex, group.name)]
                                  for vertex in obj.data.vertices
                                  if _group_weight(obj, vertex, group.name) > 0.0]
                   for group in obj.vertex_groups},
        "matrix_world": [[float(x) for x in row] for row in obj.matrix_world],
        "modifier": [[modifier.name, modifier.type,
                       modifier.object.name if modifier.type == "ARMATURE" and modifier.object else None]
                      for modifier in obj.modifiers],
    }


def _plan(obj, request, proportions):
    h = float(proportions["height"])
    shoulder_x = h * float(proportions["shoulder_width_ratio"]) * 0.46
    width = h * float(request["adjustment"]["transition_width_ratio"])
    joint = request["adjustment"]["joint"]
    requested_side = request["adjustment"]["side"]
    sides = ("L", "R") if requested_side == "BOTH" else (("L",) if requested_side == "LEFT" else ("R",))
    changes = []
    target_names = set()
    for side in sides:
        if joint == "SHOULDER":
            first, second = "chest", f"upper_arm.{side}"
            boundary = -shoulder_x * 0.10
        else:
            first, second = f"thigh.{side}", "pelvis"
            boundary = h * 0.49
        target_names.update((first, second))
        for vertex in obj.data.vertices:
            x, _y, z = vertex.co
            if (side == "L" and x < 0) or (side == "R" and x >= 0):
                continue
            value = abs(float(x)) - shoulder_x if joint == "SHOULDER" else float(z)
            if abs(value - boundary) > width:
                continue
            old_first = _group_weight(obj, vertex, first)
            old_second = _group_weight(obj, vertex, second)
            total = old_first + old_second
            if total <= 1e-8:
                continue
            t = (value - (boundary - width)) / (2.0 * width)
            t = max(0.0, min(1.0, t)); t = t * t * (3.0 - 2.0 * t)
            changes.append({"vertex": vertex.index, "first": first, "second": second,
                            "old": [old_first, old_second],
                            "new": [total * (1.0 - t), total * t]})
    proposed = {item["vertex"]: item for item in changes}
    affected_edges = []
    before_max = after_max = 0.0
    for edge in obj.data.edges:
        a, b = edge.vertices
        if a not in proposed or b not in proposed:
            continue
        left, right = proposed[a], proposed[b]
        if left["second"] != right["second"]:
            continue
        before = abs(left["old"][1] - right["old"][1])
        after = abs(left["new"][1] - right["new"][1])
        before_max = max(before_max, before); after_max = max(after_max, after)
        affected_edges.append((a, b))
    return {"changes": changes, "target_group_names": sorted(target_names),
            "affected_vertex_count": len(changes), "affected_edge_count": len(affected_edges),
            "before_max_target_weight_edge_delta": before_max,
            "after_max_target_weight_edge_delta": after_max,
            "transition_width_world": width}


def preview_character_joint_weight_copy(request, expected_request_sha256=None):
    report = {"status": "error", "errors": [], "blockers": [], "request_sha256": None,
              "source_fingerprint": None, "setup_fingerprint": None,
              "preview_fingerprint": None, "persistent_output_created": False}
    try:
        validated = validate_request(request); data = validated["request"]
        report["request_sha256"] = validated["request_sha256"]
        if expected_request_sha256 and expected_request_sha256 != report["request_sha256"]:
            raise ValueError("request fingerprint changed since review")
        scene = bpy.data.scenes.get(data["scene_name"])
        obj = scene.objects.get(data["source_object_name"]) if scene else None
        arm = scene.objects.get(data["armature_object_name"]) if scene else None
        if obj is None or obj.type != "MESH" or arm is None or arm.type != "ARMATURE":
            raise ValueError("explicit Scene, Mesh and Armature must exist")
        if not obj.get(CHARACTER_OWNER_KEY) or "gameassetai_character_request" not in obj:
            report["blockers"].append("source_is_not_owned_character_base")
        if not arm.get(RIG_OWNER_KEY) or not arm.data.get(RIG_OWNER_KEY):
            report["blockers"].append("armature_is_not_owned_character_rig")
        modifiers = [m for m in obj.modifiers if m.type == "ARMATURE"]
        if len(obj.modifiers) != 1 or len(modifiers) != 1 or modifiers[0].object != arm:
            report["blockers"].append("exact_owned_armature_modifier_required")
        if bpy.data.objects.get(data["output_object_name"]): report["blockers"].append("output_object_exists")
        if bpy.data.meshes.get(data["output_mesh_name"]): report["blockers"].append("output_mesh_exists")
        character = json.loads(obj["gameassetai_character_request"])
        plan = _plan(obj, data, character["proportions"])
        if plan["affected_vertex_count"] == 0:
            report["blockers"].append("adjustment_affects_no_vertices")
        facts = _source_facts(obj, arm)
        report["source_fingerprint"] = _sha(facts)
        setup = {"request_sha256": report["request_sha256"],
                 "source_fingerprint": report["source_fingerprint"],
                 "adjustment": data["adjustment"], "target_groups": plan["target_group_names"]}
        report["setup_fingerprint"] = _sha(setup)
        public_plan = {key: value for key, value in plan.items() if key != "changes"}
        report["preview_fingerprint"] = _sha({"setup": report["setup_fingerprint"], "plan": plan})
        report.update({"status": "candidate_for_review", "scene_name": scene.name,
                       "source_object_name": obj.name, "armature_object_name": arm.name,
                       "intended_output": {"object_name": data["output_object_name"],
                                           "mesh_name": data["output_mesh_name"]},
                       "adjustment_preview": public_plan,
                       "limitations": ["Weight-edge delta is not a deformation-quality certificate",
                                       "Geometry, materials and Armature are preserved/shared"]})
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        report["errors"].append(str(exc))
    return report
