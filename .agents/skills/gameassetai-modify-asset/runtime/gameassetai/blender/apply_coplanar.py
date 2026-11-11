"""Development-only independent copy apply; load preview and its dependencies first."""
import bmesh
import bpy
import uuid


def _coplanar_write(mesh,angle_limit):
    bm=bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.normal_update()
        bmesh.ops.dissolve_limit(bm,angle_limit=angle_limit,use_dissolve_boundaries=False,
            verts=[],edges=[e for e in bm.edges if len(e.link_faces)==2],
            delimit={"NORMAL","MATERIAL","SEAM","SHARP","UV"})
        bm.to_mesh(mesh)
    finally:
        bm.free()


def _coplanar_link(scene,obj):
    scene.collection.objects.link(obj)


def apply_coplanar(object_name, *, result_name, expected_source_sha256, angle_limit,
                   tolerance=None, geometry_tolerance=None, uv_tolerance=None,
                   authorized=False, scene_name=None):
    report={"schema":"gameassetai.coplanar-apply.v1","status":"error","errors":[]}
    copied_object=copied_mesh=scene=None
    token=uuid.uuid4().hex
    try:
        if type(authorized) is not bool or not authorized:
            raise ValueError("Explicit operation authorization required; a budget is not permission")
        if (not isinstance(result_name,str) or not result_name or "\x00" in result_name
                or len(result_name.encode())>63):
            raise ValueError("Explicit unused result name required (at most 63 UTF-8 bytes)")
        if bpy.data.objects.get(result_name) is not None:
            raise ValueError("Result name exists; overwrite/autosuffix refused")
        if _loose_file_blockers():
            raise ValueError("Apply blocked by file-wide animation/drivers/constraints")
        tolerance_options=dict(tolerance=tolerance,geometry_tolerance=geometry_tolerance,uv_tolerance=uv_tolerance)
        preview=preview_coplanar(object_name,angle_limit=angle_limit,scene_name=scene_name,**tolerance_options)
        if preview["status"]!="preview":
            raise ValueError("Source preview refused: "+str(preview))
        if not isinstance(expected_source_sha256,str) or expected_source_sha256!=preview["source_sha256"]:
            raise ValueError("Preview fingerprint missing/stale; re-preview")
        report.update(source=object_name,scene=preview["scene"],source_sha256=preview["source_sha256"])
        if not preview["changed"]:
            report["status"]="no_change"
            return report
        scene=bpy.data.scenes[preview["scene"]]
        source=scene.objects[object_name]
        before=_loose_state(source)
        copied_mesh=source.data.copy()
        copied_mesh["gameassetai_copy_owner"]=token
        copied_object=source.copy()
        copied_object["gameassetai_copy_owner"]=token
        copied_object.data=copied_mesh
        copied_object.name=result_name
        if copied_object.name!=result_name:
            raise ValueError("Blender changed output name")
        _coplanar_write(copied_mesh,angle_limit)
        bm=bmesh.new()
        try:
            bm.from_mesh(copied_mesh)
            bm.normal_update()
            actual_hash=_coplanar_geometry_hash(bm)
            counts=[len(bm.verts),len(bm.edges),len(bm.faces),len(bm.calc_loop_triangles())]
        finally:
            bm.free()
        if actual_hash!=preview["predicted_geometry_sha256"] or counts!=preview["predicted_counts"]:
            raise ValueError("Output differs from validated predicted geometry/UV/material/edge flags")
        after=_loose_state(copied_object)
        preserved=[key for key in before if key not in {"vertices","edges","surface"}]
        if any(before[key]!=after[key] for key in preserved):
            raise ValueError("Copied transform/material/UV-layer references changed")
        fresh=preview_coplanar(object_name,angle_limit=angle_limit,scene_name=scene.name,**tolerance_options)
        if _loose_state(source)!=before or fresh.get("source_sha256")!=expected_source_sha256:
            raise ValueError("Source preservation check failed")
        _coplanar_link(scene,copied_object)
        report.update(status="created",object=copied_object.name,mesh=copied_mesh.name,owner_token=token,
                      after_counts=counts,source_preserved=True,materials_shared=True,
                      triangle_reduction=preview["triangle_reduction"])
    except Exception as exc:
        report["status"]="error"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
        try:
            if copied_object is not None:
                if (copied_object.get("gameassetai_copy_owner")!=token
                        or any(c!=scene.collection for c in copied_object.users_collection)
                        or copied_object.users>len(copied_object.users_collection)):
                    raise RuntimeError("Copy ownership/users changed; cleanup aborted")
                bpy.data.objects.remove(copied_object,do_unlink=True)
            if copied_mesh is not None:
                if copied_mesh.get("gameassetai_copy_owner")!=token or copied_mesh.users:
                    raise RuntimeError("Copy mesh ownership/users changed; cleanup aborted")
                bpy.data.meshes.remove(copied_mesh)
            report["failure_cleanup"]="complete"
        except Exception as cleanup_error:
            report["failure_cleanup"]="unverified"
            report["errors"].append(str(cleanup_error))
    return report
# Retained bounded Blender capability; product support remains evidence-scoped.
