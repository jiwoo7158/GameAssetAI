import argparse
import hashlib
import json
import math
import sys
import uuid
from pathlib import Path

import bpy
from mathutils import Vector


OWNER = "gameassetai_character_style_prototype_owner"
ROLE = "gameassetai_character_component_role"
STYLE = "gameassetai_character_style_candidate"


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def tag(block, token, style, role=None):
    block[OWNER] = token
    block[STYLE] = style
    if role:
        block[ROLE] = role
    return block


def material(name, color, token, style, roughness=0.65, metallic=0.0):
    item = tag(bpy.data.materials.new(name), token, style)
    item.diffuse_color = color
    item.use_nodes = True
    node = next(node for node in item.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value = color
    node.inputs["Roughness"].default_value = roughness
    node.inputs["Metallic"].default_value = metallic
    return item


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def finish_object(obj, name, collection, material_value, token, style, role, smooth=False):
    obj.name = name
    obj.data.name = name + " Mesh"
    tag(obj, token, style, role)
    tag(obj.data, token, style, role)
    move_to_collection(obj, collection)
    obj.data.materials.append(material_value)
    for polygon in obj.data.polygons:
        polygon.use_smooth = smooth
    return obj


def add_cube(name, location, size, collection, mat, token, style, role, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.scale = Vector(size) * 0.5
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("Prototype Chamfer", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    return finish_object(obj, name, collection, mat, token, style, role)


def add_sphere(name, location, size, collection, mat, token, style, role, angular=False, smooth=False):
    if angular:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=location)
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, location=location)
    obj = bpy.context.object
    obj.scale = Vector(size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish_object(obj, name, collection, mat, token, style, role, smooth=smooth)


def add_frustum(name, location, depth, lower, upper, collection, mat, token, style, role, vertices=8):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=lower, radius2=upper, depth=depth, location=location)
    return finish_object(bpy.context.object, name, collection, mat, token, style, role)


def add_limb(name, start, end, radius_a, radius_b, collection, mat, token, style, role, vertices=8):
    start, end = Vector(start), Vector(end)
    delta = end - start
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius_a, radius2=radius_b,
                                   depth=delta.length, location=(start + end) * 0.5)
    obj = bpy.context.object
    obj.rotation_euler = Vector((0, 0, 1)).rotation_difference(delta.normalized()).to_euler()
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    return finish_object(obj, name, collection, mat, token, style, role)


def add_profile(name, profile, depth, location, collection, mat, token, style, role):
    count = len(profile)
    verts = [(x, -depth * 0.5, z) for x, z in profile] + [(x, depth * 0.5, z) for x, z in profile]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, count + index, count + following, following))
    mesh = tag(bpy.data.meshes.new(name + " Mesh"), token, style, role)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    collection.objects.link(obj)
    tag(obj, token, style, role)
    mesh.materials.append(mat)
    return obj


def rollback(token):
    for obj in list(bpy.data.objects):
        if obj.get(OWNER) == token:
            bpy.data.objects.remove(obj, do_unlink=True)
    for database in (bpy.data.meshes, bpy.data.materials):
        for block in list(database):
            if block.get(OWNER) == token and block.users == 0:
                database.remove(block)
    for collection in list(bpy.data.collections):
        if collection.get(OWNER) == token:
            bpy.data.collections.remove(collection)


def build_candidate(spec, fail_after=None):
    token = uuid.uuid4().hex
    style = spec["id"]
    if bpy.data.collections.get(spec["collection"]):
        raise ValueError("prototype collection name is occupied")
    try:
        collection = tag(bpy.data.collections.new(spec["collection"]), token, style)
        bpy.context.scene.collection.children.link(collection)
        mats = {
            key: material(f"{style} {key.title()}", value[0], token, style, *value[1:])
            for key, value in spec["materials"].items()
        }
        p = spec["proportions"]
        objects = []
        angular = style == "ANGULAR_LOW_POLY"
        # Actual body geometry, not a recolored template.
        objects.append(add_frustum(f"{style} Torso", (0, 0, p["torso_z"]), p["torso_h"],
                                   p["waist"], p["shoulders"], collection, mats["cloth"], token,
                                   style, "body_torso", 6 if angular else 10))
        objects.append(add_sphere(f"{style} Head", (0, 0, p["head_z"]), p["head"], collection,
                                  mats["skin"], token, style, "head_face", angular=angular,
                                  smooth=style == "STYLIZED_TOON"))
        for side, sign in (("L", 1), ("R", -1)):
            sx = p["shoulders"] * 0.82 * sign
            hx = p["hip_x"] * sign
            objects.append(add_limb(f"{style} UpperArm.{side}", (sx, 0, p["shoulder_z"]),
                                    (sign * p["elbow_x"], 0, p["elbow_z"]), p["arm_r"] * 1.08,
                                    p["arm_r"], collection, mats["skin"], token, style, "arm", 6 if angular else 10))
            objects.append(add_limb(f"{style} Forearm.{side}", (sign * p["elbow_x"], 0, p["elbow_z"]),
                                    (sign * p["wrist_x"], 0, p["wrist_z"]), p["arm_r"],
                                    p["arm_r"] * 0.82, collection, mats["skin"], token, style, "arm", 6 if angular else 10))
            objects.append(add_sphere(f"{style} Hand.{side}", (sign * p["hand_x"], -0.005, p["hand_z"]),
                                      p["hand"], collection, mats["skin"], token, style, "hand", angular=angular))
            objects.append(add_limb(f"{style} Thigh.{side}", (hx, 0, p["hip_z"]),
                                    (sign * p["knee_x"], 0, p["knee_z"]), p["leg_r"] * 1.1,
                                    p["leg_r"], collection, mats["pants"], token, style, "leg", 6 if angular else 10))
            objects.append(add_limb(f"{style} Shin.{side}", (sign * p["knee_x"], 0, p["knee_z"]),
                                    (sign * p["ankle_x"], 0, p["ankle_z"]), p["leg_r"],
                                    p["leg_r"] * 0.78, collection, mats["pants"], token, style, "leg", 6 if angular else 10))
            objects.append(add_cube(f"{style} Boot.{side}", (sign * p["ankle_x"], -p["foot"][1] * 0.22, p["foot_z"]),
                                    p["foot"], collection, mats["boot"], token, style, "foot", bevel=0.025))

        # Clothing is independent geometry with a readable silhouette.
        objects.append(add_frustum(f"{style} Tunic", (0, -0.012, p["tunic_z"]), p["tunic_h"],
                                   p["tunic_lower"], p["tunic_upper"], collection, mats["outfit"], token,
                                   style, "clothing_tunic", 6 if angular else 10))
        objects.append(add_cube(f"{style} Belt", (0, -0.01, p["belt_z"]),
                                (p["tunic_lower"] * 2.12, p["body_depth"] * 1.08, 0.065), collection,
                                mats["accent"], token, style, "clothing_belt", bevel=0.012))

        # Face elements sit on canonical -Y front and are distinct Meshes.
        for side, sign in (("L", 1), ("R", -1)):
            eye_x = p["eye_x"] * sign
            objects.append(add_sphere(f"{style} EyeWhite.{side}", (eye_x, p["face_y"], p["eye_z"]),
                                      p["eye"], collection, mats["eye"], token, style, "face_eye", angular=angular))
            objects.append(add_sphere(f"{style} Pupil.{side}", (eye_x, p["face_y"] - 0.024, p["eye_z"]),
                                      tuple(value * 0.48 for value in p["eye"]), collection, mats["pupil"],
                                      token, style, "face_pupil", angular=angular))
        objects.append(add_profile(f"{style} Nose", [(-0.025, -0.03), (0.025, -0.03), (0.0, 0.055)],
                                   0.045, (0, p["face_y"] - 0.01, p["nose_z"]), collection, mats["skin"],
                                   token, style, "face_nose"))
        objects.append(add_cube(f"{style} Mouth", (0, p["face_y"] - 0.026, p["mouth_z"]),
                                (p["mouth_w"], 0.018, 0.018), collection, mats["pupil"], token,
                                style, "face_mouth", bevel=0.006))

        # Hair uses real separate masses; layouts differ per style.
        for index, hair in enumerate(spec["hair"]):
            kind, location, size = hair[:3]
            if kind == "sphere":
                objects.append(add_sphere(f"{style} Hair {index:02d}", location, size, collection,
                                          mats["hair"], token, style, "hair", angular=angular))
            elif kind == "cube":
                objects.append(add_cube(f"{style} Hair {index:02d}", location, size, collection,
                                        mats["hair"], token, style, "hair", bevel=0.025))
            else:
                objects.append(add_profile(f"{style} Hair {index:02d}", size, hair[3], location,
                                           collection, mats["hair"], token, style, "hair"))

        for index, accessory in enumerate(spec.get("accessories", [])):
            profile, depth, location, role = accessory
            objects.append(add_profile(f"{style} Accessory {index:02d}", profile, depth, location,
                                       collection, mats["accent"], token, style, role))
        if fail_after is not None and len(objects) >= fail_after:
            raise RuntimeError("injected prototype failure")
        collection["gameassetai_art_direction"] = json.dumps(spec["art_direction"], sort_keys=True)
        return collection, objects, token
    except Exception:
        rollback(token)
        raise


def candidate_specs():
    shared_materials = {
        "eye": ([0.94, 0.96, 0.92, 1], 0.35, 0.0), "pupil": ([0.025, 0.035, 0.05, 1], 0.4, 0.0),
        "boot": ([0.08, 0.055, 0.04, 1], 0.76, 0.0),
    }
    def base(**overrides):
        value = {"torso_z": 1.06, "torso_h": 0.60, "waist": 0.25, "shoulders": 0.34,
                 "head_z": 1.62, "head": (0.34, 0.29, 0.37), "hip_x": 0.12, "hip_z": 0.76,
                 "shoulder_z": 1.30, "elbow_x": 0.46, "elbow_z": 1.12, "wrist_x": 0.56,
                 "wrist_z": 0.94, "hand_x": 0.585, "hand_z": 0.90, "hand": (0.075, 0.06, 0.105),
                 "arm_r": 0.065, "knee_x": 0.13, "knee_z": 0.43, "ankle_x": 0.13,
                 "ankle_z": 0.11, "leg_r": 0.095, "foot": (0.18, 0.31, 0.12), "foot_z": 0.06,
                 "tunic_z": 1.06, "tunic_h": 0.64, "tunic_lower": 0.27, "tunic_upper": 0.35,
                 "belt_z": 0.78, "body_depth": 0.23, "eye_x": 0.105, "face_y": -0.285,
                 "eye_z": 1.68, "eye": (0.075, 0.035, 0.075), "nose_z": 1.58,
                 "mouth_z": 1.50, "mouth_w": 0.10}
        value.update(overrides)
        return value
    return [
        {"id": "ANGULAR_LOW_POLY", "collection": "Candidate A Angular Low-Poly",
         "art_direction": {"label": "Angular Low-Poly Game Character", "shape": "faceted broad-shouldered readable planes",
                           "surface": "flat limited palette", "rig_forecast": "new connected deformation topology required"},
         "materials": {**shared_materials, "skin": ([0.68, 0.42, 0.27, 1], 0.72, 0.0),
                       "cloth": ([0.12, 0.22, 0.30, 1], 0.78, 0.0), "pants": ([0.14, 0.11, 0.10, 1], 0.8, 0.0),
                       "outfit": ([0.18, 0.38, 0.42, 1], 0.74, 0.0), "accent": ([0.72, 0.42, 0.10, 1], 0.5, 0.25),
                       "hair": ([0.12, 0.07, 0.035, 1], 0.82, 0.0)},
         "proportions": base(head=(0.32, 0.27, 0.34), shoulders=0.38, waist=0.24, arm_r=0.072,
                             eye=(0.065, 0.028, 0.045), mouth_w=0.13, tunic_upper=0.39),
         "hair": [("cube", (-0.18, 0.015, 1.88), (0.22, 0.30, 0.18)),
                  ("cube", (0.0, 0.025, 1.94), (0.24, 0.31, 0.20)),
                  ("cube", (0.18, 0.015, 1.88), (0.22, 0.30, 0.18)),
                  ("profile", (0, 0.13, 1.74), [(-0.32, 0.22), (-0.24, -0.20), (0.25, -0.26), (0.33, 0.18)], 0.15)],
         "accessories": [([(-0.38, -0.05), (-0.25, -0.13), (0.0, 0.07), (0.25, -0.13), (0.38, -0.05), (0.30, 0.07), (0, 0.16), (-0.30, 0.07)], 0.16, (0, 0.08, 1.30), "clothing_collar")]},
        {"id": "STYLIZED_TOON", "collection": "Candidate B Stylized Toon",
         "art_direction": {"label": "Stylized Toon Game Character", "shape": "rounded expressive balanced proportions",
                           "surface": "soft toon palette", "rig_forecast": "connected body retopology and separate garment weights required"},
         "materials": {**shared_materials, "skin": ([0.84, 0.59, 0.42, 1], 0.62, 0.0),
                       "cloth": ([0.16, 0.20, 0.34, 1], 0.68, 0.0), "pants": ([0.10, 0.16, 0.27, 1], 0.74, 0.0),
                       "outfit": ([0.63, 0.15, 0.20, 1], 0.58, 0.0), "accent": ([0.96, 0.68, 0.18, 1], 0.42, 0.05),
                       "hair": ([0.12, 0.05, 0.17, 1], 0.7, 0.0)},
         "proportions": base(head=(0.37, 0.31, 0.40), head_z=1.62, shoulders=0.32, waist=0.23,
                             elbow_x=0.43, wrist_x=0.53, hand_x=0.56, hand=(0.072, 0.058, 0.10),
                             eye_x=0.12, eye=(0.09, 0.038, 0.095), eye_z=1.70, face_y=-0.305,
                             nose_z=1.57, mouth_z=1.49, tunic_lower=0.29),
         "hair": [("sphere", (-0.20, 0.05, 1.86), (0.22, 0.30, 0.25)),
                  ("sphere", (0.0, 0.10, 1.96), (0.30, 0.31, 0.23)),
                  ("sphere", (0.21, 0.05, 1.86), (0.22, 0.30, 0.25)),
                  ("sphere", (-0.31, 0.04, 1.67), (0.10, 0.22, 0.24)),
                  ("sphere", (0.31, 0.04, 1.67), (0.10, 0.22, 0.24))],
         "accessories": [([(-0.34, -0.03), (-0.26, -0.11), (0, -0.06), (0.26, -0.11), (0.34, -0.03), (0.25, 0.09), (0, 0.15), (-0.25, 0.09)], 0.13, (0, -0.02, 1.30), "clothing_collar")]},
        {"id": "SPRITE_FRIENDLY_25D", "collection": "Candidate C Sprite-Friendly",
         "art_direction": {"label": "2.5D Sprite-Friendly 3D Character", "shape": "compact oversized landmarks asymmetric silhouette",
                           "surface": "high-contrast cel palette", "rig_forecast": "simple body rig possible; cape/ponytail need secondary treatment"},
         "materials": {**shared_materials, "skin": ([0.78, 0.49, 0.32, 1], 0.68, 0.0),
                       "cloth": ([0.10, 0.18, 0.25, 1], 0.74, 0.0), "pants": ([0.07, 0.11, 0.16, 1], 0.78, 0.0),
                       "outfit": ([0.10, 0.48, 0.44, 1], 0.60, 0.0), "accent": ([0.92, 0.30, 0.10, 1], 0.48, 0.05),
                       "hair": ([0.04, 0.12, 0.18, 1], 0.72, 0.0)},
         "proportions": base(torso_z=0.91, torso_h=0.50, head_z=1.48, head=(0.42, 0.30, 0.39),
                             shoulders=0.34, waist=0.27, shoulder_z=1.14, elbow_x=0.46, elbow_z=0.98,
                             wrist_x=0.57, wrist_z=0.82, hand_x=0.60, hand_z=0.79,
                             hand=(0.095, 0.07, 0.125), hip_z=0.67, knee_z=0.36, ankle_z=0.10,
                             foot=(0.22, 0.34, 0.14), foot_z=0.065, tunic_z=0.92, tunic_h=0.54,
                             tunic_lower=0.31, tunic_upper=0.36, belt_z=0.67, eye_x=0.13,
                             face_y=-0.295, eye_z=1.54, eye=(0.095, 0.036, 0.09), nose_z=1.43,
                             mouth_z=1.36, mouth_w=0.12),
         "hair": [("sphere", (-0.14, 0.06, 1.75), (0.34, 0.30, 0.22)),
                  ("sphere", (0.25, 0.03, 1.66), (0.22, 0.27, 0.28)),
                  ("sphere", (0.46, 0.12, 1.48), (0.13, 0.18, 0.22)),
                  ("sphere", (0.53, 0.16, 1.28), (0.10, 0.14, 0.18))],
         "accessories": [([(-0.38, 0.20), (-0.31, -0.30), (0, -0.42), (0.31, -0.30), (0.38, 0.20)], 0.08, (0, 0.19, 1.05), "clothing_cape"),
                         ([(-0.16, -0.06), (0, -0.12), (0.16, -0.06), (0.10, 0.08), (0, 0.13), (-0.10, 0.08)], 0.10, (-0.34, -0.02, 1.18), "equipment_badge")]},
    ]


def facts(collection, spec):
    bpy.context.view_layer.update()
    meshes = [obj for obj in collection.objects if obj.type == "MESH"]
    roles = sorted({obj.get(ROLE) for obj in meshes})
    bounds = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    return {"objects": len(meshes), "vertices": sum(len(obj.data.vertices) for obj in meshes),
            "triangles": sum(sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons) for obj in meshes),
            "semantic_roles": roles, "bounds": {"min": [min(p[i] for p in bounds) for i in range(3)],
                                                   "max": [max(p[i] for p in bounds) for i in range(3)]},
            "art_direction": spec["art_direction"]}


def point(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(output, candidates):
    scene = bpy.context.scene
    camera_data = bpy.data.cameras.new("B6 Art Direction Camera")
    camera = bpy.data.objects.new("B6 Art Direction Camera", camera_data)
    scene.collection.objects.link(camera)
    camera_data.type, camera_data.ortho_scale = "ORTHO", 2.35
    scene.camera = camera
    key_data = bpy.data.lights.new("B6 Art Key", "AREA"); key_data.energy = 850; key_data.size = 3.0
    key = bpy.data.objects.new("B6 Art Key", key_data); scene.collection.objects.link(key)
    point(key, (3.0, -4.0, 4.0), (0, 0, 1.0))
    fill_data = bpy.data.lights.new("B6 Art Fill", "AREA"); fill_data.energy = 350; fill_data.size = 2.5
    fill = bpy.data.objects.new("B6 Art Fill", fill_data); scene.collection.objects.link(fill)
    point(fill, (-3.0, 2.0, 2.5), (0, 0, 1.0))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.035, 0.045, 0.06)
    views = {"front": (0, -4.5, 1.0), "side": (4.5, 0, 1.0),
             "three-quarter": (3.3, -3.3, 1.05)}
    images = {}
    prototype_objects = [obj for collection, _ in candidates.values() for obj in collection.objects]
    rendered_meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    for style, (collection, _spec) in candidates.items():
        visible = set(collection.objects)
        for obj in rendered_meshes:
            obj.hide_render = obj not in visible
        for view, location in views.items():
            point(camera, location, (0, 0, 1.0))
            path = output / f"{style.lower()}-{view}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            images[f"{style}_{view}"] = str(path)
    for obj in rendered_meshes:
        obj.hide_render = False
    for obj, data in ((camera, camera_data), (key, key_data), (fill, fill_data)):
        bpy.data.objects.remove(obj, do_unlink=True)
        (bpy.data.cameras if isinstance(data, bpy.types.Camera) else bpy.data.lights).remove(data)
    return images


def main():
    options = args()
    root = options.artifact_root
    previews = root / "previews"
    previews.mkdir(exist_ok=True)
    specs = candidate_specs()
    baseline = {name: sorted(block.name for block in getattr(bpy.data, name))
                for name in ("collections", "objects", "meshes", "materials")}
    probe = json.loads(json.dumps(specs[0]))
    probe["id"] += "_ROLLBACK"; probe["collection"] += " Rollback Probe"
    refused = False
    try:
        build_candidate(probe, fail_after=1)
    except RuntimeError as error:
        refused = "injected" in str(error)
    after = {name: sorted(block.name for block in getattr(bpy.data, name)) for name in baseline}
    if not refused or baseline != after:
        raise AssertionError("prototype failure did not restore exact Blender baseline")

    candidates = {}
    candidate_facts = {}
    for spec in specs:
        collection, _objects, _token = build_candidate(spec)
        candidates[spec["id"]] = (collection, spec)
        candidate_facts[spec["id"]] = facts(collection, spec)
    signatures = {(value["objects"], value["vertices"], value["triangles"],
                   tuple(round(x, 4) for x in value["bounds"]["max"])) for value in candidate_facts.values()}
    failures = []
    if len(signatures) != len(specs):
        failures.append("style candidates do not have distinct geometry signatures")
    for style, value in candidate_facts.items():
        required = {"head_face", "face_eye", "face_pupil", "face_nose", "face_mouth",
                    "hair", "clothing_tunic", "arm", "leg", "hand", "foot"}
        if not required <= set(value["semantic_roles"]):
            failures.append(style + " is missing required visible character components")
        if value["triangles"] > 5000:
            failures.append(style + " exceeds prototype triangle budget")
    images = render(previews, candidates)
    blend = root / "character-art-direction-prototypes.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), check_existing=False)
    report = {"schema": "gameassetai.character-art-direction-prototypes.v1",
              "status": "structural_pass_user_selection_required" if not failures else "failed",
              "failures": failures, "candidates": candidate_facts, "images": images,
              "required_visual_checks": ["distinct_from_anatomical_mannequin", "game_character_readability",
                                         "face_character", "hair_clothing_integration",
                                         "multi_view_consistency", "style_distinction"],
              "rollback_verified": True, "blend": str(blend), "blender_version": bpy.app.version_string,
              "selection_state": "USER_SELECTION_REQUIRED",
              "shared_limitations": ["comparison topology is not deformation-ready",
                                     "hair and clothing are not refit/skinned",
                                     "no candidate is an approved default style"]}
    report["report_sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path = root / "validation.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError("; ".join(failures))
    print("GAMEASSETAI_CHARACTER_ART_PROTOTYPES " + json.dumps({"status": report["status"],
                                                                 "blend": str(blend), "report": str(path),
                                                                 "candidates": candidate_facts}))


if __name__ == "__main__":
    main()
