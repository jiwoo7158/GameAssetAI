"""Development-only explicit local pivot prediction; load transform/scale preview first."""
import hashlib
import json
import math
import bpy
from mathutils import Matrix, Vector


def preview_pivot_copy(object_name, *, local_pivot, geometry_tolerance, scene_name=None):
    report = {"schema": "gameassetai.pivot-copy-preview.v1", "status": "error",
              "errors": [], "mutation_authorized": False, "export_ready": None,
              "basis": "reported_base_world_no_dependency_refresh"}
    try:
        if (not isinstance(local_pivot, (list, tuple)) or len(local_pivot) != 3
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in local_pivot)):
            raise ValueError("Explicit finite three-coordinate local_pivot required")
        eligibility = preview_scale_copy(object_name, geometry_tolerance=geometry_tolerance,
                                         scene_name=scene_name)
        if eligibility["status"] not in ("preview", "no_change"):
            raise ValueError("Static source refused: " + "; ".join(eligibility["errors"]))
        obj = bpy.data.scenes[eligibility["scene"]].objects[object_name]
        point = Vector(local_pivot)
        world = obj.matrix_world.copy()
        basis = obj.matrix_basis.copy()
        # Moving the origin is not translating the visible asset or choosing its center.
        predicted_basis = basis @ Matrix.Translation(point)
        shifted = [v.co - point for v in obj.data.vertices]
        before = [world @ v.co for v in obj.data.vertices]
        after = [predicted_basis @ v for v in shifted]
        origin = world @ point
        numbers = [x for vectors in (shifted, before, after, [origin]) for v in vectors for x in v]
        numbers += [x for row in predicted_basis for x in row]
        if not all(math.isfinite(x) for x in numbers):
            raise ValueError("Nonfinite pivot prediction")
        residual = max((a - b).length for a, b in zip(before, after))
        pivot_error = (predicted_basis.translation - origin).length
        if not (math.isfinite(residual) and residual <= geometry_tolerance
                and math.isfinite(pivot_error) and pivot_error <= geometry_tolerance):
            raise ValueError("Reported world/basis or pivot prediction exceeds explicit tolerance")
        state = {"base_source_sha256": eligibility["source_sha256"],
                 "world": [list(row) for row in world], "local_pivot": list(local_pivot)}
        digest = hashlib.sha256(json.dumps(state, sort_keys=True, allow_nan=False).encode()).hexdigest()
        report.update(status="no_change" if all(v == 0 for v in local_pivot) else "preview",
                      object=obj.name, scene=eligibility["scene"], source_sha256=digest,
                      local_pivot=list(local_pivot), geometry_tolerance=float(geometry_tolerance),
                      predicted_vertices=[list(v) for v in shifted],
                      predicted_basis=[list(row) for row in predicted_basis],
                      predicted_world_origin=list(origin), maximum_position_error=residual,
                      pivot_position_error=pivot_error,
                      scale_preserved=list(obj.scale),
                      limitations=["Explicit base-mesh local point; no center/bottom policy inferred",
                                   "Same narrow independent static positive-scale XYZ eligibility as scale preview",
                                   "No IDs/copy/apply/graph refresh; reported world may be stale",
                                   "No engine, shading, conditioning or concurrency certificate"])
    except (ValueError, TypeError, RuntimeError, OverflowError) as exc:
        report["errors"].append(str(exc))
    return report


def verify_pivot_preview(object_name, *, expected_source_sha256, **parameters):
    report = preview_pivot_copy(object_name, **parameters)
    if report["status"] in ("preview", "no_change"):
        if not isinstance(expected_source_sha256, str) or report["source_sha256"] != expected_source_sha256:
            report.update(status="error", errors=["Pivot preview fingerprint missing/stale; re-preview"])
        else:
            report["freshness"] = "matches_current_supported_snapshot"
    return report

