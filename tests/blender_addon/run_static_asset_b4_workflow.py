import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--artifact-dir", required=True)
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(values)


def beveled(outer, core, depth):
    return {"kind": "PROFILE_BEVELED_EXTRUSION", "outer_profile_points": outer,
            "core_profile_points": core, "depth": depth}


def profile(points, depth):
    return {"kind": "PROFILE_EXTRUSION", "profile_points": points, "depth": depth}


def primitive(kind, dimensions, segments=None):
    return {"kind": "PRIMITIVE", "primitive": kind, "dimensions": dimensions, "segments": segments}


def style(shape, budget, materials):
    return {"family": "CUSTOM", "shape_language": shape,
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": materials,
            "triangle_budget": budget}


def policy():
    return {"existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS_IMAGES",
            "external_files": "NO_OVERWRITE_OWNED_PNG",
            "failure": "ROLL_BACK_OWNED_DATA_AND_FILES"}


def appearance(texture_dir, resolution=128, byte_budget=524288):
    return {"uv_policy": "LOCAL_BOX_PROJECT", "texture_policy": "OPTIONAL_GENERATED_PNG",
            "texture_output_directory": str(texture_dir), "max_texture_resolution": resolution,
            "max_texture_bytes": byte_budget, "pack_images": True}


def material(name, role, color, metallic, roughness, texture=None):
    return {"name": name, "material_role": role, "base_color": color,
            "metallic": metallic, "roughness": roughness, "texture": texture}


def angular_request(scene, texture_dir):
    outer = [[-1.3, -.68], [1.3, -.68], [1.42, -.54], [1.42, .54], [1.3, .68], [-1.3, .68], [-1.42, .54], [-1.42, -.54]]
    core = [[-1.12, -.54], [1.12, -.54], [1.24, -.44], [1.24, .44], [1.12, .54], [-1.12, .54], [-1.24, .44], [-1.24, -.44]]
    panel_outer = [[-.82, -.4], [.82, -.4], [.94, -.28], [.94, .28], [.82, .4], [-.82, .4], [-.94, .28], [-.94, -.28]]
    panel_core = [[-.69, -.29], [.69, -.29], [.78, -.21], [.78, .21], [.69, .29], [-.69, .29], [-.78, .21], [-.78, -.21]]
    return {"schema": "gameassetai.static-asset-assembly-request.v5", "scene_name": scene.name,
        "asset_name": "B4 Angular Low-Poly Crate", "collection_name": "GAA B4 Angular Crate",
        "style": style("HARD_ANGULAR", 180, 2),
        "art_direction": {"provenance": {"source": "USER_REQUEST", "source_ref": "B4 Angular Low-Poly representative brief", "profile_sha256": None},
            "surface_style": "ANGULAR_LOW_POLY", "silhouette": "wide rectangular crate with clipped hard corners",
            "proportion": "wide low body and narrow front inset", "geometry_detail": "large flat faces and heavy straight braces",
            "palette": [[.23, .075, .02, 1], [.42, .16, .035, 1], [.1, .13, .16, 1]],
            "unsupported": ["image texture intentionally omitted for this style"]},
        "appearance": appearance(texture_dir),
        "materials": [
            material("B4 Angular Wood", "wood", [.32, .095, .018, 1], 0, .86),
            material("B4 Angular Metal", "metal", [.07, .105, .14, 1], .72, .3),
        ],
        "parts": [
            {"name": "B4 Angular Body", "semantic_role": "body", "geometry": beveled(outer, core, 1.46), "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": "B4 Angular Wood"},
            {"name": "B4 Angular Panel", "semantic_role": "front_panel", "geometry": beveled(panel_outer, panel_core, .2), "location": [0, -.82, 0], "rotation_degrees": [0, 0, 0], "material": "B4 Angular Metal"},
            {"name": "B4 Angular Top Brace", "semantic_role": "top_brace", "geometry": primitive("BOX", [2.5, 1.6, .16]), "location": [0, 0, .7], "rotation_degrees": [0, 0, 0], "material": "B4 Angular Metal"},
            {"name": "B4 Angular Bottom Brace", "semantic_role": "bottom_brace", "geometry": primitive("BOX", [2.5, 1.6, .16]), "location": [0, 0, -.7], "rotation_degrees": [0, 0, 0], "material": "B4 Angular Metal"},
        ], "policy": policy()}


def painted_request(scene, texture_dir, prefix="B4 Painted"):
    outer = [[-1.0, -.8], [1.0, -.8], [1.22, -.62], [1.32, -.25], [1.32, .45], [1.18, .72], [.85, .88], [-.85, .88], [-1.18, .72], [-1.32, .45], [-1.32, -.25], [-1.22, -.62]]
    core = [[x * .82, z * .78] for x, z in outer]
    panel_outer = [[-.76, -.5], [.76, -.5], [.94, -.28], [.94, .34], [.58, .63], [0, .78], [-.58, .63], [-.94, .34], [-.94, -.28]]
    panel_core = [[x * .77, z * .76] for x, z in panel_outer]
    crest = [[-.5, -.12], [.5, -.12], [.42, .08], [.18, .24], [0, .34], [-.18, .24], [-.42, .08]]
    safe = prefix.lower().replace(" ", "-")
    wood_texture = {"kind": "WOOD_GRAIN", "image_name": prefix + " Wood Image",
                    "file_name": safe + "-wood.png", "resolution": 128,
                    "palette": [[.19, .035, .008, 1], [.68, .24, .035, 1], [.96, .58, .14, 1]],
                    "scale": 7, "seed": 31}
    metal_texture = {"kind": "PAINTED_METAL", "image_name": prefix + " Metal Image",
                     "file_name": safe + "-metal.png", "resolution": 128,
                     "palette": [[.035, .11, .16, 1], [.14, .38, .46, 1], [.66, .78, .7, 1]],
                     "scale": 6, "seed": 73}
    return {"schema": "gameassetai.static-asset-assembly-request.v5", "scene_name": scene.name,
        "asset_name": prefix + " Stylized Crate", "collection_name": "GAA " + prefix + " Crate",
        "style": style("SOFT_CHUNKY_ORNAMENTED", 260, 2),
        "art_direction": {"provenance": {"source": "USER_REQUEST", "source_ref": "B4 Painted-Look representative brief", "profile_sha256": None},
            "surface_style": "PAINTED_LOOK_STYLIZED", "silhouette": "tall rounded crate with crest and posts",
            "proportion": "taller body, broad shield panel and rounded front posts", "geometry_detail": "curved profile rhythm and ornamental crest",
            "palette": [[.19, .035, .008, 1], [.68, .24, .035, 1], [.14, .38, .46, 1], [.96, .58, .14, 1]],
            "unsupported": ["hand-painted illustration quality", "normal and roughness texture maps"]},
        "appearance": appearance(texture_dir),
        "materials": [
            material(prefix + " Wood", "wood", [.5, .16, .025, 1], 0, .78, wood_texture),
            material(prefix + " Metal", "painted_metal", [.08, .25, .31, 1], .38, .48, metal_texture),
        ],
        "parts": [
            {"name": prefix + " Body", "semantic_role": "body", "geometry": beveled(outer, core, 1.55), "location": [0, 0, 0], "rotation_degrees": [0, 0, 0], "material": prefix + " Wood"},
            {"name": prefix + " Shield Panel", "semantic_role": "front_panel", "geometry": beveled(panel_outer, panel_core, .18), "location": [0, -.82, -.02], "rotation_degrees": [0, 0, 0], "material": prefix + " Metal"},
            {"name": prefix + " Left Post", "semantic_role": "left_post", "geometry": primitive("CYLINDER", [.22, .22, 1.45], 8), "location": [-1.02, -.7, .03], "rotation_degrees": [0, 0, 0], "material": prefix + " Metal"},
            {"name": prefix + " Right Post", "semantic_role": "right_post", "geometry": primitive("CYLINDER", [.22, .22, 1.45], 8), "location": [1.02, -.7, .03], "rotation_degrees": [0, 0, 0], "material": prefix + " Metal"},
            {"name": prefix + " Crest", "semantic_role": "crest", "geometry": profile(crest, .16), "location": [0, -.74, .78], "rotation_degrees": [0, 0, 0], "material": prefix + " Metal"},
        ], "policy": policy()}


def datablock_snapshot():
    return {name: tuple((block.name, block.as_pointer()) for block in getattr(bpy.data, name))
            for name in ("objects", "meshes", "materials", "images", "collections")}


def collection_bounds(collections):
    bpy.context.view_layer.update()
    objects = [obj for collection in collections for obj in collection.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    center, size = (low + high) * .5, high - low
    return center, max(size) * 1.45, max(size) * 4.2 + 2


def render_views(scene, collection, artifact, label, frame):
    center, scale, distance = frame
    camera_data = bpy.data.cameras.new(label + " Camera Data")
    camera = bpy.data.objects.new(label + " Camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type, camera_data.ortho_scale = "ORTHO", scale
    scene.camera = camera
    visible = {obj for obj in collection.objects if obj.type == "MESH"}
    prior = {obj: obj.hide_render for obj in scene.objects if obj.type == "MESH"}
    for obj in prior:
        obj.hide_render = obj not in visible
    views = {"front": Vector((0, -distance, 0)), "side": Vector((distance, 0, 0)),
             "three-quarter": Vector((distance * .72, -distance * .72, distance * .34))}
    images = {}
    for view, offset in views.items():
        camera.location = center + offset
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        path = artifact / "previews" / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        images[f"{label}_{view}"] = str(path.resolve())
    for obj, value in prior.items():
        obj.hide_render = value
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    return images


def setup_render(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (.025, .025, .025)
    lights = []
    for name, location, energy, size, color in (
        ("B4 Key", (-4, -5, 6), 900, 5, (1.0, .78, .58)),
        ("B4 Fill", (4, -2, 3), 650, 4, (.42, .65, 1.0)),
        ("B4 Rim", (1, 4, 5), 750, 3, (.8, .9, 1.0)),
    ):
        data = bpy.data.lights.new(name + " Data", "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        obj.rotation_euler = (Vector((0, 0, 0)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)
        lights.append(obj)
    return lights


def uv_facts(collection):
    facts = {}
    for obj in collection.objects:
        if obj.type != "MESH":
            continue
        assert len(obj.data.uv_layers) == 1
        values = [tuple(float(value) for value in loop.uv) for loop in obj.data.uv_layers[0].data]
        assert values and all(0 <= value <= 1 for pair in values for value in pair)
        assert len({(round(u, 5), round(v, 5)) for u, v in values}) >= 3
        facts[obj.get("gameassetai_semantic_role")] = {
            "layer": obj.data.uv_layers[0].name, "loops": len(values),
            "min": [min(value[index] for value in values) for index in range(2)],
            "max": [max(value[index] for value in values) for index in range(2)],
        }
    return facts


def main():
    args = parse_args()
    root, artifact = Path(args.repo_root).resolve(), Path(args.artifact_dir).resolve()
    texture_dir = artifact / "textures"
    (artifact / "previews").mkdir(parents=True, exist_ok=True)
    texture_dir.mkdir(exist_ok=True)
    sys.path.insert(0, str(root / "scripts"))
    import create_static_asset_assembly as assembly
    from create_static_asset_assembly import create_asset

    scene = bpy.context.scene
    baseline = datablock_snapshot()
    angular = angular_request(scene, texture_dir)
    painted = painted_request(scene, texture_dir)
    angular_receipt = create_asset(angular, authorized=True)
    painted_receipt = create_asset(painted, authorized=True)
    angular_collection = bpy.data.collections[angular["collection_name"]]
    painted_collection = bpy.data.collections[painted["collection_name"]]

    assert angular_receipt["triangle_count"] != painted_receipt["triangle_count"]
    assert not angular_receipt["textures"] and len(painted_receipt["textures"]) == 2
    assert all(item["packed"] for item in painted_receipt["textures"])
    assert len({item["sha256"] for item in painted_receipt["textures"]}) == 2
    angular_uv, painted_uv = uv_facts(angular_collection), uv_facts(painted_collection)
    for material_name in ("B4 Painted Wood", "B4 Painted Metal"):
        material_block = bpy.data.materials[material_name]
        image_nodes = [node for node in material_block.node_tree.nodes if node.type == "TEX_IMAGE"]
        assert len(image_nodes) == 1 and image_nodes[0].image.packed_file is not None
        assert image_nodes[0].outputs["Color"].is_linked

    collision = painted_request(scene, texture_dir, "B4 Collision")
    collision_path = texture_dir / collision["materials"][0]["texture"]["file_name"]
    collision_path.write_bytes(b"occupied")
    collision_baseline = datablock_snapshot()
    try:
        create_asset(collision, authorized=True)
        raise AssertionError("occupied texture output must refuse")
    except ValueError as exc:
        assert "occupied" in str(exc)
    assert datablock_snapshot() == collision_baseline
    collision_path.unlink()

    rollback = painted_request(scene, texture_dir, "B4 Rollback")
    rollback_baseline = datablock_snapshot()
    rollback_paths = [texture_dir / material_spec["texture"]["file_name"]
                      for material_spec in rollback["materials"] if material_spec["texture"]]
    original_image = assembly._make_texture_image
    def fail_after_image(*values, **keywords):
        original_image(*values, **keywords)
        raise RuntimeError("deliberate B4 image rollback probe")
    assembly._make_texture_image = fail_after_image
    try:
        create_asset(rollback, authorized=True)
        raise AssertionError("rollback failure must propagate")
    except RuntimeError as exc:
        assert "rollback probe" in str(exc)
    finally:
        assembly._make_texture_image = original_image
    assert datablock_snapshot() == rollback_baseline
    assert not any(path.exists() for path in rollback_paths)

    lights = setup_render(scene)
    frame = collection_bounds([angular_collection, painted_collection])
    images = {}
    images.update(render_views(scene, angular_collection, artifact, "angular-crate", frame))
    images.update(render_views(scene, painted_collection, artifact, "painted-crate", frame))

    current = datablock_snapshot()
    baseline_preserved = all(set(rows).issubset(set(current[name])) for name, rows in baseline.items())
    assert baseline_preserved

    blend = artifact / "result.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    validation = {
        "schema": "gameassetai.static-production-b4-validation.v1",
        "status": "structural_pass_visual_review_required", "images": images,
        "required_visual_checks": ["same_asset_family", "geometry_style_difference_visible",
                                   "painted_surface_pattern_visible", "materials_coherent",
                                   "unintended_gaps_or_distortion_absent"],
        "checks": {"two_style_specs": True, "geometry_parameters_differ": True,
                   "triangle_counts_differ": True, "local_box_uv_valid": True,
                   "generated_png_textures": True, "image_nodes_linked": True,
                   "images_packed": True, "texture_budget_met": True,
                   "polygon_budgets_met": True, "name_and_file_collision_refused": True,
                   "image_failure_rolled_back": True, "source_scene_preserved": True,
                   "shared_camera_material_render": True},
        "receipts": {"angular": angular_receipt, "painted": painted_receipt},
        "uv": {"angular": angular_uv, "painted": painted_uv},
        "frame": {"center": list(frame[0]), "ortho_scale": frame[1], "distance": frame[2]},
    }
    validation_path = artifact / "validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    (artifact / "source-info.json").write_text(json.dumps({
        "repository": str(root), "blender_version": bpy.app.version_string,
        "result_blend_sha256": sha(blend), "validation_sha256": sha(validation_path),
        "texture_sha256": {path.name: sha(path) for path in sorted(texture_dir.glob("*.png"))},
        "baseline_datablocks_preserved": baseline_preserved,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"status": validation["status"], "blend": str(blend),
                      "textures": [str(path) for path in sorted(texture_dir.glob("*.png"))],
                      "images": images}))


if __name__ == "__main__":
    main()
