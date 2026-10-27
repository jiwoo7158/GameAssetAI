import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--source-blend", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--case", choices=("compact", "lanky"), required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def component_count(mesh):
    adjacent = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacent[a].add(b)
        adjacent[b].add(a)
    unseen = set(adjacent)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            for neighbor in adjacent[stack.pop()]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def topology(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        return {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "polygons": len(mesh.polygons),
            "components": component_count(mesh),
            "boundary_edges": sum(1 for edge in bm.edges if len(edge.link_faces) == 1),
            "nonmanifold_edges": sum(1 for edge in bm.edges if len(edge.link_faces) != 2),
            "all_quad": all(len(face.verts) == 4 for face in bm.faces),
            "uv_layers": [layer.name for layer in mesh.uv_layers],
            "uv_loops": len(mesh.uv_layers.active.data) if mesh.uv_layers else 0,
            "loops": len(mesh.loops),
        }
    finally:
        bm.free()


def evaluated_coordinates(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def joint_vertices(obj, first, second):
    indices = []
    first_group = obj.vertex_groups[first].index
    second_group = obj.vertex_groups[second].index
    for vertex in obj.data.vertices:
        weights = {group.group: group.weight for group in vertex.groups}
        if weights.get(first_group, 0.0) > 1e-6 and weights.get(second_group, 0.0) > 1e-6:
            indices.append(vertex.index)
    return indices


def neighborhood_quality(obj, rest, posed, first, second):
    indices = set(joint_vertices(obj, first, second))
    ratios = []
    for polygon in obj.data.polygons:
        if not indices.intersection(polygon.vertices):
            continue
        vertices = list(polygon.vertices)
        rest_area = 0.0
        posed_area = 0.0
        for index in range(1, len(vertices) - 1):
            rest_area += ((rest[vertices[index]] - rest[vertices[0]]).cross(
                rest[vertices[index + 1]] - rest[vertices[0]])).length * 0.5
            posed_area += ((posed[vertices[index]] - posed[vertices[0]]).cross(
                posed[vertices[index + 1]] - posed[vertices[0]])).length * 0.5
        if rest_area > 1e-12:
            ratios.append(posed_area / rest_area)
    ratios.sort()
    return {
        "blended_vertices": len(indices),
        "affected_faces": len(ratios),
        "minimum_area_ratio": ratios[0] if ratios else None,
        "median_area_ratio": ratios[len(ratios) // 2] if ratios else None,
    }


def point_camera(camera, location, target):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_views(output, label, obj, height):
    scene = bpy.context.scene
    hidden = {candidate: candidate.hide_render for candidate in scene.objects if candidate != obj}
    for candidate in hidden:
        candidate.hide_render = True
    camera_data = bpy.data.cameras.new("GAA Validation Camera")
    camera = bpy.data.objects.new("GAA Validation Camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = height * 1.12
    light_data = bpy.data.lights.new("GAA Validation Key", "AREA")
    light_data.energy = 900
    light_data.shape = "DISK"
    light_data.size = height * 2.0
    light = bpy.data.objects.new("GAA Validation Key", light_data)
    scene.collection.objects.link(light)
    point_camera(light, (height * 1.5, -height * 2.0, height * 2.1), (0, 0, height * 0.5))
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.world.color = (0.03, 0.03, 0.03)
    views = {
        "front": (0.0, -height * 3.2, height * 0.51),
        "side": (height * 3.2, 0.0, height * 0.51),
        "three-quarter": (height * 2.35, -height * 2.35, height * 0.54),
    }
    paths = {}
    for name, location in views.items():
        point_camera(camera, location, (0, 0, height * 0.5))
        path = output / f"{label}-{name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        paths[name] = str(path)
    bpy.data.objects.remove(camera, do_unlink=True)
    bpy.data.cameras.remove(camera_data)
    bpy.data.objects.remove(light, do_unlink=True)
    bpy.data.lights.remove(light_data)
    for candidate, value in hidden.items():
        if candidate.name in bpy.data.objects:
            candidate.hide_render = value
    return paths


def refit_probe_armature(obj, armature, height):
    """Fit only the validation rig to the accepted template's A-pose silhouette.

    The production rig Skill remains unchanged: this probe separates template
    deformation evidence from the still-open arbitrary-mesh rig-adaptation gate.
    """
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    for side, suffix in ((1.0, ".L"), (-1.0, ".R")):
        shoulder = Vector((side * height * 0.125, 0.0, height * 0.785))
        elbow = Vector((side * height * 0.205, 0.0, height * 0.675))
        wrist = Vector((side * height * 0.275, 0.0, height * 0.565))
        hand = Vector((side * height * 0.305, 0.0, height * 0.535))
        bones = armature.data.edit_bones
        bones["upper_arm" + suffix].head, bones["upper_arm" + suffix].tail = shoulder, elbow
        bones["forearm" + suffix].head, bones["forearm" + suffix].tail = elbow, wrist
        bones["hand" + suffix].head, bones["hand" + suffix].tail = wrist, hand
    bpy.ops.object.mode_set(mode="OBJECT")

    arm_names = [f"{part}.{side}" for side in ("L", "R") for part in ("upper_arm", "forearm", "hand")]
    for name in arm_names:
        obj.vertex_groups[name].remove(range(len(obj.data.vertices)))
    width = height * 0.028
    shoulder_x, elbow_x, wrist_x = height * 0.125, height * 0.205, height * 0.275
    for vertex in obj.data.vertices:
        x, _y, z = vertex.co
        ax = abs(x)
        if z < height * 0.50 or ax < shoulder_x - width:
            continue
        side = "L" if x >= 0 else "R"
        if ax <= shoulder_x + width:
            t = max(0.0, min(1.0, (ax - (shoulder_x - width)) / (2.0 * width)))
            t = t * t * (3.0 - 2.0 * t)
            obj.vertex_groups["chest"].add([vertex.index], 1.0 - t, "REPLACE")
            obj.vertex_groups[f"upper_arm.{side}"].add([vertex.index], t, "REPLACE")
        elif ax <= elbow_x + width:
            t = max(0.0, min(1.0, (ax - (elbow_x - width)) / (2.0 * width)))
            t = t * t * (3.0 - 2.0 * t)
            obj.vertex_groups["chest"].remove([vertex.index])
            obj.vertex_groups[f"upper_arm.{side}"].add([vertex.index], 1.0 - t, "REPLACE")
            obj.vertex_groups[f"forearm.{side}"].add([vertex.index], t, "REPLACE")
        elif ax <= wrist_x + width:
            t = max(0.0, min(1.0, (ax - (wrist_x - width)) / (2.0 * width)))
            t = t * t * (3.0 - 2.0 * t)
            obj.vertex_groups["chest"].remove([vertex.index])
            obj.vertex_groups[f"forearm.{side}"].add([vertex.index], 1.0 - t, "REPLACE")
            obj.vertex_groups[f"hand.{side}"].add([vertex.index], t, "REPLACE")
        else:
            obj.vertex_groups["chest"].remove([vertex.index])
            obj.vertex_groups[f"hand.{side}"].add([vertex.index], 1.0, "REPLACE")
    bpy.context.view_layer.update()


def main():
    args = parse_args()
    output = args.artifact_root / args.case
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo_root / "scripts"))
    from create_character_base import create_character
    from rig_character_base import create_rig

    profiles = {
        "compact": {
            "height": 1.58, "shoulder_width_ratio": 0.39, "hip_width_ratio": 0.27,
            "body_depth_ratio": 0.19, "limb_thickness_ratio": 0.067,
            "head_height_ratio": 0.19,
        },
        "lanky": {
            "height": 1.96, "shoulder_width_ratio": 0.29, "hip_width_ratio": 0.19,
            "body_depth_ratio": 0.13, "limb_thickness_ratio": 0.043,
            "head_height_ratio": 0.15,
        },
    }
    colors = ({"skin": [0.35, 0.60, 0.82, 1.0], "primary": [0.05, 0.20, 0.34, 1.0],
               "secondary": [0.10, 0.38, 0.44, 1.0], "boots": [0.03, 0.04, 0.06, 1.0]}
              if args.case == "compact" else
              {"skin": [0.78, 0.47, 0.28, 1.0], "primary": [0.30, 0.08, 0.04, 1.0],
               "secondary": [0.58, 0.25, 0.08, 1.0], "boots": [0.07, 0.03, 0.02, 1.0]})
    prefix = "GAA Deform " + args.case.title()
    source_hash = hashlib.sha256(args.source_blend.read_bytes()).hexdigest()
    request = {
        "schema": "gameassetai.character-base-request.v4",
        "scene_name": bpy.context.scene.name,
        "character_name": prefix,
        "collection_name": prefix + " Collection",
        "object_name": prefix + " Mesh Object",
        "mesh_name": prefix + " Mesh",
        "pose": "A_POSE",
        "topology_mode": "DEFORMATION_TEMPLATE",
        "template": {
            "source_file": str(args.source_blend.resolve()),
            "source_sha256": source_hash,
            "mesh_name": "GEO-body_male_stylized",
            "source_name": "Blender Studio Human Base Meshes",
            "source_version": "1.4.1",
            "license": "CC0-1.0",
            "front_axis": "-Y",
        },
        "proportions": profiles[args.case],
        "colors": colors,
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_SINGLE_MESH_CHARACTER", "failure": "ROLL_BACK_OWNED_DATA",
                   "rigging": "NOT_INCLUDED"},
    }
    before = {kind: sorted(item.name for item in getattr(bpy.data, kind))
              for kind in ("collections", "objects", "meshes", "materials", "images")}
    bad = json.loads(json.dumps(request))
    bad["character_name"] += " Bad"
    bad["collection_name"] += " Bad"
    bad["object_name"] += " Bad"
    bad["mesh_name"] += " Bad"
    bad["template"]["source_sha256"] = "0" * 64
    refused = False
    try:
        create_character(bad, authorized=True)
    except ValueError as error:
        refused = "SHA-256 mismatch" in str(error)
    after_failure = {kind: sorted(item.name for item in getattr(bpy.data, kind))
                     for kind in before}
    if not refused or before != after_failure:
        raise AssertionError("invalid-hash failure did not restore the exact Blender baseline")

    source_hash_before = hashlib.sha256(args.source_blend.read_bytes()).hexdigest()
    receipt = create_character(request, authorized=True)
    obj = bpy.data.objects[receipt["object_name"]]
    mesh = obj.data
    rest_topology = topology(mesh)
    rest_uv = [[float(value) for value in loop.uv] for loop in mesh.uv_layers.active.data]
    rest = evaluated_coordinates(obj)
    rest_images = render_views(output, "rest", obj, profiles[args.case]["height"])

    rig_request = {
        "schema": "gameassetai.character-rig-request.v2", "scene_name": bpy.context.scene.name,
        "mesh_object_name": obj.name, "armature_object_name": prefix + " Rig",
        "armature_data_name": prefix + " Armature", "rig_name": prefix,
        "policy": {"target": "OWNED_CHARACTER_BASE_ONLY", "existing_rig": "REFUSE",
                   "weights": "LINEAR_JOINT_BLEND_V2", "source_mesh": "PRESERVE_GEOMETRY",
                   "failure": "ROLL_BACK_RIG_CHANGES"},
    }
    rig = create_rig(rig_request, authorized=True)
    armature = bpy.data.objects[rig["armature_object_name"]]
    refit_probe_armature(obj, armature, profiles[args.case]["height"])
    for bone in armature.pose.bones:
        bone.rotation_mode = "XYZ"
    armature.pose.bones["upper_arm.L"].rotation_euler.x = math.radians(-24)
    armature.pose.bones["forearm.L"].rotation_euler.z = math.radians(-72)
    armature.pose.bones["thigh.R"].rotation_euler.x = math.radians(-32)
    armature.pose.bones["shin.R"].rotation_euler.x = math.radians(68)
    bpy.context.view_layer.update()
    posed = evaluated_coordinates(obj)
    posed_images = render_views(output, "posed", obj, profiles[args.case]["height"])
    displacements = [(posed[index] - rest[index]).length for index in range(len(rest))]
    joints = {
        "left_elbow": neighborhood_quality(obj, rest, posed, "upper_arm.L", "forearm.L"),
        "right_knee": neighborhood_quality(obj, rest, posed, "thigh.R", "shin.R"),
        "left_shoulder": neighborhood_quality(obj, rest, posed, "chest", "upper_arm.L"),
        "right_hip": neighborhood_quality(obj, rest, posed, "pelvis", "thigh.R"),
    }
    current_uv = [[float(value) for value in loop.uv] for loop in mesh.uv_layers.active.data]
    source_hash_after = hashlib.sha256(args.source_blend.read_bytes()).hexdigest()
    failures = []
    if rest_topology["components"] != 1 or rest_topology["nonmanifold_edges"] != 0:
        failures.append("template topology is not one closed manifold component")
    if not rest_topology["all_quad"] or rest_topology["uv_loops"] != rest_topology["loops"]:
        failures.append("quad or UV preservation failed")
    if rest_uv != current_uv:
        failures.append("UV coordinates changed during rig/deformation probe")
    if source_hash_before != source_hash_after:
        failures.append("external source file changed")
    if max(displacements) < profiles[args.case]["height"] * 0.03:
        failures.append("pose did not produce representative deformation")
    for name, facts in joints.items():
        if not facts["blended_vertices"] or facts["minimum_area_ratio"] is None:
            failures.append(f"{name} has no measurable blended deformation neighborhood")
        elif facts["minimum_area_ratio"] < 0.015:
            failures.append(f"{name} contains a severe collapsed face")

    blend_path = output / f"{args.case}-deformation-ready.blend"
    report = {
        "schema": "gameassetai.character-deformation-template-validation.v1",
        "case": args.case, "status": "pass" if not failures else "failed",
        "failures": failures, "request": request, "creation_receipt": receipt,
        "rig_receipt": rig, "rest_topology": rest_topology, "joint_quality": joints,
        "deformation": {"moved_vertices": sum(value > 1e-6 for value in displacements),
                        "maximum_displacement": max(displacements)},
        "source_preserved": source_hash_before == source_hash_after,
        "source_sha256": source_hash_after, "uv_preserved": rest_uv == current_uv,
        "rest_images": rest_images, "posed_images": posed_images,
        "blend": str(blend_path), "blender_version": bpy.app.version_string,
    }
    report["report_sha256"] = hashlib.sha256(canonical(report).encode("utf-8")).hexdigest()
    report_path = output / f"{args.case}-validation.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    if failures:
        raise AssertionError("; ".join(failures))
    print("GAMEASSETAI_DEFORMATION_TEMPLATE " + json.dumps({
        "status": report["status"], "case": args.case, "blend": str(blend_path),
        "report": str(report_path), "checks": {"topology": rest_topology, "joints": joints},
    }))


if __name__ == "__main__":
    main()
