"""Stage one reviewed depth-pass Mesh copy into an owned temporary blend file."""
from __future__ import annotations

import hashlib
from pathlib import Path
import uuid


def stage_2d_depth_pass_source(request, preflight, candidate, framing, stage_file, *, authorize=False):
    report = {"schema": "gameassetai.2d-depth-pass-source-stage.v1", "status": "error",
              "errors": [], "source_stage_created": False, "png_published": False}
    stage = None
    write_started = False
    temp_scene = temp_object = temp_mesh = None
    try:
        if authorize is not True:
            raise ValueError("Explicit source-stage authorization is required")
        fresh_preflight = validate_2d_depth_pass_request(request)
        if (not fresh_preflight["ready_for_blender_inspection"]
                or fresh_preflight["request_sha256"] != preflight.get("request_sha256")):
            raise ValueError("Request preflight is stale or invalid")
        fresh_candidate = inspect_2d_depth_pass_candidate(request, fresh_preflight)
        if fresh_candidate["status"] != "candidate_for_review":
            raise ValueError("Current source is not a depth-pass candidate")
        for key in ("request_sha256", "source_fingerprint", "setup_fingerprint", "output_fingerprint"):
            if fresh_candidate.get(key) != candidate.get(key):
                raise ValueError("Candidate changed before source staging")
        fresh_framing = preview_2d_depth_pass_framing(request, fresh_candidate)
        if (fresh_framing["status"] != "planned"
                or fresh_framing.get("plan_fingerprint") != framing.get("plan_fingerprint")):
            raise ValueError("Framing changed before source staging")

        stage = Path(stage_file)
        target = Path(request["output"]["target_file"])
        if (not stage.is_absolute() or stage.parent != target.parent
                or not stage.name.startswith(".gameassetai-depth-pass-")
                or not stage.name.endswith(".stage.blend")):
            raise ValueError("Stage must be an owned hidden .stage.blend beside the target")
        if stage.exists() or stage.is_symlink():
            raise ValueError("Source stage already exists")
        if target.exists() or Path(str(target) + ".meta").exists():
            raise ValueError("Output target or .meta appeared before source staging")

        source_scene = bpy.data.scenes[fresh_candidate["scene"]]
        source_object = source_scene.objects[fresh_candidate["object"]]
        token = uuid.uuid4().hex
        temp_scene = bpy.data.scenes.new("GAI_DepthPassScene_" + token)
        temp_mesh = source_object.data.copy()
        temp_mesh.name = "GAI_DepthPassMesh_" + token
        temp_object = source_object.copy()
        temp_object.name = "GAI_DepthPassObject_" + token
        temp_object.data, temp_object.parent = temp_mesh, None
        temp_object.animation_data_clear()
        temp_scene.collection.objects.link(temp_object)
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
                      stage_sha256=hashlib.sha256(data).hexdigest())
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
        report["errors"].append(str(exc))
        if write_started and stage is not None and stage.exists():
            try:
                stage.unlink()
            except OSError as cleanup:
                report["errors"].append("stage cleanup failed: " + str(cleanup))
    finally:
        if temp_object is not None and bpy.data.objects.get(temp_object.name) == temp_object:
            bpy.data.objects.remove(temp_object, do_unlink=True)
        if temp_mesh is not None and bpy.data.meshes.get(temp_mesh.name) == temp_mesh:
            bpy.data.meshes.remove(temp_mesh)
        if temp_scene is not None and bpy.data.scenes.get(temp_scene.name) == temp_scene:
            bpy.data.scenes.remove(temp_scene)
    return report



