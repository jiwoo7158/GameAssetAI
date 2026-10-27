"""Development-only texture-free static FBX stage/verify/publish operation.

Load inspect_static_fbx_candidate and promote_export_artifact first. This function
never overwrites and never removes a published target. Callers own target cleanup.
"""
from pathlib import Path
import hashlib
import uuid
import bpy


def export_static_fbx_staged(request, request_preflight, candidate, *, authorize=False):
    report = {"schema": "gameassetai.static-fbx-staged.v1", "status": "error",
              "errors": [], "overwrite_performed": False, "target_created": False,
              "stage_cleaned": False, "export_authorized": authorize is True}
    stage = None
    target = None
    published = False
    try:
        if authorize is not True:
            raise ValueError("Explicit authorize=True required")
        current = inspect_static_fbx_candidate(request, request_preflight)
        if (current["status"] != "candidate_for_review" or current["blockers"]
                or candidate.get("status") != "candidate_for_review"
                or candidate.get("request_sha256") != current.get("request_sha256")
                or candidate.get("source_fingerprint") != current.get("source_fingerprint")):
            raise ValueError("Candidate is missing, blocked, or stale")
        target = Path(request["target_file"])
        meta = Path(str(target) + ".meta")
        if (_export_path_is_link(target) or target.exists()
                or _export_path_is_link(meta) or meta.exists()):
            raise FileExistsError("Target or target .meta now exists; overwrite refused")
        token = uuid.uuid4().hex
        stage = target.parent / ("." + target.stem + ".gameassetai-" + token + ".stage.fbx")
        stage_sidecar = stage.with_suffix(".fbm")
        if stage.exists() or _export_path_is_link(stage) or stage_sidecar.exists() or _export_path_is_link(stage_sidecar):
            raise FileExistsError("Unique stage or sidecar collision")
        scene = bpy.data.scenes[request["scene_name"]]
        obj = scene.objects[request["object_name"]]
        with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0],
                                       active_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            outcome = bpy.ops.export_scene.fbx(
                filepath=str(stage), check_existing=False, use_selection=True,
                object_types={"MESH"}, bake_anim=False,
                use_mesh_modifiers=request["use_mesh_modifiers"],
                path_mode=request["path_mode"], axis_forward=request["axis_forward"],
                axis_up=request["axis_up"], global_scale=request["global_scale"],
                apply_unit_scale=request["apply_unit_scale"],
                apply_scale_options=request["apply_scale_options"],
                use_space_transform=request["use_space_transform"],
                bake_space_transform=request["bake_space_transform"])
        if "FINISHED" not in outcome or not stage.is_file() or _export_path_is_link(stage):
            raise RuntimeError("FBX stage was not created as a regular file")
        if stage_sidecar.exists() or _export_path_is_link(stage_sidecar):
            raise RuntimeError("Unexpected FBX sidecar; preserve stage tree for inspection")
        content = stage.read_bytes()
        if not content.startswith(b"Kaydara FBX Binary"):
            raise RuntimeError("Staged file is not binary FBX")
        model_record = obj.name.encode("utf-8") + b"\x00\x01Model"
        if model_record not in content:
            raise RuntimeError("Requested Object model record missing from staged FBX")
        current_after = inspect_static_fbx_candidate(request, request_preflight)
        if (current_after.get("source_fingerprint") != current["source_fingerprint"]
                or current_after.get("status") != "candidate_for_review"):
            raise RuntimeError("Blender source changed during staged export")
        if (_export_path_is_link(target) or target.exists()
                or _export_path_is_link(meta) or meta.exists()):
            raise FileExistsError("Target or target .meta appeared before publication")
        publication = promote_export_artifact(stage, target)
        published = True
        if (not target.is_file() or target.read_bytes() != content
                or publication["overwrite_performed"]):
            raise RuntimeError("Published target verification failed")
        byte_count = len(content)
        digest = hashlib.sha256(content).hexdigest()
        if not stage.samefile(target):
            raise RuntimeError("Published target is not the verified staged file")
        stage.unlink()
        report.update(status="created", target_created=True, stage_cleaned=True,
                      target=str(target), bytes=byte_count, sha256=digest,
                      request_sha256=current["request_sha256"],
                      source_fingerprint=current["source_fingerprint"],
                      sidecars=[], object=obj.name, scene=scene.name)
    except (ValueError, TypeError, OverflowError, KeyError, OSError, RuntimeError) as exc:
        report["errors"].append(str(exc))
        if target is not None and (target.exists() or _export_path_is_link(target)):
            published = True
            report["target_created"] = True
        # Before publication, remove only our exact regular stage. Unexpected
        # sidecars are intentionally preserved rather than guessed/deleted.
        if (not published and stage is not None and stage.is_file()
                and not _export_path_is_link(stage)
                and not stage.with_suffix(".fbm").exists()):
            stage.unlink()
            report["stage_cleaned"] = True
    return report

