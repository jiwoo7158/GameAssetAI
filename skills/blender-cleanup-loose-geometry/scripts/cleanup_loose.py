"""Execute inside Blender. Preview, or clean only an exact invocation-owned copy."""
from __future__ import annotations

import json
import hashlib
import uuid
import bpy
import bmesh


def _loose_surface(mesh):
    return [{"positions": [list(mesh.vertices[i].co) for i in face.vertices],
             "uv": [[list(layer.data[i].uv) for i in face.loop_indices] for layer in mesh.uv_layers],
             "material": face.material_index, "smooth": face.use_smooth}
            for face in mesh.polygons]


def _loose_state(obj):
    mesh = obj.data
    return {"vertices": [list(v.co) for v in mesh.vertices],
            "edges": [list(e.vertices) for e in mesh.edges], "surface": _loose_surface(mesh),
            "materials": [m.name if m else None for m in mesh.materials],
            "uv_names": [layer.name for layer in mesh.uv_layers],
            "matrix": [list(row) for row in obj.matrix_world],
            "location": list(obj.location), "scale": list(obj.scale),
            "rotation_euler":list(obj.rotation_euler),"rotation_quaternion":list(obj.rotation_quaternion),
            "rotation_axis_angle":list(obj.rotation_axis_angle),
            "delta_location":list(obj.delta_location),"delta_scale":list(obj.delta_scale),
            "delta_rotation_euler":list(obj.delta_rotation_euler),
            "delta_rotation_quaternion":list(obj.delta_rotation_quaternion)}


def _loose_file_blockers():
    owners = set(bpy.data.user_map())
    owners.update(owner.node_tree for owner in list(owners)
                  if getattr(owner, "node_tree", None) is not None)
    blockers = []
    for owner in owners:
        animation = getattr(owner, "animation_data", None)
        pose = getattr(owner, "pose", None)
        if ((animation and (animation.action or len(animation.drivers) or len(animation.nla_tracks)))
                or len(getattr(owner, "constraints", ()))
                or (pose and any(len(b.constraints) for b in pose.bones))):
            blockers.append(owner.name_full)
    return sorted(blockers)


def _loose_write(mesh, remove_isolated_vertices, remove_wire_edges):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        if remove_wire_edges:
            # Direct removal avoids hard-coded delete operator context enums.
            for edge in list(bm.edges):
                if not edge.link_faces:
                    bm.edges.remove(edge)
        if remove_isolated_vertices:
            for vertex in list(bm.verts):
                if not vertex.link_edges:
                    bm.verts.remove(vertex)
        bm.to_mesh(mesh)
    finally:
        bm.free()


def cleanup_loose_geometry(object_name, result_name=None, scene_name=None,
                           remove_isolated_vertices=False, remove_wire_edges=False, apply=False,
                           expected_source_sha256=None):
    report = {"schema": "gameassetai.loose-cleanup.v1", "status": "error", "errors": []}
    copied_object = copied_mesh = scene = None
    token = uuid.uuid4().hex
    try:
        if any(not isinstance(v, bool) for v in (remove_isolated_vertices, remove_wire_edges, apply)):
            raise ValueError("Cleanup options and apply must be explicit booleans")
        if not isinstance(object_name, str) or not object_name:
            raise ValueError("Explicit source object name required")
        if scene_name is not None and (not isinstance(scene_name, str) or not scene_name):
            raise ValueError("scene_name must be a nonempty string or None")
        scene = bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
        source = scene.objects.get(object_name) if scene else None
        if source is None or source.type != "MESH":
            raise ValueError("Named mesh not found in the specified Scene")
        mesh = source.data
        if bpy.context.mode != "OBJECT" or mesh.is_editmode:
            raise ValueError("Require Object mode; no user mode change performed")
        if source.library or mesh.library or source.override_library or mesh.override_library:
            raise ValueError("Linked/override data is unsupported")
        if (source.parent or len(source.children) or source.modifiers or source.constraints
                or source.vertex_groups or mesh.shape_keys or source.animation_data or mesh.animation_data):
            raise ValueError("Dependent rig/animation/modifier/group/parent data requires another workflow")
        if mesh.has_custom_normals:
            raise ValueError("Custom normals require separate preservation verification")
        supported = {"position", ".edge_verts", ".corner_vert", ".corner_edge", "material_index",
                     "sharp_face", "sharp_edge", ".select_vert", ".select_edge", ".select_poly",
                     ".uv_select_face", ".uv_select_vert", ".uv_select_edge",
                     *(uv.name for uv in mesh.uv_layers)}
        unsupported = [attribute.name for attribute in mesh.attributes if attribute.name not in supported]
        if unsupported:
            raise ValueError("Generic attributes are not yet supported: " + str(unsupported))
        before = _loose_state(source)
        serialized = json.dumps([source.name,mesh.name,before],sort_keys=True,allow_nan=False)
        source_sha256 = hashlib.sha256(serialized.encode()).hexdigest()
        if not mesh.polygons:
            raise ValueError("No polygon surface; wire-only assets are not cleanup targets")
        edges_used = set()
        for face in mesh.polygons:
            vertices = list(face.vertices)
            edges_used.update(tuple(sorted((a,b))) for a,b in zip(vertices,vertices[1:]+vertices[:1]))
        wire = [e.index for e in mesh.edges if tuple(sorted(e.vertices)) not in edges_used]
        wire_indices = set(wire)
        remaining_edges = [e for e in mesh.edges if not remove_wire_edges or e.index not in wire_indices]
        connected = {i for e in remaining_edges for i in e.vertices}
        isolated = [v.index for v in mesh.vertices if v.index not in connected]
        report.update({"source": source.name, "scene": scene.name,
                       "source_sha256":source_sha256,
                       "options": {"remove_isolated_vertices":remove_isolated_vertices,
                                   "remove_wire_edges":remove_wire_edges},
                       "wire_edges": wire if remove_wire_edges else [],
                       "isolated_vertices": isolated if remove_isolated_vertices else [],
                       "before_counts": [len(mesh.vertices),len(mesh.edges),len(mesh.polygons)]})
        if not apply:
            report["status"] = "preview"
            return report
        if not isinstance(result_name, str) or not result_name or len(result_name.encode()) > 63 or "\x00" in result_name:
            raise ValueError("Explicit unused result name required (at most 63 UTF-8 bytes)")
        if bpy.data.objects.get(result_name) is not None:
            raise ValueError("Result name already exists; overwrite/autosuffix refused")
        blockers = _loose_file_blockers()
        if blockers:
            raise ValueError("Apply blocked by file-wide animation/constraints: " + str(blockers))
        if not report["wire_edges"] and not report["isolated_vertices"]:
            report["status"] = "no_change"
            return report
        if expected_source_sha256 != source_sha256:
            raise ValueError("Preview fingerprint missing/stale; re-preview before apply")
        copied_mesh = mesh.copy()
        copied_mesh["gameassetai_copy_owner"] = token
        copied_object = source.copy()
        copied_object["gameassetai_copy_owner"] = token
        copied_object.data = copied_mesh
        copied_object.name = result_name
        if copied_object.name != result_name:
            raise ValueError("Blender did not preserve the explicit output name")
        _loose_write(copied_mesh,remove_isolated_vertices,remove_wire_edges)
        after = _loose_state(copied_object)
        if any(before[k] != after[k] for k in ("surface","materials","uv_names","matrix","location","scale")):
            raise RuntimeError("Retained surface/UV/material/transform validation failed")
        expected_counts = [report["before_counts"][0]-len(report["isolated_vertices"]),
                           report["before_counts"][1]-len(report["wire_edges"]),report["before_counts"][2]]
        counts = [len(copied_mesh.vertices),len(copied_mesh.edges),len(copied_mesh.polygons)]
        if counts != expected_counts or _loose_state(source) != before:
            raise RuntimeError("Removal counts or source preservation validation failed")
        scene.collection.objects.link(copied_object)
        report.update({"status":"created", "object":copied_object.name,"mesh":copied_mesh.name,
                       "owner_token":token,"after_counts":counts,"source_preserved":True,
                       "materials_shared":True})
    except Exception as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            if copied_object is not None:
                if (copied_object.get("gameassetai_copy_owner") != token
                        or any(c != scene.collection for c in copied_object.users_collection)
                        or copied_object.users > len(copied_object.users_collection)):
                    raise RuntimeError("New object ownership/users changed; cleanup aborted")
                bpy.data.objects.remove(copied_object, do_unlink=True)
            if copied_mesh is not None:
                if copied_mesh.get("gameassetai_copy_owner") != token or copied_mesh.users:
                    raise RuntimeError("New mesh ownership/users changed; cleanup aborted")
                bpy.data.meshes.remove(copied_mesh)
            report["failure_cleanup"] = "complete"
        except Exception as cleanup_error:
            report["failure_cleanup"] = "unverified"
            report["errors"].append(str(cleanup_error))
    return report
