"""Synthetic-only native capability experiment, not a reusable apply operation."""
import bmesh
import math
import uuid


def run_coplanar_experiment(fail_after=None):
    if fail_after not in {None,"copy","write"}:
        raise ValueError("Unknown synthetic failure point")
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Require Object-mode window; do not force user mode")
    scene=bpy.context.scene
    before=source_fingerprint(scene)
    collections=(bpy.data.scenes,bpy.data.objects,bpy.data.meshes,bpy.data.materials)
    names_before=[[item.name for item in c] for c in collections]
    token=uuid.uuid4().hex
    fixture=bpy.data.scenes.new("GAI_Coplanar_"+token)
    fixture["gameassetai_test_owner"]=token
    owned=[]
    checks=[]
    results=[]

    def own(item,collection):
        item["gameassetai_test_owner"]=token
        owned.append((item,collection))
        return item

    def check(label,condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    def surface(mesh):
        mesh.calc_loop_triangles()
        bm=bmesh.new()
        try:
            bm.from_mesh(mesh)
            boundary=sorted(tuple(sorted(tuple(v.co) for v in e.verts))
                            for e in bm.edges if e.is_boundary)
        finally:
            bm.free()
        uv=mesh.uv_layers[0]
        mapping=sorted(set((tuple(mesh.vertices[mesh.loops[i].vertex_index].co),
                            tuple(uv.data[i].uv),p.material_index)
                           for p in mesh.polygons for i in p.loop_indices))
        return {"boundary":boundary,"mapping":mapping,
                "area":sum(p.area for p in mesh.polygons),
                "counts":[len(mesh.vertices),len(mesh.edges),len(mesh.polygons),len(mesh.loop_triangles)]}

    try:
        for case in ("continuous","uv_nonaffine","uv_split","material","seam","sharp","noncoplanar"):
            mesh=own(bpy.data.meshes.new("GAI_"+case+"_"+token),bpy.data.meshes)
            mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0.25 if case=="noncoplanar" else 0)],
                             [],[(0,1,2),(0,2,3)])
            source=own(bpy.data.objects.new("GAI_Source_"+case+"_"+token,mesh),bpy.data.objects)
            fixture.collection.objects.link(source)
            uv=mesh.uv_layers.new(name="ExperimentUV")
            for p in mesh.polygons:
                for i in p.loop_indices:
                    co=mesh.vertices[mesh.loops[i].vertex_index].co
                    uv.data[i].uv=(co.x+(2 if case=="uv_split" and p.index==1 else 0),co.y)
                    if case=="uv_nonaffine" and mesh.loops[i].vertex_index==2:
                        uv.data[i].uv.y=0.3
            for index in range(2 if case=="material" else 1):
                material=own(bpy.data.materials.new("GAI_Mat_"+case+str(index)+"_"+token),bpy.data.materials)
                mesh.materials.append(material)
            if case=="material":
                mesh.polygons[1].material_index=1
            for edge in mesh.edges:
                if set(edge.vertices)=={0,2}:
                    edge.use_seam=case=="seam"
                    edge.use_edge_sharp=case=="sharp"
            source_state=surface(mesh)
            preview_names=[[item.name for item in c] for c in collections]
            preview=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,tolerance=1e-6)
            check(case+"_preview_no_ids",preview_names==[[item.name for item in c] for c in collections])
            check(case+"_preview_source_preserved",surface(mesh)==source_state)
            check(case+"_preview_no_authorization",preview["mutation_authorized"] is False)
            if case in {"uv_nonaffine","uv_split","noncoplanar"}:
                check(case+"_preview_blocked",preview["status"]=="blocked")
            else:
                check(case+"_preview_prediction_"+json.dumps(preview),preview["status"]=="preview"
                      and preview["predicted_counts"]==([4,4,1,2] if case=="continuous" else [4,5,2,2]))
                check(case+"_preview_no_triangle_claim",preview["triangle_reduction"] is False)
            if case=="continuous":
                old_hash=preview["source_sha256"]
                separate=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                           geometry_tolerance=1e-6,uv_tolerance=1e-6)
                check("separate_tolerance_legacy_equivalence",separate.get("source_sha256")==old_hash
                      and separate.get("predicted_geometry_sha256")==preview["predicted_geometry_sha256"])
                changed_uv_bound=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                           geometry_tolerance=1e-6,uv_tolerance=2e-6)
                check("separate_uv_bound_fingerprint",changed_uv_bound.get("source_sha256")!=old_hash)
                for p in mesh.polygons:
                    for i in p.loop_indices:
                        if mesh.loops[i].vertex_index==2:
                            uv.data[i].uv.y=1.00001
                strict_uv=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                           geometry_tolerance=0.01,uv_tolerance=1e-7)
                loose_uv=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                           geometry_tolerance=1e-7,uv_tolerance=0.01)
                check("native_separate_uv_units",strict_uv["status"]=="blocked"
                      and loose_uv["status"]=="preview")
                for p in mesh.polygons:
                    for i in p.loop_indices:
                        if mesh.loops[i].vertex_index==2:
                            uv.data[i].uv.y=1
                internal=next(e for e in mesh.edges if set(e.vertices)=={0,2})
                internal.use_seam=True
                flag_preview=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,tolerance=1e-6)
                check("preview_seam_fingerprint",flag_preview.get("source_sha256")!=old_hash
                      and flag_preview.get("predicted_counts")==[4,5,2,2])
                internal.use_seam=False
                for i in mesh.polygons[0].loop_indices:
                    if mesh.loops[i].vertex_index==2:
                        uv.data[i].uv.y=0.3
                uv_changed=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,tolerance=1e-6)
                check("preview_uv_fingerprint_and_block",uv_changed.get("source_sha256")!=old_hash
                      and uv_changed["status"]=="blocked")
                for i in mesh.polygons[0].loop_indices:
                    if mesh.loops[i].vertex_index==2:
                        uv.data[i].uv.y=1
                for value in (True,0,-1,float("nan"),0.01):
                    check("preview_invalid_angle_"+str(value),preview_coplanar(source.name,
                          scene_name=fixture.name,angle_limit=value,tolerance=1e-6)["status"]=="error")
                for value in (True,0,-1,float("inf")):
                    check("preview_invalid_tolerance_"+str(value),preview_coplanar(source.name,
                          scene_name=fixture.name,angle_limit=0.001,tolerance=value)["status"]=="error")
                check("preview_missing_target",preview_coplanar("GAI_Missing_"+token,
                      scene_name=fixture.name,angle_limit=0.001,tolerance=1e-6)["status"]=="error")
                from types import SimpleNamespace
                globals_=preview_coplanar.__globals__
                real_bmesh=globals_["bmesh"]
                freed=[]
                class TrackedBMesh:
                    def __init__(self):
                        self.bm=real_bmesh.new()
                    def __getattr__(self,name):
                        return getattr(self.bm,name)
                    def free(self):
                        self.bm.free()
                        freed.append(True)
                def fail_dissolve(*args,**kwargs):
                    raise RuntimeError("synthetic preview operator failure")
                try:
                    globals_["bmesh"]=SimpleNamespace(new=TrackedBMesh,
                        ops=SimpleNamespace(dissolve_limit=fail_dissolve))
                    failed_preview=preview_coplanar(source.name,scene_name=fixture.name,
                                                   angle_limit=0.001,tolerance=1e-6)
                finally:
                    globals_["bmesh"]=real_bmesh
                check("preview_failure_reported",failed_preview["status"]=="error"
                      and "synthetic preview operator failure" in failed_preview["errors"][0])
                check("preview_failure_bmesh_freed",freed==[True])
                check("preview_failure_preserved_ids_source",preview_names==[[item.name for item in c] for c in collections]
                      and surface(mesh)==source_state)
                # Larger geometry units must not silently weaken normalized UV checks.
                for vertex in mesh.vertices:
                    vertex.co*=1000
                scaled=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                        geometry_tolerance=0.001,uv_tolerance=1e-7)
                check("scaled_geometry_separate_uv",scaled["status"]=="preview"
                      and scaled["predicted_counts"]==[4,4,1,2])
                for vertex in mesh.vertices:
                    vertex.co/=1000
                extra_uv=mesh.uv_layers.new(name="SecondAffineUV")
                for p in mesh.polygons:
                    for i in p.loop_indices:
                        co=mesh.vertices[mesh.loops[i].vertex_index].co
                        extra_uv.data[i].uv=(co.x*2+3,co.y*3+4)
                multi=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                       geometry_tolerance=1e-6,uv_tolerance=1e-6)
                check("all_uv_layers_affine_preview",multi["status"]=="preview")
                multi_applied=apply_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                    geometry_tolerance=1e-6,uv_tolerance=1e-6,authorized=True,
                    expected_source_sha256=multi.get("source_sha256"),result_name="GAI_MultiUV_"+token)
                check("all_uv_layers_copy_apply",multi_applied["status"]=="created")
                multi_obj=own(bpy.data.objects[multi_applied["object"]],bpy.data.objects)
                own(multi_obj.data,bpy.data.meshes)
                check("all_uv_layers_output_names",[layer.name for layer in multi_obj.data.uv_layers]
                      ==["ExperimentUV","SecondAffineUV"])
                for p in mesh.polygons:
                    for i in p.loop_indices:
                        if mesh.loops[i].vertex_index==2: extra_uv.data[i].uv.y+=0.1
                broken_second=preview_coplanar(source.name,scene_name=fixture.name,angle_limit=0.001,
                                              geometry_tolerance=1e-6,uv_tolerance=1e-6)
                check("second_uv_layer_blocks",broken_second["status"]=="blocked"
                      and broken_second["uv_layer"]=="SecondAffineUV")
                mesh.uv_layers.remove(extra_uv)
                check("scaled_multi_uv_source_restored",surface(mesh)==source_state)
            corners=[(tuple(mesh.vertices[mesh.loops[i].vertex_index].co),tuple(uv.data[i].uv))
                     for p in mesh.polygons for i in p.loop_indices]
            uv_guard=check_affine_uv(corners,tolerance=1e-6)
            check(case+"_affine_guard",uv_guard["status"]==
                  ("blocked" if case in {"uv_nonaffine","uv_split","noncoplanar"} else "affine"))
            apply_options=dict(scene_name=fixture.name,angle_limit=0.001,tolerance=1e-6,
                               result_name="GAI_Applied_"+case+"_"+token,
                               expected_source_sha256=preview.get("source_sha256"),authorized=True)
            applied=apply_coplanar(source.name,**apply_options)
            if case=="continuous":
                check("apply_created_"+str(applied),applied["status"]=="created")
                applied_obj=own(bpy.data.objects[applied["object"]],bpy.data.objects)
                own(applied_obj.data,bpy.data.meshes)
                check("apply_independent_source_and_surface",applied_obj.data!=mesh and surface(mesh)==source_state
                      and surface(applied_obj.data)["counts"]==[4,4,1,2]
                      and surface(applied_obj.data)["mapping"]==source_state["mapping"])
                names_at_apply=[[item.name for item in c] for c in collections]
                for key,value in (("authorized",False),("authorized","yes"),
                                  ("expected_source_sha256",None),("expected_source_sha256","stale"),
                                  ("result_name",applied_obj.name)):
                    options=dict(apply_options,result_name="GAI_Refused_"+token)
                    options[key]=value
                    refused=apply_coplanar(source.name,**options)
                    check("apply_refusal_"+key+str(value),refused["status"]=="error"
                          and refused["failure_cleanup"]=="complete")
                check("apply_refusals_no_ids",names_at_apply==[[item.name for item in c] for c in collections])
                # A legitimate old preview must become stale after relevant state changes.
                source.location.x=2
                stale_apply=apply_coplanar(source.name,**dict(apply_options,result_name="GAI_Stale_"+token))
                check("apply_real_stale_transform",stale_apply["status"]=="error"
                      and "missing/stale" in stale_apply["errors"][0])
                source.location.x=0
                changed_parameters=apply_coplanar(source.name,**dict(apply_options,
                    result_name="GAI_Param_"+token,tolerance=2e-6))
                check("apply_parameter_bound_hash",changed_parameters["status"]=="error"
                      and "missing/stale" in changed_parameters["errors"][0])
                separate_stale=apply_coplanar(source.name,**dict(apply_options,tolerance=None,
                    geometry_tolerance=1e-6,uv_tolerance=2e-6,result_name="GAI_UVParam_"+token))
                check("apply_uv_bound_hash",separate_stale["status"]=="error"
                      and "missing/stale" in separate_stale["errors"][0])
                source.vertex_groups.new(name="PreserveGroup")
                sensitive=apply_coplanar(source.name,**dict(apply_options,result_name="GAI_Group_"+token))
                check("apply_group_refused",sensitive["status"]=="error")
                source.vertex_groups.clear()
                source.shape_key_add(name="Basis")
                sensitive=apply_coplanar(source.name,**dict(apply_options,result_name="GAI_Shape_"+token))
                check("apply_shape_key_refused",sensitive["status"]=="error")
                source.shape_key_clear()
                source.animation_data_create()
                sensitive=apply_coplanar(source.name,**dict(apply_options,result_name="GAI_Anim_"+token))
                check("apply_animation_binding_refused",sensitive["status"]=="error")
                source.animation_data_clear()
                unrelated=own(bpy.data.objects.new("GAI_Constraint_"+token,None),bpy.data.objects)
                fixture.collection.objects.link(unrelated)
                constraint=unrelated.constraints.new("COPY_LOCATION")
                names_with_guard=[[item.name for item in c] for c in collections]
                guarded=apply_coplanar(source.name,**dict(apply_options,result_name="GAI_Graph_"+token))
                check("apply_unrelated_constraint_guard",guarded["status"]=="error"
                      and "file-wide" in guarded["errors"][0])
                check("apply_dependency_guard_no_ids",names_with_guard==[[item.name for item in c] for c in collections])
                unrelated.constraints.remove(constraint)
                names_at_apply=names_with_guard
                apply_globals=apply_coplanar.__globals__
                real_write=apply_globals["_coplanar_write"]
                real_link=apply_globals["_coplanar_link"]
                for stage in ("write","validation","link"):
                    def failed_write(*args):
                        raise RuntimeError("synthetic apply write failure")
                    def corrupt_write(copied,angle):
                        real_write(copied,angle)
                        copied.vertices[0].co.z+=1
                    def failed_link(target,obj):
                        real_link(target,obj)
                        raise RuntimeError("synthetic apply link failure")
                    try:
                        if stage=="write": apply_globals["_coplanar_write"]=failed_write
                        if stage=="validation": apply_globals["_coplanar_write"]=corrupt_write
                        if stage=="link": apply_globals["_coplanar_link"]=failed_link
                        options=dict(apply_options,result_name="GAI_ApplyFail_"+stage+"_"+token)
                        failed=apply_coplanar(source.name,**options)
                    finally:
                        apply_globals["_coplanar_write"]=real_write
                        apply_globals["_coplanar_link"]=real_link
                    check("apply_"+stage+"_rolled_back",failed["status"]=="error"
                          and failed["failure_cleanup"]=="complete")
                    check("apply_"+stage+"_preserved_ids_source",names_at_apply==[[item.name for item in c] for c in collections]
                          and surface(mesh)==source_state)
                applied_obj.data.vertices[0].co.z+=0.5
                check("apply_copy_edit_preserves_source",surface(mesh)==source_state)
            else:
                check(case+"_apply_refused_or_noop",applied["status"]==
                      ("error" if case in {"uv_nonaffine","uv_split","noncoplanar"} else "no_change"))
                check(case+"_apply_no_ids",preview_names==[[item.name for item in c] for c in collections])
            geometry_before=[tuple(v.co) for v in mesh.vertices]
            copy_mesh=own(mesh.copy(),bpy.data.meshes)
            copy_obj=own(source.copy(),bpy.data.objects)
            copy_obj.data=copy_mesh
            copy_obj.name="GAI_Copy_"+case+"_"+token
            check(case+"_unused_name",copy_obj.name=="GAI_Copy_"+case+"_"+token)
            if fail_after=="copy":
                raise RuntimeError("synthetic failure after copy")
            bm=bmesh.new()
            try:
                bm.from_mesh(copy_mesh)
                bm.normal_update()
                candidates=[e for e in bm.edges if len(e.link_faces)==2]
                check(case+"_explicit_internal_edge",len(candidates)==1)
                bmesh.ops.dissolve_limit(bm,angle_limit=0.001,use_dissolve_boundaries=False,
                    verts=[],edges=candidates,delimit={"NORMAL","MATERIAL","SEAM","SHARP","UV"})
                bm.to_mesh(copy_mesh)
            finally:
                bm.free()
            if fail_after=="write":
                raise RuntimeError("synthetic failure after write")
            output=surface(copy_mesh)
            check(case+"_independent",copy_obj.data!=source.data)
            check(case+"_source_preserved",surface(mesh)==source_state
                  and [tuple(v.co) for v in mesh.vertices]==geometry_before)
            check(case+"_boundary_uv_material",output["boundary"]==source_state["boundary"]
                  and output["mapping"]==source_state["mapping"])
            check(case+"_area",math.isclose(output["area"],source_state["area"],rel_tol=1e-6,abs_tol=1e-6))
            expected=[4,4,1,2] if case in {"continuous","uv_nonaffine"} else [4,5,2,2]
            check(case+"_counts_actual_"+str(output["counts"]),output["counts"]==expected)
            if case in {"seam","sharp"}:
                retained=[e for e in copy_mesh.edges if set(e.vertices)=={0,2}]
                check(case+"_protected_flag",len(retained)==1 and
                      (retained[0].use_seam if case=="seam" else retained[0].use_edge_sharp))
            # Validate before exposing the synthetic output to any Scene.
            fixture.collection.objects.link(copy_obj)
            results.append({"case":case,"before":source_state["counts"],"after":output["counts"],
                            "uv_guard":uv_guard["status"],"general_uv_quality_certified":False})
        # Disconnected geometry is still whole-object scope, never current selection.
        islands_mesh=own(bpy.data.meshes.new("GAI_IslandsMesh_"+token),bpy.data.meshes)
        islands_mesh.from_pydata([(0,0,0),(1,0,0),(1,1,0),(0,1,0),
                                 (3,0,0),(4,0,0),(4,1,0),(3,1,0)],[],
                                [(0,1,2),(0,2,3),(4,5,6),(4,6,7)])
        islands=own(bpy.data.objects.new("GAI_Islands_"+token,islands_mesh),bpy.data.objects)
        fixture.collection.objects.link(islands)
        islands_mesh.materials.append(material)
        islands_uv=islands_mesh.uv_layers.new(name="IslandUV")
        for p in islands_mesh.polygons:
            for i in p.loop_indices:
                co=islands_mesh.vertices[islands_mesh.loops[i].vertex_index].co
                islands_uv.data[i].uv=co.xy
        islands_state=_loose_state(islands)
        island_preview=preview_coplanar(islands.name,scene_name=fixture.name,angle_limit=0.001,
                                       geometry_tolerance=1e-6,uv_tolerance=1e-6)
        check("disconnected_affine_whole_object_scope",island_preview["status"]=="preview"
              and island_preview["scope"]=="whole_simple_planar_mesh"
              and len(island_preview["candidate_internal_edges"])==2
              and island_preview["predicted_counts"]==[8,8,2,4])
        protected=next(e for e in islands_mesh.edges if set(e.vertices)=={0,2})
        protected.use_seam=True
        one_protected=preview_coplanar(islands.name,scene_name=fixture.name,angle_limit=0.001,
                                      geometry_tolerance=1e-6,uv_tolerance=1e-6)
        check("disconnected_component_seam_protection",one_protected["status"]=="preview"
              and one_protected["predicted_counts"]==[8,9,3,4])
        island_apply=apply_coplanar(islands.name,scene_name=fixture.name,angle_limit=0.001,
            geometry_tolerance=1e-6,uv_tolerance=1e-6,authorized=True,
            expected_source_sha256=one_protected["source_sha256"],result_name="GAI_IslandCopy_"+token)
        check("disconnected_protected_copy_created",island_apply["status"]=="created")
        island_copy=own(bpy.data.objects[island_apply["object"]],bpy.data.objects)
        own(island_copy.data,bpy.data.meshes)
        check("disconnected_protected_edge_retained",any(set(e.vertices)=={0,2} and e.use_seam
                                                      for e in island_copy.data.edges))
        protected.use_seam=False
        for p in islands_mesh.polygons:
            for i in p.loop_indices:
                if islands_mesh.loops[i].vertex_index>=4:
                    islands_uv.data[i].uv.y+=2
        split_islands=preview_coplanar(islands.name,scene_name=fixture.name,angle_limit=0.001,
                                      geometry_tolerance=1e-6,uv_tolerance=1e-6)
        check("different_uv_island_maps_blocked",split_islands["status"]=="blocked")
        island_names=[[item.name for item in c] for c in collections]
        refused_islands=apply_coplanar(islands.name,scene_name=fixture.name,angle_limit=0.001,
            geometry_tolerance=1e-6,uv_tolerance=1e-6,authorized=True,
            expected_source_sha256=one_protected["source_sha256"],result_name="GAI_IslandRefused_"+token)
        check("different_uv_islands_apply_no_ids",refused_islands["status"]=="error"
              and island_names==[[item.name for item in c] for c in collections])
        for p in islands_mesh.polygons:
            for i in p.loop_indices:
                if islands_mesh.loops[i].vertex_index>=4:
                    islands_uv.data[i].uv.y-=2
        check("disconnected_source_restored",_loose_state(islands)==islands_state)
    finally:
        for item,collection in owned:
            if collection.get(item.name)!=item or item.get("gameassetai_test_owner")!=token:
                raise RuntimeError("Fixture ownership changed; cleanup aborted")
            if collection==bpy.data.objects and any(c!=fixture.collection for c in item.users_collection):
                raise RuntimeError("External fixture link; cleanup aborted")
        for collection in (bpy.data.objects,bpy.data.meshes,bpy.data.materials):
            for item,owner in owned:
                if owner==collection:
                    if collection==bpy.data.objects:
                        collection.remove(item,do_unlink=True)
                    else:
                        if item.users:
                            raise RuntimeError("Unexpected fixture users; cleanup aborted")
                        collection.remove(item)
        if fixture.get("gameassetai_test_owner")!=token or fixture.objects:
            raise RuntimeError("Fixture Scene ownership changed; cleanup aborted")
        bpy.data.scenes.remove(fixture)
    check("original_fingerprint_restored",source_fingerprint(scene)==before)
    check("all_names_restored",names_before==[[item.name for item in c] for c in collections])
    return {"status":"passed","check_count":len(checks),"cases":results,
            "fixture_cleanup":"complete","source_fingerprint":before,
            "blender_version":bpy.app.version_string,"triangle_reduction":False}


def run_coplanar_failure_tests():
    original=source_fingerprint(bpy.context.scene)
    collections=(bpy.data.scenes,bpy.data.objects,bpy.data.meshes,bpy.data.materials)
    names=[[item.name for item in c] for c in collections]
    for stage in ("copy","write"):
        try:
            run_coplanar_experiment(fail_after=stage)
        except RuntimeError as exc:
            if str(exc)!="synthetic failure after "+stage:
                raise
        else:
            raise AssertionError("Expected synthetic failure")
        if names!=[[item.name for item in c] for c in collections]:
            raise AssertionError("Synthetic failure leaked IDs")
        if source_fingerprint(bpy.context.scene)!=original:
            raise AssertionError("Synthetic failure changed original Scene")
    return {"status":"passed","check_count":4,"fixture_cleanup":"complete"}
