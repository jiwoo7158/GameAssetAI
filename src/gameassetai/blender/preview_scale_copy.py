"""Development analytic preview only. Load inspect_static_transform first."""
import hashlib
import json
import math
from mathutils import Matrix, Vector
import bpy


def preview_scale_copy(object_name, *, geometry_tolerance, scene_name=None):
    report = {"schema": "gameassetai.scale-copy-preview.v1", "status": "error",
              "errors": [], "mutation_authorized": False,
              "scope": "positive_scale_simple_mesh_local_basis", "export_ready": None}
    try:
        if type(geometry_tolerance) not in (int, float) or not math.isfinite(geometry_tolerance) or geometry_tolerance <= 0:
            raise ValueError("Explicit finite positive geometry_tolerance required")
        inspection = inspect_static_transform(object_name, scene_name=scene_name)
        if inspection["status"] != "ok":
            raise ValueError("Transform inspection refused: " + "; ".join(inspection["errors"]))
        scene = bpy.data.scenes[inspection["scene"]]
        obj = scene.objects[object_name]
        mesh = obj.data
        if (obj.parent or obj.children or obj.constraints or obj.modifiers or obj.vertex_groups
                or obj.animation_data or mesh.animation_data or mesh.shape_keys or mesh.has_custom_normals
                or obj.library or mesh.library or obj.override_library or mesh.override_library):
            raise ValueError("Dependent/linked/custom-normal source unsupported")
        if obj.rotation_mode != "XYZ":
            raise ValueError("Initial preview supports XYZ rotation only")
        if (tuple(obj.delta_location) != (0, 0, 0) or tuple(obj.delta_scale) != (1, 1, 1)
                or tuple(obj.delta_rotation_euler) != (0, 0, 0)
                or tuple(obj.delta_rotation_quaternion) != (1, 0, 0, 0)):
            raise ValueError("Delta transforms unsupported")
        scale = tuple(obj.scale)
        if any(value <= 0 for value in scale):
            raise ValueError("Initial preview requires strictly positive scale; reflection/singular handling deferred")
        if not mesh.polygons:
            raise ValueError("Polygon surface required")
        supported = {"position", ".edge_verts", ".corner_vert", ".corner_edge", "material_index",
                     "sharp_face", "sharp_edge", "uv_seam", ".select_vert", ".select_edge", ".select_poly",
                     ".uv_select_face", ".uv_select_vert", ".uv_select_edge", *(uv.name for uv in mesh.uv_layers)}
        if any(a.name not in supported for a in mesh.attributes):
            raise ValueError("Unsupported generic attributes")
        predicted_basis = Matrix.LocRotScale(obj.location, obj.rotation_euler.to_quaternion(), Vector((1, 1, 1)))
        basis = obj.matrix_basis.copy()
        predicted_vertices = [Vector(tuple(v.co[i] * scale[i] for i in range(3))) for v in mesh.vertices]
        before_positions = [basis @ v.co for v in mesh.vertices]
        after_positions = [predicted_basis @ v for v in predicted_vertices]
        if not all(math.isfinite(x) for vectors in (predicted_vertices, before_positions, after_positions)
                   for vector in vectors for x in vector):
            raise ValueError("Nonfinite predicted coordinates")
        residual = max((a - b).length for a, b in zip(before_positions, after_positions))
        if not math.isfinite(residual) or residual > geometry_tolerance:
            raise ValueError("Predicted local-basis positions exceed explicit tolerance")
        # Bind Scene and effective parameters as well as data: not an apply authorization.
        state = {"scene": scene.name, "object": obj.name, "mesh": mesh.name,
                 "transform": inspection["raw_transform"], "rotation_mode": obj.rotation_mode,
                 "basis": [list(row) for row in basis],
                 "parent_inverse": [list(row) for row in obj.matrix_parent_inverse],
                 "vertices": [list(v.co) for v in mesh.vertices],
                 "edges": [[list(e.vertices), e.use_seam, e.use_edge_sharp] for e in mesh.edges],
                 "faces": [[list(p.vertices), p.material_index, p.use_smooth] for p in mesh.polygons],
                 "uv": [[layer.name, layer.active_render, [list(item.uv) for item in layer.data]] for layer in mesh.uv_layers],
                 "active_uv": mesh.uv_layers.active_index,
                 "materials": [[slot.link, slot.material.name if slot.material else None] for slot in obj.material_slots],
                 "parameters": {"geometry_tolerance": float(geometry_tolerance)}}
        digest = hashlib.sha256(json.dumps(state, sort_keys=True, allow_nan=False).encode()).hexdigest()
        predicted = [list(v) for v in predicted_vertices]
        report.update(status="no_change" if scale == (1, 1, 1) else "preview",
                      object=obj.name, scene=scene.name, source_sha256=digest,
                      parameters=state["parameters"], before_scale=list(scale), predicted_scale=[1, 1, 1],
                      predicted_vertices=predicted, predicted_basis=[list(row) for row in predicted_basis],
                      maximum_local_basis_position_error=residual,
                      limitations=["Analytic local-basis prediction, not evaluated world/normal/tangent validation",
                                   "No copy is created; pivot/location/rotation are not requested to change",
                                   "Shared materials are references, not a deep backup",
                                   "No apply API or engine readiness certificate"])
    except (ValueError, TypeError, RuntimeError, OverflowError) as exc:
        report["errors"].append(str(exc))
    return report


def verify_scale_preview(object_name, *, expected_source_sha256, geometry_tolerance, scene_name=None):
    report = preview_scale_copy(object_name, geometry_tolerance=geometry_tolerance, scene_name=scene_name)
    if report["status"] in ("preview", "no_change"):
        if not isinstance(expected_source_sha256, str) or report["source_sha256"] != expected_source_sha256:
            report.update(status="error", errors=["Preview fingerprint missing/stale; re-preview"])
        else:
            report["freshness"] = "matches_current_supported_snapshot"
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
