"""Blender 5.0.1 independent-copy Decimate capability experiment."""
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


def _facts(obj):
    mesh = obj.data
    vertices = [[float(v) for v in vertex.co] for vertex in mesh.vertices]
    polygons = [list(polygon.vertices) for polygon in mesh.polygons]
    uv = []
    for layer in mesh.uv_layers:
        uv.append({"name": layer.name, "values": [[float(v) for v in item.uv]
                                                   for item in layer.data]})
    data = {"vertices": vertices, "polygons": polygons, "uv": uv,
            "materials": [material.name if material else None for material in mesh.materials]}
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    triangles = sum(max(0, len(polygon) - 2) for polygon in polygons)
    radii = [math.sqrt(sum(value * value for value in point)) for point in vertices]
    return {"sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "triangles": triangles, "vertices": len(vertices), "polygons": len(polygons),
            "uv_layers": len(uv), "uv_finite": all(math.isfinite(value)
                for layer in uv for pair in layer["values"] for value in pair),
            "materials": data["materials"], "radius_min": min(radii), "radius_max": max(radii)}


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path)
    parser.parse_args(tail)
    token = uuid.uuid4().hex[:10]
    original_scene = bpy.context.scene
    original_active = bpy.context.view_layer.objects.active
    original_selection = sorted(obj.name for obj in bpy.context.selected_objects)
    before = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects),
        ("meshes", bpy.data.meshes), ("materials", bpy.data.materials))}
    scene = bpy.data.scenes.new("GAA_LOD_Decimate_" + token)
    bpy.context.window.scene = scene
    mesh = bpy.data.meshes.new("GAA_LOD_SourceMesh_" + token)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    bm.to_mesh(mesh); bm.free(); mesh.update()
    source = bpy.data.objects.new("GAA_LOD_Source_" + token, mesh); scene.collection.objects.link(source)
    material = bpy.data.materials.new("GAA_LOD_Material_" + token); mesh.materials.append(material)
    layer = mesh.uv_layers.new(name="GAA_LOD_UV")
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co.normalized()
        layer.data[loop.index].uv = (math.atan2(co.y, co.x)/(2*math.pi)+0.5,
                                     math.acos(max(-1.0,min(1.0,co.z)))/math.pi)
    source_before = _facts(source)
    copy_obj = source.copy(); copy_obj.name = "GAA_LOD_Copy_" + token
    copy_obj.data = source.data.copy(); copy_obj.data.name = "GAA_LOD_CopyMesh_" + token
    scene.collection.objects.link(copy_obj)
    checks = []
    try:
        assert source_before["triangles"] > 100 and source_before["uv_finite"]
        checks.append("representative_source")
        assert copy_obj.data is not source.data and copy_obj.data.users == 1
        checks.append("independent_copy")
        modifier = copy_obj.modifiers.new("GAA_LOD_Decimate", "DECIMATE")
        modifier.decimate_type = "COLLAPSE"; modifier.ratio = 0.5
        rna = modifier.bl_rna.properties
        assert "ratio" in rna and "decimate_type" in rna
        checks.append("blender_rna_verified")
        bpy.context.view_layer.objects.active = copy_obj
        copy_obj.select_set(True); source.select_set(False)
        result = bpy.ops.object.modifier_apply(modifier=modifier.name)
        assert result == {"FINISHED"}; checks.append("modifier_applied_to_copy")
        reduced = _facts(copy_obj)
        assert 0 < reduced["triangles"] < source_before["triangles"]
        checks.append("base_triangles_reduced")
        assert _facts(source) == source_before; checks.append("source_preserved")
        assert reduced["uv_layers"] == 1 and reduced["uv_finite"]
        assert reduced["materials"] == source_before["materials"]
        checks.append("uv_material_structure_retained")
        assert math.isfinite(reduced["radius_min"]) and math.isfinite(reduced["radius_max"])
        checks.append("finite_result")
        summary = {"source": source_before, "result": reduced,
                   "triangle_ratio": reduced["triangles"] / source_before["triangles"],
                   "radius_delta": [reduced["radius_min"] - source_before["radius_min"],
                                    reduced["radius_max"] - source_before["radius_max"]]}
    finally:
        bpy.context.window.scene = original_scene
        for obj in list(scene.objects):
            owned_mesh = obj.data; bpy.data.objects.remove(obj, do_unlink=True)
            if owned_mesh.users == 0: bpy.data.meshes.remove(owned_mesh)
        bpy.data.scenes.remove(scene)
        if material.users == 0: bpy.data.materials.remove(material)
        for obj in bpy.context.selected_objects: obj.select_set(False)
        for name in original_selection:
            obj = bpy.data.objects.get(name)
            if obj: obj.select_set(True)
        bpy.context.view_layer.objects.active = original_active
    after = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects),
        ("meshes", bpy.data.meshes), ("materials", bpy.data.materials))}
    assert before == after; checks.append("exact_teardown")
    print("GAMEASSETAI_RESULT=" + json.dumps({"status":"passed",
          "blender_version":bpy.app.version_string,"check_count":len(checks),"checks":checks,
          "summary":summary}, sort_keys=True))


if __name__ == "__main__": main()
