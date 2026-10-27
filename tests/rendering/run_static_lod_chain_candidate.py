"""Blender regression for read-only existing static LOD-chain inspection."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import uuid

import bpy


def _mesh(scene, name, vertices, faces):
    mesh = bpy.data.meshes.new(name + "Mesh"); mesh.from_pydata(vertices, [], faces); mesh.update()
    obj = bpy.data.objects.new(name, mesh); scene.collection.objects.link(obj); return obj


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path); args = parser.parse_args(tail)
    repo = args.repo_root.resolve(strict=True)
    helper_root = args.helper_root.resolve(strict=True) if args.helper_root else repo / "scripts"
    sys.path.insert(0, str(helper_root))
    from inspect_static_lod_chain_candidate import inspect_static_lod_chain_candidate
    from validate_static_lod_chain_request import SCHEMA, validate_static_lod_chain_request

    token = uuid.uuid4().hex[:10]; original_scene = bpy.context.scene
    before = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects), ("meshes", bpy.data.meshes))}
    scene = bpy.data.scenes.new("GAA_LOD_" + token); bpy.context.window.scene = scene
    cube_v=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    cube_f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    oct_v=[(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]
    oct_f=[(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]
    tet_v=[(1,1,1),(-1,-1,1),(-1,1,-1),(1,-1,-1)]
    tet_f=[(0,1,2),(0,3,1),(0,2,3),(1,3,2)]
    objects=[_mesh(scene,"LOD0_"+token,cube_v,cube_f),
             _mesh(scene,"LOD1_"+token,oct_v,oct_f),
             _mesh(scene,"LOD2_"+token,tet_v,tet_f)]
    request={"schema":SCHEMA,"scene_name":scene.name,
             "levels":[{"level_index":i,"object_name":obj.name} for i,obj in enumerate(objects)],
             "geometry_source":"BASE_MESH","coordinate_space":"WORLD",
             "policy":{"object_selection":"EXPLICIT_ONLY","modifier_evaluation":"BASE_MESH_ONLY",
                       "mutation":"READ_ONLY","transform_alignment":"EXACT_WORLD_MATRIX",
                       "triangle_order":"STRICTLY_DECREASING"}}
    checks=[]
    try:
        preflight=validate_static_lod_chain_request(request)
        assert preflight["status"]=="ready"; checks.append("request_ready")
        candidate=inspect_static_lod_chain_candidate(request,preflight["request_sha256"])
        assert candidate["status"]=="candidate_for_review" and not candidate["errors"]
        assert not candidate["blockers"]; checks.append("candidate_clear")
        assert [level["mesh"]["triangle_count"] for level in candidate["levels"]]==[12,8,4]
        checks.append("strict_triangle_chain")
        assert all(level["relation_to_lod0"]["world_matrix_matches_lod0"]
                   for level in candidate["levels"]); checks.append("exact_matrix_alignment")
        stale=inspect_static_lod_chain_candidate(request,"0"*64)
        assert stale["status"]=="error" and stale["errors"]; checks.append("stale_refused")
        objects[2].location.x=0.25
        bpy.context.view_layer.update()
        shifted=inspect_static_lod_chain_candidate(request)
        assert shifted["blockers"] and any("world_matrix" in reason for reason in shifted["blockers"][-1]["reasons"])
        objects[2].location.x=0.0; bpy.context.view_layer.update()
        checks.append("matrix_mismatch_blocked")
        modifier=objects[1].modifiers.new("Owned_"+token,"TRIANGULATE")
        dependency=inspect_static_lod_chain_candidate(request)
        assert dependency["blockers"]; objects[1].modifiers.remove(modifier)
        checks.append("dependency_blocked")
        bad={**request,"levels":[request["levels"][0],request["levels"][2],request["levels"][1]]}
        bad["levels"]=[dict(level,level_index=i) for i,level in enumerate(bad["levels"])]
        order=inspect_static_lod_chain_candidate(bad)
        assert order["blockers"] and any("triangle_count" in reason for entry in order["blockers"] for reason in entry["reasons"])
        checks.append("nondecreasing_blocked")
        assert len(scene.objects)==3; checks.append("read_only")
    finally:
        bpy.context.window.scene=original_scene
        for obj in list(scene.objects):
            mesh=obj.data; bpy.data.objects.remove(obj,do_unlink=True)
            if mesh.users==0: bpy.data.meshes.remove(mesh)
        bpy.data.scenes.remove(scene)
    after={kind: sorted(item.name for item in collection) for kind,collection in (
        ("scenes",bpy.data.scenes),("objects",bpy.data.objects),("meshes",bpy.data.meshes))}
    assert before==after; checks.append("exact_teardown")
    import json
    print("GAMEASSETAI_RESULT="+json.dumps({"status":"passed","blender_version":bpy.app.version_string,
          "check_count":len(checks),"checks":checks},sort_keys=True))


if __name__=="__main__": main()
