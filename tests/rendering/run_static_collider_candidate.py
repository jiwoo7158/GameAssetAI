"""Blender regression for read-only existing static-collider candidate inspection."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
import uuid

import bpy


def _mesh(scene, name, vertices, faces):
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces); mesh.update()
    obj = bpy.data.objects.new(name, mesh); scene.collection.objects.link(obj)
    return obj


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path)
    args = parser.parse_args(tail); repo = args.repo_root.resolve(strict=True)
    helper_root = args.helper_root.resolve(strict=True) if args.helper_root else repo / "scripts"
    sys.path.insert(0, str(helper_root))
    from inspect_static_collider_candidate import inspect_static_collider_candidate
    from validate_static_collider_request import SCHEMA, validate_static_collider_request

    token = uuid.uuid4().hex[:10]
    original_scene = bpy.context.scene
    before = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects), ("meshes", bpy.data.meshes))}
    scene = bpy.data.scenes.new("GAA_Collider_" + token)
    cube_vertices = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                     (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    cube_faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    render = _mesh(scene, "Render_" + token, cube_vertices, cube_faces)
    collider = _mesh(scene, "Collider_" + token,
                     [(x*1.1,y*1.1,z*1.1) for x,y,z in cube_vertices], cube_faces)
    ground = _mesh(scene, "Ground_" + token,
                   [(-2,-2,-1.2),(2,-2,-1.2),(2,2,-1.2),(-2,2,-1.2)], [(0,1,2,3)])
    bpy.context.window.scene = scene
    request = {"schema": SCHEMA, "scene_name": scene.name,
               "render_object_name": render.name,
               "colliders": [
                   {"id": "body", "object_name": collider.name,
                    "collider_kind": "CONVEX_MESH_CANDIDATE",
                    "convexity_tolerance_ratio": 0.0001},
                   {"id": "ground", "object_name": ground.name,
                    "collider_kind": "STATIC_TRIANGLE_MESH",
                    "convexity_tolerance_ratio": None}],
               "geometry_source": "BASE_MESH", "coordinate_space": "WORLD",
               "policy": {"object_selection": "EXPLICIT_ONLY",
                          "modifier_evaluation": "BASE_MESH_ONLY", "mutation": "READ_ONLY"}}
    checks = []
    try:
        preflight = validate_static_collider_request(request)
        assert preflight["status"] == "ready"; checks.append("request_ready")
        candidate = inspect_static_collider_candidate(request, preflight["request_sha256"])
        assert candidate["status"] == "candidate_for_review" and not candidate["errors"]
        assert not candidate["blockers"]; checks.append("candidate_clear")
        assert candidate["colliders"][0]["convexity"]["within_tolerance"]
        assert candidate["colliders"][0]["mesh"]["triangle_count"] == 12
        checks.append("closed_convex_evidence")
        assert candidate["colliders"][1]["mesh"]["boundary_edge_count"] == 4
        assert candidate["colliders"][1]["convexity"] is None
        checks.append("triangle_mesh_reported_without_convex_claim")
        stale = inspect_static_collider_candidate(request, "0" * 64)
        assert stale["status"] == "error" and stale["errors"]
        checks.append("stale_request_refused")
        convex_open = {**request, "colliders": [dict(request["colliders"][1],
                       collider_kind="CONVEX_MESH_CANDIDATE",
                       convexity_tolerance_ratio=0.0001)]}
        open_report = inspect_static_collider_candidate(convex_open)
        assert open_report["status"] == "candidate_for_review" and open_report["blockers"]
        checks.append("open_convex_blocked")
        modifier = collider.modifiers.new("Owned_" + token, "TRIANGULATE")
        dependency = inspect_static_collider_candidate(request)
        assert dependency["status"] == "candidate_for_review" and dependency["blockers"]
        collider.modifiers.remove(modifier); checks.append("dependency_blocked")
        assert (render.data.vertices[0].co[:] == cube_vertices[0]
                and len(scene.objects) == 3)
        checks.append("read_only")
    finally:
        bpy.context.window.scene = original_scene
        for obj in list(scene.objects):
            mesh = obj.data; bpy.data.objects.remove(obj, do_unlink=True)
            if mesh.users == 0: bpy.data.meshes.remove(mesh)
        bpy.data.scenes.remove(scene)
    after = {kind: sorted(item.name for item in collection) for kind, collection in (
        ("scenes", bpy.data.scenes), ("objects", bpy.data.objects), ("meshes", bpy.data.meshes))}
    assert before == after; checks.append("exact_teardown")
    import json
    print("GAMEASSETAI_RESULT=" + json.dumps({"status": "passed",
          "blender_version": bpy.app.version_string, "check_count": len(checks), "checks": checks},
          sort_keys=True))


if __name__ == "__main__":
    main()
