"""Read-only mesh diagnostics, executed inside Blender through an external MCP."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
import bpy


def _diagnostic_constraints(constraints):
    if constraints is None:
        return {}
    if not isinstance(constraints, dict):
        raise ValueError("constraints must be a dictionary or None")
    allowed = {"max_triangles", "max_materials", "require_uv", "closed_surface"}
    if set(constraints) - allowed:
        raise ValueError("Unsupported constraints: " + str(sorted(set(constraints) - allowed)))
    for key, value in constraints.items():
        if key.startswith("max_"):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a nonnegative integer")
        elif not isinstance(value, bool):
            raise ValueError(f"{key} must be an explicit boolean")
    return dict(constraints)


def _diagnostic_metrics(mesh):
    coordinates = [tuple(v.co) for v in mesh.vertices]
    finite = all(math.isfinite(value) for point in coordinates for value in point)
    edge_uses = defaultdict(list)
    vertex_edges = Counter()
    edge_keys = []
    for edge in mesh.edges:
        key = tuple(sorted(edge.vertices))
        edge_keys.append(key)
        for vertex in edge.vertices:
            vertex_edges[vertex] += 1
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for a, b in zip(vertices, vertices[1:] + vertices[:1]):
            edge_uses[tuple(sorted((a, b)))].append((a, b))
    if finite:
        mesh.calc_loop_triangles()
    uvs_finite = all(math.isfinite(value) for layer in mesh.uv_layers
                     for item in layer.data for value in item.uv)
    return {
        "vertices": len(mesh.vertices), "edges": len(mesh.edges), "polygons": len(mesh.polygons),
        "triangles": len(mesh.loop_triangles) if finite else None,
        "coordinates_finite": finite, "uv_layers": len(mesh.uv_layers), "uv_values_finite": uvs_finite,
        "boundary_edges": sum(len(edge_uses[key]) == 1 for key in edge_keys),
        "wire_edges": sum(len(edge_uses[key]) == 0 for key in edge_keys),
        "overconnected_edges": sum(len(edge_uses[key]) > 2 for key in edge_keys),
        "loose_vertices": sum(vertex_edges[i] == 0 for i in range(len(mesh.vertices))),
        "inconsistent_winding_edges": sum(len(edge_uses[key]) == 2
                                          and edge_uses[key][0] == edge_uses[key][1] for key in edge_keys),
        "duplicate_edge_keys": len(edge_keys) - len(set(edge_keys)),
        "coincident_vertex_coordinates": len(coordinates) - len(set(coordinates)) if finite else None,
        "zero_length_edges": sum((mesh.vertices[e.vertices[0]].co - mesh.vertices[e.vertices[1]].co)
                                 .length_squared == 0 for e in mesh.edges) if finite else None,
        "zero_area_polygons": sum(p.area == 0 for p in mesh.polygons) if finite else None,
        "ngons": sum(len(p.vertices) > 4 for p in mesh.polygons),
    }


def _diagnostic_has_animation(owner):
    data = getattr(owner, "animation_data", None)
    return bool(data and (data.action or len(data.nla_tracks) or len(data.drivers)))


def _diagnostic_evaluation_blockers():
    # Graph refresh can write animated source properties, even during a read query.
    # File-wide conservative guard includes dependencies outside the target Scene.
    owners = set(bpy.data.user_map())
    owners.update(owner.node_tree for owner in list(owners)
                  if getattr(owner, "node_tree", None) is not None)
    blockers = []
    for owner in owners:
        pose = getattr(owner, "pose", None)
        if (_diagnostic_has_animation(owner) or len(getattr(owner, "constraints", ()))
                or (pose and any(len(bone.constraints) for bone in pose.bones))):
            blockers.append(owner.name_full)
    return sorted(blockers)


def diagnose_mesh(object_name, scene_name=None, constraints=None, evaluate=False):
    report = {"schema": "gameassetai.mesh-diagnostics.v1", "status": "error", "errors": [],
              "findings": [], "verdict": "unverified"}
    try:
        constraints = _diagnostic_constraints(constraints)
        if not isinstance(object_name, str) or not object_name:
            raise ValueError("An explicit nonempty object name is required")
        if not isinstance(evaluate, bool):
            raise ValueError("evaluate must be a boolean")
        scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
        if scene is None:
            raise ValueError(f"Scene not found: {scene_name}")
        obj = scene.objects.get(object_name)
        if obj is None:
            raise ValueError(f"Object not found in scene: {object_name}")
        if obj.type != "MESH":
            raise ValueError(f"Target is not a mesh: {obj.name} ({obj.type})")
        if obj.data.is_editmode:
            raise ValueError("Edit-mode data is unverified; no mode change or edit flush performed")
        if evaluate and scene != bpy.context.scene:
            raise ValueError("Evaluated diagnostics require the current Scene")
        if evaluate:
            blockers = _diagnostic_evaluation_blockers()
            if blockers:
                raise ValueError("Viewport evaluation blocked by animation/drivers/constraints in file; "
                                 "use base diagnostics. Blockers: " + str(blockers))
        report.update({"object": obj.name, "scene": scene.name, "blender_version": bpy.app.version_string,
                       "basis": "viewport_evaluated" if evaluate else "base",
                       "supplied_constraints": constraints,
                       "unrequested_constraints": sorted({"max_triangles", "max_materials", "require_uv",
                                                           "closed_surface"} - set(constraints))})
        evaluated = None
        try:
            mesh = obj.data
            if evaluate:
                depsgraph = bpy.context.evaluated_depsgraph_get()
                evaluated = obj.evaluated_get(depsgraph)
                mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                if mesh is None:
                    raise RuntimeError("Evaluation did not produce a mesh")
            metrics = _diagnostic_metrics(mesh)
            report["metrics"] = metrics
        finally:
            if evaluated is not None:
                evaluated.to_mesh_clear()

        def finding(code, severity, detail):
            report["findings"].append({"code": code, "severity": severity, "detail": detail})

        world_finite = all(math.isfinite(value) for row in obj.matrix_world for value in row)
        determinant = float(obj.matrix_world.to_3x3().determinant()) if world_finite else None
        determinant_finite = determinant is None or math.isfinite(determinant)
        scale_finite = all(math.isfinite(value) for value in obj.scale)
        report["transform"] = {"world_values_finite": world_finite,
                               "world_determinant": determinant if determinant_finite else None,
                               "local_scale": [value if math.isfinite(value) else None for value in obj.scale]}
        if not scale_finite:
            finding("nonfinite_local_scale", "error", "Nonfinite local scale values were encoded as null")
        if not determinant_finite:
            finding("nonfinite_transform_determinant", "error", "Computed determinant is not representable")
        if not world_finite:
            finding("nonfinite_transform", "error", "World matrix contains nonfinite values")
        elif determinant == 0:
            finding("noninvertible_transform", "error", "World transform is singular")
        elif determinant < 0:
            finding("mirrored_world_transform", "review", "Review winding/export conventions; do not auto-apply")
        if any(abs(value - 1) > 1e-6 for value in obj.scale):
            finding("unapplied_local_scale", "review", "Applying scale would modify data; no correction performed")
        if metrics["polygons"] == 0:
            finding("empty_surface", "error", "Mesh has no polygon faces")
        if not metrics["coordinates_finite"]:
            finding("nonfinite_coordinates", "error", "Topology area/triangle checks were withheld")
        if not metrics["uv_values_finite"]:
            finding("nonfinite_uvs", "error", "UV coordinates contain nonfinite values")
        for key in ("zero_area_polygons", "zero_length_edges"):
            if metrics[key]:
                finding(key, "error", f"Count: {metrics[key]}")
        for key in ("boundary_edges", "wire_edges", "overconnected_edges", "loose_vertices",
                    "inconsistent_winding_edges", "duplicate_edge_keys", "coincident_vertex_coordinates", "ngons"):
            if metrics[key]:
                finding(key, "review", f"Count: {metrics[key]}; may be intentional depending on asset role")
        material_count = len(obj.material_slots)
        report["material_slots"] = material_count
        if not material_count or any(slot.material is None for slot in obj.material_slots):
            finding("missing_material_assignment", "review", "Material-free/vertex-color pipelines may be intentional")
        if obj.data.users > 1:
            finding("shared_mesh_data", "review", "Preserve all linked users during any future modification")
        sensitive = bool(obj.data.shape_keys or _diagnostic_has_animation(obj)
                         or _diagnostic_has_animation(obj.data)
                         or (obj.parent and obj.parent.type == "ARMATURE")
                         or any(mod.type == "ARMATURE" for mod in obj.modifiers))
        report["preservation_sensitive"] = sensitive
        if sensitive:
            finding("rig_shape_or_animation_data", "review", "Cannot certify this asset as static; preserve existing inputs")
        if obj.modifiers and not evaluate:
            finding("modifiers_not_evaluated", "review", "Reported topology is base mesh, not final output")
        if evaluate:
            finding("viewport_basis_only", "info", "Viewport evaluation is not render/engine/export evaluation")
        if "max_triangles" in constraints:
            if metrics["triangles"] is None:
                finding("triangle_budget_unverified", "error", "No verified triangle count")
            elif metrics["triangles"] > constraints["max_triangles"]:
                finding("triangle_budget_exceeded", "error", f"{metrics['triangles']} > {constraints['max_triangles']}")
        if "max_materials" in constraints and material_count > constraints["max_materials"]:
            finding("material_budget_exceeded", "error", f"{material_count} > {constraints['max_materials']}")
        if constraints.get("require_uv") and metrics["uv_layers"] == 0:
            finding("required_uv_missing", "error", "Supplied constraint requires at least one UV layer")
        if constraints.get("closed_surface") and any(metrics[key] for key in
                ("boundary_edges", "wire_edges", "overconnected_edges", "duplicate_edge_keys")):
            finding("required_closed_surface_failed", "error", "Edge-incidence closure check failed")
        severities = {item["severity"] for item in report["findings"]}
        report["verdict"] = "issues" if "error" in severities else "needs_review" if "review" in severities else "no_findings"
        report["status"] = "ok"
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    return report
