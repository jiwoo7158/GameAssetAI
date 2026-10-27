"""Guarded persistent independent-copy application for a reviewed static LOD preview."""
from __future__ import annotations

import uuid

import bpy

from preview_static_lod_copy import (_dependencies, _facts, _public, _restore_context,
                                     _sha256, preview_static_lod_copy)


SCHEMA = "gameassetai.static-lod-copy-apply.v1"


def _matches_preview(facts, preview):
    public = _public(facts)
    return all(public.get(key) == preview.get(key) for key in (
        "vertex_count", "edge_count", "polygon_count", "triangle_count", "world_matrix",
        "world_bounds", "material_slots", "uv_layers"))


def _validate_output(obj, source, reviewed):
    facts = _facts(obj)
    if obj.data is source.data or obj.data.users != 1:
        raise ValueError("output Mesh is not independent")
    if obj.matrix_world != source.matrix_world:
        raise ValueError("output world matrix differs from source")
    if not _matches_preview(facts, reviewed["preview"]):
        raise ValueError("persistent output differs from reviewed preview")
    return facts


def apply_static_lod_copy(request, *, expected_request_sha256,
                          expected_source_fingerprint, expected_setup_fingerprint,
                          expected_preview_fingerprint, authorized=False):
    """Create exactly one reviewed Object/Mesh pair, or roll back only those owned IDs."""
    report = {"schema": SCHEMA, "status": "error", "errors": [],
              "request_sha256": None, "source_fingerprint": None,
              "setup_fingerprint": None, "preview_fingerprint": None,
              "receipt_fingerprint": None, "mutation_authorized": False,
              "published": False, "failure_cleanup": None}
    created_object = created_mesh = target_scene = None
    token = uuid.uuid4().hex
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selected = list(bpy.context.selected_objects)
    original_frame = original_scene.frame_current
    original_subframe = original_scene.frame_subframe
    try:
        if type(authorized) is not bool or not authorized:
            raise ValueError("explicit apply authorization=true is required")
        for label, value in (("expected_request_sha256", expected_request_sha256),
                             ("expected_source_fingerprint", expected_source_fingerprint),
                             ("expected_setup_fingerprint", expected_setup_fingerprint),
                             ("expected_preview_fingerprint", expected_preview_fingerprint)):
            if not isinstance(value, str) or len(value) != 64:
                raise ValueError(label + " must be an exact reviewed SHA-256")
        fresh = preview_static_lod_copy(request, expected_request_sha256)
        report.update({key: fresh.get(key) for key in (
            "request_sha256", "source_fingerprint", "setup_fingerprint", "preview_fingerprint")})
        if fresh["status"] != "candidate_for_review" or fresh["errors"] or fresh["blockers"]:
            raise ValueError("fresh blocker-free preview is required")
        expected = {"request_sha256": expected_request_sha256,
                    "source_fingerprint": expected_source_fingerprint,
                    "setup_fingerprint": expected_setup_fingerprint,
                    "preview_fingerprint": expected_preview_fingerprint}
        for key, value in expected.items():
            if fresh.get(key) != value:
                raise ValueError(key + " changed since review")
        target_scene = bpy.data.scenes[request["scene_name"]]
        source = target_scene.objects[request["source_object_name"]]
        source_before = _facts(source)
        if _dependencies(source):
            raise ValueError("source dependencies changed after preview")
        if bpy.data.objects.get(request["output_object_name"]) is not None:
            raise ValueError("output Object appeared after preview")
        if bpy.data.meshes.get(request["output_mesh_name"]) is not None:
            raise ValueError("output Mesh appeared after preview")

        created_mesh = source.data.copy()
        created_mesh.name = request["output_mesh_name"]
        created_mesh["gameassetai_lod_copy_owner"] = token
        if created_mesh.name != request["output_mesh_name"]:
            raise ValueError("Blender changed the requested output Mesh name")
        created_object = source.copy()
        created_object.name = request["output_object_name"]
        created_object.data = created_mesh
        created_object.matrix_world = source.matrix_world.copy()
        created_object["gameassetai_lod_copy_owner"] = token
        if created_object.name != request["output_object_name"]:
            raise ValueError("Blender changed the requested output Object name")
        target_scene.collection.objects.link(created_object)
        bpy.context.window.scene = target_scene
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        created_object.select_set(True)
        bpy.context.view_layer.objects.active = created_object
        modifier = created_object.modifiers.new("GameAssetAI LOD Copy", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = float(request["operation"]["ratio"])
        if hasattr(modifier, "use_collapse_triangulate"):
            modifier.use_collapse_triangulate = False
        result = bpy.ops.object.modifier_apply(modifier=modifier.name)
        if result != {"FINISHED"}:
            raise RuntimeError("Blender did not apply the persistent Decimate modifier")
        output_facts = _validate_output(created_object, source, fresh)
        if _sha256(_facts(source)) != _sha256(source_before):
            raise ValueError("source changed during persistent apply")
        receipt = {"request_sha256": fresh["request_sha256"],
                   "source_fingerprint": fresh["source_fingerprint"],
                   "setup_fingerprint": fresh["setup_fingerprint"],
                   "preview_fingerprint": fresh["preview_fingerprint"],
                   "scene_name": target_scene.name,
                   "source_object_name": source.name,
                   "output": _public(output_facts),
                   "source_preserved": True, "output_independent": True}
        report.update({"status": "created", "mutation_authorized": True,
                       "published": True, "failure_cleanup": "not_needed",
                       "output": _public(output_facts), "source_preserved": True,
                       "output_independent": True,
                       "receipt_fingerprint": _sha256(receipt)})
    except (ValueError, TypeError, RuntimeError, OverflowError, ZeroDivisionError) as exc:
        report["errors"].append(str(exc))
        try:
            if created_object is not None and created_object.name in bpy.data.objects:
                if (created_object.get("gameassetai_lod_copy_owner") != token
                        or bpy.data.objects.get(created_object.name) is not created_object):
                    raise RuntimeError("output Object ownership changed; rollback stopped")
                bpy.data.objects.remove(created_object, do_unlink=True)
            if created_mesh is not None and created_mesh.name in bpy.data.meshes:
                if (created_mesh.get("gameassetai_lod_copy_owner") != token
                        or created_mesh.users != 0
                        or bpy.data.meshes.get(created_mesh.name) is not created_mesh):
                    raise RuntimeError("output Mesh ownership/users changed; rollback stopped")
                bpy.data.meshes.remove(created_mesh)
            report["failure_cleanup"] = "complete"
        except RuntimeError as cleanup_error:
            report["failure_cleanup"] = "unverified"
            report["errors"].append(str(cleanup_error))
    finally:
        _restore_context(original_scene, original_active, original_selected,
                         original_frame, original_subframe)
    return report
