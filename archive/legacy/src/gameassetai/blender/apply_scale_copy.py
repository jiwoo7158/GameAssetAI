"""Development copy-only scale application. Load inspector and scale preview first."""
import bpy
import uuid
from mathutils import Matrix, Vector


def _scale_file_blockers():
    owners = set(bpy.data.user_map())
    owners.update(owner.node_tree for owner in list(owners)
                  if getattr(owner, "node_tree", None) is not None)
    return sorted(owner.name_full for owner in owners
                  if getattr(owner, "animation_data", None)
                  or len(getattr(owner, "constraints", ()))
                  or (getattr(owner, "pose", None) and
                      any(len(b.constraints) for b in owner.pose.bones)))


def _scale_write(mesh, scale):
    mesh.transform(Matrix.Diagonal((*scale, 1)))


def _scale_link(scene, obj):
    scene.collection.objects.link(obj)


def _scale_surface(obj):
    mesh = obj.data
    return {"edges": [[list(e.vertices), e.use_seam, e.use_edge_sharp] for e in mesh.edges],
            "faces": [[list(p.vertices), p.material_index, p.use_smooth] for p in mesh.polygons],
            "uv": [[layer.name, layer.active_render, [list(item.uv) for item in layer.data]] for layer in mesh.uv_layers],
            "active_uv": mesh.uv_layers.active_index,
            "materials": [(slot.link, slot.material) for slot in obj.material_slots]}


def apply_scale_copy(object_name, *, result_name, expected_source_sha256,
                     geometry_tolerance, authorized=False, scene_name=None):
    report = {"schema": "gameassetai.scale-copy-apply.v1", "status": "error", "errors": [],
              "export_ready": None}
    copied_object = copied_mesh = scene = None
    token = uuid.uuid4().hex
    try:
        if type(authorized) is not bool or not authorized:
            raise ValueError("Explicit operation authorization required; profile budgets are not permission")
        if (not isinstance(result_name, str) or not result_name or "\x00" in result_name
                or len(result_name.encode("utf-8")) > 63):
            raise ValueError("Explicit unused result name required, at most 63 UTF-8 bytes")
        if bpy.data.objects.get(result_name) is not None:
            raise ValueError("Result name exists; overwrite/autosuffix refused")
        if _scale_file_blockers():
            raise ValueError("Apply blocked by file-wide animation/drivers/constraints")
        preview = verify_scale_preview(object_name, expected_source_sha256=expected_source_sha256,
                        geometry_tolerance=geometry_tolerance, scene_name=scene_name)
        if preview["status"] not in ("preview", "no_change"):
            raise ValueError("Fresh preview refused: " + str(preview["errors"]))
        if preview["status"] == "no_change":
            report["status"] = "no_change"
            return report
        scene = bpy.data.scenes[preview["scene"]]
        source = scene.objects[object_name]
        before_transform = inspect_static_transform(object_name, scene_name=scene.name)
        surface = _scale_surface(source)
        basis = source.matrix_basis.copy()
        world = source.matrix_world.copy()
        origin = world @ Vector((0, 0, 0))
        positions = [world @ v.co for v in source.data.vertices]
        # No graph refresh: refuse stale/inconsistent reported world state, not repair it.
        probes = [Vector((0, 0, 0)), *(v.co for v in source.data.vertices)]
        if any(not (world @ p - basis @ p).length <= geometry_tolerance for p in probes):
            raise ValueError("Reported world/basis state inconsistent; inspect before applying")
        copied_mesh = source.data.copy()
        copied_mesh["gameassetai_copy_owner"] = token
        copied_object = source.copy()
        copied_object["gameassetai_copy_owner"] = token
        copied_object.data = copied_mesh
        copied_object.name = result_name
        if copied_object.name != result_name:
            raise ValueError("Blender changed output name")
        _scale_write(copied_mesh, tuple(source.scale))
        copied_object.scale = (1, 1, 1)
        # Native test showed scale-channel assignment leaves cached world matrix stale.
        # Set only the new unparented copy's world matrix; never refresh the whole file.
        copied_object.matrix_world = copied_object.matrix_basis.copy()
        copied_object.scale = (1, 1, 1)  # Matrix decomposition may introduce sub-unit rounding.
        copied_object.location = source.location
        copied_object.rotation_euler = source.rotation_euler
        # Unlinked copy validation uses basis directly, no Scene fallback or graph update.
        if _scale_surface(copied_object) != surface or len(copied_mesh.vertices) != len(preview["predicted_vertices"]):
            raise ValueError("Copied topology/UV/material data changed")
        if tuple(copied_object.scale) != (1, 1, 1):
            raise ValueError("Output scale is not unit")
        for key, values in before_transform["raw_transform"].items():
            if key != "scale" and list(getattr(copied_object, key)) != values:
                raise ValueError("Copied non-scale transform changed")
        if copied_object.matrix_parent_inverse != source.matrix_parent_inverse:
            raise ValueError("Parent-inverse matrix changed")
        for index, vertex in enumerate(copied_mesh.vertices):
            if (not (vertex.co - Vector(preview["predicted_vertices"][index])).length <= geometry_tolerance
                    or not (copied_object.matrix_basis @ vertex.co - positions[index]).length <= geometry_tolerance):
                raise ValueError("Output coordinates differ from preview/source positions")
        if not (copied_object.matrix_basis @ Vector((0, 0, 0)) - origin).length <= geometry_tolerance:
            raise ValueError("Output pivot/origin changed")
        fresh = verify_scale_preview(object_name, expected_source_sha256=expected_source_sha256,
                       geometry_tolerance=geometry_tolerance, scene_name=scene.name)
        if fresh["status"] != "preview" or _scale_surface(source) != surface or source.matrix_world != world:
            raise ValueError("Source preservation check failed")
        _scale_link(scene, copied_object)
        # Linking may change reported state; validate without forcing a dependency refresh.
        if (copied_object.data != copied_mesh or copied_mesh == source.data
                or tuple(copied_object.scale) != (1, 1, 1)
                or _scale_surface(copied_object) != surface):
            raise ValueError("Linked output independence/scale/topology/UV/material changed")
        for key, values in before_transform["raw_transform"].items():
            if key != "scale" and list(getattr(copied_object, key)) != values:
                raise ValueError("Linked non-scale transform changed")
        if copied_object.matrix_parent_inverse != source.matrix_parent_inverse:
            raise ValueError("Linked parent-inverse matrix changed")
        for vertex, position in zip(copied_mesh.vertices, positions):
            if not (copied_object.matrix_world @ vertex.co - position).length <= geometry_tolerance:
                raise ValueError("Linked reported-world positions changed")
        if source.matrix_world != world or verify_scale_preview(object_name, expected_source_sha256=expected_source_sha256,
                              geometry_tolerance=geometry_tolerance, scene_name=scene.name)["status"] != "preview":
            raise ValueError("Source changed after link")
        report.update(status="created", object=copied_object.name, mesh=copied_mesh.name,
                      owner_token=token, source_preserved=True, materials_shared=True,
                      validation_basis="base_coordinates_and_reported_world_no_graph_refresh")
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            if copied_object is not None:
                if (copied_object.get("gameassetai_copy_owner") != token
                        or any(c != scene.collection for c in copied_object.users_collection)
                        or copied_object.users > len(copied_object.users_collection)):
                    raise RuntimeError("Copy ownership/users changed; cleanup stopped")
                bpy.data.objects.remove(copied_object, do_unlink=True)
            if copied_mesh is not None:
                if copied_mesh.get("gameassetai_copy_owner") != token or copied_mesh.users:
                    raise RuntimeError("Copy Mesh ownership/users changed; cleanup stopped")
                bpy.data.meshes.remove(copied_mesh)
            report["failure_cleanup"] = "complete"
        except Exception as cleanup_error:
            report["failure_cleanup"] = "unverified"
            report["errors"].append(str(cleanup_error))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
