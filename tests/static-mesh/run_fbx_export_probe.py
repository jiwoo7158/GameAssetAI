"""One synthetic FBX file probe; no game profile or engine-import assertion."""
from pathlib import Path
import uuid
import bpy


def run_fbx_export_probe(*, artifact_root):
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Object mode required; do not force mode")
    root = Path(artifact_root).resolve(strict=True)
    if root.name != "validation" or root.parent.name != ".local":
        raise ValueError("Probe root must be a repository .local/validation directory")
    original = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selected = tuple(o.name for o in bpy.context.selected_objects)
    fingerprint = source_fingerprint(original)
    tracked = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes,
               bpy.data.materials, bpy.data.actions, bpy.data.images)
    names = [[item.name for item in collection] for collection in tracked]
    token = uuid.uuid4().hex
    fixture = bpy.data.scenes.new("GAI_FBXProbe_" + token)
    mesh = bpy.data.meshes.new("GAI_FBXProbeMesh_" + token)
    obj = bpy.data.objects.new("GAI_FBXProbeObject_" + token, mesh)
    material = bpy.data.materials.new("GAI_FBXProbeMaterial_" + token)
    for item in (fixture, mesh, obj, material):
        item["gameassetai_test_owner"] = token
    fixture.collection.objects.link(obj)
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    uv_layer = mesh.uv_layers.new(name="ProbeUV")
    for entry, uv in zip(uv_layer.data, ((0, 0), (1, 0), (0, 1))):
        entry.uv = uv
    mesh.materials.append(material)
    obj.location = (1, 2, 3)
    obj.scale = (2, 1, 1)
    owned_dir = root / ("gameassetai-fbx-" + token)
    owned_file = owned_dir / "probe.fbx"
    collision_file = owned_dir / "collision.fbx"
    published_file = owned_dir / "published.fbx"
    imported_scene = None
    imported_objects = []
    imported_meshes = []
    imported_materials = []
    checks = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    try:
        owned_dir.mkdir(mode=0o700)
        assert owned_dir.resolve() == root / owned_dir.name
        with bpy.context.temp_override(scene=fixture, view_layer=fixture.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            check("operator_poll", bpy.ops.export_scene.fbx.poll())
            observed_scope = (bpy.context.scene == fixture,
                              [item.name for item in bpy.context.selected_objects])
            outcome = bpy.ops.export_scene.fbx(
                filepath=str(owned_file), use_selection=True, object_types={"MESH"},
                bake_anim=False, use_mesh_modifiers=False, path_mode="AUTO",
                axis_forward="-Z", axis_up="Y", global_scale=1.0, apply_unit_scale=False)
        check("operator_finished", "FINISHED" in outcome)
        check("one_regular_artifact", owned_file.is_file() and not owned_file.is_symlink()
              and list(owned_dir.iterdir()) == [owned_file])
        content = owned_file.read_bytes()
        check("fbx_binary_header", content.startswith(b"Kaydara FBX Binary"))
        model_record = obj.name.encode("utf-8") + b"\x00\x01Model"
        check("synthetic_model_record_present", model_record in content)
        hits = {}
        for name in ("Cube", "Light", "Camera"):
            position = content.find(name.encode("utf-8") + b"\x00\x01Model")
            if position >= 0:
                hits[name] = position
        check("temp_override_scope", observed_scope == (True, [obj.name]))
        check("unrelated_original_model_records_absent", not hits)
        imported_scene = bpy.data.scenes.new("GAI_FBXImport_" + token)
        imported_scene["gameassetai_test_owner"] = token
        before_objects = set(bpy.data.objects)
        before_meshes = set(bpy.data.meshes)
        before_materials = set(bpy.data.materials)
        with bpy.context.temp_override(scene=imported_scene,
                                       view_layer=imported_scene.view_layers[0]):
            check("import_operator_poll", bpy.ops.import_scene.fbx.poll())
            import_outcome = bpy.ops.import_scene.fbx(
                filepath=str(owned_file), use_anim=False, use_image_search=False)
        imported_objects = list(set(bpy.data.objects) - before_objects)
        imported_meshes = list(set(bpy.data.meshes) - before_meshes)
        imported_materials = list(set(bpy.data.materials) - before_materials)
        for item in (*imported_objects, *imported_meshes, *imported_materials):
            item["gameassetai_test_owner"] = token
        check("import_operator_finished", "FINISHED" in import_outcome)
        check("one_imported_mesh", len(imported_objects) == len(imported_meshes) == 1
              and imported_objects[0].data == imported_meshes[0]
              and imported_objects[0].type == "MESH")
        check("import_scope", list(imported_objects[0].users_collection) == [imported_scene.collection])
        check("import_surface", len(imported_meshes[0].vertices) == 3
              and len(imported_meshes[0].polygons) == 1
              and len(imported_meshes[0].uv_layers) == 1)
        check("import_material_reference", len(imported_meshes[0].materials) == 1
              and imported_meshes[0].materials[0] is not None)
        source_positions = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        imported_positions = [imported_objects[0].matrix_world @ vertex.co
                              for vertex in imported_meshes[0].vertices]
        world_residual = max(min((point - candidate).length for candidate in imported_positions)
                             for point in source_positions)
        check("blender_roundtrip_world_positions", world_residual <= 1e-5)
        source_uv = sorted(tuple(round(component, 6) for component in entry.uv)
                           for entry in mesh.uv_layers[0].data)
        imported_uv = sorted(tuple(round(component, 6) for component in entry.uv)
                             for entry in imported_meshes[0].uv_layers[0].data)
        check("blender_roundtrip_uv_values", source_uv == imported_uv)
        sentinel = ("GAI_TEST_OWNED_" + token).encode("ascii")
        with collision_file.open("xb") as handle:
            handle.write(sentinel)
        check("collision_sentinel_owned", collision_file.read_bytes() == sentinel)
        with bpy.context.temp_override(scene=fixture, view_layer=fixture.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            collision_result = bpy.ops.export_scene.fbx(
                filepath=str(collision_file), check_existing=False, use_selection=True,
                object_types={"MESH"}, bake_anim=False, use_mesh_modifiers=False,
                path_mode="AUTO", axis_forward="-Z", axis_up="Y",
                global_scale=1.0, apply_unit_scale=False)
        check("native_overwrite_hazard_observed", "FINISHED" in collision_result
              and collision_file.read_bytes().startswith(b"Kaydara FBX Binary"))
        publication = promote_export_artifact(owned_file, published_file)
        check("atomic_no_overwrite_publish", publication["status"] == "published"
              and not publication["overwrite_performed"]
              and owned_file.read_bytes() == published_file.read_bytes())
        published_bytes = published_file.read_bytes()
        try:
            promote_export_artifact(collision_file, published_file)
        except FileExistsError:
            blocked = True
        else:
            blocked = False
        check("publication_collision_preserves_target", blocked
              and published_file.read_bytes() == published_bytes
              and collision_file.is_file())
        check("context_unchanged", bpy.context.scene == original
              and bpy.context.view_layer.objects.active == original_active
              and tuple(o.name for o in bpy.context.selected_objects) == original_selected)
        check("original_preserved_before_cleanup", source_fingerprint(original) == fingerprint)
        byte_count = len(content)
    finally:
        for item in imported_objects:
            if (item.get("gameassetai_test_owner") != token
                    or any(c not in (imported_scene.collection, original.collection)
                           for c in item.users_collection)):
                raise RuntimeError("Unexpected imported Object ownership/links; cleanup stopped")
            bpy.data.objects.remove(item, do_unlink=True)
        for item in imported_meshes:
            if item.get("gameassetai_test_owner") != token or item.users:
                raise RuntimeError("Unexpected imported Mesh users; cleanup stopped")
            bpy.data.meshes.remove(item)
        for item in imported_materials:
            if item.get("gameassetai_test_owner") != token or item.users:
                raise RuntimeError("Unexpected imported Material users; cleanup stopped")
            bpy.data.materials.remove(item)
        if imported_scene is not None:
            if imported_scene.get("gameassetai_test_owner") != token or len(imported_scene.objects):
                raise RuntimeError("Unexpected imported Scene users; cleanup stopped")
            bpy.data.scenes.remove(imported_scene)
        # Exact newly owned path only; unexpected artifacts remain for inspection.
        if owned_dir.exists():
            expected = {path for path in (owned_file, collision_file, published_file) if path.exists()}
            if (set(owned_dir.iterdir()) == expected
                    and all(path.is_file() and not path.is_symlink()
                            and path.resolve(strict=True).parent == owned_dir.resolve(strict=True)
                            for path in expected)):
                for path in expected:
                    path.unlink()
                owned_dir.rmdir()
            elif list(owned_dir.iterdir()):
                raise RuntimeError("Unexpected FBX probe artifacts; cleanup stopped")
            else:
                owned_dir.rmdir()
        assert all(item.get("gameassetai_test_owner") == token for item in (fixture, mesh, obj, material))
        assert obj.data == mesh and list(obj.users_collection) == [fixture.collection]
        bpy.data.objects.remove(obj, do_unlink=True)
        assert mesh.users == 0
        bpy.data.meshes.remove(mesh)
        assert material.users == 0
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(fixture)
    check("blender_ids_restored", names == [[item.name for item in collection] for collection in tracked])
    check("original_preserved", source_fingerprint(original) == fingerprint)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "artifact_cleanup": "complete", "fixture_cleanup": "complete",
            "fbx_byte_count": byte_count, "test_axis_forward": "-Z", "test_axis_up": "Y",
            "test_global_scale": 1.0, "test_apply_unit_scale": False,
            "blender_roundtrip_world_residual": world_residual,
            "engine_import_certified": False, "source_fingerprint": fingerprint}
