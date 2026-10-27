"""Read-only Blender inspection of an explicitly ordered existing static LOD chain."""
from __future__ import annotations

import hashlib
import json
import math

import bpy
from mathutils import Vector

from validate_static_lod_chain_request import validate_static_lod_chain_request


SCHEMA = "gameassetai.static-lod-chain-candidate.v1"


def _finite(values):
    return all(math.isfinite(float(value)) for value in values)


def _dependencies(obj):
    found = []
    if obj.parent is not None: found.append("parent")
    if obj.modifiers: found.append("modifiers")
    if obj.constraints: found.append("constraints")
    if obj.data.shape_keys is not None: found.append("shape_keys")
    if obj.vertex_groups: found.append("vertex_groups")
    if obj.animation_data is not None or obj.data.animation_data is not None:
        found.append("animation")
    if obj.library or obj.override_library or obj.data.library or obj.data.override_library:
        found.append("linked_or_override_data")
    return found


def _facts(obj):
    mesh = obj.data
    local = [[float(value) for value in vertex.co] for vertex in mesh.vertices]
    polygons = [{"vertices": list(polygon.vertices),
                 "material_index": int(polygon.material_index)} for polygon in mesh.polygons]
    if not local or not polygons or not _finite(v for point in local for v in point):
        raise ValueError(obj.name + " must have nonempty finite base geometry")
    matrix = [[float(value) for value in row] for row in obj.matrix_world]
    if not _finite(v for row in matrix for v in row):
        raise ValueError(obj.name + " has a nonfinite world matrix")
    determinant = float(obj.matrix_world.to_3x3().determinant())
    if not math.isfinite(determinant) or determinant == 0.0:
        raise ValueError(obj.name + " must have a finite nonsingular world transform")
    world = [list(obj.matrix_world @ Vector(point)) for point in local]
    low = [min(point[axis] for point in world) for axis in range(3)]
    high = [max(point[axis] for point in world) for axis in range(3)]
    center = [(a + b) / 2.0 for a, b in zip(low, high)]
    extents = [(b - a) / 2.0 for a, b in zip(low, high)]
    return {"object_name": obj.name, "mesh_name": mesh.name,
            "vertex_count": len(local), "edge_count": len(mesh.edges),
            "polygon_count": len(polygons),
            "triangle_count": sum(max(0, len(p["vertices"]) - 2) for p in polygons),
            "world_matrix": matrix, "world_determinant": determinant,
            "world_bounds": {"minimum": low, "maximum": high,
                             "center": center, "half_extents": extents},
            "material_slots": [slot.material.name if slot.material else None
                               for slot in obj.material_slots],
            "local_vertices": local, "polygons": polygons}


def _public(facts):
    return {key: value for key, value in facts.items()
            if key not in ("local_vertices", "polygons")}


def inspect_static_lod_chain_candidate(request, expected_request_sha256=None):
    """Return one hash-bound read-only LOD-chain candidate report."""
    report = {"schema": SCHEMA, "status": "error", "request_sha256": None,
              "source_fingerprint": None, "errors": [], "blockers": [],
              "review_items": [], "mutation_authorized": False}
    try:
        preflight = validate_static_lod_chain_request(request)
        report["request_sha256"] = preflight["request_sha256"]
        if preflight["status"] != "ready":
            report["errors"].extend(preflight["errors"]); return report
        if (expected_request_sha256 is not None
                and expected_request_sha256 != preflight["request_sha256"]):
            report["errors"].append("request fingerprint changed since review"); return report
        scene = bpy.data.scenes.get(request["scene_name"])
        if scene is None: raise ValueError("named Scene is missing")
        objects = []
        for level in request["levels"]:
            obj = scene.objects.get(level["object_name"])
            if obj is None or obj.type != "MESH":
                raise ValueError("named base-Mesh Object is missing from Scene: "
                                 + level["object_name"])
            if bpy.context.mode != "OBJECT" or obj.mode != "OBJECT" or obj.data.is_editmode:
                raise ValueError("Object mode is required for all named LOD Meshes")
            objects.append(obj)
        facts = [_facts(obj) for obj in objects]
        base = facts[0]
        base_matrix = base["world_matrix"]
        base_triangles = base["triangle_count"]
        base_center = Vector(base["world_bounds"]["center"])
        base_extents = base["world_bounds"]["half_extents"]
        base_diagonal = 2.0 * math.sqrt(sum(value * value for value in base_extents))
        level_reports, fingerprint_levels = [], []
        previous_triangles = None
        for spec, obj, item in zip(request["levels"], objects, facts):
            dependencies = _dependencies(obj)
            reasons = list(dependencies)
            matrix_matches = item["world_matrix"] == base_matrix
            if not matrix_matches: reasons.append("world_matrix_differs_from_lod0")
            triangles = item["triangle_count"]
            decreases = previous_triangles is None or triangles < previous_triangles
            if not decreases: reasons.append("triangle_count_not_strictly_decreasing")
            if triangles <= 0: reasons.append("no_base_triangles")
            if reasons:
                report["blockers"].append({"level_index": spec["level_index"],
                                           "object_name": obj.name, "reasons": reasons})
            center_offset = (Vector(item["world_bounds"]["center"]) - base_center).length
            relation = {"world_matrix_matches_lod0": matrix_matches,
                        "triangle_count_decreases_from_previous": decreases,
                        "triangle_ratio_to_lod0": triangles / base_triangles,
                        "triangle_ratio_to_previous": (None if previous_triangles is None
                                                       else triangles / previous_triangles),
                        "bounds_center_offset": center_offset,
                        "bounds_center_offset_ratio_to_lod0_diagonal": (
                            None if base_diagonal == 0.0 else center_offset / base_diagonal),
                        "half_extent_ratios_to_lod0": [
                            None if base_extents[axis] == 0.0
                            else item["world_bounds"]["half_extents"][axis] / base_extents[axis]
                            for axis in range(3)],
                        "material_slots_match_lod0": item["material_slots"] == base["material_slots"]}
            if not relation["material_slots_match_lod0"]:
                report["review_items"].append({"level_index": spec["level_index"],
                                               "reason": "material_slots_differ_from_lod0"})
            level_reports.append({"level_index": spec["level_index"],
                                  "object_name": obj.name, "mesh": _public(item),
                                  "dependencies": dependencies, "relation_to_lod0": relation})
            fingerprint_levels.append({"level_index": spec["level_index"],
                                       "facts": item, "dependencies": dependencies})
            previous_triangles = triangles
        canonical = json.dumps({"request_sha256": preflight["request_sha256"],
                                "scene_name": scene.name, "levels": fingerprint_levels},
                               sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        report.update({"status": "candidate_for_review", "scene_name": scene.name,
                       "levels": level_reports,
                       "source_fingerprint": hashlib.sha256(
                           canonical.encode("utf-8")).hexdigest(),
                       "limitations": [
                           "Base Meshes only; modifiers and dependency-graph evaluation are refused",
                           "Bounds and triangle ratios do not certify silhouette or visual quality",
                           "No engine screen thresholds, import settings or runtime cost are validated"]})
    except (ValueError, TypeError, RuntimeError, OverflowError, ZeroDivisionError) as exc:
        report["errors"].append(str(exc))
    return report
