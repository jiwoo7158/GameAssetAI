"""Native staged texture-free FBX export on exact owned synthetic data."""
from pathlib import Path
import hashlib
import json
import uuid
import bpy


def run_fbx_staged_export_tests(*, artifact_root):
    if bpy.context.mode != "OBJECT":
        raise RuntimeError("Object mode required; do not force mode")
    root = Path(artifact_root).resolve(strict=True)
    if root.name != "validation" or root.parent.name != ".local" or root.is_symlink():
        raise ValueError("Artifact root must be a real repository .local/validation directory")
    original = bpy.context.scene
    original_fingerprint = source_fingerprint(original)
    tracked = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes,
               bpy.data.materials, bpy.data.actions, bpy.data.images)
    names = [[item.name for item in collection] for collection in tracked]
    token = uuid.uuid4().hex
    owned = root / ("gameassetai-staged-" + token)
    owned.mkdir(mode=0o700)
    scene = bpy.data.scenes.new("GAI_Staged_" + token)
    mesh = bpy.data.meshes.new("GAI_StagedMesh_" + token)
    obj = bpy.data.objects.new("GAI_StagedObject_" + token, mesh)
    material = bpy.data.materials.new("GAI_StagedMaterial_" + token)
    for item in (scene, mesh, obj, material):
        item["gameassetai_test_owner"] = token
    scene.collection.objects.link(obj)
    mesh.from_pydata([(0, 0, 0), (2, 0, 0), (2, 1, 0), (0, 1, 0)],
                     [], [(0, 1, 2), (0, 2, 3)])
    mesh.uv_layers.new(name="ProbeUV")
    mesh.materials.append(material)
    request = {"schema": "gameassetai.static-fbx-request.v1", "scene_name": scene.name,
               "object_name": obj.name, "target_file": str(owned / "published.fbx"),
               "axis_forward": "-Z", "axis_up": "Y", "global_scale": 1,
               "apply_unit_scale": False, "apply_scale_options": "FBX_SCALE_NONE",
               "use_space_transform": True, "bake_space_transform": False,
               "use_mesh_modifiers": False,
               "path_mode": "AUTO", "overwrite": False}
    def preflight(values=request):
        canonical = json.dumps(values, sort_keys=True, ensure_ascii=True,
                               separators=(",", ":"), allow_nan=False)
        return {"schema": values["schema"], "ready_for_blender_inspection": True,
                "errors": [], "request_sha256": hashlib.sha256(canonical.encode()).hexdigest()}
    def candidate(values=request):
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            return inspect_static_fbx_candidate(values, preflight(values))
    def export(values=request, observed=None, authorize=True):
        if observed is None:
            observed = candidate(values)
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            return export_static_fbx_staged(values, preflight(values), observed,
                                             authorize=authorize)
    checks = []
    def check(label, condition):
        if not condition:
            raise AssertionError(label)
        checks.append(label)
    try:
        denied = export(authorize=False)
        check("authorization_refused", denied["status"] == "error"
              and not list(owned.iterdir()))
        stale_candidate = candidate()
        mesh.vertices[0].co.x = 0.25
        stale = export(observed=stale_candidate)
        check("stale_candidate_refused", stale["status"] == "error"
              and not list(owned.iterdir()))
        mesh.vertices[0].co.x = 0.0
        result = export()
        target = owned / "published.fbx"
        check("published_one_fbx", result["status"] == "created"
              and result["target_created"] and result["stage_cleaned"]
              and list(owned.iterdir()) == [target])
        content = target.read_bytes()
        check("published_verified", result["bytes"] == len(content)
              and result["sha256"] == hashlib.sha256(content).hexdigest()
              and result["sidecars"] == [])
        check("source_preserved", candidate()["source_fingerprint"] == result["source_fingerprint"])
        race_request = dict(request, target_file=str(owned / "meta-race.fbx"))
        race_observed = candidate(race_request)
        real_inspector = inspect_static_fbx_candidate
        calls = [0]
        def inject_meta_race(values, report):
            observed = real_inspector(values, report)
            calls[0] += 1
            if calls[0] == 2:
                Path(str(values["target_file"]) + ".meta").write_bytes(b"owned-meta-race")
            return observed
        globals()["inspect_static_fbx_candidate"] = inject_meta_race
        try:
            raced = export(race_request, race_observed)
        finally:
            globals()["inspect_static_fbx_candidate"] = real_inspector
        race_meta = Path(str(race_request["target_file"]) + ".meta")
        check("meta_race_refused", raced["status"] == "error"
              and not Path(race_request["target_file"]).exists()
              and race_meta.read_bytes() == b"owned-meta-race"
              and not any(".gameassetai-" in p.name for p in owned.iterdir()))
        race_meta.unlink()
        second_request = dict(request, target_file=str(owned / "collision.fbx"))
        collision = owned / "collision.fbx"
        collision.write_bytes(b"owned-sentinel")
        refused = export(second_request)
        check("collision_preserved", refused["status"] == "error"
              and collision.read_bytes() == b"owned-sentinel")
        check("no_stage_leak", not any(".gameassetai-" in p.name for p in owned.iterdir()))
    finally:
        expected = {p for p in (owned / "published.fbx", owned / "collision.fbx") if p.exists()}
        if set(owned.iterdir()) != expected or any(not p.is_file() or p.is_symlink() for p in expected):
            raise RuntimeError("Unexpected staged-export artifacts; cleanup stopped")
        for path in expected:
            path.unlink()
        owned.rmdir()
        if any(item.get("gameassetai_test_owner") != token for item in (scene, mesh, obj, material)):
            raise RuntimeError("Fixture ownership mismatch; cleanup stopped")
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users:
            raise RuntimeError("Unexpected Mesh users; cleanup stopped")
        bpy.data.meshes.remove(mesh)
        if material.users:
            raise RuntimeError("Unexpected Material users; cleanup stopped")
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("blender_ids_restored", names == [[item.name for item in collection] for collection in tracked])
    check("original_preserved", source_fingerprint(original) == original_fingerprint)
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "fixture_cleanup": "complete", "artifact_cleanup": "complete",
            "source_fingerprint": original_fingerprint}
