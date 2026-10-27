"""Native Blender regression; load inspector/fingerprint and cleanup helper first."""
import uuid


def run_loose_cleanup_tests():
    if bpy.context.mode != "OBJECT" or bpy.context.window is None:
        raise RuntimeError("Require Object-mode window; do not force mode")
    token = uuid.uuid4().hex
    original_scene = bpy.context.scene
    before = source_fingerprint(original_scene)
    collections = (bpy.data.scenes,bpy.data.objects,bpy.data.meshes,bpy.data.materials,
                   bpy.data.actions,bpy.data.shape_keys)
    names_before = [[id.name for id in c] for c in collections]
    fixture = bpy.data.scenes.new("GAI_Loose_"+token)
    fixture["gameassetai_test_owner"] = token
    owned = []
    checks = []

    def own(id, collection):
        id["gameassetai_test_owner"] = token
        owned.append((id,collection))
        return id

    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    def remember_result(report):
        check("created_"+str(len(checks)),report["status"]=="created")
        obj = bpy.data.objects[report["object"]]
        mesh = obj.data
        check("owner_token_"+str(len(checks)),obj.get("gameassetai_copy_owner")==report["owner_token"]
              and mesh.get("gameassetai_copy_owner")==report["owner_token"])
        own(obj,bpy.data.objects)
        own(mesh,bpy.data.meshes)
        return obj

    def run(obj, **options):
        if options.get("apply") and "expected_source_sha256" not in options:
            preview_options={k:v for k,v in options.items() if k not in {"apply","result_name"}}
            preview=cleanup_loose_geometry(obj.name,scene_name=fixture.name,**preview_options)
            options["expected_source_sha256"]=preview.get("source_sha256")
        return cleanup_loose_geometry(obj.name,scene_name=fixture.name,**options)

    try:
        mesh = own(bpy.data.meshes.new("GAI_SourceMesh_"+token),bpy.data.meshes)
        # Removal shifts surface indices: isolated vertex first, not only last.
        mesh.from_pydata([(9,9,9),(0,0,0),(1,0,0),(0,1,0),(5,0,0),(6,0,0)],
                         [(4,5)],[(1,2,3)])
        source = own(bpy.data.objects.new("GAI_Source_"+token,mesh),bpy.data.objects)
        fixture.collection.objects.link(source)
        linked = own(bpy.data.objects.new("GAI_Linked_"+token,mesh),bpy.data.objects)
        fixture.collection.objects.link(linked)
        material = own(bpy.data.materials.new("GAI_Material_"+token),bpy.data.materials)
        mesh.materials.append(material)
        uv = mesh.uv_layers.new(name="FixtureUV")
        for item, value in zip(uv.data,[(0,0),(1,0),(0,1)]):
            item.uv = value
        mesh.polygons[0].use_smooth = True
        original = _loose_state(source)
        id_names = [[id.name for id in c] for c in collections]
        report = run(source,remove_isolated_vertices=True,remove_wire_edges=True)
        if report["status"]!="preview":
            raise AssertionError("preview failed: "+json.dumps(report))
        check("preview_indices",report["isolated_vertices"]==[0,4,5]
              and len(report["wire_edges"])==1)
        check("preview_no_ids",id_names==[[id.name for id in c] for c in collections])
        explicit_preview = report
        report = run(source,apply=True,result_name="GAI_NoOp_"+token)
        check("no_implicit_removal",report["status"]=="no_change")
        check("no_op_no_ids",id_names==[[id.name for id in c] for c in collections])
        # Real workflow passes explicit preview data, not the convenience run wrapper.
        result = remember_result(cleanup_loose_geometry(source.name,scene_name=fixture.name,
                                     apply=True,result_name="GAI_Clean_"+token,
                                     remove_isolated_vertices=True,remove_wire_edges=True,
                                     expected_source_sha256=explicit_preview["source_sha256"]))
        check("surface_and_uv_retained",_loose_surface(result.data)==original["surface"])
        check("source_and_linked_preserved",_loose_state(source)==original and linked.data==mesh)
        check("independent_mesh",result.data!=mesh and len(result.data.vertices)==3)
        check("materials_shared",result.data.materials[0]==material)
        result.data.vertices[0].co.z=1
        check("copy_edit_cannot_change_source",_loose_state(source)==original)
        wire_only = remember_result(run(source,apply=True,result_name="GAI_Wire_"+token,remove_wire_edges=True))
        check("wire_endpoints_preserved_without_permission",len(wire_only.data.vertices)==6)
        isolated_only = remember_result(run(source,apply=True,result_name="GAI_Isolated_"+token,
                                            remove_isolated_vertices=True))
        check("wire_retained_without_permission",len(isolated_only.data.vertices)==5 and len(isolated_only.data.edges)==4)
        # User-reported installed workflow: quad + isolated vertex + wire endpoints.
        quad_mesh=own(bpy.data.meshes.new("GAI_QuadMesh_"+token),bpy.data.meshes)
        quad_mesh.from_pydata([(9,9,9),(0,0,0),(1,0,0),(1,1,0),(0,1,0),(5,0,0),(6,0,0)],
                             [(5,6)],[(1,2,3,4)])
        quad=own(bpy.data.objects.new("GAI_Quad_"+token,quad_mesh),bpy.data.objects)
        fixture.collection.objects.link(quad)
        quad_uv=quad_mesh.uv_layers.new(name="QuadUV")
        for item,value in zip(quad_uv.data,[(0,0),(1,0),(1,1),(0,1)]):
            item.uv=value
        quad_before=_loose_state(quad)
        quad_preview=run(quad,remove_isolated_vertices=True,remove_wire_edges=True)
        check("quad_preview_categories",quad_preview["status"]=="preview"
              and quad_preview["isolated_vertices"]==[0,5,6] and len(quad_preview["wire_edges"])==1)
        quad_copy=remember_result(cleanup_loose_geometry(quad.name,scene_name=fixture.name,
            apply=True,result_name="GAI_QuadClean_"+token,
            remove_isolated_vertices=True,remove_wire_edges=True,
            expected_source_sha256=quad_preview["source_sha256"]))
        check("quad_counts_7_to_4",len(quad_mesh.vertices)==7 and len(quad_mesh.edges)==5
              and len(quad_copy.data.vertices)==4 and len(quad_copy.data.edges)==4
              and len(quad_copy.data.polygons)==1)
        check("quad_surface_uv_source_preserved",_loose_state(quad)==quad_before
              and _loose_surface(quad_copy.data)==quad_before["surface"] and quad_copy.data!=quad_mesh)
        cleaned_preview=run(quad_copy,remove_isolated_vertices=True,remove_wire_edges=True)
        check("quad_no_remaining_loose_geometry",cleaned_preview["status"]=="preview"
              and cleaned_preview["isolated_vertices"]==[] and cleaned_preview["wire_edges"]==[])
        quad_wire=remember_result(run(quad,apply=True,result_name="GAI_QuadWire_"+token,remove_wire_edges=True))
        check("quad_wire_only_retains_all_vertices",len(quad_wire.data.vertices)==7
              and len(quad_wire.data.edges)==4 and _loose_surface(quad_wire.data)==quad_before["surface"])
        id_names = [[id.name for id in c] for c in collections]
        copy_before_collision = _loose_state(result)
        collision = run(source,apply=True,result_name=result.name,remove_wire_edges=True)
        check("collision_refused",collision["status"]=="error")
        check("collision_preserves_existing_copy",_loose_state(result)==copy_before_collision)
        check("invalid_boolean",run(source,remove_wire_edges="yes")["status"]=="error")
        check("missing_name",cleanup_loose_geometry("__missing_"+token)["status"]=="error")
        check("no_implicit_source",cleanup_loose_geometry(None)["status"]=="error")
        check("missing_result_name",run(source,apply=True,remove_wire_edges=True)["status"]=="error")
        check("failure_no_new_ids",id_names==[[id.name for id in c] for c in collections])
        stale = run(source,remove_wire_edges=True)["source_sha256"]
        before_stale = _loose_state(source)
        original_coordinate = tuple(source.data.vertices[0].co)
        source.data.vertices[0].co.z += 0.1
        changed_source = _loose_state(source)
        stale_result = run(source,apply=True,result_name="GAI_Stale_"+token,
                           remove_wire_edges=True,expected_source_sha256=stale)
        check("stale_preview_guard",stale_result["status"]=="error")
        check("stale_refusal_preserves_changed_source_and_ids",_loose_state(source)==changed_source
              and id_names==[[id.name for id in c] for c in collections])
        source.data.vertices[0].co = original_coordinate
        check("stale_fixture_coordinate_exactly_restored",_loose_state(source)==before_stale)
        check("missing_preview_guard",run(source,apply=True,result_name="GAI_NoPreview_"+token,
              remove_wire_edges=True,expected_source_sha256=None)["status"]=="error")
        globals_ = cleanup_loose_geometry.__globals__
        write = globals_["_loose_write"]
        try:
            def fail_write(*args):
                raise RuntimeError("simulated copied-mesh failure")
            globals_["_loose_write"] = fail_write
            failure = run(source,apply=True,result_name="GAI_Failure_"+token,remove_wire_edges=True)
        finally:
            globals_["_loose_write"] = write
        check("failed_copy_rolled_back",failure["status"]=="error" and failure["failure_cleanup"]=="complete")
        check("failure_no_leaks",id_names==[[id.name for id in c] for c in collections])
        try:
            def corrupt_surface(mesh,*options):
                write(mesh,*options)
                mesh.vertices[1].co.z += 1
            globals_["_loose_write"]=corrupt_surface
            failure=run(source,apply=True,result_name="GAI_BadSurface_"+token,remove_wire_edges=True)
        finally:
            globals_["_loose_write"]=write
        check("changed_surface_validation_refused",failure["status"]=="error"
              and "surface/UV/material/transform" in failure["errors"][0] and failure["failure_cleanup"]=="complete")
        check("validation_failure_no_leaks",id_names==[[id.name for id in c] for c in collections])
        source.location = (2,3,4)
        source.scale = (2,1,0.5)
        source.rotation_euler = (0.2,0.3,0.4)
        fixture.view_layers[0].update()
        transformed = _loose_state(source)
        transformed_copy=remember_result(run(source,apply=True,result_name="GAI_Transform_"+token,remove_wire_edges=True))
        check("nonidentity_transforms_retained",_loose_state(transformed_copy)["matrix"]==transformed["matrix"]
              and _loose_state(source)==transformed)
        source.rotation_euler.x=float("nan")
        check("nonfinite_unflushed_rotation_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.rotation_euler.x=0.2
        source.parent=linked
        check("parent_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.parent=None
        types = {i.identifier for i in bpy.types.ObjectModifiers.bl_rna.functions["new"].parameters["type"].enum_items}
        check("modifier_enum_available","SUBSURF" in types)
        modifier=source.modifiers.new("PreserveModifier","SUBSURF")
        check("modifier_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.modifiers.remove(modifier)
        source.vertex_groups.new(name="PreserveGroup")
        check("vertex_group_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.vertex_groups.clear()
        source.shape_key_add(name="Basis")
        check("shape_key_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.shape_key_clear()
        source.keyframe_insert(data_path="location",frame=1)
        action = own(source.animation_data.action,bpy.data.actions)
        check("animation_source_guard",run(source,remove_wire_edges=True)["status"]=="error")
        blocked=run(wire_only,apply=True,result_name="GAI_Blocked_"+token,remove_isolated_vertices=True)
        check("unrelated_animation_apply_guard",blocked["status"]=="error" and "Apply blocked" in blocked["errors"][0])
        source.animation_data_clear()
        source.data.attributes.new("UnsupportedColor", "FLOAT", "POINT")
        check("generic_attribute_guard",run(source,remove_wire_edges=True)["status"]=="error")
        source.data.attributes.remove(source.data.attributes["UnsupportedColor"])
        mesh.vertices[0].co.x=float("nan")
        check("nonfinite_guard",run(source,remove_wire_edges=True)["status"]=="error")
        mesh.vertices[0].co.x=9
        window=bpy.context.window
        original_layer=bpy.context.view_layer
        try:
            window.scene=fixture
            fixture.view_layers[0].objects.active=source
            source.select_set(True)
            modes={i.identifier for i in bpy.ops.object.mode_set.get_rna_type().properties["mode"].enum_items}
            check("mode_enum_available",{"EDIT","OBJECT"}.issubset(modes))
            bpy.ops.object.mode_set(mode="EDIT")
            check("edit_mode_guard",run(source,remove_wire_edges=True)["status"]=="error")
            check("edit_mode_not_changed",bpy.context.mode=="EDIT_MESH")
        finally:
            if window.scene==fixture and bpy.context.mode!="OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            window.scene=original_scene
            window.view_layer=original_layer
        check("no_original_mode_selection_change",bpy.context.scene==original_scene and bpy.context.mode=="OBJECT")
    finally:
        for id,collection in owned:
            if collection.get(id.name)!=id or id.get("gameassetai_test_owner")!=token:
                raise RuntimeError("Fixture ownership changed; cleanup aborted")
        for id,collection in owned:
            if collection==bpy.data.objects:
                if any(c!=fixture.collection for c in id.users_collection):
                    raise RuntimeError("External fixture link; cleanup aborted")
        for id,collection in owned:
            if collection==bpy.data.objects:
                collection.remove(id,do_unlink=True)
        for collection in (bpy.data.meshes,bpy.data.actions,bpy.data.materials):
            for id,owner_collection in owned:
                if owner_collection==collection:
                    if id.users:
                        raise RuntimeError("Unexpected users; cleanup aborted")
                    collection.remove(id)
        bpy.data.scenes.remove(fixture)
    check("original_fingerprint_restored",source_fingerprint(original_scene)==before)
    check("all_names_restored",names_before==[[id.name for id in c] for c in collections])
    return {"status":"passed","check_count":len(checks),"checks":checks,
            "fixture_cleanup":"complete","source_fingerprint":before,
            "safety_refusals": {"existing_result_name": collision,
                                "changed_source_old_preview": stale_result}}
