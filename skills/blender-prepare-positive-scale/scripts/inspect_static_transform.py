"""Development-only read-only transform snapshot; no apply, evaluation or export."""
import math
import bpy


def inspect_static_transform(object_name, *, scene_name=None):
    report = {"schema": "gameassetai.transform-preflight.v1", "status": "error",
              "errors": [], "mutation_authorized": False, "export_ready": None,
              "basis": "reported_base_state_no_dependency_refresh",
              "freshness": "snapshot_only", "review_items": []}
    try:
        if not isinstance(object_name, str) or not object_name:
            raise ValueError("Explicit object name required")
        if scene_name is not None and (not isinstance(scene_name, str) or not scene_name):
            raise ValueError("Invalid scene name")
        scene = bpy.data.scenes.get(scene_name) if scene_name is not None else bpy.context.scene
        if scene is None:
            raise ValueError("Scene missing")
        obj = scene.objects.get(object_name)
        if obj is None or obj.type != "MESH":
            raise ValueError("Named mesh missing from target Scene")
        if bpy.context.mode != "OBJECT" or obj.mode != "OBJECT" or obj.data.is_editmode:
            raise ValueError("Object mode required; edit data is not flushed")
        raw = {key: list(getattr(obj, key)) for key in
               ("location", "scale", "rotation_euler", "rotation_quaternion",
                "rotation_axis_angle", "delta_location", "delta_scale",
                "delta_rotation_euler", "delta_rotation_quaternion")}
        matrices = {key: [list(row) for row in getattr(obj, key)] for key in
                    ("matrix_basis", "matrix_parent_inverse", "matrix_world")}
        coordinates = [list(v.co) for v in obj.data.vertices]
        numbers = [value for vector in raw.values() for value in vector]
        numbers += [value for matrix in matrices.values() for row in matrix for value in row]
        numbers += [value for vector in coordinates for value in vector]
        if not all(math.isfinite(value) for value in numbers):
            raise ValueError("Nonfinite raw transform, reported matrix or vertex coordinate")
        determinant = obj.matrix_world.to_3x3().determinant()
        if not math.isfinite(determinant):
            raise ValueError("Nonfinite reported world determinant")
        # Exact predicates only; no implicit game/scale tolerance or near-zero certificate.
        scale = raw["scale"]
        reviews = []
        if scale != [1.0, 1.0, 1.0]:
            reviews.append("nonunit_local_scale")
        if len(set(abs(value) for value in scale)) > 1:
            reviews.append("nonuniform_local_scale")
        if determinant < 0:
            reviews.append("reported_world_reflection")
        if determinant == 0:
            reviews.append("reported_world_singular")
        if any(value == 0 for value in scale):
            reviews.append("zero_local_scale")
        if obj.parent is not None:
            reviews.append("parent_dependency")
        if obj.constraints or obj.modifiers:
            reviews.append("constraints_or_modifiers_not_evaluated")
        if obj.data.shape_keys or obj.vertex_groups or obj.animation_data or obj.data.animation_data:
            reviews.append("preservation_sensitive_bindings")
        if obj.library or obj.override_library or obj.data.library or obj.data.override_library:
            reviews.append("linked_or_override_data")
        if not coordinates:
            reviews.append("empty_mesh")
        bounds = None
        if coordinates:
            low = [min(v[axis] for v in coordinates) for axis in range(3)]
            high = [max(v[axis] for v in coordinates) for axis in range(3)]
            center = [(a + b) / 2 for a, b in zip(low, high)]
            if not all(math.isfinite(value) for value in center):
                raise ValueError("Nonfinite bounds center")
            bounds = {"minimum": low, "maximum": high, "center": center}
        report.update({"status": "ok", "object": obj.name, "scene": scene.name,
                       "rotation_mode": obj.rotation_mode, "raw_transform": raw,
                       "reported_matrices": matrices, "reported_world_determinant": determinant,
                       "local_base_bounds": bounds, "local_origin": [0.0, 0.0, 0.0],
                       "parent": obj.parent.name if obj.parent else None,
                       "review_items": reviews,
                       "limitations": ["Reported matrices can be stale without dependency refresh",
                           "Exact zero test does not certify numerical conditioning",
                           "Bounds use base vertices, not modifiers, deformation or engine geometry",
                           "Pivot placement requires user/Profile intent; bounds center is not a target"]})
    except (ValueError, TypeError, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report
