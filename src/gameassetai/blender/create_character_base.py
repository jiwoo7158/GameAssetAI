import hashlib
import json
import math
import uuid
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from validate_character_base_request import (
    MATERIAL_KEYS, REGION_LIMITS, validate_request, validate_revision_request,
)


OWNER_KEY = "gameassetai_character_owner"
SOURCE_KIND_KEY = "gameassetai_character_source_kind"
SOURCE_SHA_KEY = "gameassetai_character_source_sha256"
SOURCE_NAME_KEY = "gameassetai_character_source_name"
SOURCE_VERSION_KEY = "gameassetai_character_source_version"
SOURCE_LICENSE_KEY = "gameassetai_character_source_license"
SCHEMA_KEY = "gameassetai_character_schema"
ART_DIRECTION_KEY = "gameassetai_character_art_direction"
REGION_PREFIX = "gameassetai_region_"
REGION_NAMES = ("head", "torso", "arm", "hand", "leg", "foot")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _tag(data_block, token):
    data_block[OWNER_KEY] = token
    return data_block


def _new_faces(bm, before, material_index):
    for face in bm.faces:
        if face not in before:
            face.material_index = material_index


def _add_box(bm, center, dimensions, material_index):
    before = set(bm.faces)
    result = bmesh.ops.create_cube(bm, size=1.0)
    matrix = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*dimensions, 1.0))
    bmesh.ops.transform(bm, verts=result["verts"], matrix=matrix)
    _new_faces(bm, before, material_index)


def _add_icosphere(bm, center, dimensions, material_index):
    before = set(bm.faces)
    result = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    scale = Vector(dimensions) * 0.5
    matrix = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((*scale, 1.0))
    bmesh.ops.transform(bm, verts=result["verts"], matrix=matrix)
    _new_faces(bm, before, material_index)


def _add_limb(bm, start, end, radius, material_index, segments=8):
    start, end = Vector(start), Vector(end)
    direction = end - start
    length = direction.length
    before = set(bm.faces)
    result = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=1.0, radius2=0.92, depth=1.0,
    )
    rotation = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized()).to_matrix().to_4x4()
    scale = Matrix.Diagonal((radius, radius, length, 1.0))
    matrix = Matrix.Translation((start + end) * 0.5) @ rotation @ scale
    bmesh.ops.transform(bm, verts=result["verts"], matrix=matrix)
    _new_faces(bm, before, material_index)


def _make_material(name, color, token, metallic=0.0, roughness=0.65):
    material = _tag(bpy.data.materials.new(name), token)
    material.diffuse_color = color
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = color
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return material


def _component_count(mesh):
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    unseen = set(adjacency)
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
    return count


def _voxel_connect(obj, voxel_size):
    mesh = obj.data
    source_vertices = [tuple(vertex.co) for vertex in mesh.vertices]
    source_polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    source_materials = [polygon.material_index for polygon in mesh.polygons]
    source_tree = BVHTree.FromPolygons(source_vertices, source_polygons, all_triangles=False)
    window = bpy.context.window
    original_scene = window.scene if window else None
    original_active = bpy.context.view_layer.objects.active
    original_selected = list(bpy.context.selected_objects)
    try:
        if window:
            window.scene = obj.users_scene[0]
        for selected in bpy.context.selected_objects:
            selected.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        mesh.remesh_voxel_size = voxel_size
        mesh.remesh_voxel_adaptivity = 0.0
        bpy.ops.object.voxel_remesh()
        for polygon in mesh.polygons:
            nearest = source_tree.find_nearest(polygon.center)
            if nearest and nearest[2] is not None:
                polygon.material_index = source_materials[nearest[2]]
        mesh.update()
    finally:
        obj.select_set(False)
        if window and original_scene:
            window.scene = original_scene
        for selected in original_selected:
            if bpy.data.objects.get(selected.name) is selected:
                selected.select_set(True)
        if original_active and bpy.data.objects.get(original_active.name) is original_active:
            bpy.context.view_layer.objects.active = original_active


def _mesh_components(mesh):
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(adjacency)
    components = []
    while remaining:
        component = {remaining.pop()}
        stack = list(component)
        while stack:
            for neighbor in adjacency[stack.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _boolean_connect(obj, token):
    """Union semantic volumes without the global voxel remesh that fused both legs."""
    source_mesh = obj.data
    components = _mesh_components(source_mesh)
    if len(components) < 2:
        return
    polygon_sets = []
    for vertices in components:
        polygons = [polygon for polygon in source_mesh.polygons if polygon.vertices[0] in vertices]
        if polygons:
            polygon_sets.append((vertices, polygons))
    polygon_sets.sort(key=lambda item: len(item[1]), reverse=True)
    collection = obj.users_collection[0]
    operands = []
    window = bpy.context.window
    original_scene = window.scene if window else None
    original_active = bpy.context.view_layer.objects.active
    original_selected = list(bpy.context.selected_objects)
    try:
        for index, (vertex_indices, polygons) in enumerate(polygon_sets):
            ordered = sorted(vertex_indices)
            remap = {old: new for new, old in enumerate(ordered)}
            vertices = [tuple(source_mesh.vertices[old].co) for old in ordered]
            faces = [[remap[old] for old in polygon.vertices] for polygon in polygons]
            part_mesh = _tag(bpy.data.meshes.new(f"{source_mesh.name} Boolean Part {index:02d}"), token)
            part_mesh.from_pydata(vertices, [], faces)
            part_mesh.update()
            for material in source_mesh.materials:
                part_mesh.materials.append(material)
            for target, source in zip(part_mesh.polygons, polygons):
                target.material_index = source.material_index
            part = _tag(bpy.data.objects.new(f"{obj.name} Boolean Part {index:02d}", part_mesh), token)
            collection.objects.link(part)
            operands.append(part)

        base = operands.pop(0)
        base.name = f"{obj.name} Boolean Working"
        if window:
            window.scene = obj.users_scene[0]
        for operand in operands:
            for selected in bpy.context.selected_objects:
                selected.select_set(False)
            base.select_set(True)
            bpy.context.view_layer.objects.active = base
            modifier = base.modifiers.new(name="GameAssetAI Semantic Union", type="BOOLEAN")
            modifier.operation = "UNION"
            modifier.solver = "EXACT"
            modifier.object = operand
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            operand_mesh = operand.data
            bpy.data.objects.remove(operand, do_unlink=True)
            if operand_mesh.users == 0:
                bpy.data.meshes.remove(operand_mesh)

        result_mesh = base.data
        requested_mesh_name = source_mesh.name
        obj.data = result_mesh
        bpy.data.objects.remove(base, do_unlink=True)
        if source_mesh.users == 0:
            bpy.data.meshes.remove(source_mesh)
        result_mesh.name = requested_mesh_name
        obj.data.update()
    except Exception:
        for operand in list(operands):
            if bpy.data.objects.get(operand.name) is operand:
                bpy.data.objects.remove(operand, do_unlink=True)
        raise
    finally:
        if window and original_scene:
            window.scene = original_scene
        for selected in original_selected:
            if bpy.data.objects.get(selected.name) is selected:
                selected.select_set(True)
        if original_active and bpy.data.objects.get(original_active.name) is original_active:
            bpy.context.view_layer.objects.active = original_active


def _semantic_clearance(mesh, height):
    foot_vertices = [vertex.co for vertex in mesh.vertices if vertex.co.z < height * 0.09]
    lower_vertices = [vertex.co for vertex in mesh.vertices if height * 0.075 < vertex.co.z < height * 0.34]

    def clearance(vertices):
        negative = [point.x for point in vertices if point.x < 0.0]
        positive = [point.x for point in vertices if point.x > 0.0]
        return min(positive) - max(negative) if negative and positive else 0.0

    cross_side_edges = 0
    for edge in mesh.edges:
        a, b = (mesh.vertices[index].co for index in edge.vertices)
        if a.x * b.x < 0.0 and max(a.z, b.z) < height * 0.30:
            cross_side_edges += 1
    return {
        "foot_centerline_clearance": clearance(foot_vertices),
        "lower_leg_centerline_clearance": clearance(lower_vertices),
        "cross_side_edges_below_knee": cross_side_edges,
    }


def _non_manifold_edge_count(mesh):
    topology = bmesh.new()
    try:
        topology.from_mesh(mesh)
        return sum(1 for edge in topology.edges if len(edge.link_faces) != 2)
    finally:
        topology.free()


def _quadriflow_micro_edge_count(mesh, tolerance=1.0e-4):
    """Match Blender's QuadriFlow preflight coordinate comparison."""
    return sum(
        1 for edge in mesh.edges
        if all(abs(mesh.vertices[edge.vertices[0]].co[axis]
                   - mesh.vertices[edge.vertices[1]].co[axis]) <= tolerance
               for axis in range(3))
    )


def _cleanup_boolean_micro_edges(mesh, tolerance=1.0e-4):
    """Remove exact-Boolean sliver edges that Blender QuadriFlow rejects."""
    before = _quadriflow_micro_edge_count(mesh, tolerance)
    if before:
        topology = bmesh.new()
        try:
            topology.from_mesh(mesh)
            bmesh.ops.dissolve_degenerate(
                topology, dist=tolerance, edges=list(topology.edges))
            bmesh.ops.recalc_face_normals(topology, faces=list(topology.faces))
            topology.to_mesh(mesh)
            mesh.update()
        finally:
            topology.free()
    return before, _quadriflow_micro_edge_count(mesh, tolerance)


def _smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def _blend(low, high, factor):
    return low + (high - low) * _smoothstep(factor)


def _load_template_mesh(data, token):
    template = data["template"]
    source = Path(template["source_file"])
    if not source.is_file() or source.is_symlink():
        raise ValueError("template source_file must be an existing regular, non-symbolic .blend file")
    actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_sha != template["source_sha256"]:
        raise ValueError(
            f"template source SHA-256 mismatch: expected {template['source_sha256']}, got {actual_sha}"
        )
    before_materials = {item.as_pointer() for item in bpy.data.materials}
    before_images = {item.as_pointer() for item in bpy.data.images}
    with bpy.data.libraries.load(str(source), link=False) as (source_data, target_data):
        if template["mesh_name"] not in source_data.meshes:
            raise ValueError(f"template Mesh does not exist: {template['mesh_name']}")
        target_data.meshes = [template["mesh_name"]]
    mesh = target_data.meshes[0] if target_data.meshes else None
    if mesh is None:
        raise RuntimeError("template Mesh could not be loaded")
    _tag(mesh, token)
    for material in bpy.data.materials:
        if material.as_pointer() not in before_materials:
            _tag(material, token)
    for image in bpy.data.images:
        if image.as_pointer() not in before_images:
            _tag(image, token)
    if mesh.shape_keys is not None:
        raise ValueError("template Mesh with Shape Keys is not supported")
    if mesh.materials:
        raise ValueError("template Mesh must not carry external Material dependencies")
    if not mesh.vertices or not mesh.polygons:
        raise ValueError("template Mesh must be non-empty")
    mesh.name = data["mesh_name"]
    return mesh, actual_sha


def _adapt_template_mesh(mesh, proportions):
    """Apply a bounded smooth regional warp without changing topology or UV loops."""
    coordinates = [vertex.co.copy() for vertex in mesh.vertices]
    minimum_z = min(point.z for point in coordinates)
    maximum_z = max(point.z for point in coordinates)
    source_height = maximum_z - minimum_z
    if source_height <= 0.0:
        raise ValueError("template Mesh has no positive height")
    target_height = proportions["height"]
    shoulder_scale = proportions["shoulder_width_ratio"] / 0.34
    hip_scale = proportions["hip_width_ratio"] / 0.24
    depth_scale = proportions["body_depth_ratio"] / 0.17
    limb_scale = proportions["limb_thickness_ratio"] / 0.055
    head_scale = proportions["head_height_ratio"] / 0.17
    target_head_base = 1.0 - proportions["head_height_ratio"]

    def vertical(normalized):
        landmarks = (
            (0.0, 0.0), (0.075, 0.07), (0.29, 0.30), (0.52, 0.52),
            (0.78, 0.78), (0.84, target_head_base), (1.0, 1.0),
        )
        for (source_a, target_a), (source_b, target_b) in zip(landmarks, landmarks[1:]):
            if normalized <= source_b:
                factor = (normalized - source_a) / (source_b - source_a)
                return _blend(target_a, target_b, factor)
        return 1.0

    for vertex, original in zip(mesh.vertices, coordinates):
        normalized = max(0.0, min(1.0, (original.z - minimum_z) / source_height))
        if normalized < 0.52:
            x_scale = 0.72 * hip_scale + 0.28 * limb_scale
            y_scale = 0.45 * depth_scale + 0.55 * limb_scale
        elif normalized < 0.78:
            factor = (normalized - 0.52) / 0.26
            x_scale = _blend(hip_scale, shoulder_scale, factor)
            y_scale = depth_scale
        elif normalized < 0.84:
            x_scale = shoulder_scale
            y_scale = _blend(depth_scale, head_scale, (normalized - 0.78) / 0.06)
        else:
            x_scale = head_scale
            y_scale = head_scale
        vertex.co.x = original.x * x_scale * target_height / source_height
        vertex.co.y = original.y * y_scale * target_height / source_height
        vertex.co.z = vertical(normalized) * target_height
    mesh.update()
    return {
        "source_height": source_height,
        "target_height": target_height,
        "warp": "SMOOTH_REGIONAL_V1",
    }


def _assign_template_materials(mesh, materials, height):
    for material in materials:
        mesh.materials.append(material)
    for polygon in mesh.polygons:
        center = polygon.center
        if center.z < height * 0.105:
            polygon.material_index = 3
        elif center.z < height * 0.54:
            polygon.material_index = 2
        elif center.z > height * 0.82 or abs(center.x) > height * 0.16:
            polygon.material_index = 0
        else:
            polygon.material_index = 1


def _mesh_topology_sha256(mesh):
    payload = {
        "vertices": len(mesh.vertices),
        "edges": [tuple(edge.vertices) for edge in mesh.edges],
        "polygons": [tuple(polygon.vertices) for polygon in mesh.polygons],
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _mesh_uv_sha256(mesh):
    if not mesh.uv_layers or mesh.uv_layers.active is None:
        return None
    payload = [[round(item.uv.x, 9), round(item.uv.y, 9)] for item in mesh.uv_layers.active.data]
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def _region_attribute(mesh, name):
    attribute = mesh.attributes.get(REGION_PREFIX + name)
    if attribute is None or attribute.domain != "POINT" or attribute.data_type != "FLOAT":
        raise ValueError(f"required character semantic region attribute is missing: {name}")
    return attribute


def _write_semantic_regions(mesh):
    points = [vertex.co.copy() for vertex in mesh.vertices]
    minimum_z = min(point.z for point in points)
    maximum_z = max(point.z for point in points)
    height = maximum_z - minimum_z
    maximum_x = max(abs(point.x) for point in points)
    if height <= 0.0 or maximum_x <= 0.0:
        raise ValueError("character Mesh bounds are invalid for semantic regions")

    def ramp(value, low, high):
        if high <= low:
            return float(value >= high)
        return _smoothstep((value - low) / (high - low))

    values = {name: [] for name in REGION_NAMES}
    for point in points:
        z = (point.z - minimum_z) / height
        x = abs(point.x) / maximum_x
        head = ramp(z, 0.78, 0.84)
        hand = ramp(x, 0.76, 0.90) * (1.0 - ramp(z, 0.86, 0.94)) * ramp(z, 0.47, 0.58)
        arm = ramp(x, 0.30, 0.48) * ramp(z, 0.47, 0.58) * (1.0 - ramp(z, 0.84, 0.91))
        foot = (1.0 - ramp(z, 0.10, 0.145))
        leg = (1.0 - ramp(z, 0.48, 0.57)) * (1.0 - foot * 0.55)
        torso = ramp(z, 0.46, 0.57) * (1.0 - ramp(z, 0.78, 0.85)) * (1.0 - ramp(x, 0.28, 0.48))
        for name, value in (("head", head), ("torso", torso), ("arm", arm),
                            ("hand", hand), ("leg", leg), ("foot", foot)):
            values[name].append(max(0.0, min(1.0, value)))
    for name in REGION_NAMES:
        old = mesh.attributes.get(REGION_PREFIX + name)
        if old is not None:
            mesh.attributes.remove(old)
        attribute = mesh.attributes.new(REGION_PREFIX + name, "FLOAT", "POINT")
        for item, value in zip(attribute.data, values[name]):
            item.value = value
    mesh.update()
    return {name: sum(1 for value in values[name] if value > 1.0e-6) for name in REGION_NAMES}


def _apply_region_controls(mesh, controls):
    """Apply bounded semantic-region deformations while preserving indices and UV loops."""
    factors = {key: float(controls.get(key, 1.0)) for key in REGION_LIMITS}
    weights = {
        name: [item.value for item in _region_attribute(mesh, name).data]
        for name in REGION_NAMES
    }
    original = [vertex.co.copy() for vertex in mesh.vertices]
    minimum_z = min(point.z for point in original)
    maximum_z = max(point.z for point in original)
    height = maximum_z - minimum_z
    maximum_x = max(abs(point.x) for point in original)
    hip_z = minimum_z + height * 0.53
    shoulder_z = minimum_z + height * 0.78
    head_pivot_z = minimum_z + height * 0.81
    shoulder_x = maximum_x * 0.30
    wrist_x = maximum_x * 0.76
    foot_x = maximum_x * 0.18

    changed = set()
    unchanged = set()
    influenced = set()
    for index, (vertex, source) in enumerate(zip(mesh.vertices, original)):
        point = source.copy()
        total_weight = 0.0

        def scale_axis(axis, pivot, factor, weight):
            nonlocal point, total_weight
            if abs(factor - 1.0) <= 1.0e-12 or weight <= 0.0:
                return
            influenced.add(index)
            point[axis] = pivot + (point[axis] - pivot) * (1.0 + (factor - 1.0) * weight)
            total_weight = max(total_weight, weight)

        scale_axis(0, 0.0, factors["torso_width_scale"], weights["torso"][index])
        scale_axis(2, hip_z, factors["leg_length_scale"], weights["leg"][index])

        side = -1.0 if source.x < 0.0 else 1.0
        arm_weight = weights["arm"][index]
        scale_axis(0, side * shoulder_x, factors["arm_length_scale"], arm_weight)
        scale_axis(2, shoulder_z, factors["arm_length_scale"], arm_weight * 0.45)
        scale_axis(1, 0.0, factors["arm_thickness_scale"], arm_weight)

        head_weight = weights["head"][index]
        scale_axis(0, 0.0, factors["head_scale"] * factors["head_width_scale"], head_weight)
        scale_axis(1, 0.0, factors["head_scale"] * factors["head_depth_scale"], head_weight)
        scale_axis(2, head_pivot_z, factors["head_scale"], head_weight)

        hand_weight = weights["hand"][index]
        hand_factor = factors["hand_scale"]
        scale_axis(0, side * wrist_x, hand_factor, hand_weight)
        scale_axis(1, 0.0, hand_factor, hand_weight)
        scale_axis(2, minimum_z + height * 0.61, hand_factor, hand_weight)

        foot_weight = weights["foot"][index]
        foot_factor = factors["foot_scale"]
        scale_axis(0, side * foot_x, foot_factor, foot_weight)
        scale_axis(1, 0.0, foot_factor, foot_weight)
        scale_axis(2, minimum_z + height * 0.055, foot_factor, foot_weight * 0.45)

        vertex.co = point
        if total_weight > 0.0 and (point - source).length > 1.0e-10:
            changed.add(index)
        else:
            unchanged.add(index)
    mesh.update()
    unaffected = set(range(len(mesh.vertices))) - influenced
    return {
        "operation": "SEMANTIC_REGION_WARP_V1",
        "controls": factors,
        "changed_vertices": len(changed),
        "unchanged_vertices": len(unchanged),
        "influenced_vertices": len(influenced),
        "influenced_without_displacement": len(influenced - changed),
        "unaffected_vertices": len(unaffected),
        # Retain the v5 receipt field as a compatibility alias. In v5 it meant
        # vertices outside any active regional control, not every unmoved vertex.
        "untouched_vertices": len(unaffected),
        "changed_indices": sorted(changed),
        "unchanged_indices": sorted(unchanged),
        "unaffected_indices": sorted(unaffected),
        "untouched_indices": sorted(unaffected),
    }


def _rollback(token):
    for obj in list(bpy.data.objects):
        if obj.get(OWNER_KEY) == token:
            bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        if mesh.get(OWNER_KEY) == token and mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for material in list(bpy.data.materials):
        if material.get(OWNER_KEY) == token and material.users == 0:
            bpy.data.materials.remove(material)
    for image in list(bpy.data.images):
        if image.get(OWNER_KEY) == token and image.users == 0:
            bpy.data.images.remove(image)
    for collection in list(bpy.data.collections):
        if collection.get(OWNER_KEY) == token:
            bpy.data.collections.remove(collection)


def create_character(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent character creation")
    validated = validate_request(request)
    data = validated["request"]
    scene = bpy.data.scenes.get(data["scene_name"])
    if scene is None:
        raise ValueError(f"Scene does not exist: {data['scene_name']}")
    for database, name, label in (
        (bpy.data.collections, data["collection_name"], "collection_name"),
        (bpy.data.objects, data["object_name"], "object_name"),
        (bpy.data.meshes, data["mesh_name"], "mesh_name"),
    ):
        if database.get(name):
            raise ValueError(f"{label} is already in use: {name}")

    token = uuid.uuid4().hex
    material_names = {key: f"{data['character_name']} {key.title()}" for key in MATERIAL_KEYS}
    occupied = [name for name in material_names.values() if bpy.data.materials.get(name)]
    if occupied:
        raise ValueError(f"material names are already in use: {occupied}")

    try:
        collection = _tag(bpy.data.collections.new(data["collection_name"]), token)
        scene.collection.children.link(collection)
        materials = []
        for key in MATERIAL_KEYS:
            metallic = 0.08 if key == "secondary" else 0.0
            roughness = 0.5 if key == "boots" else 0.68
            materials.append(_make_material(material_names[key], data["colors"][key], token, metallic, roughness))

        p = data["proportions"]
        h = p["height"]
        shoulder = h * p["shoulder_width_ratio"]
        hip = h * p["hip_width_ratio"]
        depth = h * p["body_depth_ratio"]
        limb = h * p["limb_thickness_ratio"]
        head_h = h * p["head_height_ratio"]
        topology_mode = data.get("topology_mode", "VOLUME_ISLANDS")
        source_sha = None
        adaptation = None
        region_counts = None
        regional_application = None
        if topology_mode == "DEFORMATION_TEMPLATE":
            mesh, source_sha = _load_template_mesh(data, token)
            adaptation = _adapt_template_mesh(mesh, p)
            if data["schema"] == "gameassetai.character-base-request.v5":
                region_counts = _write_semantic_regions(mesh)
                regional_application = _apply_region_controls(mesh, data["regions"])
            _assign_template_materials(mesh, materials, h)
        else:
            bm = bmesh.new()
            # V1 retains separate volumes; V2 may fuse overlapping volumes after construction.
            _add_box(bm, (0, 0, h * 0.59), (hip, depth * 0.92, h * 0.10), 2)
            _add_box(bm, (0, 0, h * 0.735), (shoulder * 0.82, depth, h * 0.22), 1)
            _add_limb(bm, (0, 0, h * 0.82), (0, 0, h * 0.845), limb * 0.72, 0, 8)
            _add_icosphere(bm, (0, 0, h * 0.91), (head_h * 0.72, head_h * 0.68, head_h), 0)

            hip_x = hip * 0.27
            knee_z, ankle_z = h * 0.32, h * 0.085
            for side in (-1.0, 1.0):
                upper_start = (side * hip_x, 0, h * 0.56)
                knee = (side * hip_x * 1.04, 0, knee_z)
                ankle = (side * hip_x * 1.02, 0, ankle_z)
                _add_limb(bm, upper_start, knee, limb * 1.18, 1, 10)
                _add_limb(bm, knee, ankle, limb, 0, 10)
                _add_box(bm, (side * hip_x * 1.02, -depth * 0.18, h * 0.045), (limb * 2.15, depth * 1.25, h * 0.09), 3)

            shoulder_z = h * 0.79
            shoulder_x = shoulder * 0.46
            upper = h * 0.17
            lower = h * 0.16
            drop = 0.0 if data["pose"] == "T_POSE" else h * 0.085
            for side in (-1.0, 1.0):
                start = Vector((side * shoulder_x, 0, shoulder_z))
                elbow = start + Vector((side * upper, 0, -drop))
                hand = elbow + Vector((side * lower, 0, -drop * 0.72))
                _add_limb(bm, start, elbow, limb, 1, 8)
                _add_limb(bm, elbow, hand, limb * 0.86, 0, 8)
                _add_icosphere(bm, hand + Vector((side * limb * 0.8, 0, -limb * 0.15)), (limb * 1.7, limb * 1.45, limb * 2.1), 0)

            mesh = _tag(bpy.data.meshes.new(data["mesh_name"]), token)
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            for material in materials:
                mesh.materials.append(material)
        obj = _tag(bpy.data.objects.new(data["object_name"], mesh), token)
        obj["gameassetai_character_request"] = _canonical(data)
        obj["gameassetai_character_front_axis"] = "-Y"
        obj[SCHEMA_KEY] = data["schema"]
        mesh[SCHEMA_KEY] = data["schema"]
        collection[SCHEMA_KEY] = data["schema"]
        if data["schema"] == "gameassetai.character-base-request.v5":
            art_json = _canonical(data["art_direction"])
            obj[ART_DIRECTION_KEY] = art_json
            mesh[ART_DIRECTION_KEY] = art_json
            collection[ART_DIRECTION_KEY] = art_json
        if topology_mode == "DEFORMATION_TEMPLATE":
            template = data["template"]
            obj[SOURCE_KIND_KEY] = "CC0_TEMPLATE"
            obj[SOURCE_SHA_KEY] = source_sha
            obj[SOURCE_NAME_KEY] = template["source_name"]
            obj[SOURCE_VERSION_KEY] = template["source_version"]
            obj[SOURCE_LICENSE_KEY] = template["license"]
            for key in (SOURCE_KIND_KEY, SOURCE_SHA_KEY, SOURCE_NAME_KEY, SOURCE_VERSION_KEY, SOURCE_LICENSE_KEY):
                mesh[key] = obj[key]
        collection.objects.link(obj)
        components_before = _component_count(mesh)
        if topology_mode == "VOXEL_CONNECTED":
            _voxel_connect(obj, h * 0.018)
        elif topology_mode == "BOOLEAN_CONNECTED":
            _boolean_connect(obj, token)
            mesh = obj.data
            micro_edges_before, micro_edges_after = _cleanup_boolean_micro_edges(mesh)
            if micro_edges_after:
                raise RuntimeError(
                    "connected topology retained QuadriFlow-incompatible micro edges: "
                    f"{micro_edges_after}"
                )
        elif topology_mode != "DEFORMATION_TEMPLATE":
            micro_edges_before = micro_edges_after = 0
        else:
            micro_edges_before = micro_edges_after = 0
        components_after = _component_count(mesh)
        if topology_mode in {"VOXEL_CONNECTED", "BOOLEAN_CONNECTED", "DEFORMATION_TEMPLATE"} and components_after != 1:
            raise RuntimeError(f"connected topology produced {components_after} components")
        semantic_checks = _semantic_clearance(mesh, h)
        non_manifold_edges = _non_manifold_edge_count(mesh)
        if topology_mode == "BOOLEAN_CONNECTED":
            minimum_clearance = h * 0.005
            if semantic_checks["foot_centerline_clearance"] <= minimum_clearance:
                raise RuntimeError("connected topology failed foot centerline clearance")
            if semantic_checks["lower_leg_centerline_clearance"] <= minimum_clearance:
                raise RuntimeError(
                    "connected topology failed lower-leg centerline clearance: "
                    f"{semantic_checks['lower_leg_centerline_clearance']}"
                )
            if semantic_checks["cross_side_edges_below_knee"]:
                raise RuntimeError("connected topology created cross-side edges below the knee")
            if non_manifold_edges:
                raise RuntimeError(f"connected topology produced {non_manifold_edges} non-manifold edges")
        if topology_mode == "DEFORMATION_TEMPLATE":
            if non_manifold_edges:
                raise RuntimeError(f"template topology produced {non_manifold_edges} non-manifold edges")
            if any(len(polygon.vertices) != 4 for polygon in mesh.polygons):
                raise RuntimeError("template topology must remain all-quad")
            if not mesh.uv_layers or len(mesh.uv_layers.active.data) != len(mesh.loops):
                raise RuntimeError("template topology must retain one complete active UV layer")
            if data["schema"] == "gameassetai.character-base-request.v5":
                triangles = sum(max(0, len(polygon.vertices) - 2) for polygon in mesh.polygons)
                if triangles > data["art_direction"]["polygon_budget"]:
                    raise RuntimeError(
                        f"character triangle budget exceeded: {triangles} > "
                        f"{data['art_direction']['polygon_budget']}"
                    )

        world_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        minimum = [min(point[i] for point in world_corners) for i in range(3)]
        maximum = [max(point[i] for point in world_corners) for i in range(3)]
        receipt = {
            "status": "created",
            "character_name": data["character_name"],
            "collection_name": collection.name,
            "object_name": obj.name,
            "mesh_name": mesh.name,
            "pose": data["pose"],
            "vertices": len(mesh.vertices),
            "polygons": len(mesh.polygons),
            "material_names": [material.name for material in materials],
            "topology_mode": topology_mode,
            "components_before": components_before,
            "components_after": components_after,
            "semantic_checks": semantic_checks,
            "non_manifold_edges": non_manifold_edges,
            "quadriflow_micro_edges_before": micro_edges_before,
            "quadriflow_micro_edges_after": micro_edges_after,
            "world_bounds": {"min": minimum, "max": maximum},
            "request_sha256": validated["request_sha256"],
            "rigged": False,
        }
        if topology_mode == "DEFORMATION_TEMPLATE":
            receipt["template"] = {
                "source_name": data["template"]["source_name"],
                "source_version": data["template"]["source_version"],
                "license": data["template"]["license"],
                "mesh_name": data["template"]["mesh_name"],
                "source_sha256": source_sha,
            }
            receipt["adaptation"] = adaptation
            receipt["uv_layers"] = [layer.name for layer in mesh.uv_layers]
            receipt["all_quad"] = all(len(polygon.vertices) == 4 for polygon in mesh.polygons)
            receipt["topology_sha256"] = _mesh_topology_sha256(mesh)
            receipt["uv_sha256"] = _mesh_uv_sha256(mesh)
            if data["schema"] == "gameassetai.character-base-request.v5":
                receipt["art_direction"] = data["art_direction"]
                receipt["semantic_region_vertices"] = region_counts
                receipt["regional_application"] = {
                    key: value for key, value in regional_application.items()
                    if key not in {"changed_indices", "unchanged_indices", "unaffected_indices", "untouched_indices"}
                }
                receipt["triangles"] = sum(max(0, len(polygon.vertices) - 2) for polygon in mesh.polygons)
                receipt["polygon_budget"] = data["art_direction"]["polygon_budget"]
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
        return receipt
    except Exception:
        _rollback(token)
        raise


def remove_created_character(receipt):
    obj = bpy.data.objects.get(receipt["object_name"])
    collection = bpy.data.collections.get(receipt["collection_name"])
    if obj is None or collection is None:
        return
    token = obj.get(OWNER_KEY)
    if not token or collection.get(OWNER_KEY) != token:
        raise RuntimeError("character ownership cannot be verified; refusing cleanup")
    _rollback(token)


def revise_character_copy(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent character revision")
    validated = validate_revision_request(request)
    data = validated["request"]
    scene = bpy.data.scenes.get(data["scene_name"])
    source_collection = bpy.data.collections.get(data["source_collection_name"])
    source_object = bpy.data.objects.get(data["source_object_name"])
    if scene is None or source_collection is None or source_object is None:
        raise ValueError("scene, source collection and source object must exist")
    if (source_object.type != "MESH"
            or source_collection.objects.get(source_object.name) is not source_object):
        raise ValueError("source object must be a Mesh directly contained in source collection")
    source_mesh = source_object.data
    source_token = source_object.get(OWNER_KEY)
    if (not source_token or source_collection.get(OWNER_KEY) != source_token
            or source_mesh.get(OWNER_KEY) != source_token):
        raise ValueError("source must be a GameAssetAI-owned character")
    if source_object.get(SCHEMA_KEY) != "gameassetai.character-base-request.v5":
        raise ValueError("revision v1 requires a Creation v5 character")
    if source_object.modifiers or source_object.vertex_groups or source_mesh.shape_keys is not None:
        raise ValueError("revision v1 requires an unrigged source without modifiers, vertex groups or Shape Keys")
    for database, name, label in (
        (bpy.data.collections, data["collection_name"], "collection_name"),
        (bpy.data.objects, data["object_name"], "object_name"),
        (bpy.data.meshes, data["mesh_name"], "mesh_name"),
    ):
        if database.get(name):
            raise ValueError(f"{label} is already in use: {name}")

    source_topology = _mesh_topology_sha256(source_mesh)
    source_uv = _mesh_uv_sha256(source_mesh)
    source_coordinates = [vertex.co.copy() for vertex in source_mesh.vertices]
    source_materials = tuple(source_mesh.materials)
    token = uuid.uuid4().hex
    try:
        collection = _tag(bpy.data.collections.new(data["collection_name"]), token)
        scene.collection.children.link(collection)
        mesh = source_mesh.copy()
        _tag(mesh, token)
        mesh.name = data["mesh_name"]
        obj = source_object.copy()
        _tag(obj, token)
        obj.data = mesh
        obj.name = data["object_name"]
        obj.animation_data_clear()
        collection.objects.link(obj)
        application = _apply_region_controls(mesh, data["regional_adjustments"])

        if _mesh_topology_sha256(mesh) != source_topology:
            raise RuntimeError("character revision changed topology")
        if _mesh_uv_sha256(mesh) != source_uv:
            raise RuntimeError("character revision changed UV coordinates")
        if tuple(mesh.materials) != source_materials:
            raise RuntimeError("character revision changed Material references")
        if any((vertex.co - original).length > 1.0e-12 for vertex, original in zip(source_mesh.vertices, source_coordinates)):
            raise RuntimeError("character revision modified source Mesh coordinates")
        for index in application["unaffected_indices"]:
            if (mesh.vertices[index].co - source_coordinates[index]).length > 1.0e-12:
                raise RuntimeError("character revision changed an untouched vertex")

        request_json = _canonical(data)
        obj["gameassetai_character_revision_request"] = request_json
        obj[SCHEMA_KEY] = data["schema"]
        mesh[SCHEMA_KEY] = data["schema"]
        collection[SCHEMA_KEY] = data["schema"]
        for datablock in (obj, mesh, collection):
            datablock[ART_DIRECTION_KEY] = source_object.get(ART_DIRECTION_KEY, "{}")
            datablock["gameassetai_character_revision_source"] = source_object.name
        triangles = sum(max(0, len(polygon.vertices) - 2) for polygon in mesh.polygons)
        receipt = {
            "status": "revised",
            "character_name": data["character_name"],
            "collection_name": collection.name,
            "object_name": obj.name,
            "mesh_name": mesh.name,
            "source_collection_name": source_collection.name,
            "source_object_name": source_object.name,
            "request_sha256": validated["request_sha256"],
            "topology_sha256": source_topology,
            "uv_sha256": source_uv,
            "vertices": len(mesh.vertices),
            "polygons": len(mesh.polygons),
            "triangles": triangles,
            "material_names": [material.name for material in mesh.materials],
            "regional_application": {
                key: value for key, value in application.items()
                if key not in {"changed_indices", "unchanged_indices", "unaffected_indices", "untouched_indices"}
            },
            "source_preserved": True,
            "uv_preserved": True,
            "topology_preserved": True,
            "materials_shared_read_only": True,
            "rigged": False,
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
        return receipt
    except Exception:
        _rollback(token)
        raise

# Retained bounded Blender capability; product support remains evidence-scoped.
