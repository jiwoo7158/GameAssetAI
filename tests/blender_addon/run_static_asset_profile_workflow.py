import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(values)


def primitive(kind, dimensions, segments=None):
    return {"kind": "PRIMITIVE", "primitive": kind, "dimensions": dimensions, "segments": segments}


def profile(points, depth):
    return {"kind": "PROFILE_EXTRUSION", "profile_points": points, "depth": depth}


def policy():
    return {
        "existing_names": "REFUSE",
        "source_scene": "PRESERVE",
        "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
        "failure": "ROLL_BACK_OWNED_DATA",
    }


def revision_policy():
    return {
        "existing_names": "REFUSE",
        "source": "PRESERVE",
        "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
        "failure": "ROLL_BACK_OWNED_DATA",
    }


def style(budget):
    return {
        "family": "STYLIZED_LOW_POLY",
        "shape_language": "BOLD_ANGULAR",
        "silhouette_strategy": "EXPLICIT_PART_GEOMETRY",
        "shading": "FLAT",
        "material_strategy": "DECLARED_LIMITED",
        "max_materials": 3,
        "triangle_budget": budget,
    }


def snapshot(collection):
    return {
        obj.get("gameassetai_semantic_role"): {
            "vertices": [tuple(round(value, 8) for value in vertex.co) for vertex in obj.data.vertices],
            "location": tuple(round(value, 8) for value in obj.location),
            "rotation": tuple(round(value, 8) for value in obj.rotation_euler),
            "scale": tuple(round(value, 8) for value in obj.scale),
            "materials": tuple(material.name for material in obj.data.materials),
        }
        for obj in collection.objects
    }


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    maximum = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return minimum, maximum


def review_frame(objects):
    minimum, maximum = bounds(objects)
    center = (minimum + maximum) * 0.5
    size = maximum - minimum
    return {
        "minimum": tuple(float(value) for value in minimum),
        "maximum": tuple(float(value) for value in maximum),
        "center": tuple(float(value) for value in center),
        "ortho_scale": float(max(size.x, size.y, size.z) * 1.35),
        "distance": float(max(size) * 4.0 + 2.0),
    }


def render_views(scene, collections, target, artifact_dir, label, framing=None):
    camera_data = bpy.data.cameras.new(f"GAA {label} Review Camera Data")
    camera = bpy.data.objects.new(f"GAA {label} Review Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    framing = framing or review_frame(list(target.objects))
    center = Vector(framing["center"])
    camera_data.ortho_scale = framing["ortho_scale"]
    distance = framing["distance"]

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "WORLD"
    scene.display.shading.show_backface_culling = True

    target_objects = set(target.objects)
    prior_visibility = {obj: obj.hide_render for obj in scene.objects if obj.type == "MESH"}
    for obj in prior_visibility:
        obj.hide_render = obj not in target_objects

    views = {
        "front": Vector((0.0, -distance, 0.0)),
        "side": Vector((distance, 0.0, 0.0)),
        "three-quarter": Vector((distance * 0.7, -distance * 0.7, distance * 0.28)),
    }
    outputs = []
    for name, offset in views.items():
        camera.location = center + offset
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        output = artifact_dir / "previews" / f"{label}-{name}.png"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        outputs.append(output)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    for obj, hidden in prior_visibility.items():
        obj.hide_render = hidden
    return outputs


def profile_quality(receipt):
    return [
        part["mesh_quality"] for part in receipt["parts"]
        if part["geometry_kind"] == "PROFILE_EXTRUSION"
    ]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    artifact_dir = Path(args.artifact_dir).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    (artifact_dir / "previews").mkdir(exist_ok=True)
    sys.path.insert(0, str(repo_root / "scripts"))
    import create_static_asset_assembly as assembly
    from create_static_asset_assembly import create_asset, revise_asset_copy

    scene = bpy.context.scene
    baseline = {
        "objects": sorted(bpy.data.objects.keys()),
        "meshes": sorted(bpy.data.meshes.keys()),
        "materials": sorted(bpy.data.materials.keys()),
        "collections": sorted(bpy.data.collections.keys()),
    }
    materials = [
        {"name": "GAA Axe Dark Wood", "base_color": [0.16, 0.055, 0.018, 1.0], "metallic": 0.0, "roughness": 0.82},
        {"name": "GAA Axe Forged Steel", "base_color": [0.18, 0.27, 0.38, 1.0], "metallic": 0.72, "roughness": 0.27},
        {"name": "GAA Axe Leather", "base_color": [0.32, 0.08, 0.025, 1.0], "metallic": 0.0, "roughness": 0.9},
    ]
    axe = {
        "schema": "gameassetai.static-asset-assembly-request.v3",
        "scene_name": scene.name,
        "asset_name": "Stylized Low Poly Fantasy Axe",
        "collection_name": "GAA Stylized Fantasy Axe",
        "style": style(220),
        "materials": materials,
        "parts": [
            {"name": "GAA Axe Handle", "semantic_role": "handle", "geometry": primitive("CYLINDER", [0.28, 0.28, 3.6], 10), "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "GAA Axe Dark Wood"},
            {"name": "GAA Axe Grip", "semantic_role": "grip", "geometry": primitive("CYLINDER", [0.36, 0.36, 0.9], 10), "location": [0, 0, -1.28], "rotation_degrees": [0, 0, 0], "material": "GAA Axe Leather"},
            {"name": "GAA Axe Collar", "semantic_role": "collar", "geometry": primitive("BOX", [0.62, 0.44, 0.48]), "location": [0, 0, 1.42], "rotation_degrees": [0, 0, 0], "material": "GAA Axe Forged Steel"},
            {"name": "GAA Axe Blade", "semantic_role": "blade", "geometry": profile([[-0.12, -0.5], [0.98, -0.43], [1.34, -0.18], [1.18, 0.68], [0.43, 0.9], [-0.12, 0.5]], 0.28), "location": [0.12, 0, 1.48], "rotation_degrees": [0, 0, 0], "material": "GAA Axe Forged Steel"},
            {"name": "GAA Axe Rear Spike", "semantic_role": "rear_spike", "geometry": profile([[-0.08, -0.24], [0.78, 0.0], [-0.08, 0.24]], 0.24), "location": [-0.36, 0, 1.48], "rotation_degrees": [0, 0, 180], "material": "GAA Axe Forged Steel"},
            {"name": "GAA Axe Pommel", "semantic_role": "pommel", "geometry": primitive("ICOSPHERE", [0.42, 0.42, 0.42], 12), "location": [0, 0, -1.92], "rotation_degrees": [0, 0, 0], "material": "GAA Axe Forged Steel"},
        ],
        "policy": policy(),
    }
    original_receipt = create_asset(axe, authorized=True)
    original_collection = bpy.data.collections[axe["collection_name"]]
    source_snapshot = snapshot(original_collection)

    revision = {
        "schema": "gameassetai.static-asset-revision-request.v2",
        "scene_name": scene.name,
        "source_collection_name": axe["collection_name"],
        "asset_name": "Wide Sharp Stylized Fantasy Axe",
        "collection_name": "GAA Wide Sharp Fantasy Axe",
        "revisions": [{
            "semantic_role": "blade",
            "geometry": profile([[-0.12, -0.6], [1.12, -0.54], [1.72, 0.0], [1.46, 0.82], [0.45, 1.02], [-0.12, 0.54]], 0.3),
            "location": None,
            "rotation_degrees": None,
        }],
        "policy": revision_policy(),
    }
    revised_receipt = revise_asset_copy(revision, authorized=True)
    revised_collection = bpy.data.collections[revision["collection_name"]]
    revised_snapshot = snapshot(revised_collection)

    assert snapshot(original_collection) == source_snapshot
    assert source_snapshot["blade"]["vertices"] != revised_snapshot["blade"]["vertices"]
    assert source_snapshot["blade"]["scale"] == revised_snapshot["blade"]["scale"] == (1.0, 1.0, 1.0)
    for role in set(source_snapshot) - {"blade"}:
        assert source_snapshot[role]["vertices"] == revised_snapshot[role]["vertices"]
        assert source_snapshot[role]["materials"] == revised_snapshot[role]["materials"]

    rollback = json.loads(json.dumps(revision))
    rollback["asset_name"] = "Rollback Geometry Axe"
    rollback["collection_name"] = "GAA Rollback Geometry Axe"
    original_replacement = assembly._replacement_part
    def fail_after_replacement(*values, **keywords):
        original_replacement(*values, **keywords)
        raise RuntimeError("deliberate v3 geometry rollback probe")
    assembly._replacement_part = fail_after_replacement
    try:
        revise_asset_copy(rollback, authorized=True)
        raise AssertionError("deliberate v3 geometry failure must propagate")
    except RuntimeError as exc:
        assert "rollback probe" in str(exc)
    finally:
        assembly._replacement_part = original_replacement
    assert bpy.data.collections.get(rollback["collection_name"]) is None
    assert not any(obj.name.startswith("Rollback Geometry Axe") for obj in bpy.data.objects)

    shield = {
        "schema": "gameassetai.static-asset-assembly-request.v3",
        "scene_name": scene.name,
        "asset_name": "Stylized Profile Shield",
        "collection_name": "GAA Stylized Profile Shield",
        "style": style(100),
        "materials": [
            {"name": "GAA Shield Wood", "base_color": [0.11, 0.18, 0.24, 1.0], "metallic": 0.0, "roughness": 0.78},
            {"name": "GAA Shield Steel", "base_color": [0.3, 0.38, 0.48, 1.0], "metallic": 0.68, "roughness": 0.3},
        ],
        "parts": [
            {"name": "GAA Shield Face", "semantic_role": "shield_face", "geometry": profile([[-0.78, -0.55], [0, -1.18], [0.78, -0.55], [0.95, 0.8], [0, 1.16], [-0.95, 0.8]], 0.22), "location": [4.5, 0, 0], "rotation_degrees": [0, 0, 0], "material": "GAA Shield Wood"},
            {"name": "GAA Shield Boss", "semantic_role": "boss", "geometry": primitive("ICOSPHERE", [0.62, 0.34, 0.62], 12), "location": [4.5, -0.15, 0], "rotation_degrees": [0, 0, 0], "material": "GAA Shield Steel"},
        ],
        "policy": policy(),
    }
    shield_receipt = create_asset(shield, authorized=True)
    shield_collection = bpy.data.collections[shield["collection_name"]]
    assert any(part["geometry_kind"] == "PROFILE_EXTRUSION" for part in shield_receipt["parts"])

    concave = {
        "schema": "gameassetai.static-asset-assembly-request.v3",
        "scene_name": scene.name,
        "asset_name": "Concave Profile Quality Probe",
        "collection_name": "GAA Concave Profile Quality Probe",
        "style": style(40),
        "materials": [{"name": "GAA Concave Probe Material", "base_color": [0.4, 0.2, 0.1, 1], "metallic": 0.0, "roughness": 0.8}],
        "parts": [{
            "name": "GAA Concave Probe", "semantic_role": "concave_probe",
            "geometry": profile([[0, 0], [2, 0], [2, 2], [1, 1], [0, 2]], 0.35),
            "location": [0, 0, 0], "rotation_degrees": [0, 0, 0],
            "material": "GAA Concave Probe Material",
        }],
        "policy": policy(),
    }
    concave_receipt = create_asset(concave, authorized=True)
    assert all(item["closed_manifold"] and item["normals_outward"] for item in profile_quality(concave_receipt))
    assembly.remove_created_asset(concave_receipt)
    assert bpy.data.collections.get(concave["collection_name"]) is None

    all_profile_quality = (
        profile_quality(original_receipt) + profile_quality(revised_receipt)
        + profile_quality(shield_receipt) + profile_quality(concave_receipt)
    )
    assert all(item["closed_manifold"] for item in all_profile_quality)
    assert all(item["normals_outward"] for item in all_profile_quality)
    assert all(item["signed_volume"] > 0 for item in all_profile_quality)
    assert all(item["zero_area_faces"] == 0 for item in all_profile_quality)
    assert all(item["duplicate_vertices"] == 0 for item in all_profile_quality)

    collections = [original_collection, revised_collection, shield_collection]
    preview_paths = []
    shared_axe_frame = review_frame(list(original_collection.objects) + list(revised_collection.objects))
    preview_paths.extend(render_views(scene, collections, original_collection, artifact_dir, "axe-original", shared_axe_frame))
    preview_paths.extend(render_views(scene, collections, revised_collection, artifact_dir, "axe-revised", shared_axe_frame))
    preview_paths.extend(render_views(scene, collections, shield_collection, artifact_dir, "profile-shield"))

    blend_path = artifact_dir / "result.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    validation = {
        "status": "structural_pass_visual_review_required",
        "schema": "gameassetai.static-production-v3-validation.v1",
        "baseline": baseline,
        "original_receipt": original_receipt,
        "revision_receipt": revised_receipt,
        "secondary_receipt": shield_receipt,
        "checks": {
            "profile_extrusion_created": True,
            "geometry_revision_changed_vertices": True,
            "revision_object_scale_unchanged": True,
            "source_preserved_exactly": True,
            "unrelated_parts_preserved": True,
            "shared_materials_preserved": True,
            "induced_failure_rolled_back": True,
            "secondary_non_weapon_profile_created": True,
            "style_budget_enforced": True,
            "flat_shading_enforced": all(not polygon.use_smooth for collection in collections for obj in collection.objects for polygon in obj.data.polygons),
            "profile_normals_outward": all(item["normals_outward"] for item in all_profile_quality),
            "profile_closed_manifold": all(item["closed_manifold"] for item in all_profile_quality),
            "profile_positive_signed_volume": all(item["signed_volume"] > 0 for item in all_profile_quality),
            "profile_no_zero_area_faces": all(item["zero_area_faces"] == 0 for item in all_profile_quality),
            "profile_no_duplicate_vertices": all(item["duplicate_vertices"] == 0 for item in all_profile_quality),
            "convex_and_concave_profiles_checked": True,
            "original_revision_shared_camera_framing": True,
            "backface_culling_review_rendered": True,
        },
        "profile_quality": all_profile_quality,
        "shared_axe_camera": shared_axe_frame,
        "visual_review": {
            "status": "pending",
            "required_views": [path.relative_to(artifact_dir).as_posix() for path in preview_paths],
        },
    }
    validation_path = artifact_dir / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    source_info = {
        "repository": str(repo_root),
        "blender_version": bpy.app.version_string,
        "result_blend_sha256": sha256(blend_path),
        "validation_sha256": sha256(validation_path),
    }
    (artifact_dir / "source-info.json").write_text(json.dumps(source_info, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "pass",
        "blend": str(blend_path),
        "validation": str(validation_path),
        "previews": [str(path) for path in preview_paths],
    }))


if __name__ == "__main__":
    main()
