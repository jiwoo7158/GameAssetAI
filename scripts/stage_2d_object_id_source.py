"""Stage reviewed Mesh copies for an explicit multi-Object color-ID pass."""
from __future__ import annotations

import hashlib
from pathlib import Path
import uuid


def stage_2d_object_id_source(request, preflight, candidate, framing, stage_file, *, authorize=False):
    report = {"schema": "gameassetai.2d-object-id-source-stage.v1", "status": "error",
              "errors": [], "source_stage_created": False, "png_published": False}
    stage, created_data = None, []
    write_started = False
    temp_scene = None
    try:
        if authorize is not True:
            raise ValueError("Explicit Object-ID source-stage authorization is required")
        fresh_preflight = validate_2d_object_id_request(request)
        if (not fresh_preflight["ready_for_blender_inspection"]
                or fresh_preflight["request_sha256"] != preflight.get("request_sha256")):
            raise ValueError("Request preflight is stale or invalid")
        fresh_candidate = inspect_2d_object_id_candidate(request, fresh_preflight)
        if fresh_candidate["status"] != "candidate_for_review":
            raise ValueError("Current source is not an Object-ID candidate")
        for key in ("request_sha256", "source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if fresh_candidate.get(key) != candidate.get(key):
                raise ValueError("Candidate changed before source staging")
        fresh_framing = preview_2d_object_id_framing(request, fresh_candidate)
        if (fresh_framing["status"] != "planned"
                or fresh_framing.get("plan_fingerprint") != framing.get("plan_fingerprint")):
            raise ValueError("Framing changed before source staging")
        stage, target = Path(stage_file), Path(request["output"]["target_file"])
        if (not stage.is_absolute() or stage.parent != target.parent
                or not stage.name.startswith(".gameassetai-object-id-")
                or not stage.name.endswith(".stage.blend")):
            raise ValueError("Stage must be an owned hidden .stage.blend beside the target")
        if stage.exists() or stage.is_symlink():
            raise ValueError("Object-ID source stage already exists")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta appeared before source staging")

        scene = bpy.data.scenes[fresh_candidate["scene"]]
        names = [item["name"] for item in fresh_candidate["objects"]]
        token = uuid.uuid4().hex
        temp_scene = bpy.data.scenes.new("GAI_ObjectIdScene_" + token)
        for index, name in enumerate(names):
            source = scene.objects[name]
            mesh = source.data.copy()
            mesh.name = "GAI_ObjectIdMesh_" + str(index) + "_" + token
            obj = source.copy()
            obj.name = "GAI_ObjectIdObject_" + str(index) + "_" + token
            obj.data, obj.parent = mesh, None
            obj.animation_data_clear()
            obj["gameassetai_object_id_index"] = index + 1
            obj["gameassetai_object_id_source_name"] = name
            temp_scene.collection.objects.link(obj)
            created_data.append((obj, mesh))
        write_started = True
        bpy.data.libraries.write(str(stage), {temp_scene}, path_remap="ABSOLUTE",
                                 fake_user=False, compress=False)
        data = stage.read_bytes()
        if not data.startswith(b"BLENDER") or len(data) < 64:
            raise RuntimeError("Staged blend file failed structural verification")
        report.update(status="created", source_stage_created=True,
                      request_sha256=fresh_candidate["request_sha256"],
                      source_fingerprint=fresh_candidate["source_fingerprint"],
                      setup_fingerprint=fresh_candidate["setup_fingerprint"],
                      output_fingerprint=fresh_candidate["output_fingerprint"],
                      plan_fingerprint=fresh_framing["plan_fingerprint"],
                      stage_file=str(stage), stage_size=len(data),
                      stage_sha256=hashlib.sha256(data).hexdigest(), staged_objects=len(names))
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
        report["errors"].append(str(exc))
        if write_started and stage is not None and stage.exists():
            try:
                stage.unlink()
            except OSError as cleanup:
                report["errors"].append("stage cleanup failed: " + str(cleanup))
    finally:
        for obj, mesh in created_data:
            if bpy.data.objects.get(obj.name) == obj:
                bpy.data.objects.remove(obj, do_unlink=True)
            if bpy.data.meshes.get(mesh.name) == mesh:
                bpy.data.meshes.remove(mesh)
        if temp_scene is not None and bpy.data.scenes.get(temp_scene.name) == temp_scene:
            bpy.data.scenes.remove(temp_scene)
    return report
