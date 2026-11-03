"""Focused B4 publication safety and B5 static-production representative workflow."""
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


def primitive(kind, dimensions, segments=None):
    return {"kind": "PRIMITIVE", "primitive": kind,
            "dimensions": dimensions, "segments": segments}


def profile(points, depth):
    return {"kind": "PROFILE_EXTRUSION", "profile_points": points, "depth": depth}


def beveled(outer, core, depth):
    return {"kind": "PROFILE_BEVELED_EXTRUSION", "outer_profile_points": outer,
            "core_profile_points": core, "depth": depth}


def style(shape, budget, material_count):
    return {"family": "CUSTOM", "shape_language": shape,
            "silhouette_strategy": "EXPLICIT_PART_GEOMETRY", "shading": "FLAT",
            "material_strategy": "DECLARED_LIMITED", "max_materials": material_count,
            "triangle_budget": budget}


def material(name, role, color, metallic, roughness, texture=None):
    return {"name": name, "material_role": role, "base_color": color,
            "metallic": metallic, "roughness": roughness, "texture": texture}


def part(name, role, geometry, location, material_name, uv_rotation=0):
    return {"name": name, "semantic_role": role, "geometry": geometry,
            "location": location, "rotation_degrees": [0, 0, 0],
            "material": material_name,
            "uv_mapping": {"rotation_degrees": uv_rotation,
                           "mirror_u": False, "mirror_v": False}}


def texture(kind, image_name, file_name, palette, scale, seed, resolution=128):
    return {"kind": kind, "image_name": image_name, "file_name": file_name,
            "resolution": resolution, "palette": palette, "scale": scale, "seed": seed}


def policy():
    return {"existing_names": "REFUSE", "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS_IMAGES",
            "external_files": "NO_OVERWRITE_OWNED_PNG",
            "failure": "ROLL_BACK_OWNED_DATA_AND_FILES"}


def appearance(texture_dir):
    return {"uv_policy": "LOCAL_BOX_PROJECT", "texture_policy": "OPTIONAL_GENERATED_PNG",
            "texture_output_directory": str(texture_dir), "max_texture_resolution": 128,
            "max_texture_bytes": 524288, "pack_images": True}


def art(surface, silhouette, proportion, detail, palette, source_ref, unsupported=()):
    return {"provenance": {"source": "USER_REQUEST", "source_ref": source_ref,
                           "profile_sha256": None},
            "surface_style": surface, "silhouette": silhouette,
            "proportion": proportion, "geometry_detail": detail,
            "palette": palette, "unsupported": list(unsupported)}


def request(scene, texture_dir, *, asset, collection, shape, budget, materials, parts,
            surface, silhouette, proportion, detail, palette, unsupported=()):
    return {"schema": "gameassetai.static-asset-assembly-request.v5",
            "scene_name": scene.name, "asset_name": asset, "collection_name": collection,
            "style": style(shape, budget, len(materials)),
            "art_direction": art(surface, silhouette, proportion, detail, palette,
                                 f"B5 representative brief: {asset}", unsupported),
            "appearance": appearance(texture_dir), "materials": materials,
            "parts": parts, "policy": policy()}


def revision(scene, source, asset, collection, revisions):
    return {"schema": "gameassetai.static-asset-revision-request.v4",
            "scene_name": scene.name, "source_collection_name": source,
            "asset_name": asset, "collection_name": collection,
            "revisions": revisions,
            "policy": {"existing_names": "REFUSE", "source": "PRESERVE",
                       "revision": "NEW_COLLECTION_OBJECTS_MESHES_REGENERATED_UV_SHARED_MATERIALS_IMAGES",
                       "failure": "ROLL_BACK_OWNED_DATA"}}


def shield_request(scene, texture_dir):
    outer = [[-1.36, -.88], [-.95, -1.25], [0, -1.58], [.95, -1.25],
             [1.36, -.88], [1.48, .28], [1.05, 1.18], [0, 1.52],
             [-1.05, 1.18], [-1.48, .28]]
    core = [[x * .84, z * .84] for x, z in outer]
    rim_outer = [[x * 1.06, z * 1.06] for x, z in outer]
    rim_core = [[x * .91, z * .91] for x, z in outer]
    wood_palette = [[.12, .025, .006, 1], [.42, .12, .018, 1], [.78, .37, .07, 1]]
    metal_palette = [[.03, .07, .1, 1], [.16, .34, .42, 1], [.58, .73, .7, 1]]
    wood = texture("WOOD_GRAIN", "B5 Shield Wood Image", "shield-wood.png",
                   wood_palette, 6, 17)
    metal = texture("PAINTED_METAL", "B5 Shield Metal Image", "shield-metal.png",
                    metal_palette, 5, 29)
    materials = [
        material("B5 Shield Wood", "wood", wood_palette[1], 0, .82, wood),
        material("B5 Shield Metal", "metal", metal_palette[1], .52, .42, metal),
    ]
    parts = [
        part("B5 Shield Core", "shield_core", beveled(outer, core, .34), [0, 0, 0],
             "B5 Shield Wood", 90),
        part("B5 Shield Rim", "metal_rim", beveled(rim_outer, rim_core, .16), [0, .12, 0],
             "B5 Shield Metal", 90),
        part("B5 Shield Boss", "central_boss", primitive("CYLINDER", [.7, .7, .34], 12),
             [0, -.38, 0], "B5 Shield Metal"),
        part("B5 Shield Vertical Brace", "vertical_brace", primitive("BOX", [.18, .16, 2.25]),
             [0, .24, 0], "B5 Shield Metal"),
    ]
    palette = wood_palette + metal_palette
    return request(scene, texture_dir, asset="B5 Fantasy Shield", collection="GAA B5 Shield",
                   shape="BROAD_HERALDIC_TAPER", budget=260, materials=materials, parts=parts,
                   surface="PAINTED_LOOK_STYLIZED", silhouette="broad heraldic shield with tapered lower point",
                   proportion="wide guarded rim and compact central boss",
                   detail="beveled wooden core, metal edge, boss and rear brace", palette=palette,
                   unsupported=("painted heraldic illustration", "normal maps"))


def shield_revision(scene):
    source = shield_request(scene, Path("."))
    core = copy.deepcopy(source["parts"][0]["geometry"])
    rim = copy.deepcopy(source["parts"][1]["geometry"])
    for geometry in (core, rim):
        geometry["outer_profile_points"] = [[x * 1.16, z] for x, z in geometry["outer_profile_points"]]
        geometry["core_profile_points"] = [[x * 1.14, z] for x, z in geometry["core_profile_points"]]
    rim["depth"] = .24
    return revision(scene, "GAA B5 Shield", "B5 Wide Shield", "GAA B5 Shield Revised", [
        {"semantic_role": "shield_core", "geometry": core, "location": None,
         "rotation_degrees": None},
        {"semantic_role": "metal_rim", "geometry": rim, "location": [0, .14, 0],
         "rotation_degrees": None},
    ])


def lantern_request(scene, texture_dir):
    metal = [.08, .12, .15, 1]
    wood = [.3, .085, .018, 1]
    glow = [1.0, .38, .035, 1]
    materials = [material("B5 Lantern Metal", "metal", metal, .62, .38),
                 material("B5 Lantern Wood", "wood", wood, 0, .82),
                 material("B5 Lantern Glow", "glow_core", glow, 0, .28)]
    roof = [[-1.0, -.2], [1.0, -.2], [.68, .32], [0, .68], [-.68, .32]]
    parts = [
        part("B5 Lantern Base", "base", primitive("CYLINDER", [1.55, 1.55, .28], 8),
             [0, 0, -.92], "B5 Lantern Metal"),
        part("B5 Lantern Glow", "glow_chamber", primitive("CYLINDER", [.78, .78, 1.45], 8),
             [0, 0, -.06], "B5 Lantern Glow"),
        part("B5 Lantern Left Frame", "left_frame", primitive("BOX", [.18, .18, 1.78]),
             [-.58, 0, -.05], "B5 Lantern Metal"),
        part("B5 Lantern Right Frame", "right_frame", primitive("BOX", [.18, .18, 1.78]),
             [.58, 0, -.05], "B5 Lantern Metal"),
        part("B5 Lantern Front Frame", "front_frame", primitive("BOX", [.18, .18, 1.78]),
             [0, -.58, -.05], "B5 Lantern Metal"),
        part("B5 Lantern Rear Frame", "rear_frame", primitive("BOX", [.18, .18, 1.78]),
             [0, .58, -.05], "B5 Lantern Metal"),
        part("B5 Lantern Roof", "roof", profile(roof, 1.5), [0, 0, .92], "B5 Lantern Wood", 90),
        part("B5 Lantern Cap", "top_frame", primitive("CYLINDER", [.56, .56, .22], 8),
             [0, 0, 1.34], "B5 Lantern Metal"),
    ]
    return request(scene, texture_dir, asset="B5 Fantasy Lantern", collection="GAA B5 Lantern",
                   shape="TALL_CAGED_GLOW", budget=260, materials=materials, parts=parts,
                   surface="ANGULAR_LOW_POLY", silhouette="tall caged lantern with pitched roof",
                   proportion="slender glowing chamber, broad foot and roof",
                   detail="four frame posts connect base to roof around a separate glow core",
                   palette=[metal, wood, glow])


def lantern_revision(scene):
    tall = primitive("CYLINDER", [.78, .78, 1.78], 8)
    post = primitive("BOX", [.18, .18, 2.12])
    revisions = [{"semantic_role": "glow_chamber", "geometry": tall,
                  "location": [0, 0, .08], "rotation_degrees": None}]
    for role, x, y in (("left_frame", -.58, 0), ("right_frame", .58, 0),
                       ("front_frame", 0, -.58), ("rear_frame", 0, .58)):
        revisions.append({"semantic_role": role, "geometry": copy.deepcopy(post),
                          "location": [x, y, .08], "rotation_degrees": None})
    revisions.extend([
        {"semantic_role": "roof", "geometry": None, "location": [0, 0, 1.18],
         "rotation_degrees": None},
        {"semantic_role": "top_frame", "geometry": None, "location": [0, 0, 1.6],
         "rotation_degrees": None},
    ])
    return revision(scene, "GAA B5 Lantern", "B5 Tall Lantern", "GAA B5 Lantern Revised", revisions)


def doorway_request(scene, texture_dir):
    stone = [.26, .29, .34, 1]
    trim = [.1, .13, .17, 1]
    rune = [.08, .38, .48, 1]
    materials = [material("B5 Doorway Stone", "stone", stone, 0, .92),
                 material("B5 Doorway Metal", "metal", trim, .55, .42),
                 material("B5 Doorway Rune", "rune", rune, .18, .35)]
    pillar_outer = [[-.42, -1.45], [.42, -1.45], [.52, -1.25], [.52, 1.25],
                    [.38, 1.48], [-.38, 1.48], [-.52, 1.25], [-.52, -1.25]]
    pillar_core = [[x * .76, z * .91] for x, z in pillar_outer]
    header_outer = [[-2.05, -.38], [2.05, -.38], [2.22, 0], [1.62, .72],
                    [.68, .98], [0, 1.18], [-.68, .98], [-1.62, .72], [-2.22, 0]]
    header_core = [[x * .86, z * .75] for x, z in header_outer]
    parts = [
        part("B5 Doorway Left Pillar", "left_pillar", beveled(pillar_outer, pillar_core, .78),
             [-1.45, 0, 1.45], "B5 Doorway Stone", 90),
        part("B5 Doorway Right Pillar", "right_pillar", beveled(pillar_outer, pillar_core, .78),
             [1.45, 0, 1.45], "B5 Doorway Stone", 90),
        part("B5 Doorway Header", "header", beveled(header_outer, header_core, .82),
             [0, 0, 3.18], "B5 Doorway Stone", 90),
        part("B5 Doorway Left Foot", "left_foot", primitive("BOX", [1.15, 1.0, .32]),
             [-1.45, 0, .16], "B5 Doorway Metal"),
        part("B5 Doorway Right Foot", "right_foot", primitive("BOX", [1.15, 1.0, .32]),
             [1.45, 0, .16], "B5 Doorway Metal"),
        part("B5 Doorway Rune", "keystone_rune", primitive("ICOSPHERE", [.46, .26, .46], 3),
             [0, -.52, 3.55], "B5 Doorway Rune"),
    ]
    return request(scene, texture_dir, asset="B5 Modular Stone Doorway", collection="GAA B5 Doorway",
                   shape="MODULAR_MONUMENTAL_ARCH", budget=360, materials=materials, parts=parts,
                   surface="ANGULAR_LOW_POLY", silhouette="two pillars and high header enclosing an open passage",
                   proportion="modular three metre passage with broad cap",
                   detail="beveled stone members, metal feet and centered rune",
                   palette=[stone, trim, rune])


def doorway_revision(scene):
    source = doorway_request(scene, Path("."))
    pillar = copy.deepcopy(source["parts"][0]["geometry"])
    pillar["outer_profile_points"] = [[x, z * 1.16] for x, z in pillar["outer_profile_points"]]
    pillar["core_profile_points"] = [[x, z * 1.16] for x, z in pillar["core_profile_points"]]
    header = copy.deepcopy(source["parts"][2]["geometry"])
    header["outer_profile_points"] = [[x * 1.16, z] for x, z in header["outer_profile_points"]]
    header["core_profile_points"] = [[x * 1.14, z] for x, z in header["core_profile_points"]]
    return revision(scene, "GAA B5 Doorway", "B5 Wide Tall Doorway", "GAA B5 Doorway Revised", [
        {"semantic_role": "left_pillar", "geometry": copy.deepcopy(pillar), "location": [-1.72, 0, 1.68],
         "rotation_degrees": None},
        {"semantic_role": "right_pillar", "geometry": copy.deepcopy(pillar), "location": [1.72, 0, 1.68],
         "rotation_degrees": None},
        {"semantic_role": "header", "geometry": header, "location": [0, 0, 3.64],
         "rotation_degrees": None},
        {"semantic_role": "left_foot", "geometry": None, "location": [-1.72, 0, .16],
         "rotation_degrees": None},
        {"semantic_role": "right_foot", "geometry": None, "location": [1.72, 0, .16],
         "rotation_degrees": None},
        {"semantic_role": "keystone_rune", "geometry": None, "location": [0, -.52, 4.02],
         "rotation_degrees": None},
    ])


def snapshot():
    return {name: tuple((block.name, block.as_pointer()) for block in getattr(bpy.data, name))
            for name in ("objects", "meshes", "materials", "images", "collections")}


def file_set(directory):
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in directory.iterdir() if path.is_file()}


def failure_request(scene, texture_dir, prefix, texture_count=1):
    palettes = [[[.1, .02, .01, 1], [.55, .16, .03, 1], [.85, .42, .08, 1]],
                [[.03, .08, .1, 1], [.12, .32, .4, 1], [.5, .72, .7, 1]]]
    materials = []
    for index in range(texture_count):
        spec = texture("WOOD_GRAIN" if index == 0 else "PAINTED_METAL",
                       f"{prefix} Image {index}", f"{prefix.lower()}-{index}.png",
                       palettes[index], 5, index + 3, 32)
        materials.append(material(f"{prefix} Material {index}", f"role_{index}",
                                  palettes[index][1], index * .4, .7, spec))
    palette = [color for colors in palettes[:texture_count] for color in colors]
    return request(scene, texture_dir, asset=prefix, collection=f"GAA {prefix}", shape="TEST_ONLY",
                   budget=30, materials=materials,
                   parts=[part(f"{prefix} Body", "body", primitive("BOX", [1, 1, 1]),
                               [0, 0, 0], materials[0]["name"])],
                   surface="CUSTOM", silhouette="box fixture",
                   proportion="unit fixture", detail="publication plumbing only", palette=palette)


def expect_failure(assembly, create_asset, payload, texture_dir, hook, replacement, message):
    before_data, before_files = snapshot(), file_set(texture_dir)
    original = getattr(assembly, hook)
    setattr(assembly, hook, replacement(original))
    try:
        try:
            create_asset(payload, authorized=True)
            raise AssertionError(f"failure probe did not fail: {message}")
        except (RuntimeError, ValueError) as exc:
            assert message in str(exc), (message, str(exc))
    finally:
        setattr(assembly, hook, original)
    assert snapshot() == before_data
    assert file_set(texture_dir) == before_files


def test_publication_failures(assembly, create_asset, scene, texture_dir):
    def raises(message):
        def factory(_original):
            def fail(*_args, **_kwargs):
                raise RuntimeError(message)
            return fail
        return factory

    before = failure_request(scene, texture_dir, "B5 Before Save")
    expect_failure(assembly, create_asset, before, texture_dir, "_save_texture_image",
                   raises("before-save-probe"), "before-save-probe")

    partial = failure_request(scene, texture_dir, "B5 Partial Save")
    def partial_factory(_original):
        def fail(image):
            Path(image.filepath_raw).write_bytes(b"partial-png")
            raise RuntimeError("partial-save-probe")
        return fail
    expect_failure(assembly, create_asset, partial, texture_dir, "_save_texture_image",
                   partial_factory, "partial-save-probe")

    pack = failure_request(scene, texture_dir, "B5 Pack Failure")
    expect_failure(assembly, create_asset, pack, texture_dir, "_pack_texture_image",
                   raises("pack-failure-probe"), "pack-failure-probe")

    second = failure_request(scene, texture_dir, "B5 Second Failure", 2)
    def second_factory(original):
        calls = {"count": 0}
        def fail(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("second-texture-probe")
            return original(*args, **kwargs)
        return fail
    expect_failure(assembly, create_asset, second, texture_dir, "_make_texture_image",
                   second_factory, "second-texture-probe")

    collision = failure_request(scene, texture_dir, "B5 Publish Collision")
    user_path = texture_dir / collision["materials"][0]["texture"]["file_name"]
    before_data, before_files = snapshot(), file_set(texture_dir)
    original_publish = assembly._publish_staged_file
    def collide(staged, output):
        output.write_bytes(b"user-owned-race-winner")
        return original_publish(staged, output)
    assembly._publish_staged_file = collide
    try:
        try:
            create_asset(collision, authorized=True)
            raise AssertionError("collision probe did not fail")
        except ValueError as exc:
            assert "became occupied" in str(exc)
    finally:
        assembly._publish_staged_file = original_publish
    assert snapshot() == before_data
    assert user_path.read_bytes() == b"user-owned-race-winner"
    user_path.unlink()
    assert file_set(texture_dir) == before_files

    geometry = failure_request(scene, texture_dir, "B5 Geometry Failure")
    expect_failure(assembly, create_asset, geometry, texture_dir, "_make_mesh",
                   raises("geometry-after-material-probe"), "geometry-after-material-probe")
    return {"before_save": True, "partial_save": True, "pack_failure": True,
            "second_texture": True, "publication_collision_preserved_user_file": True,
            "geometry_after_material": True}


def mesh_signature(obj):
    return {"vertices": [tuple(round(float(value), 6) for value in vertex.co)
                         for vertex in obj.data.vertices],
            "materials": [material.as_pointer() for material in obj.data.materials],
            "uv": [[round(float(value), 6) for value in loop.uv]
                   for loop in obj.data.uv_layers[0].data]}


def collection_by_role(collection):
    return {obj.get("gameassetai_semantic_role"): obj for obj in collection.objects}


def verify_pair(source, revised, changed_roles):
    source_roles, revised_roles = collection_by_role(source), collection_by_role(revised)
    assert set(source_roles) == set(revised_roles)
    for role in source_roles:
        left, right = source_roles[role], revised_roles[role]
        assert left.as_pointer() != right.as_pointer() and left.data.as_pointer() != right.data.as_pointer()
        assert [item.as_pointer() for item in left.data.materials] == [item.as_pointer() for item in right.data.materials]
        assert len(right.data.uv_layers) == 1
        if role in changed_roles:
            assert (mesh_signature(left)["vertices"] != mesh_signature(right)["vertices"]
                    or tuple(left.location) != tuple(right.location))
        else:
            assert mesh_signature(left) == mesh_signature(right)
            assert tuple(left.location) == tuple(right.location)


def bounds(collections):
    objects = [obj for collection in collections for obj in collection.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    center, size = (low + high) * .5, high - low
    return center, max(size) * 1.45, max(size) * 4.0 + 2


def setup_render(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.018, .022, .03)
    for name, location, energy, size, color in (
        ("B5 Key", (-5, -6, 7), 1050, 5, (1.0, .78, .58)),
        ("B5 Fill", (5, -2, 4), 700, 4, (.42, .65, 1.0)),
        ("B5 Rim", (1, 5, 6), 850, 3, (.75, .9, 1.0)),
    ):
        data = bpy.data.lights.new(name + " Data", "AREA")
        data.energy, data.size, data.color = energy, size, color
        obj = bpy.data.objects.new(name, data)
        obj.location = location
        obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(obj)


def render_pair(scene, source, revised, artifact, family):
    frame = bounds([source, revised])
    images = {}
    for collection, variant in ((source, "original"), (revised, "revised")):
        visible = set(collection.objects)
        prior = {obj: obj.hide_render for obj in scene.objects if obj.type == "MESH"}
        for obj in prior:
            obj.hide_render = obj not in visible
        camera_data = bpy.data.cameras.new(f"B5 {family} Camera Data")
        camera = bpy.data.objects.new(f"B5 {family} Camera", camera_data)
        scene.collection.objects.link(camera)
        scene.camera, camera_data.type, camera_data.ortho_scale = camera, "ORTHO", frame[1]
        for view, offset in {"front": (0, -1, .08), "side": (1, 0, .08),
                             "three-quarter": (.72, -.72, .34)}.items():
            direction = Vector(offset).normalized() * frame[2]
            camera.location = frame[0] + direction
            camera.rotation_euler = (frame[0] - camera.location).to_track_quat("-Z", "Y").to_euler()
            output = artifact / "previews" / f"{family}-{variant}-{view}.png"
            scene.render.filepath = str(output)
            bpy.ops.render.render(write_still=True)
            images[f"{family}_{variant}_{view}"] = str(output.resolve())
        bpy.data.objects.remove(camera, do_unlink=True)
        bpy.data.cameras.remove(camera_data)
        for obj, hidden in prior.items():
            obj.hide_render = hidden
    return images


def uv_facts(collection):
    result = {}
    for role, obj in collection_by_role(collection).items():
        assert len(obj.data.uv_layers) == 1
        values = [tuple(float(value) for value in loop.uv) for loop in obj.data.uv_layers[0].data]
        assert values and all(-1e-6 <= value <= 1.000001 for pair in values for value in pair)
        assert len({(round(u, 5), round(v, 5)) for u, v in values}) >= 3
        result[role] = {"loops": len(values), "mapping": json.loads(
            obj.data["gameassetai_uv_mapping_spec"])}
    return result


def main():
    args = parse_args()
    root, artifact = Path(args.repo_root).resolve(), Path(args.artifact_dir).resolve()
    texture_dir = artifact / "textures"
    (artifact / "previews").mkdir(parents=True, exist_ok=True)
    texture_dir.mkdir(exist_ok=True)
    sys.path.insert(0, str(root / "scripts"))
    import create_static_asset_assembly as assembly
    from validate_static_asset_assembly_request import validate_request, validate_revision_request
    create_asset, revise_asset_copy = assembly.create_asset, assembly.revise_asset_copy
    scene = bpy.context.scene
    baseline = snapshot()
    failure_checks = test_publication_failures(assembly, create_asset, scene, texture_dir)

    requests = {"shield": shield_request(scene, texture_dir),
                "lantern": lantern_request(scene, texture_dir),
                "doorway": doorway_request(scene, texture_dir)}
    revisions = {"shield": shield_revision(scene), "lantern": lantern_revision(scene),
                 "doorway": doorway_revision(scene)}
    # Validate the complete representative batch before creating any persistent data or files.
    for payload in requests.values():
        validate_request(copy.deepcopy(payload))
    for payload in revisions.values():
        validate_revision_request(copy.deepcopy(payload))
    receipts, revision_receipts, pairs = {}, {}, {}
    changed = {"shield": {"shield_core", "metal_rim"},
               "lantern": {"glow_chamber", "left_frame", "right_frame", "front_frame",
                           "rear_frame", "roof", "top_frame"},
               "doorway": {"left_pillar", "right_pillar", "header", "left_foot",
                           "right_foot", "keystone_rune"}}
    for family in ("shield", "lantern", "doorway"):
        receipts[family] = create_asset(requests[family], authorized=True)
        revision_receipts[family] = revise_asset_copy(revisions[family], authorized=True)
        source = bpy.data.collections[requests[family]["collection_name"]]
        revised = bpy.data.collections[revisions[family]["collection_name"]]
        verify_pair(source, revised, changed[family])
        assert receipts[family]["art_direction_application"]["palette_exact_match"]
        assert revision_receipts[family]["replaced_geometry_uv_regenerated"]
        pairs[family] = (source, revised)

    assert len(receipts["shield"]["textures"]) == 2
    assert all(item["packed"] for item in receipts["shield"]["textures"])
    for family, receipt in receipts.items():
        assert receipt["triangle_count"] <= receipt["style"]["triangle_budget"]
        assert revision_receipts[family]["triangle_count"] <= receipt["style"]["triangle_budget"]

    setup_render(scene)
    images = {}
    for family, pair in pairs.items():
        images.update(render_pair(scene, *pair, artifact, family))
    blend = artifact / "result.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    current = snapshot()
    baseline_preserved = all(set(rows).issubset(set(current[name])) for name, rows in baseline.items())
    assert baseline_preserved
    validation = {
        "schema": "gameassetai.static-production-b5-validation.v1",
        "status": "structural_pass_visual_review_required", "images": images,
        "required_visual_checks": ["asset_types_recognizable", "game_silhouettes_coherent",
                                   "parts_visibly_connected", "revisions_match_requests",
                                   "texture_and_materials_coherent", "geometry_defects_absent"],
        "checks": {"publication_failure_matrix": failure_checks,
                   "three_domains_created_and_revised": True,
                   "v5_revision_independent_meshes": True,
                   "unrelated_parts_preserved": True,
                   "shared_materials_and_images": True,
                   "replacement_uv_regenerated": True,
                   "uv_mapping_valid": True, "polygon_budgets_met": True,
                   "art_direction_applied_facts_recorded": True,
                   "palette_consistency": True, "source_scene_preserved": baseline_preserved,
                   "same_family_camera_frames": True},
        "receipts": receipts, "revision_receipts": revision_receipts,
        "uv": {family: {"original": uv_facts(pair[0]), "revised": uv_facts(pair[1])}
               for family, pair in pairs.items()},
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
                      "images": len(images), "textures": len(list(texture_dir.glob("*.png"))) }))


if __name__ == "__main__":
    main()
