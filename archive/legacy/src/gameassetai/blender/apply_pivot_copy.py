"""Development-only copy apply; load scale apply and pivot preview helpers first."""
import uuid
import bpy
from mathutils import Matrix, Vector


def _pivot_file_blockers():
    owners = set(bpy.data.user_map())
    owners.update(owner.node_tree for owner in list(owners)
                  if getattr(owner, "node_tree", None) is not None)
    return sorted(owner.name_full for owner in owners
                  if getattr(owner, "animation_data", None)
                  or len(getattr(owner, "constraints", ()))
                  or (getattr(owner, "pose", None) and
                      any(len(b.constraints) for b in owner.pose.bones)))


def _pivot_surface(obj):
    mesh = obj.data
    return {"edges": [[list(e.vertices), e.use_seam, e.use_edge_sharp] for e in mesh.edges],
            "faces": [[list(p.vertices), p.material_index, p.use_smooth] for p in mesh.polygons],
            "uv": [[layer.name, layer.active_render, [list(item.uv) for item in layer.data]] for layer in mesh.uv_layers],
            "active_uv": mesh.uv_layers.active_index,
            "materials": [(slot.link, slot.material) for slot in obj.material_slots]}


def _pivot_write(mesh, point):
    mesh.transform(Matrix.Translation(-Vector(point)))


def _pivot_link(scene, obj):
    scene.collection.objects.link(obj)


def apply_pivot_copy(object_name, *, local_pivot, geometry_tolerance,
                     expected_source_sha256, result_name, authorized=False, scene_name=None):
    report = {"schema": "gameassetai.pivot-copy-apply.v1", "status": "error", "errors": []}
    copied_object = copied_mesh = None
    token = uuid.uuid4().hex
    try:
        if authorized is not True:
            raise ValueError("Explicit apply authorization required")
        if (not isinstance(result_name, str) or not result_name or "\x00" in result_name
                or len(result_name.encode("utf-8")) > 63 or result_name in bpy.data.objects):
            raise ValueError("Unused explicit <=63 UTF-8 byte result name required")
        if _pivot_file_blockers():
            raise ValueError("File-wide animation/constraint blockers; no graph refresh allowed")
        parameters = dict(local_pivot=local_pivot, geometry_tolerance=geometry_tolerance, scene_name=scene_name)
        preview = verify_pivot_preview(object_name, expected_source_sha256=expected_source_sha256, **parameters)
        if preview["status"] not in ("preview", "no_change"):
            raise ValueError("; ".join(preview["errors"]))
        if preview["status"] == "no_change":
            report.update(status="no_change", source_sha256=preview["source_sha256"])
            return report
        scene = bpy.data.scenes[preview["scene"]]
        source = scene.objects[object_name]
        world = source.matrix_world.copy()
        surface = _pivot_surface(source)
        raw = inspect_static_transform(object_name, scene_name=scene.name)["raw_transform"]
        positions = [world @ v.co for v in source.data.vertices]
        copied_mesh = source.data.copy()
        copied_mesh["gameassetai_copy_owner"] = token
        copied_object = source.copy()
        copied_object["gameassetai_copy_owner"] = token
        copied_object.data = copied_mesh
        copied_object.name = result_name
        if copied_object.name != result_name:
            raise ValueError("Output name changed")
        _pivot_write(copied_mesh, local_pivot)
        copied_object.matrix_world = Matrix(preview["predicted_basis"])
        # Matrix decomposition can round channels; restore exact source rotation/scale.
        copied_object.rotation_euler = source.rotation_euler
        copied_object.scale = source.scale
        copied_object.location = Vector(preview["predicted_world_origin"])

        def validate():
            if (copied_object.data != copied_mesh or copied_mesh == source.data
                    or len(copied_mesh.vertices) != len(preview["predicted_vertices"])
                    or _pivot_surface(copied_object) != surface
                    or copied_object.matrix_parent_inverse != source.matrix_parent_inverse):
                raise ValueError("Pivot output independence/surface/parent-inverse changed")
            for key, values in raw.items():
                if key != "location" and list(getattr(copied_object, key)) != values:
                    raise ValueError("Pivot output non-location channels changed")
            for vertex, predicted, position in zip(copied_mesh.vertices, preview["predicted_vertices"], positions):
                if not (vertex.co - Vector(predicted)).length <= geometry_tolerance:
                    raise ValueError("Pivot copied coordinates differ from preview")
                if not (copied_object.matrix_world @ vertex.co - position).length <= geometry_tolerance:
                    raise ValueError("Pivot copied reported-world positions changed")
            if not (copied_object.matrix_world.translation - Vector(preview["predicted_world_origin"])).length <= geometry_tolerance:
                raise ValueError("Pivot copied world origin changed")
            fresh = verify_pivot_preview(object_name, expected_source_sha256=expected_source_sha256, **parameters)
            if fresh["status"] != "preview" or source.matrix_world != world or _pivot_surface(source) != surface:
                raise ValueError("Pivot source preservation check failed")

        validate()
        _pivot_link(scene, copied_object)
        validate()
        report.update(status="created", object=copied_object.name, mesh=copied_mesh.name,
                      owner_token=token, source_sha256=preview["source_sha256"],
                      source_preserved=True, materials_shared=True,
                      validation_basis="base_and_reported_world_no_graph_refresh")
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            if copied_object is not None:
                if (copied_object.get("gameassetai_copy_owner") != token
                        or any(c != scene.collection for c in copied_object.users_collection)
                        or copied_object.users > len(copied_object.users_collection)):
                    raise RuntimeError("Pivot copy ownership/users changed; cleanup stopped")
                bpy.data.objects.remove(copied_object, do_unlink=True)
            if copied_mesh is not None:
                if copied_mesh.get("gameassetai_copy_owner") != token or copied_mesh.users:
                    raise RuntimeError("Pivot Mesh ownership/users changed; cleanup stopped")
                bpy.data.meshes.remove(copied_mesh)
            report["failure_cleanup"] = "complete"
        except Exception as cleanup:
            report.update(failure_cleanup="unverified", cleanup_error=str(cleanup), owner_token=token)
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
