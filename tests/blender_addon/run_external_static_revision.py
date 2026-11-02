import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


PART_ROLES = [
    ("Mesh_CarriageBody", "carriage_body"), ("Mesh_TrailLeft", "trail_left"),
    ("Mesh_TrailRight", "trail_right"), ("Mesh_Barrel", "barrel"),
    ("Mesh_MuzzleBand", "muzzle_band"), ("Mesh_Bore", "bore"),
    ("Mesh_Breech", "breech"), ("Mesh_Axle", "axle"),
    ("Mesh_WheelLeft", "wheel_left"), ("Mesh_HubLeft", "hub_left"),
    ("Mesh_WheelRight", "wheel_right"), ("Mesh_HubRight", "hub_right"),
    ("Mesh_ElevationBlock", "elevation_block"),
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--glb", required=True)
    parser.add_argument("--sha256", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def datablock_snapshot():
    return {name: tuple((block.name, block.as_pointer()) for block in getattr(bpy.data, name))
            for name in ("objects", "meshes", "materials", "collections", "images")}


def mesh_snapshot(collection):
    result = {}
    for obj in collection.objects:
        role = obj.get("gameassetai_semantic_role")
        if obj.type != "MESH" or not role:
            continue
        result[role] = {
            "vertices": tuple(tuple(round(float(v), 8) for v in vertex.co) for vertex in obj.data.vertices),
            "edges": tuple(tuple(edge.vertices) for edge in obj.data.edges),
            "polygons": tuple(tuple(polygon.vertices) for polygon in obj.data.polygons),
            "materials": tuple(material.name for material in obj.data.materials),
            "uv": tuple((layer.name, tuple((round(float(loop.uv.x), 8), round(float(loop.uv.y), 8))
                                           for loop in layer.data)) for layer in obj.data.uv_layers),
            "matrix_local": tuple(round(float(value), 8) for row in obj.matrix_local for value in row),
            "mesh_pointer": obj.data.as_pointer(),
        }
    return result


def bounds(collections):
    bpy.context.view_layer.update()
    objects = [obj for collection in collections for obj in collection.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    center, size = (low + high) * .5, high - low
    return {"center": tuple(center), "ortho_scale": float(max(size) * 1.35),
            "distance": float(max(size) * 4 + 2)}


def render_views(scene, collection, artifact, label, frame):
    data = bpy.data.cameras.new(label + " Camera Data")
    camera = bpy.data.objects.new(label + " Camera", data)
    scene.collection.objects.link(camera)
    scene.camera, data.type, data.ortho_scale = camera, "ORTHO", frame["ortho_scale"]
    center, distance = Vector(frame["center"]), frame["distance"]
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    visible = {obj for obj in collection.objects if obj.type == "MESH"}
    prior = {obj: obj.hide_render for obj in scene.objects if obj.type == "MESH"}
    for obj in prior:
        obj.hide_render = obj not in visible
    views = {"front": Vector((0, -distance, 0)), "side": Vector((distance, 0, 0)),
             "three-quarter": Vector((distance * .7, -distance * .7, distance * .32))}
    images = {}
    for view, offset in views.items():
        camera.location = center + offset
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = artifact / "previews" / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        images[f"{label}_{view}"] = str(path.resolve())
    for obj, state in prior.items():
        obj.hide_render = state
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(data)
    return images


def request(scene, glb, sha):
    return {
        "schema": "gameassetai.external-static-revision-request.v1", "scene_name": scene.name,
        "asset_name": "GAA Extended Trail Field Cannon",
        "source_collection_name": "GAA External Field Cannon Source",
        "collection_name": "GAA Extended Trail Field Cannon",
        "source_file": str(glb), "source_sha256": sha,
        "part_roles": [{"object_name": name, "semantic_role": role} for name, role in PART_ROLES],
        "revisions": [
            {"semantic_role": "trail_left", "operation": "LOCAL_AXIS_END_OFFSET",
             "axis": "X", "side": "MIN", "threshold": -.5, "delta": -.45},
            {"semantic_role": "trail_right", "operation": "LOCAL_AXIS_END_OFFSET",
             "axis": "X", "side": "MIN", "threshold": -.5, "delta": -.45},
        ],
        "provenance": {"producer": "Kiln", "version": "1.5.0",
                       "source_ref": "p_7dde98dc80a9/field-cannon-revised.glb",
                       "license": "generator MIT; evaluation asset user-owned"},
        "policy": {"existing_names": "REFUSE", "source_file": "READ_ONLY",
                   "import": "NEW_COLLECTION_OWNED_SOURCE",
                   "revision": "NEW_COLLECTION_INDEPENDENT_MESHES_SHARED_MATERIALS",
                   "failure": "ROLL_BACK_OPERATION_DELTA"},
    }


def main():
    args = parse_args()
    root, artifact = Path(args.repo_root).resolve(), Path(args.artifact_dir).resolve()
    glb = Path(args.glb).resolve(strict=True)
    artifact.mkdir(parents=True, exist_ok=True)
    (artifact / "previews").mkdir(exist_ok=True)
    sys.path.insert(0, str(root / "scripts"))
    import create_static_asset_assembly as assembly
    from create_static_asset_assembly import revise_external_glb
    scene = bpy.context.scene
    baseline = datablock_snapshot()
    source_hash_before = hashlib.sha256(glb.read_bytes()).hexdigest()
    assert source_hash_before == args.sha256
    payload = request(scene, glb, args.sha256)

    bad_hash = json.loads(json.dumps(payload))
    bad_hash["source_sha256"] = "0" * 64
    try:
        revise_external_glb(bad_hash, authorized=True)
        raise AssertionError("bad hash must refuse")
    except ValueError as exc:
        assert "SHA-256 mismatch" in str(exc)
    assert datablock_snapshot() == baseline

    occupied_root = bpy.data.objects.new(payload["asset_name"] + " Root 1", None)
    scene.collection.objects.link(occupied_root)
    collision_baseline = datablock_snapshot()
    try:
        revise_external_glb(payload, authorized=True)
        raise AssertionError("result root name collision must refuse")
    except ValueError as exc:
        assert "result root names are occupied" in str(exc)
    assert datablock_snapshot() == collision_baseline
    bpy.data.objects.remove(occupied_root, do_unlink=True)
    assert datablock_snapshot() == baseline

    original_apply = assembly._apply_external_region_revision
    def induced_failure(obj, revision):
        original_apply(obj, revision)
        raise RuntimeError("deliberate external revision rollback probe")
    assembly._apply_external_region_revision = induced_failure
    try:
        revise_external_glb(payload, authorized=True)
        raise AssertionError("induced failure must propagate")
    except RuntimeError as exc:
        assert "rollback probe" in str(exc)
    finally:
        assembly._apply_external_region_revision = original_apply
    assert datablock_snapshot() == baseline

    receipt = revise_external_glb(payload, authorized=True)
    source_collection = bpy.data.collections[payload["source_collection_name"]]
    result_collection = bpy.data.collections[payload["collection_name"]]
    source_state, result_state = mesh_snapshot(source_collection), mesh_snapshot(result_collection)
    changed = {"trail_left", "trail_right"}
    assert set(source_state) == set(result_state) == {role for _, role in PART_ROLES}
    for role in source_state:
        assert source_state[role]["mesh_pointer"] != result_state[role]["mesh_pointer"]
        assert source_state[role]["edges"] == result_state[role]["edges"]
        assert source_state[role]["polygons"] == result_state[role]["polygons"]
        assert source_state[role]["materials"] == result_state[role]["materials"]
        assert source_state[role]["uv"] == result_state[role]["uv"]
        assert source_state[role]["matrix_local"] == result_state[role]["matrix_local"]
        if role in changed:
            assert source_state[role]["vertices"] != result_state[role]["vertices"]
        else:
            assert source_state[role]["vertices"] == result_state[role]["vertices"]
    assert all(part["independent_mesh"] for part in receipt["parts"])
    assert hashlib.sha256(glb.read_bytes()).hexdigest() == source_hash_before

    frame = bounds([source_collection, result_collection])
    images = {}
    images.update(render_views(scene, source_collection, artifact, "external-original", frame))
    images.update(render_views(scene, result_collection, artifact, "external-revised", frame))
    blend = artifact / "result.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    validation = {
        "schema": "gameassetai.external-static-revision-validation.v1",
        "status": "structural_pass_visual_review_required", "images": images,
        "required_visual_checks": ["asset_recognizable", "requested_trail_extension_visible",
                                   "overall_form_preserved", "unintended_gaps_or_distortion_absent",
                                   "materials_visually_preserved"],
        "source": {"path": str(glb), "sha256": source_hash_before,
                   "provenance": payload["provenance"]},
        "mapping": payload["part_roles"], "receipt": receipt,
        "checks": {"explicit_mapping_complete": True, "source_file_preserved": True,
                   "imported_source_preserved": True, "result_meshes_independent": True,
                   "selected_regions_changed": True, "unrelated_vertices_preserved": True,
                   "topology_preserved": True, "materials_preserved": True,
                   "uv_layers_preserved": True, "object_transforms_preserved": True,
                   "empty_parent_hierarchy_preserved": True, "bad_hash_refused": True,
                   "result_root_name_collision_refused": True,
                   "induced_failure_rolled_back": True, "shared_camera_comparison": True},
    }
    validation_path = artifact / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    (artifact / "source-info.json").write_text(json.dumps({
        "repository": str(root), "blender_version": bpy.app.version_string,
        "external_input_sha256": source_hash_before, "result_blend_sha256": sha(blend),
        "validation_sha256": sha(validation_path)}, indent=2), encoding="utf-8")
    print(json.dumps({"status": validation["status"], "blend": str(blend),
                      "validation": str(validation_path), "images": images}))


if __name__ == "__main__":
    main()
