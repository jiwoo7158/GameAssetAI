"""Blender regression for transient independent-copy LOD preview."""
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
    mesh = obj.data
    value = {"vertices": [[float(x) for x in vertex.co] for vertex in mesh.vertices],
             "polygons": [list(polygon.vertices) for polygon in mesh.polygons],
             "materials": [material.name if material else None for material in mesh.materials],
             "uv": [{"name": layer.name,
                     "values": [[float(x) for x in item.uv] for item in layer.data]}
                    for layer in mesh.uv_layers]}
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                        separators=(",", ":")).encode("utf-8")).hexdigest()


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path); args = parser.parse_args(tail)
    repo = args.repo_root.resolve(strict=True)
    helper = args.helper_root.resolve(strict=True) if args.helper_root else repo / "scripts"
    sys.path.insert(0, str(helper))
    from preview_static_lod_copy import preview_static_lod_copy
    from validate_static_lod_copy_request import SCHEMA, validate_static_lod_copy_request

    token = uuid.uuid4().hex[:10]
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selected = sorted(obj.name for obj in bpy.context.selected_objects)
    original_frame, original_subframe = original_scene.frame_current, original_scene.frame_subframe
    before = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects),
        ("meshes", bpy.data.meshes), ("materials", bpy.data.materials))}
    scene = bpy.data.scenes.new("GAA_LOD_Preview_" + token); bpy.context.window.scene = scene
    mesh = bpy.data.meshes.new("GAA_LOD_SourceMesh_" + token)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    source = bpy.data.objects.new("GAA_LOD_Source_" + token, mesh); scene.collection.objects.link(source)
    material = bpy.data.materials.new("GAA_LOD_Material_" + token); mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="GAA_LOD_UV")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co.normalized()
        uv.data[loop.index].uv = (math.atan2(co.y, co.x)/(2*math.pi)+0.5,
                                  math.acos(max(-1.0, min(1.0, co.z)))/math.pi)
    output_object = "GAA_LOD_Output_" + token; output_mesh = "GAA_LOD_OutputMesh_" + token
    request = {"schema": SCHEMA, "scene_name": scene.name,
               "source_object_name": source.name, "output_object_name": output_object,
               "output_mesh_name": output_mesh,
               "operation": {"method": "DECIMATE_COLLAPSE", "ratio": 0.5,
                             "triangulate": False},
               "policy": {"geometry_source": "BASE_MESH_ONLY", "dependency_handling": "REFUSE",
                          "source_mutation": "PRESERVE", "output_independence": "NEW_OBJECT_AND_MESH",
                          "transform": "COPY_EXACT", "materials": "SHARE_DATABLOCKS_READ_ONLY",
                          "uv_layers": "COPY", "authorization": "PREVIEW_THEN_EXPLICIT_APPLY"}}
    checks = []
    try:
        preflight = validate_static_lod_copy_request(request)
        assert preflight["status"] == "ready"; checks.append("request_ready")
        source_before = _source_hash(source)
        candidate = preview_static_lod_copy(request, preflight["request_sha256"])
        if candidate["errors"] or candidate["blockers"]:
            print("GAMEASSETAI_DIAGNOSTIC=" + json.dumps(candidate, sort_keys=True))
        assert candidate["status"] == "candidate_for_review" and not candidate["errors"]
        assert not candidate["blockers"]; checks.append("candidate_clear")
        assert candidate["source"]["triangle_count"] == 320
        assert candidate["preview"]["triangle_count"] == 160
        assert candidate["relation_to_source"]["actual_triangle_ratio"] == 0.5
        checks.append("real_triangle_reduction")
        assert candidate["relation_to_source"]["world_matrix_matches"]
        assert candidate["relation_to_source"]["material_slots_match"]
        assert candidate["relation_to_source"]["uv_layer_names_match"]
        checks.append("structure_preserved")
        assert _source_hash(source) == source_before; checks.append("source_preserved")
        assert bpy.data.objects.get(output_object) is None and bpy.data.meshes.get(output_mesh) is None
        assert not any(item.name.startswith(".gameassetai-lod-preview-") for item in bpy.data.scenes)
        checks.append("preview_ids_removed")
        stale = preview_static_lod_copy(request, "0" * 64)
        assert stale["status"] == "error" and stale["errors"]
        checks.append("stale_request_refused")
        collision = bpy.data.objects.new(output_object, None)
        blocked = preview_static_lod_copy(request)
        assert "output_object_name_already_exists" in blocked["blockers"]
        bpy.data.objects.remove(collision)
        checks.append("output_collision_blocked")
        modifier = source.modifiers.new("Owned_" + token, "TRIANGULATE")
        dependency = preview_static_lod_copy(request)
        assert "modifiers" in dependency["blockers"]
        source.modifiers.remove(modifier); checks.append("dependency_blocked")
        assert bpy.context.scene == scene and bpy.context.view_layer.objects.active is None
        checks.append("preview_context_restored")
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
          "checks": checks, "preview": {"source_triangles": 320, "result_triangles": 160,
                                         "ratio": 0.5}}, sort_keys=True))


if __name__ == "__main__": main()
