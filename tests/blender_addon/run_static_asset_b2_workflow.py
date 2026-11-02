import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def primitive(kind, dimensions, segments=None):
    return {"kind": "PRIMITIVE", "primitive": kind, "dimensions": dimensions, "segments": segments}


def beveled(outer, core, depth):
    return {
        "kind": "PROFILE_BEVELED_EXTRUSION",
        "outer_profile_points": outer,
        "core_profile_points": core,
        "depth": depth,
    }


def creation_policy():
    return {"existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS", "failure": "ROLL_BACK_OWNED_DATA"}


def revision_policy():
    return {"existing_names": "REFUSE", "source": "PRESERVE",
            "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS", "failure": "ROLL_BACK_OWNED_DATA"}


def style(budget, max_materials=3):
    return {"family": "STYLIZED_LOW_POLY", "shape_language": "BOLD_ANGULAR",
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": max_materials,
            "triangle_budget": budget}


def snapshot(collection):
    return {obj.get("gameassetai_semantic_role"): {
        "vertices": [tuple(round(value, 8) for value in vertex.co) for vertex in obj.data.vertices],
        "location": tuple(round(value, 8) for value in obj.location),
        "rotation": tuple(round(value, 8) for value in obj.rotation_euler),
        "scale": tuple(round(value, 8) for value in obj.scale),
        "materials": tuple(material.name for material in obj.data.materials),
    } for obj in collection.objects}


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


def shared_frame(collections):
    bpy.context.view_layer.update()
    low, high = bounds([obj for collection in collections for obj in collection.objects])
    center = (low + high) * 0.5
    size = high - low
    return {"center": tuple(center), "ortho_scale": float(max(size) * 1.35),
            "distance": float(max(size) * 4 + 2)}


def render_views(scene, target, artifact, label, frame):
    data = bpy.data.cameras.new(f"{label} Camera Data")
    camera = bpy.data.objects.new(f"{label} Camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type = "ORTHO"
    data.ortho_scale = frame["ortho_scale"]
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
    scene.display.shading.show_backface_culling = True
    visible = set(target.objects)
    prior = {obj: obj.hide_render for obj in scene.objects if obj.type == "MESH"}
    for obj in prior:
        obj.hide_render = obj not in visible
    views = {"front": Vector((0, -distance, 0)), "side": Vector((distance, 0, 0)),
             "three-quarter": Vector((distance * .7, -distance * .7, distance * .3))}
    outputs = {}
    for view, offset in views.items():
        camera.location = center + offset
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        output = artifact / "previews" / f"{label}-{view}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        outputs[f"{label}_{view}"] = str(output.resolve())
    for obj, hidden in prior.items():
        obj.hide_render = hidden
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(data)
    return outputs


def assert_revision(source_collection, revised_collection, changed_roles):
    source = snapshot(source_collection)
    revised = snapshot(revised_collection)
    for role in changed_roles:
        assert source[role]["vertices"] != revised[role]["vertices"]
        assert source[role]["scale"] == revised[role]["scale"] == (1.0, 1.0, 1.0)
    for role in set(source) - set(changed_roles):
        assert source[role] == revised[role]
    return source, revised


def main():
    parsed = args()
    root, artifact = Path(parsed.repo_root).resolve(), Path(parsed.artifact_dir).resolve()
    (artifact / "previews").mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(root / "scripts"))
    import create_static_asset_assembly as module
    from create_static_asset_assembly import create_asset, revise_asset_copy
    scene = bpy.context.scene

    axe_materials = [
        {"name": "B2 Axe Wood", "base_color": [.15, .045, .012, 1], "metallic": 0, "roughness": .82},
        {"name": "B2 Axe Steel", "base_color": [.18, .28, .42, 1], "metallic": .75, "roughness": .26},
        {"name": "B2 Axe Leather", "base_color": [.34, .075, .02, 1], "metallic": 0, "roughness": .9},
    ]
    axe_outer = [[-.15, -.55], [1.2, -.48], [1.65, -.18], [1.75, .2], [1.35, .75], [.45, .95], [-.15, .55]]
    axe_core = [[-.08, -.38], [.75, -.32], [1.12, -.12], [1.2, .18], [.95, .53], [.38, .68], [-.08, .38]]
    axe = {"schema": "gameassetai.static-asset-assembly-request.v4", "scene_name": scene.name,
           "asset_name": "B2 Fantasy Axe", "collection_name": "GAA B2 Fantasy Axe", "style": style(240),
           "materials": axe_materials, "parts": [
               {"name": "B2 Axe Handle", "semantic_role": "handle", "geometry": primitive("CYLINDER", [.28, .28, 3.7], 10), "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "B2 Axe Wood"},
               {"name": "B2 Axe Grip", "semantic_role": "grip", "geometry": primitive("CYLINDER", [.36, .36, .9], 10), "location": [0, 0, -1.35], "rotation_degrees": [0, 0, 0], "material": "B2 Axe Leather"},
               {"name": "B2 Axe Collar", "semantic_role": "collar", "geometry": primitive("BOX", [.62, .48, .5]), "location": [0, 0, 1.48], "rotation_degrees": [0, 0, 0], "material": "B2 Axe Steel"},
               {"name": "B2 Axe Blade", "semantic_role": "blade", "geometry": beveled(axe_outer, axe_core, .38), "location": [.12, 0, 1.5], "rotation_degrees": [0, 0, 0], "material": "B2 Axe Steel"},
               {"name": "B2 Axe Pommel", "semantic_role": "pommel", "geometry": primitive("ICOSPHERE", [.42, .42, .42], 12), "location": [0, 0, -1.95], "rotation_degrees": [0, 0, 0], "material": "B2 Axe Steel"},
           ], "policy": creation_policy()}
    axe_receipt = create_asset(axe, authorized=True)
    axe_collection = bpy.data.collections[axe["collection_name"]]
    axe_revision = {"schema": "gameassetai.static-asset-revision-request.v3", "scene_name": scene.name,
        "source_collection_name": axe["collection_name"], "asset_name": "B2 Wide Bevel Axe",
        "collection_name": "GAA B2 Wide Bevel Axe", "revisions": [{"semantic_role": "blade",
            "geometry": beveled(
                [[-.15, -.6], [1.28, -.54], [1.82, -.22], [1.92, .2], [1.48, .84], [.45, 1.02], [-.15, .58]],
                [[-.06, -.28], [.58, -.25], [.9, -.08], [.96, .16], [.76, .4], [.32, .52], [-.06, .28]], .28),
            "location": None, "rotation_degrees": None}], "policy": revision_policy()}
    axe_revised_receipt = revise_asset_copy(axe_revision, authorized=True)
    axe_revised_collection = bpy.data.collections[axe_revision["collection_name"]]
    assert_revision(axe_collection, axe_revised_collection, {"blade"})

    wood = {"name": "B2 Crate Wood", "base_color": [.28, .105, .025, 1], "metallic": 0, "roughness": .8}
    metal = {"name": "B2 Crate Metal", "base_color": [.12, .18, .24, 1], "metallic": .72, "roughness": .32}
    body_outer = [[-1.1, -.72], [1.1, -.72], [1.28, -.54], [1.28, .54], [1.1, .72], [-1.1, .72], [-1.28, .54], [-1.28, -.54]]
    body_core = [[-.98, -.58], [.98, -.58], [1.08, -.46], [1.08, .46], [.98, .58], [-.98, .58], [-1.08, .46], [-1.08, -.46]]
    panel_outer = [[-.72, -.42], [.72, -.42], [.84, -.3], [.84, .3], [.72, .42], [-.72, .42], [-.84, .3], [-.84, -.3]]
    panel_core = [[-.6, -.3], [.6, -.3], [.68, -.22], [.68, .22], [.6, .3], [-.6, .3], [-.68, .22], [-.68, -.22]]
    crate = {"schema": "gameassetai.static-asset-assembly-request.v4", "scene_name": scene.name,
        "asset_name": "B2 Reinforced Crate", "collection_name": "GAA B2 Reinforced Crate",
        "style": style(260, 2), "materials": [wood, metal], "parts": [
            {"name": "B2 Crate Body", "semantic_role": "body", "geometry": beveled(body_outer, body_core, 1.5), "location": [4.4, 0, 0], "rotation_degrees": [0, 0, 0], "material": "B2 Crate Wood"},
            {"name": "B2 Crate Front Panel", "semantic_role": "front_panel", "geometry": beveled(panel_outer, panel_core, .22), "location": [4.4, -.84, 0], "rotation_degrees": [0, 0, 0], "material": "B2 Crate Metal"},
            {"name": "B2 Crate Top Brace", "semantic_role": "top_brace", "geometry": primitive("BOX", [2.05, 1.64, .14]), "location": [4.4, 0, .73], "rotation_degrees": [0, 0, 0], "material": "B2 Crate Metal"},
            {"name": "B2 Crate Bottom Brace", "semantic_role": "bottom_brace", "geometry": primitive("BOX", [2.05, 1.64, .14]), "location": [4.4, 0, -.73], "rotation_degrees": [0, 0, 0], "material": "B2 Crate Metal"},
        ], "policy": creation_policy()}
    crate_receipt = create_asset(crate, authorized=True)
    crate_collection = bpy.data.collections[crate["collection_name"]]
    crate_revision = {"schema": "gameassetai.static-asset-revision-request.v3", "scene_name": scene.name,
        "source_collection_name": crate["collection_name"], "asset_name": "B2 Revised Crate",
        "collection_name": "GAA B2 Revised Crate", "revisions": [
            {"semantic_role": "body", "geometry": beveled(body_outer,
                [[-.84, -.5], [.84, -.5], [.94, -.38], [.94, .38], [.84, .5], [-.84, .5], [-.94, .38], [-.94, -.38]], 1.5),
             "location": None, "rotation_degrees": None},
            {"semantic_role": "front_panel", "geometry": beveled(panel_outer,
                [[-.52, -.24], [.52, -.24], [.58, -.18], [.58, .18], [.52, .24], [-.52, .24], [-.58, .18], [-.58, -.18]], .34),
             "location": [4.4, -.9, 0], "rotation_degrees": None},
        ], "policy": revision_policy()}
    crate_revised_receipt = revise_asset_copy(crate_revision, authorized=True)
    crate_revised_collection = bpy.data.collections[crate_revision["collection_name"]]
    assert_revision(crate_collection, crate_revised_collection, {"body", "front_panel"})

    rollback = json.loads(json.dumps(axe_revision))
    rollback["asset_name"], rollback["collection_name"] = "B2 Rollback", "GAA B2 Rollback"
    original_replacement = module._replacement_part
    def fail(*values, **keywords):
        original_replacement(*values, **keywords)
        raise RuntimeError("deliberate B2 rollback probe")
    module._replacement_part = fail
    try:
        revise_asset_copy(rollback, authorized=True)
        raise AssertionError("rollback failure must propagate")
    except RuntimeError as exc:
        assert "rollback probe" in str(exc)
    finally:
        module._replacement_part = original_replacement
    assert bpy.data.collections.get(rollback["collection_name"]) is None

    receipts = [axe_receipt, axe_revised_receipt, crate_receipt, crate_revised_receipt]
    qualities = [part["mesh_quality"] for receipt in receipts for part in receipt["parts"] if part["geometry_kind"] == "PROFILE_BEVELED_EXTRUSION"]
    assert len(qualities) == 6
    assert all(item["closed_manifold"] and item["normals_outward"] and item["signed_volume"] > 0 for item in qualities)
    assert all(item["zero_area_faces"] == item["duplicate_vertices"] == 0 for item in qualities)
    assert all(not polygon.use_smooth for collection in (axe_collection, axe_revised_collection, crate_collection, crate_revised_collection) for obj in collection.objects for polygon in obj.data.polygons)

    images = {}
    axe_frame = shared_frame([axe_collection, axe_revised_collection])
    crate_frame = shared_frame([crate_collection, crate_revised_collection])
    images.update(render_views(scene, axe_collection, artifact, "axe-original", axe_frame))
    images.update(render_views(scene, axe_revised_collection, artifact, "axe-revised", axe_frame))
    images.update(render_views(scene, crate_collection, artifact, "crate-original", crate_frame))
    images.update(render_views(scene, crate_revised_collection, artifact, "crate-revised", crate_frame))
    blend = artifact / "result.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    validation = {"schema": "gameassetai.static-production-b2-validation.v1",
        "status": "structural_pass_visual_review_required", "images": images,
        "required_visual_checks": ["assets_recognizable", "real_cross_section_change", "requested_revision_visible", "unintended_gaps_or_overlap_absent", "low_poly_flat_shading_usable"],
        "checks": {"v4_axe_created": True, "v4_crate_created": True,
            "beveled_geometry_reused_across_asset_types": True, "semantic_revisions_changed_mesh_vertices": True,
            "object_scale_unchanged": True, "source_and_unrelated_parts_preserved": True,
            "materials_preserved": True, "closed_manifold": True, "outward_normals": True,
            "positive_volume": True, "zero_area_faces_absent": True, "triangle_budgets_met": True,
            "flat_shading": True, "induced_failure_rolled_back": True,
            "shared_camera_comparison": True, "visual_review_recorded": False},
        "receipts": {"axe": axe_receipt, "axe_revision": axe_revised_receipt,
                     "crate": crate_receipt, "crate_revision": crate_revised_receipt},
        "mesh_quality": qualities, "frames": {"axe": axe_frame, "crate": crate_frame}}
    validation_path = artifact / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    (artifact / "source-info.json").write_text(json.dumps({
        "repository": str(root), "blender_version": bpy.app.version_string,
        "result_blend_sha256": sha(blend), "validation_sha256": sha(validation_path)}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "structural_pass_visual_review_required", "blend": str(blend),
                      "validation": str(validation_path), "images": images}))


if __name__ == "__main__":
    main()
