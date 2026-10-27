"""Read-only Blender inspection of explicitly named existing static collider Meshes."""
from __future__ import annotations

import hashlib
import json
import math

import bpy
from mathutils import Vector

from validate_static_collider_request import validate_static_collider_request


SCHEMA = "gameassetai.static-collider-candidate.v1"


def _finite(values):
    return all(math.isfinite(float(value)) for value in values)


def _matrix_values(matrix):
    return [[float(value) for value in row] for row in matrix]


def _mesh_facts(obj):
    mesh = obj.data
    local = [[float(value) for value in vertex.co] for vertex in mesh.vertices]
    if not local or not _finite(value for point in local for value in point):
        raise ValueError(obj.name + " must have finite base vertices")
    matrix = obj.matrix_world
    matrix_values = _matrix_values(matrix)
    if not _finite(value for row in matrix_values for value in row):
        raise ValueError(obj.name + " has a nonfinite world matrix")
    determinant = float(matrix.to_3x3().determinant())
    if not math.isfinite(determinant) or determinant == 0.0:
        raise ValueError(obj.name + " must have a finite nonsingular world transform")
    world = [list(matrix @ Vector(point)) for point in local]
    polygons = [list(polygon.vertices) for polygon in mesh.polygons]
    edge_use = {}
    degenerate_faces = 0
    for vertices in polygons:
        for position, first in enumerate(vertices):
            second = vertices[(position + 1) % len(vertices)]
            key = tuple(sorted((int(first), int(second))))
            edge_use[key] = edge_use.get(key, 0) + 1
        if len(set(vertices)) < 3:
            degenerate_faces += 1
            continue
        normal = Vector((0.0, 0.0, 0.0))
        for position, index in enumerate(vertices):
            current = Vector(local[index])
            following = Vector(local[vertices[(position + 1) % len(vertices)]])
            normal.x += (current.y - following.y) * (current.z + following.z)
            normal.y += (current.z - following.z) * (current.x + following.x)
            normal.z += (current.x - following.x) * (current.y + following.y)
        if normal.length == 0.0:
            degenerate_faces += 1
    low = [min(point[axis] for point in world) for axis in range(3)]
    high = [max(point[axis] for point in world) for axis in range(3)]
    return {"object_name": obj.name, "mesh_name": mesh.name,
            "vertex_count": len(local), "edge_count": len(mesh.edges),
            "polygon_count": len(polygons),
            "triangle_count": sum(max(0, len(vertices) - 2) for vertices in polygons),
            "world_matrix": matrix_values, "world_determinant": determinant,
            "world_bounds": {"minimum": low, "maximum": high},
            "boundary_edge_count": sum(count == 1 for count in edge_use.values()),
            "nonmanifold_edge_count": sum(count != 2 for count in edge_use.values()),
            "degenerate_face_count": degenerate_faces,
            "local_vertices": local, "polygons": polygons}


def _dependencies(obj):
    found = []
    if obj.parent is not None:
        found.append("parent")
    if obj.modifiers:
        found.append("modifiers")
    if obj.constraints:
        found.append("constraints")
    if obj.data.shape_keys is not None:
        found.append("shape_keys")
    if obj.vertex_groups:
        found.append("vertex_groups")
    if obj.animation_data is not None or obj.data.animation_data is not None:
        found.append("animation")
    if obj.library or obj.override_library or obj.data.library or obj.data.override_library:
        found.append("linked_or_override_data")
    return found


def _convex_facts(facts, tolerance_ratio):
    vertices = [Vector(point) for point in facts["local_vertices"]]
    low = [min(point[axis] for point in facts["local_vertices"]) for axis in range(3)]
    high = [max(point[axis] for point in facts["local_vertices"]) for axis in range(3)]
    diagonal = math.sqrt(sum((b - a) ** 2 for a, b in zip(low, high)))
    centroid = sum(vertices, Vector()) / len(vertices)
    maximum = 0.0
    valid_planes = 0
    for indices in facts["polygons"]:
        if len(set(indices)) < 3:
            continue
        normal = Vector((0.0, 0.0, 0.0))
        for position, index in enumerate(indices):
            current = vertices[index]
            following = vertices[indices[(position + 1) % len(indices)]]
            normal.x += (current.y - following.y) * (current.z + following.z)
            normal.y += (current.z - following.z) * (current.x + following.x)
            normal.z += (current.x - following.x) * (current.y + following.y)
        if normal.length == 0.0:
            continue
        normal.normalize(); point = vertices[indices[0]]
        if normal.dot(centroid - point) > 0.0:
            normal.negate()
        maximum = max(maximum, max(normal.dot(vertex - point) for vertex in vertices))
        valid_planes += 1
    ratio = math.inf if diagonal == 0.0 else maximum / diagonal
    closed = (facts["boundary_edge_count"] == 0
              and facts["nonmanifold_edge_count"] == 0
              and facts["polygon_count"] > 0)
    return {"closed_two_manifold": closed, "local_bounds_diagonal": diagonal,
            "valid_face_plane_count": valid_planes,
            "maximum_outside_distance": maximum,
            "maximum_outside_ratio": ratio,
            "tolerance_ratio": float(tolerance_ratio),
            "within_tolerance": (closed and facts["degenerate_face_count"] == 0
                                 and valid_planes == facts["polygon_count"]
                                 and math.isfinite(ratio) and ratio <= tolerance_ratio)}


def _bounds_relation(render, collider):
    rlow, rhigh = render["minimum"], render["maximum"]
    clow, chigh = collider["minimum"], collider["maximum"]
    intersects = all(clow[axis] <= rhigh[axis] and rlow[axis] <= chigh[axis]
                     for axis in range(3))
    return {"intersects": intersects,
            "collider_contains_render_bounds": all(
                clow[axis] <= rlow[axis] and chigh[axis] >= rhigh[axis]
                for axis in range(3)),
            "render_contains_collider_bounds": all(
                rlow[axis] <= clow[axis] and rhigh[axis] >= chigh[axis]
                for axis in range(3))}


def inspect_static_collider_candidate(request, expected_request_sha256=None):
    """Inspect exact base Meshes and return a hash-bound candidate; never mutate Blender."""
    report = {"schema": SCHEMA, "status": "error", "request_sha256": None,
              "source_fingerprint": None, "errors": [], "blockers": [],
              "mutation_authorized": False}
    try:
        preflight = validate_static_collider_request(request)
        report["request_sha256"] = preflight["request_sha256"]
        if preflight["status"] != "ready":
            report["errors"].extend(preflight["errors"])
            return report
        if (expected_request_sha256 is not None
                and expected_request_sha256 != preflight["request_sha256"]):
            report["errors"].append("request fingerprint changed since review")
            return report
        scene = bpy.data.scenes.get(request["scene_name"])
        if scene is None:
            raise ValueError("named Scene is missing")
        names = [request["render_object_name"]] + [item["object_name"]
                                                    for item in request["colliders"]]
        objects = []
        for name in names:
            obj = scene.objects.get(name)
            if obj is None or obj.type != "MESH":
                raise ValueError("named base-Mesh Object is missing from Scene: " + name)
            if bpy.context.mode != "OBJECT" or obj.mode != "OBJECT" or obj.data.is_editmode:
                raise ValueError("Object mode is required for all named Meshes")
            objects.append(obj)
        render_obj, collider_objects = objects[0], objects[1:]
        render_facts = _mesh_facts(render_obj)
        render_dependencies = _dependencies(render_obj)
        if render_dependencies:
            report["blockers"].append({"object_name": render_obj.name,
                                       "reasons": render_dependencies})
        collider_reports = []
        fingerprint_objects = [{"role": "RENDER", "facts": render_facts,
                                "dependencies": render_dependencies}]
        for spec, obj in zip(request["colliders"], collider_objects):
            facts = _mesh_facts(obj)
            dependencies = _dependencies(obj)
            reasons = list(dependencies)
            convex = None
            if spec["collider_kind"] == "CONVEX_MESH_CANDIDATE":
                convex = _convex_facts(facts, spec["convexity_tolerance_ratio"])
                if not convex["within_tolerance"]:
                    reasons.append("convex_candidate_not_closed_or_outside_tolerance")
            if reasons:
                report["blockers"].append({"object_name": obj.name, "reasons": reasons})
            public_facts = {key: value for key, value in facts.items()
                            if key not in ("local_vertices", "polygons")}
            collider_reports.append({"position": len(collider_reports), "id": spec["id"],
                                     "object_name": obj.name,
                                     "collider_kind": spec["collider_kind"],
                                     "mesh": public_facts, "dependencies": dependencies,
                                     "convexity": convex,
                                     "render_bounds_relation": _bounds_relation(
                                         render_facts["world_bounds"], facts["world_bounds"])})
            fingerprint_objects.append({"role": spec["collider_kind"], "id": spec["id"],
                                        "facts": facts, "dependencies": dependencies,
                                        "convexity": convex})
        source = {"request_sha256": preflight["request_sha256"],
                  "scene_name": scene.name, "objects": fingerprint_objects}
        canonical = json.dumps(source, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        report.update({"status": "candidate_for_review", "scene_name": scene.name,
                       "render_object": {key: value for key, value in render_facts.items()
                                         if key not in ("local_vertices", "polygons")},
                       "render_dependencies": render_dependencies,
                       "colliders": collider_reports,
                       "source_fingerprint": hashlib.sha256(
                           canonical.encode("utf-8")).hexdigest(),
                       "limitations": [
                           "Base Meshes only; modifiers and dependency-graph evaluation are refused",
                           "AABB relations do not certify collision coverage or gameplay suitability",
                           "Convex evidence is geometric preflight, not engine import certification"]})
    except (ValueError, TypeError, RuntimeError, OverflowError) as exc:
        report["errors"].append(str(exc))
    return report
