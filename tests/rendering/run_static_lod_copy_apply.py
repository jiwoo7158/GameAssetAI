"""Blender regression for guarded persistent independent-copy LOD apply and rollback."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

import bmesh
import bpy


def _source_hash(obj):
    value = {"vertices": [[float(x) for x in vertex.co] for vertex in obj.data.vertices],
             "polygons": [list(polygon.vertices) for polygon in obj.data.polygons],
             "materials": [material.name if material else None for material in obj.data.materials],
             "uv": [{"name": layer.name, "values": [[float(x) for x in item.uv]
                                                       for item in layer.data]}
                    for layer in obj.data.uv_layers]}
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                        separators=(",", ":")).encode("utf-8")).hexdigest()


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path); args = parser.parse_args(tail)
    repo = args.repo_root.resolve(strict=True)
    helper = args.helper_root.resolve(strict=True) if args.helper_root else repo / "scripts"
    sys.path.insert(0, str(helper))
    import apply_static_lod_copy as apply_module
    from preview_static_lod_copy import preview_static_lod_copy
    from validate_static_lod_copy_request import SCHEMA

    token = uuid.uuid4().hex[:10]
    original_scene = bpy.context.scene; original_active = bpy.context.view_layer.objects.active
    original_selected = sorted(obj.name for obj in bpy.context.selected_objects)
    original_frame, original_subframe = original_scene.frame_current, original_scene.frame_subframe
    before = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects),
        ("meshes", bpy.data.meshes), ("materials", bpy.data.materials))}
    scene = bpy.data.scenes.new("GAA_LOD_Apply_" + token); bpy.context.window.scene = scene
    mesh = bpy.data.meshes.new("GAA_LOD_ApplySourceMesh_" + token)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    source = bpy.data.objects.new("GAA_LOD_ApplySource_" + token, mesh); scene.collection.objects.link(source)
    material = bpy.data.materials.new("GAA_LOD_ApplyMaterial_" + token); mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="GAA_LOD_UV")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co.normalized()
        uv.data[loop.index].uv = (math.atan2(co.y, co.x)/(2*math.pi)+0.5,
                                  math.acos(max(-1.0, min(1.0, co.z)))/math.pi)
    output_object = "GAA_LOD_Applied_" + token; output_mesh = "GAA_LOD_AppliedMesh_" + token
    request = {"schema": SCHEMA, "scene_name": scene.name, "source_object_name": source.name,
               "output_object_name": output_object, "output_mesh_name": output_mesh,
               "operation": {"method": "DECIMATE_COLLAPSE", "ratio": 0.5, "triangulate": False},
               "policy": {"geometry_source": "BASE_MESH_ONLY", "dependency_handling": "REFUSE",
                          "source_mutation": "PRESERVE", "output_independence": "NEW_OBJECT_AND_MESH",
                          "transform": "COPY_EXACT", "materials": "SHARE_DATABLOCKS_READ_ONLY",
                          "uv_layers": "COPY", "authorization": "PREVIEW_THEN_EXPLICIT_APPLY"}}
    checks = []
    try:
        reviewed = preview_static_lod_copy(request)
        assert reviewed["status"] == "candidate_for_review" and not reviewed["blockers"]
        checks.append("reviewed_preview_ready")
        kwargs = {"expected_request_sha256": reviewed["request_sha256"],
                  "expected_source_fingerprint": reviewed["source_fingerprint"],
                  "expected_setup_fingerprint": reviewed["setup_fingerprint"],
                  "expected_preview_fingerprint": reviewed["preview_fingerprint"]}
        refused = apply_module.apply_static_lod_copy(request, authorized=False, **kwargs)
        assert refused["status"] == "error" and refused["failure_cleanup"] == "complete"
        assert bpy.data.objects.get(output_object) is None; checks.append("authorization_required")
        stale = dict(kwargs); stale["expected_preview_fingerprint"] = "0" * 64
        refused = apply_module.apply_static_lod_copy(request, authorized=True, **stale)
        assert refused["status"] == "error" and bpy.data.objects.get(output_object) is None
        checks.append("stale_preview_refused")
        source_before = _source_hash(source)
        result = apply_module.apply_static_lod_copy(request, authorized=True, **kwargs)
        if result["status"] != "created":
            print("GAMEASSETAI_DIAGNOSTIC=" + json.dumps(result, sort_keys=True))
        assert result["status"] == "created" and result["published"]
        assert result["output"]["triangle_count"] == 160 and result["receipt_fingerprint"]
        checks.append("persistent_copy_created")
        output = bpy.data.objects[output_object]
        assert output.data.name == output_mesh and output.data is not source.data and output.data.users == 1
        assert output.matrix_world == source.matrix_world; checks.append("independent_exact_transform")
        assert _source_hash(source) == source_before and result["source_preserved"]
        checks.append("source_preserved")
        assert bpy.context.scene == scene and bpy.context.view_layer.objects.active is None
        checks.append("success_context_restored")
        bpy.data.objects.remove(output, do_unlink=True)
        applied_mesh = bpy.data.meshes.get(output_mesh)
        if applied_mesh and applied_mesh.users == 0: bpy.data.meshes.remove(applied_mesh)
        original_validator = apply_module._validate_output
        def forced_failure(*_args):
            raise ValueError("forced post-create validation failure")
        apply_module._validate_output = forced_failure
        try:
            failed = apply_module.apply_static_lod_copy(request, authorized=True, **kwargs)
        finally:
            apply_module._validate_output = original_validator
        assert failed["status"] == "error" and failed["failure_cleanup"] == "complete"
        assert bpy.data.objects.get(output_object) is None and bpy.data.meshes.get(output_mesh) is None
        checks.append("post_create_failure_rolled_back")
        assert _source_hash(source) == source_before; checks.append("rollback_preserved_source")
        assert bpy.context.scene == scene and bpy.context.view_layer.objects.active is None
        checks.append("failure_context_restored")
    finally:
        bpy.context.window.scene = original_scene
        for obj in list(scene.objects):
            owned_mesh = obj.data; bpy.data.objects.remove(obj, do_unlink=True)
            if owned_mesh and owned_mesh.users == 0: bpy.data.meshes.remove(owned_mesh)
        bpy.data.scenes.remove(scene)
        if material.users == 0: bpy.data.materials.remove(material)
        original_scene.frame_set(original_frame, subframe=original_subframe)
        for obj in bpy.context.selected_objects: obj.select_set(False)
        for name in original_selected:
            obj = bpy.data.objects.get(name)
            if obj: obj.select_set(True)
        bpy.context.view_layer.objects.active = original_active
    after = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects),
        ("meshes", bpy.data.meshes), ("materials", bpy.data.materials))}
    assert before == after; checks.append("exact_teardown")
    print("GAMEASSETAI_RESULT=" + json.dumps({"status": "passed",
          "blender_version": bpy.app.version_string, "check_count": len(checks),
          "checks": checks}, sort_keys=True))


if __name__ == "__main__": main()
