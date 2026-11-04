import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-blend", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topology(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        return {
            "vertices": len(mesh.vertices), "edges": len(mesh.edges), "polygons": len(mesh.polygons),
            "triangles": sum(max(0, len(face.verts) - 2) for face in bm.faces),
            "nonmanifold_edges": sum(1 for edge in bm.edges if len(edge.link_faces) != 2),
            "all_quad": all(len(face.verts) == 4 for face in bm.faces),
            "uv_layers": [layer.name for layer in mesh.uv_layers],
            "uv_loops": len(mesh.uv_layers.active.data) if mesh.uv_layers else 0,
            "loops": len(mesh.loops),
        }
    finally:
        bm.free()


def symmetry_error(mesh):
    tree = KDTree(len(mesh.vertices))
    for vertex in mesh.vertices:
        tree.insert(vertex.co, vertex.index)
    tree.balance()
    return max((tree.find(Vector((-v.co.x, v.co.y, v.co.z)))[2] for v in mesh.vertices), default=0.0)


def point_at(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_views(output, objects, height):
    scene = bpy.context.scene
    camera_data = bpy.data.cameras.new("GAA B6 Validation Camera")
    camera = bpy.data.objects.new("GAA B6 Validation Camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 1.18
    scene.camera = camera
    key_data = bpy.data.lights.new("GAA B6 Key", "AREA")
    key_data.energy, key_data.shape, key_data.size = 850, "DISK", height * 1.8
    key = bpy.data.objects.new("GAA B6 Key", key_data)
    scene.collection.objects.link(key)
    point_at(key, (height * 1.4, -height * 2.0, height * 2.0), (0, 0, height * 0.5))
    fill_data = bpy.data.lights.new("GAA B6 Fill", "AREA")
    fill_data.energy, fill_data.size = 350, height * 1.4
    fill = bpy.data.objects.new("GAA B6 Fill", fill_data)
    scene.collection.objects.link(fill)
    point_at(fill, (-height * 1.7, height * 1.2, height * 1.2), (0, 0, height * 0.5))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    views = {
        "front": (0, -height * 3.2, height * 0.51),
        "side": (height * 3.2, 0, height * 0.51),
        "three-quarter": (height * 2.35, -height * 2.35, height * 0.54),
    }
    images = {}
    candidates = [item for item in scene.objects if item.type == "MESH"]
    for label, visible in objects.items():
        for item in candidates:
            item.hide_render = item is not visible
        for view, location in views.items():
            point_at(camera, location, (0, 0, height * 0.5))
            path = output / f"{label}-{view}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            images[f"{label}_{view}"] = str(path)
    for item in candidates:
        item.hide_render = False
    for obj, data in ((camera, camera_data), (key, key_data), (fill, fill_data)):
        bpy.data.objects.remove(obj, do_unlink=True)
        if isinstance(data, bpy.types.Camera):
            bpy.data.cameras.remove(data)
        else:
            bpy.data.lights.remove(data)
    return images


def base_request(source, digest):
    return {
        "schema": "gameassetai.character-base-request.v5", "scene_name": bpy.context.scene.name,
        "character_name": "GAA B6 SD Adventurer", "collection_name": "GAA B6 SD Adventurer Collection",
        "object_name": "GAA B6 SD Adventurer Object", "mesh_name": "GAA B6 SD Adventurer Mesh",
        "pose": "A_POSE", "topology_mode": "DEFORMATION_TEMPLATE",
        "template": {"source_file": str(source.resolve()), "source_sha256": digest,
                     "mesh_name": "GEO-body_male_stylized", "source_name": "Blender Studio Human Base Meshes",
                     "source_version": "1.4.1", "license": "CC0-1.0", "front_axis": "-Y"},
        "proportions": {"height": 1.55, "shoulder_width_ratio": 0.36, "hip_width_ratio": 0.25,
                        "body_depth_ratio": 0.18, "limb_thickness_ratio": 0.06,
                        "head_height_ratio": 0.21},
        "regions": {"head_scale": 1.18, "head_width_scale": 1.05, "head_depth_scale": 1.04,
                    "torso_width_scale": 1.04, "arm_length_scale": 0.92,
                    "arm_thickness_scale": 1.05, "leg_length_scale": 0.94,
                    "hand_scale": 1.12, "foot_scale": 1.15},
        "colors": {"skin": [0.72, 0.43, 0.27, 1], "primary": [0.10, 0.23, 0.38, 1],
                   "secondary": [0.58, 0.18, 0.08, 1], "boots": [0.045, 0.03, 0.025, 1]},
        "art_direction": {
            "style_family": "STYLIZED_LOW_POLY_SD", "silhouette": "large head compact limbs broad hands and feet",
            "shape_language": "rounded primary masses with readable extremities",
            "palette": [[0.72, 0.43, 0.27, 1], [0.10, 0.23, 0.38, 1],
                        [0.58, 0.18, 0.08, 1], [0.045, 0.03, 0.025, 1]],
            "polygon_budget": 30000,
            "provenance": {"source": "USER_REQUEST", "source_ref": "B6.1 representative request",
                           "profile_sha256": None},
            "unsupported": ["hair", "clothing", "equipment", "facial rig"],
        },
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_SINGLE_MESH_CHARACTER", "failure": "ROLL_BACK_OWNED_DATA",
                   "rigging": "NOT_INCLUDED"},
    }


def revision_request():
    return {
        "schema": "gameassetai.character-base-revision-request.v1", "scene_name": bpy.context.scene.name,
        "source_collection_name": "GAA B6 SD Adventurer Collection",
        "source_object_name": "GAA B6 SD Adventurer Object",
        "character_name": "GAA B6 SD Adventurer Revised",
        "collection_name": "GAA B6 SD Adventurer Revised Collection",
        "object_name": "GAA B6 SD Adventurer Revised Object", "mesh_name": "GAA B6 SD Adventurer Revised Mesh",
        "regional_adjustments": {"head_scale": 1.08, "arm_length_scale": 0.88,
                                 "hand_scale": 1.12, "foot_scale": 1.10},
        "policy": {"existing_names": "REFUSE", "source": "PRESERVE",
                   "revision": "NEW_COLLECTION_OBJECT_MESH_SHARED_MATERIALS_PRESERVE_UV_TOPOLOGY",
                   "failure": "ROLL_BACK_OWNED_DATA", "rigging": "NOT_INCLUDED"},
    }


def b5_publication_failure(static_module, output):
    directory = output / "b5-publication-probe"
    directory.mkdir()
    sentinel = directory / "user-owned.png"
    sentinel.write_bytes(b"USER OWNED")
    token = uuid.uuid4().hex
    ledger = []
    spec = {"kind": "WOOD_GRAIN", "image_name": "GAA B5 Publication Probe",
            "file_name": "owned-probe.png", "resolution": 16,
            "palette": [[0.2, 0.05, 0.01, 1], [0.7, 0.3, 0.05, 1]], "scale": 4, "seed": 7}
    original = static_module._verify_published_file
    raised = False
    published_before_cleanup = False
    try:
        static_module._verify_published_file = lambda *_args: (_ for _ in ()).throw(RuntimeError("injected post-link verification failure"))
        static_module._make_texture_image(spec, directory, token, ledger)
    except RuntimeError as error:
        raised = "injected" in str(error)
        published_before_cleanup = (directory / spec["file_name"]).is_file()
        static_module._cleanup_created_files(ledger)
        static_module._rollback(token)
    finally:
        static_module._verify_published_file = original
    staged = list(directory.glob("*.staged.png")) + list(directory.glob(".*.staged.png"))
    residue = [image.name for image in bpy.data.images if image.get(static_module.OWNER_KEY) == token]
    result = {"injected_failure_raised": raised, "published_before_cleanup": published_before_cleanup,
              "published_after_cleanup": (directory / spec["file_name"]).exists(),
              "staged_after_cleanup": [str(path) for path in staged], "blender_image_residue": residue,
              "user_file_preserved": sentinel.read_bytes() == b"USER OWNED"}
    if not all((raised, published_before_cleanup, result["user_file_preserved"])) or result["published_after_cleanup"] or staged or residue:
        raise AssertionError(f"B5 publication rollback failed: {result}")
    return result


def main():
    args = arguments()
    output = args.artifact_root
    output.mkdir(parents=True, exist_ok=True)
    previews = output / "previews"
    previews.mkdir(exist_ok=True)
    sys.path.insert(0, str(args.repo_root / "scripts"))
    import create_character_base as character
    import create_static_asset_assembly as static

    publication = b5_publication_failure(static, output)
    source_before = file_sha(args.source_blend)
    request = base_request(args.source_blend, source_before)
    bad = json.loads(json.dumps(request))
    bad["character_name"] += " Bad"; bad["collection_name"] += " Bad"
    bad["object_name"] += " Bad"; bad["mesh_name"] += " Bad"
    bad["template"]["source_sha256"] = "0" * 64
    baseline = {name: sorted(item.name for item in getattr(bpy.data, name))
                for name in ("collections", "objects", "meshes", "materials", "images")}
    refused = False
    try:
        character.create_character(bad, authorized=True)
    except ValueError as error:
        refused = "SHA-256 mismatch" in str(error)
    if not refused or baseline != {name: sorted(item.name for item in getattr(bpy.data, name)) for name in baseline}:
        raise AssertionError("invalid-source creation did not roll back exactly")

    created = character.create_character(request, authorized=True)
    source_obj = bpy.data.objects[created["object_name"]]
    source_mesh = source_obj.data
    source_coords = [vertex.co.copy() for vertex in source_mesh.vertices]
    source_uv = [[float(value) for value in loop.uv] for loop in source_mesh.uv_layers.active.data]
    source_topology = topology(source_mesh)
    source_materials = tuple(source_mesh.materials)

    injected = revision_request()
    injected["character_name"] += " Failure"; injected["collection_name"] += " Failure"
    injected["object_name"] += " Failure"; injected["mesh_name"] += " Failure"
    revision_baseline = {name: sorted(item.name for item in getattr(bpy.data, name))
                         for name in ("collections", "objects", "meshes", "materials", "images")}
    original_apply = character._apply_region_controls
    rollback_raised = False
    try:
        character._apply_region_controls = lambda *_args: (_ for _ in ()).throw(RuntimeError("injected revision failure"))
        character.revise_character_copy(injected, authorized=True)
    except RuntimeError as error:
        rollback_raised = "injected" in str(error)
    finally:
        character._apply_region_controls = original_apply
    revision_rollback = rollback_raised and revision_baseline == {
        name: sorted(item.name for item in getattr(bpy.data, name)) for name in revision_baseline}
    if not revision_rollback:
        raise AssertionError("injected character revision did not roll back exactly")

    revised = character.revise_character_copy(revision_request(), authorized=True)
    revised_obj = bpy.data.objects[revised["object_name"]]
    revised_mesh = revised_obj.data
    revised_topology = topology(revised_mesh)
    revised_uv = [[float(value) for value in loop.uv] for loop in revised_mesh.uv_layers.active.data]
    displacements = [(revised_mesh.vertices[index].co - source_coords[index]).length
                     for index in range(len(source_coords))]
    unchanged = sum(value <= 1e-12 for value in displacements)
    failures = []
    if source_topology != revised_topology:
        failures.append("revision topology differs")
    if source_uv != revised_uv:
        failures.append("revision UV differs")
    if tuple(revised_mesh.materials) != source_materials:
        failures.append("revision Material references differ")
    if source_obj.data is revised_obj.data or revised_mesh.users != 1:
        failures.append("revision Mesh is not independent")
    if not any(value > 1e-5 for value in displacements) or unchanged < 100:
        failures.append("revision lacks both meaningful changed and preserved vertices")
    if any((vertex.co - original).length > 1e-12 for vertex, original in zip(source_mesh.vertices, source_coords)):
        failures.append("source coordinates changed")
    for facts in (source_topology, revised_topology):
        if facts["nonmanifold_edges"] or not facts["all_quad"] or facts["uv_loops"] != facts["loops"]:
            failures.append("template topology or UV integrity failed")
    source_symmetry = symmetry_error(source_mesh)
    revised_symmetry = symmetry_error(revised_mesh)
    if max(source_symmetry, revised_symmetry) > 1e-4:
        failures.append("bilateral symmetry tolerance exceeded")
    if file_sha(args.source_blend) != source_before:
        failures.append("external template source changed")

    images = render_views(previews, {"original": source_obj, "revised": revised_obj}, request["proportions"]["height"])
    blend = output / "b6-1-stylized-sd-character.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    report = {
        "schema": "gameassetai.character-b6-validation.v1",
        "status": "structural_pass_visual_review_required" if not failures else "failed",
        "failures": failures, "source_sha256": source_before, "request": request,
        "creation_receipt": created, "revision_receipt": revised,
        "b5_publication_failure": publication, "revision_failure_rollback": revision_rollback,
        "topology": {"original": source_topology, "revised": revised_topology},
        "geometry_change": {"moved_vertices": sum(value > 1e-8 for value in displacements),
                            "unchanged_vertices": unchanged, "maximum_displacement": max(displacements)},
        "symmetry_max_error": {"original": source_symmetry, "revised": revised_symmetry},
        "source_preserved": True, "uv_preserved": source_uv == revised_uv,
        "materials_shared_read_only": tuple(revised_mesh.materials) == source_materials,
        "rig_compatibility": {"status": "not_evaluated", "reason": "B6.1 shape acceptance precedes bounded M2 gate"},
        "images": images,
        "required_visual_checks": ["styled_character_readability", "proportion_request",
                                   "front_side_three_quarter_consistency", "hands_feet_face_integrity",
                                   "revision_visible", "no_body_intersection"],
        "blend": str(blend), "blender_version": bpy.app.version_string,
    }
    report["report_sha256"] = hashlib.sha256(canonical(report).encode()).hexdigest()
    report_path = output / "validation.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError("; ".join(failures))
    print("GAMEASSETAI_B6_WORKFLOW " + json.dumps({"status": report["status"], "blend": str(blend),
                                                   "report": str(report_path), "images": images}))


if __name__ == "__main__":
    main()
