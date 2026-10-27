"""Blender development preview. Load cleanup_loose and check_affine_uv first."""
import bmesh
import hashlib
import json
import math
import bpy


def _coplanar_geometry_hash(bm):
    layers=list(bm.loops.layers.uv.values())
    faces=[]
    for face in bm.faces:
        corners=[(tuple(loop.vert.co),tuple(tuple(loop[layer].uv) for layer in layers)) for loop in face.loops]
        cycle=min(tuple(corners[i:]+corners[:i]) for i in range(len(corners)))
        faces.append((cycle,face.material_index,face.smooth))
    state=[sorted(tuple(v.co) for v in bm.verts),
           sorted((tuple(sorted(tuple(v.co) for v in e.verts)),e.seam,e.smooth) for e in bm.edges),
           list(bm.loops.layers.uv.keys()),sorted(faces)]
    return hashlib.sha256(json.dumps(state,allow_nan=False).encode()).hexdigest()


def preview_coplanar(object_name, *, angle_limit, tolerance=None, geometry_tolerance=None,
                     uv_tolerance=None, scene_name=None):
    report={"schema":"gameassetai.coplanar-preview.v1","status":"error","errors":[],
            "mutation_authorized":False,"scope":"whole_simple_planar_mesh"}
    bm=None
    try:
        geometry_tolerance,uv_tolerance=_affine_tolerances(tolerance,geometry_tolerance,uv_tolerance)
        for key,value in (("angle_limit",angle_limit),):
            if type(value) not in {int,float} or not math.isfinite(value) or value<=0:
                raise ValueError(key+" must be explicitly finite and positive")
        if angle_limit>0.001:
            raise ValueError("Prototype supports angle_limit at most 0.001 radians")
        if not isinstance(object_name,str) or not object_name:
            raise ValueError("Explicit object name required")
        if scene_name is not None and (not isinstance(scene_name,str) or not scene_name):
            raise ValueError("Explicit valid Scene name required")
        scene=bpy.context.scene if scene_name is None else bpy.data.scenes.get(scene_name)
        obj=scene.objects.get(object_name) if scene else None
        if obj is None or obj.type!="MESH":
            raise ValueError("Named mesh not found")
        mesh=obj.data
        if bpy.context.mode!="OBJECT" or mesh.is_editmode:
            raise ValueError("Require Object mode; no mode change")
        if (obj.library or mesh.library or obj.override_library or mesh.override_library
                or obj.parent or obj.children or obj.modifiers or obj.constraints
                or obj.vertex_groups or mesh.shape_keys or obj.animation_data or mesh.animation_data
                or mesh.has_custom_normals):
            raise ValueError("Dependent/linked/custom-normal source unsupported")
        supported={"position",".edge_verts",".corner_vert",".corner_edge","material_index",
                   "sharp_face","sharp_edge","uv_seam",".select_vert",".select_edge",".select_poly",
                   ".uv_select_face",".uv_select_vert",".uv_select_edge",*(uv.name for uv in mesh.uv_layers)}
        if any(attribute.name not in supported for attribute in mesh.attributes):
            raise ValueError("Unsupported generic attributes")
        seam_attribute=mesh.attributes.get("uv_seam")
        if seam_attribute and (seam_attribute.domain!="EDGE" or seam_attribute.data_type!="BOOLEAN"):
            raise ValueError("Unexpected uv_seam attribute schema")
        if not mesh.polygons:
            raise ValueError("No polygon surface")
        if any(p.material_index>=len(mesh.materials) or mesh.materials[p.material_index] is None for p in mesh.polygons):
            raise ValueError("Prototype requires valid assigned surface materials")
        report.update(object=obj.name,scene=scene.name,parameters={"angle_limit":angle_limit,
                      "geometry_tolerance":geometry_tolerance,"uv_tolerance":uv_tolerance})
        if not mesh.uv_layers:
            raise ValueError("Prototype requires verified UV mapping")
        flags=[(list(e.vertices),e.use_seam,e.use_edge_sharp) for e in mesh.edges]
        state=[obj.name,mesh.name,_loose_state(obj),flags,
               [list(p.normal) for p in mesh.polygons],report["parameters"]]
        report["source_sha256"]=hashlib.sha256(json.dumps(state,sort_keys=True,allow_nan=False).encode()).hexdigest()
        for layer in mesh.uv_layers:
            corners=[(tuple(mesh.vertices[mesh.loops[i].vertex_index].co),tuple(layer.data[i].uv))
                     for p in mesh.polygons for i in p.loop_indices]
            guard=check_affine_uv(corners,geometry_tolerance=geometry_tolerance,uv_tolerance=uv_tolerance)
            if guard["status"]!="affine":
                report.update(status="blocked",reason=guard["reason"],uv_layer=layer.name)
                return report
        bm=bmesh.new()
        bm.from_mesh(mesh)
        bm.normal_update()

        def snapshot():
            layers=list(bm.loops.layers.uv.values())
            return {"counts":[len(bm.verts),len(bm.edges),len(bm.faces),len(bm.calc_loop_triangles())],
                    "boundary":sorted(tuple(sorted(tuple(v.co) for v in e.verts)) for e in bm.edges if e.is_boundary),
                    "surface":sorted(set((tuple(loop.vert.co),tuple(tuple(loop[layer].uv) for layer in layers),
                                           face.material_index,face.smooth)
                                          for face in bm.faces for loop in face.loops)),
                    "area":sum(f.calc_area() for f in bm.faces)}

        # Loose/nonmanifold input requires a different workflow, not hidden cleanup.
        if any(not v.link_edges for v in bm.verts) or any(len(e.link_faces) not in {1,2} for e in bm.edges):
            raise ValueError("Loose/nonmanifold geometry unsupported")
        if any(f.calc_area()<=0 for f in bm.faces):
            raise ValueError("Degenerate faces unsupported")
        before=snapshot()
        bm.edges.index_update()
        candidates=[e for e in bm.edges if len(e.link_faces)==2]
        report["candidate_internal_edges"]=[e.index for e in candidates]
        bmesh.ops.dissolve_limit(bm,angle_limit=angle_limit,use_dissolve_boundaries=False,
            verts=[],edges=candidates,delimit={"NORMAL","MATERIAL","SEAM","SHARP","UV"})
        after=snapshot()
        if (before["boundary"]!=after["boundary"] or before["surface"]!=after["surface"]
                or not math.isclose(before["area"],after["area"],rel_tol=1e-6,abs_tol=geometry_tolerance**2)):
            raise ValueError("Predicted boundary/UV/material/smooth/area preservation failed")
        report.update(status="preview",before_counts=before["counts"],predicted_counts=after["counts"],
                      predicted_geometry_sha256=_coplanar_geometry_hash(bm),
                      changed=before["counts"]!=after["counts"],
                      triangle_reduction=after["counts"][3]<before["counts"][3],
                      preservation="bounded_in_memory_checks_passed")
    except Exception as exc:
        report["status"]="error"
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if bm is not None:
            bm.free()
    return report
