import hashlib
import json
import math
import uuid
from pathlib import Path

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

from validate_static_asset_assembly_request import (
    validate_external_revision_request,
    validate_kiln_import_request,
    validate_request,
    validate_revision_request,
)


OWNER_KEY = "gameassetai_creation_owner"
ROLE_KEY = "gameassetai_semantic_role"
ASSEMBLY_SCHEMA_KEY = "gameassetai_static_assembly_schema"
GEOMETRY_SPEC_KEY = "gameassetai_geometry_spec"
STYLE_SPEC_KEY = "gameassetai_style_spec"
IMPORT_OWNER_KEY = "gameassetai_kiln_import_owner"
PROVENANCE_KIND_KEY = "gameassetai_source_kind"
PROVENANCE_SHA_KEY = "gameassetai_source_sha256"
PROVENANCE_VERSION_KEY = "gameassetai_kiln_version"
PROVENANCE_PROGRAM_KEY = "gameassetai_kiln_program_ref"
EXTERNAL_SOURCE_OWNER_KEY = "gameassetai_external_source_owner"
EXTERNAL_RESULT_OWNER_KEY = "gameassetai_external_revision_owner"
EXTERNAL_SOURCE_SHA_KEY = "gameassetai_external_source_sha256"


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _tag(data_block, token):
    data_block[OWNER_KEY] = token
    return data_block


def _geometry_for_part(part):
    if "geometry" in part:
        return part["geometry"]
    return {
        "kind": "PRIMITIVE",
        "primitive": part["primitive"],
        "dimensions": part["dimensions"],
        "segments": part["segments"],
    }


def _make_profile_extrusion(mesh, geometry):
    points = geometry["profile_points"]
    half_depth = geometry["depth"] * 0.5
    count = len(points)
    vertices = [(x, -half_depth, z) for x, z in points]
    vertices.extend((x, half_depth, z) for x, z in points)
    faces = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, count + index, count + following, following))
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return _profile_mesh_quality(mesh, geometry)


def _make_profile_beveled_extrusion(mesh, geometry):
    outer = geometry["outer_profile_points"]
    core = geometry["core_profile_points"]
    half_depth = geometry["depth"] * 0.5
    count = len(outer)
    vertices = [(x, -half_depth, z) for x, z in core]
    vertices.extend((x, 0.0, z) for x, z in outer)
    vertices.extend((x, half_depth, z) for x, z in core)
    faces = [tuple(range(count)), tuple(reversed(range(count * 2, count * 3)))]
    for index in range(count):
        following = (index + 1) % count
        faces.append((index, count + index, count + following, following))
        faces.append((count + index, count * 2 + index, count * 2 + following, count + following))
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return _beveled_profile_mesh_quality(mesh, geometry)


def _profile_mesh_quality(mesh, geometry):
    points = geometry["profile_points"]
    count = len(points)
    mesh.calc_loop_triangles()
    if len(mesh.vertices) != count * 2 or len(mesh.polygons) != count + 2:
        raise ValueError("PROFILE_EXTRUSION topology does not match its geometry specification")
    if len(mesh.loop_triangles) != 4 * count - 4:
        raise ValueError("PROFILE_EXTRUSION triangle count does not match its geometry specification")
    if any(polygon.area <= 1e-12 for polygon in mesh.polygons):
        raise ValueError("PROFILE_EXTRUSION contains a zero-area face")
    coordinates = [tuple(round(component, 12) for component in vertex.co) for vertex in mesh.vertices]
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("PROFILE_EXTRUSION contains duplicate 3D vertices")
    if mesh.polygons[0].normal.y >= -0.999999 or mesh.polygons[1].normal.y <= 0.999999:
        raise ValueError("PROFILE_EXTRUSION cap normals are inconsistent")
    for index, polygon in enumerate(mesh.polygons[2:]):
        following = (index + 1) % count
        dx = points[following][0] - points[index][0]
        dz = points[following][1] - points[index][1]
        expected = Vector((dz, 0.0, -dx)).normalized()
        if polygon.normal.dot(expected) <= 0.999999:
            raise ValueError("PROFILE_EXTRUSION side normals are inconsistent")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if any(not edge.is_manifold for edge in bm.edges):
        bm.free()
        raise ValueError("PROFILE_EXTRUSION must be a closed manifold Mesh")
    signed_volume = bm.calc_volume(signed=True)
    bm.free()
    area2 = sum(
        points[index][0] * points[(index + 1) % count][1]
        - points[(index + 1) % count][0] * points[index][1]
        for index in range(count)
    )
    expected_volume = area2 * 0.5 * geometry["depth"]
    tolerance = max(1e-9, expected_volume * 1e-6)
    if signed_volume <= 0 or abs(signed_volume - expected_volume) > tolerance:
        raise ValueError("PROFILE_EXTRUSION signed volume is inconsistent")
    return {
        "closed_manifold": True,
        "normals_outward": True,
        "zero_area_faces": 0,
        "duplicate_vertices": 0,
        "signed_volume": float(signed_volume),
        "triangles": len(mesh.loop_triangles),
    }


def _beveled_profile_mesh_quality(mesh, geometry):
    outer = geometry["outer_profile_points"]
    count = len(outer)
    mesh.calc_loop_triangles()
    if len(mesh.vertices) != count * 3 or len(mesh.polygons) != count * 2 + 2:
        raise ValueError("PROFILE_BEVELED_EXTRUSION topology does not match its geometry specification")
    if len(mesh.loop_triangles) != 6 * count - 4:
        raise ValueError("PROFILE_BEVELED_EXTRUSION triangle count does not match its geometry specification")
    if any(polygon.area <= 1e-12 for polygon in mesh.polygons):
        raise ValueError("PROFILE_BEVELED_EXTRUSION contains a zero-area face")
    coordinates = [tuple(round(component, 12) for component in vertex.co) for vertex in mesh.vertices]
    if len(set(coordinates)) != len(coordinates):
        raise ValueError("PROFILE_BEVELED_EXTRUSION contains duplicate 3D vertices")
    if mesh.polygons[0].normal.y >= -0.999999 or mesh.polygons[1].normal.y <= 0.999999:
        raise ValueError("PROFILE_BEVELED_EXTRUSION cap normals are inconsistent")
    for index in range(count):
        following = (index + 1) % count
        dx = outer[following][0] - outer[index][0]
        dz = outer[following][1] - outer[index][1]
        expected = Vector((dz, 0.0, -dx)).normalized()
        for polygon in (mesh.polygons[2 + index * 2], mesh.polygons[3 + index * 2]):
            if polygon.normal.dot(expected) <= 0:
                raise ValueError("PROFILE_BEVELED_EXTRUSION band normals are inconsistent")
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if any(not edge.is_manifold for edge in bm.edges):
        bm.free()
        raise ValueError("PROFILE_BEVELED_EXTRUSION must be a closed manifold Mesh")
    signed_volume = bm.calc_volume(signed=True)
    bm.free()
    if signed_volume <= 1e-12:
        raise ValueError("PROFILE_BEVELED_EXTRUSION signed volume must be positive")
    return {
        "closed_manifold": True,
        "normals_outward": True,
        "zero_area_faces": 0,
        "duplicate_vertices": 0,
        "signed_volume": float(signed_volume),
        "triangles": len(mesh.loop_triangles),
    }


def _make_mesh(part, token):
    mesh = _tag(bpy.data.meshes.new(part["name"] + " Mesh"), token)
    geometry = _geometry_for_part(part)
    mesh[GEOMETRY_SPEC_KEY] = _canonical(geometry)
    if geometry["kind"] == "PROFILE_EXTRUSION":
        quality = _make_profile_extrusion(mesh, geometry)
        mesh["gameassetai_profile_mesh_quality"] = _canonical(quality)
        return mesh
    if geometry["kind"] == "PROFILE_BEVELED_EXTRUSION":
        quality = _make_profile_beveled_extrusion(mesh, geometry)
        mesh["gameassetai_profile_mesh_quality"] = _canonical(quality)
        return mesh
    dimensions = Vector(geometry["dimensions"])
    if geometry["primitive"] == "WEDGE":
        vertices = [
            (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
            (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5),
            (0.0, -0.5, 0.5), (0.0, 0.5, 0.5),
        ]
        vertices = [(x * dimensions.x, y * dimensions.y, z * dimensions.z) for x, y, z in vertices]
        faces = [(0, 1, 3, 2), (0, 4, 5, 2), (1, 3, 5, 4), (0, 1, 4), (2, 5, 3)]
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        return mesh
    bm = bmesh.new()
    if geometry["primitive"] == "BOX":
        result = bmesh.ops.create_cube(bm, size=1.0)
        verts = result["verts"]
    elif geometry["primitive"] == "CYLINDER":
        result = bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=geometry["segments"],
            radius1=1.0,
            radius2=1.0,
            depth=1.0,
        )
        verts = result["verts"]
        dimensions = Vector((dimensions.x * 0.5, dimensions.y * 0.5, dimensions.z))
    else:
        subdivisions = 1 if geometry["segments"] <= 12 else 2
        result = bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
        verts = result["verts"]
        dimensions *= 0.5
    bmesh.ops.transform(bm, verts=verts, matrix=Matrix.Diagonal((*dimensions, 1.0)))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    return mesh


def _make_material(spec, token):
    material = _tag(bpy.data.materials.new(spec["name"]), token)
    material.diffuse_color = spec["base_color"]
    material.use_nodes = True
    principled = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    principled.inputs["Base Color"].default_value = spec["base_color"]
    principled.inputs["Metallic"].default_value = spec["metallic"]
    principled.inputs["Roughness"].default_value = spec["roughness"]
    return material


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
    for collection in list(bpy.data.collections):
        if collection.get(OWNER_KEY) == token:
            bpy.data.collections.remove(collection)


def create_asset(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent asset creation")
    validated = validate_request(request)
    normalized = validated["request"]
    scene = bpy.data.scenes.get(normalized["scene_name"])
    if scene is None:
        raise ValueError(f"Scene does not exist: {normalized['scene_name']}")
    if bpy.data.collections.get(normalized["collection_name"]):
        raise ValueError("collection_name is already in use")
    occupied_objects = [part["name"] for part in normalized["parts"] if bpy.data.objects.get(part["name"])]
    occupied_meshes = [part["name"] + " Mesh" for part in normalized["parts"] if bpy.data.meshes.get(part["name"] + " Mesh")]
    occupied_materials = [spec["name"] for spec in normalized["materials"] if bpy.data.materials.get(spec["name"])]
    if occupied_objects or occupied_meshes or occupied_materials:
        raise ValueError(f"requested names are occupied: {occupied_objects + occupied_meshes + occupied_materials}")

    token = uuid.uuid4().hex
    created = {"objects": [], "meshes": [], "materials": [], "collection": normalized["collection_name"]}
    try:
        collection = _tag(bpy.data.collections.new(normalized["collection_name"]), token)
        collection[ASSEMBLY_SCHEMA_KEY] = normalized["schema"]
        if "style" in normalized:
            collection[STYLE_SPEC_KEY] = _canonical(normalized["style"])
        scene.collection.children.link(collection)
        materials = {}
        for spec in normalized["materials"]:
            material = _make_material(spec, token)
            materials[spec["name"].casefold()] = material
            created["materials"].append(material.name)

        for part in normalized["parts"]:
            mesh = _make_mesh(part, token)
            obj = _tag(bpy.data.objects.new(part["name"], mesh), token)
            if "semantic_role" in part:
                obj[ROLE_KEY] = part["semantic_role"]
            obj.location = part["location"]
            obj.rotation_euler = Euler(tuple(math.radians(value) for value in part["rotation_degrees"]), "XYZ")
            obj.data.materials.append(materials[part["material"].casefold()])
            if "style" in normalized:
                for polygon in obj.data.polygons:
                    polygon.use_smooth = normalized["style"]["shading"] != "FLAT"
            collection.objects.link(obj)
            created["objects"].append(obj.name)
            created["meshes"].append(mesh.name)

        facts = []
        for object_name in created["objects"]:
            obj = bpy.data.objects[object_name]
            obj.data.calc_loop_triangles()
            facts.append({
                "name": obj.name,
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "triangles": len(obj.data.loop_triangles),
                "material": obj.data.materials[0].name,
                "location": [float(v) for v in obj.location],
                "semantic_role": obj.get(ROLE_KEY),
                "geometry_kind": json.loads(obj.data[GEOMETRY_SPEC_KEY])["kind"],
                "mesh_quality": (
                    json.loads(obj.data["gameassetai_profile_mesh_quality"])
                    if obj.data.get("gameassetai_profile_mesh_quality") is not None else None
                ),
            })
        triangle_count = sum(item["triangles"] for item in facts)
        if "style" in normalized and triangle_count > normalized["style"]["triangle_budget"]:
            raise ValueError(
                f"actual triangles {triangle_count} exceed style.triangle_budget "
                f"{normalized['style']['triangle_budget']}"
            )
        receipt = {
            "status": "created",
            "asset_name": normalized["asset_name"],
            "collection_name": collection.name,
            "request_sha256": validated["request_sha256"],
            "parts": facts,
            "style": normalized.get("style"),
            "triangle_count": triangle_count,
            "source_scene_preserved": True,
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
        return receipt
    except Exception:
        _rollback(token)
        raise


def _mesh_dimensions(mesh):
    coordinates = [vertex.co for vertex in mesh.vertices]
    minimum = Vector((min(value.x for value in coordinates), min(value.y for value in coordinates), min(value.z for value in coordinates)))
    maximum = Vector((max(value.x for value in coordinates), max(value.y for value in coordinates), max(value.z for value in coordinates)))
    return maximum - minimum


def _duplicate_part(source, object_name, mesh_name, token):
    mesh = source.data.copy()
    mesh.name = mesh_name
    _tag(mesh, token)
    obj = source.copy()
    obj.name = object_name
    obj.data = mesh
    _tag(obj, token)
    return obj


def _replacement_part(source, object_name, mesh_name, geometry, token):
    part = {"name": object_name, "geometry": geometry}
    mesh = _make_mesh(part, token)
    mesh.name = mesh_name
    for material in source.data.materials:
        mesh.materials.append(material)
    obj = source.copy()
    obj.name = object_name
    obj.data = mesh
    _tag(obj, token)
    return obj


def revise_asset_copy(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent asset revision")
    validated = validate_revision_request(request)
    normalized = validated["request"]
    scene = bpy.data.scenes.get(normalized["scene_name"])
    source = bpy.data.collections.get(normalized["source_collection_name"])
    if scene is None:
        raise ValueError(f"Scene does not exist: {normalized['scene_name']}")
    if source is None or source.get(OWNER_KEY) is None:
        raise ValueError("source collection is missing or is not an owned GameAssetAI assembly")
    if not source.objects:
        raise ValueError("source collection is empty")
    source_token = source.get(OWNER_KEY)
    geometry_revision = normalized["schema"].endswith((".v2", ".v3"))
    required_source_schema = {
        "gameassetai.static-asset-revision-request.v2": "gameassetai.static-asset-assembly-request.v3",
        "gameassetai.static-asset-revision-request.v3": "gameassetai.static-asset-assembly-request.v4",
    }.get(normalized["schema"])
    if required_source_schema and source.get(ASSEMBLY_SCHEMA_KEY) != required_source_schema:
        raise ValueError(
            f"{normalized['schema']} requires an owned {required_source_schema} source"
        )
    role_objects = {}
    for obj in source.objects:
        role = obj.get(ROLE_KEY)
        if obj.type != "MESH" or obj.get(OWNER_KEY) != source_token or not role:
            raise ValueError("source must contain only owned semantic Mesh parts created by schema v2")
        if geometry_revision and obj.data.get(GEOMETRY_SPEC_KEY) is None:
            raise ValueError("geometry revision requires complete source geometry metadata")
        folded = role.casefold()
        if folded in role_objects:
            raise ValueError("source semantic roles are ambiguous")
        role_objects[folded] = obj
    revisions = {item["semantic_role"].casefold(): item for item in normalized["revisions"]}
    missing = sorted(role for role in revisions if role not in role_objects)
    if missing:
        raise ValueError(f"revision roles do not exist in source: {missing}")
    if bpy.data.collections.get(normalized["collection_name"]):
        raise ValueError("collection_name is already in use")

    names = []
    for obj in source.objects:
        role = obj.get(ROLE_KEY)
        names.append((f"{normalized['asset_name']} {role}", f"{normalized['asset_name']} {role} Mesh"))
    occupied = []
    for object_name, mesh_name in names:
        if bpy.data.objects.get(object_name):
            occupied.append(object_name)
        if bpy.data.meshes.get(mesh_name):
            occupied.append(mesh_name)
    if occupied:
        raise ValueError(f"requested names are occupied: {occupied}")

    token = uuid.uuid4().hex
    try:
        collection = _tag(bpy.data.collections.new(normalized["collection_name"]), token)
        collection[ASSEMBLY_SCHEMA_KEY] = source.get(ASSEMBLY_SCHEMA_KEY, "gameassetai.static-asset-assembly-request.v2")
        if source.get(STYLE_SPEC_KEY) is not None:
            collection[STYLE_SPEC_KEY] = source[STYLE_SPEC_KEY]
        scene.collection.children.link(collection)
        facts = []
        for source_obj, (object_name, mesh_name) in zip(source.objects, names):
            revision = revisions.get(source_obj[ROLE_KEY].casefold())
            replacement_geometry = revision.get("geometry") if revision is not None else None
            obj = (
                _replacement_part(source_obj, object_name, mesh_name, replacement_geometry, token)
                if replacement_geometry is not None
                else _duplicate_part(source_obj, object_name, mesh_name, token)
            )
            revision = revisions.get(obj[ROLE_KEY].casefold())
            if revision is not None:
                if "dimensions" in revision and revision["dimensions"] is not None:
                    current = _mesh_dimensions(obj.data)
                    if min(current) <= 0:
                        raise ValueError(f"source role has a zero local dimension: {obj[ROLE_KEY]}")
                    requested = Vector(revision["dimensions"])
                    scale = Vector((requested.x / current.x, requested.y / current.y, requested.z / current.z))
                    obj.data.transform(Matrix.Diagonal((*scale, 1.0)))
                    obj.data.update()
                if revision["location"] is not None:
                    obj.location = revision["location"]
                if revision["rotation_degrees"] is not None:
                    obj.rotation_euler = Euler(tuple(math.radians(value) for value in revision["rotation_degrees"]), "XYZ")
            collection.objects.link(obj)
            obj.data.calc_loop_triangles()
            facts.append({
                "name": obj.name,
                "semantic_role": obj[ROLE_KEY],
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "triangles": len(obj.data.loop_triangles),
                "dimensions": [float(value) for value in _mesh_dimensions(obj.data)],
                "location": [float(value) for value in obj.location],
                "source_object": source_obj.name,
                "geometry_kind": json.loads(obj.data[GEOMETRY_SPEC_KEY])["kind"],
                "geometry_replaced": replacement_geometry is not None,
                "mesh_quality": (
                    json.loads(obj.data["gameassetai_profile_mesh_quality"])
                    if obj.data.get("gameassetai_profile_mesh_quality") is not None else None
                ),
            })
        style = json.loads(source[STYLE_SPEC_KEY]) if source.get(STYLE_SPEC_KEY) is not None else None
        triangle_count = sum(item["triangles"] for item in facts)
        if style is not None and triangle_count > style["triangle_budget"]:
            raise ValueError(
                f"revised triangles {triangle_count} exceed source style.triangle_budget "
                f"{style['triangle_budget']}"
            )
        receipt = {
            "status": "created",
            "operation": "copy_geometry_revision" if geometry_revision else "copy_revision",
            "asset_name": normalized["asset_name"],
            "source_collection_name": source.name,
            "collection_name": collection.name,
            "request_sha256": validated["request_sha256"],
            "revised_roles": [item["semantic_role"] for item in normalized["revisions"]],
            "parts": facts,
            "style": style,
            "triangle_count": triangle_count,
            "source_preserved": True,
            "shared_materials": True,
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
        return receipt
    except Exception:
        _rollback(token)
        raise


def remove_created_asset(receipt):
    collection = bpy.data.collections.get(receipt["collection_name"])
    if collection is None:
        return
    tokens = {obj.get(OWNER_KEY) for obj in collection.objects}
    tokens.discard(None)
    if len(tokens) != 1 or collection.get(OWNER_KEY) not in tokens:
        raise RuntimeError("asset ownership cannot be verified; refusing cleanup")
    _rollback(tokens.pop())


_IMPORT_DATASETS = (
    "objects", "meshes", "materials", "images", "collections", "cameras", "lights",
    "armatures", "actions", "curves",
)


def _snapshot_import_data():
    return {
        name: {block.as_pointer() for block in getattr(bpy.data, name)}
        for name in _IMPORT_DATASETS
    }


def _import_delta(before):
    return {
        name: [block for block in getattr(bpy.data, name) if block.as_pointer() not in before[name]]
        for name in _IMPORT_DATASETS
    }


def _rollback_import_delta(before):
    delta = _import_delta(before)
    for obj in list(delta["objects"]):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(delta["collections"]):
        bpy.data.collections.remove(collection)
    for name in ("meshes", "materials", "images", "cameras", "lights", "armatures", "actions", "curves"):
        dataset = getattr(bpy.data, name)
        for block in list(delta[name]):
            if block.users == 0:
                dataset.remove(block)


def _restore_context(selected, active, active_layer_collection):
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in selected:
        if obj.name in bpy.context.view_layer.objects:
            obj.select_set(True)
    if active is not None and active.name in bpy.context.view_layer.objects:
        bpy.context.view_layer.objects.active = active
    else:
        bpy.context.view_layer.objects.active = None
    if active_layer_collection is not None:
        bpy.context.view_layer.active_layer_collection = active_layer_collection


def _tag_import(block, token, request):
    block[IMPORT_OWNER_KEY] = token
    block[PROVENANCE_KIND_KEY] = "KILN_GLB"
    block[PROVENANCE_SHA_KEY] = request["source_sha256"]
    block[PROVENANCE_VERSION_KEY] = request["provenance"]["version"]
    if request["provenance"]["program_ref"] is not None:
        block[PROVENANCE_PROGRAM_KEY] = request["provenance"]["program_ref"]


def import_kiln_glb(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent GLB import")
    validated = validate_kiln_import_request(request)
    normalized = validated["request"]
    scene = bpy.data.scenes.get(normalized["scene_name"])
    if scene is None:
        raise ValueError(f"Scene does not exist: {normalized['scene_name']}")
    if scene != bpy.context.scene:
        raise ValueError("scene_name must identify the active Blender Scene")
    source = Path(normalized["source_file"])
    if not source.is_file() or source.is_symlink():
        raise ValueError("source_file must be an existing regular, non-symbolic GLB file")
    actual_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_sha != normalized["source_sha256"]:
        raise ValueError(f"source SHA-256 mismatch: expected {normalized['source_sha256']}, got {actual_sha}")
    if bpy.data.collections.get(normalized["collection_name"]):
        raise ValueError("collection_name is already in use")
    occupied = [item["object_name"] for item in normalized["part_roles"] if bpy.data.objects.get(item["object_name"])]
    if occupied:
        raise ValueError(f"mapped object names are occupied: {occupied}")

    before = _snapshot_import_data()
    before_names = {name: {block.name for block in getattr(bpy.data, name)} for name in _IMPORT_DATASETS}
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    active_layer_collection = bpy.context.view_layer.active_layer_collection
    token = uuid.uuid4().hex
    try:
        collection = bpy.data.collections.new(normalized["collection_name"])
        scene.collection.children.link(collection)
        layer_collection = bpy.context.view_layer.layer_collection.children.get(collection.name)
        if layer_collection is None:
            raise RuntimeError("target collection is not available in the active View Layer")
        bpy.context.view_layer.active_layer_collection = layer_collection
        result = bpy.ops.import_scene.gltf(filepath=str(source))
        if "FINISHED" not in result:
            raise RuntimeError(f"Blender glTF importer did not finish: {sorted(result)}")

        delta = _import_delta(before)
        imported_objects = delta["objects"]
        meshes = [obj for obj in imported_objects if obj.type == "MESH"]
        unsupported = sorted(obj.name for obj in imported_objects if obj.type not in {"MESH", "EMPTY"})
        if unsupported or delta["cameras"] or delta["lights"] or delta["armatures"] or delta["actions"]:
            raise ValueError(f"GLB contains unsupported non-static data: {unsupported}")
        if not meshes:
            raise ValueError("GLB did not create any Mesh objects")

        for data_kind in ("objects", "meshes", "materials"):
            for block in delta[data_kind]:
                head, separator, suffix = block.name.rpartition(".")
                if separator and len(suffix) == 3 and suffix.isdigit() and head in before_names[data_kind]:
                    raise ValueError(f"import name collision: {data_kind[:-1]} {head}")

        role_map = {item["object_name"]: item["semantic_role"] for item in normalized["part_roles"]}
        imported_names = {obj.name for obj in meshes}
        missing = sorted(set(role_map) - imported_names)
        unmapped = sorted(imported_names - set(role_map))
        if missing or unmapped:
            raise ValueError(f"part role mapping must cover every imported Mesh; missing={missing}, unmapped={unmapped}")

        for obj in imported_objects:
            for owner in list(obj.users_collection):
                if owner != collection:
                    owner.objects.unlink(obj)
            if collection.objects.get(obj.name) is None:
                collection.objects.link(obj)
        for extra in list(delta["collections"]):
            if extra != collection and extra.users == 0:
                bpy.data.collections.remove(extra)

        delta = _import_delta(before)
        for name in _IMPORT_DATASETS:
            for block in delta[name]:
                _tag_import(block, token, normalized)
        for obj in meshes:
            obj[ROLE_KEY] = role_map[obj.name]

        parts = []
        for obj in sorted(meshes, key=lambda value: value.name.casefold()):
            parts.append({
                "name": obj.name,
                "semantic_role": obj[ROLE_KEY],
                "mesh": obj.data.name,
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "materials": [slot.name for slot in obj.data.materials],
            })
        created = {
            name: sorted(block.name for block in delta[name])
            for name in _IMPORT_DATASETS
            if delta[name]
        }
        receipt = {
            "status": "created",
            "operation": "kiln_glb_import",
            "asset_name": normalized["asset_name"],
            "collection_name": collection.name,
            "source_file": str(source),
            "source_sha256": actual_sha,
            "provenance": normalized["provenance"],
            "request_sha256": validated["request_sha256"],
            "parts": parts,
            "created": created,
            "source_file_preserved": True,
            "existing_scene_data_preserved": True,
            "native_revision_compatibility": "NOT_VALIDATED",
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode("utf-8")).hexdigest()
        return receipt
    except Exception:
        _rollback_import_delta(before)
        raise
    finally:
        _restore_context(selected, active, active_layer_collection)


def remove_imported_asset(receipt):
    collection = bpy.data.collections.get(receipt["collection_name"])
    if collection is None:
        return
    token = collection.get(IMPORT_OWNER_KEY)
    if not token or any(obj.get(IMPORT_OWNER_KEY) != token for obj in collection.objects):
        raise RuntimeError("import ownership cannot be verified; refusing cleanup")
    for obj in collection.objects:
        if obj.type == "MESH":
            if obj.data.get(IMPORT_OWNER_KEY) != token:
                raise RuntimeError("import Mesh ownership cannot be verified; refusing cleanup")
            if any(material and material.get(IMPORT_OWNER_KEY) != token for material in obj.data.materials):
                raise RuntimeError("import Material ownership cannot be verified; refusing cleanup")
    for obj in list(bpy.data.objects):
        if obj.get(IMPORT_OWNER_KEY) == token:
            bpy.data.objects.remove(obj, do_unlink=True)
    for name in ("meshes", "materials", "images", "cameras", "lights", "armatures", "actions", "curves"):
        dataset = getattr(bpy.data, name)
        for block in list(dataset):
            if block.get(IMPORT_OWNER_KEY) == token and block.users == 0:
                dataset.remove(block)
    if collection.get(IMPORT_OWNER_KEY) == token:
        bpy.data.collections.remove(collection)


def _external_mesh_snapshot(obj):
    mesh = obj.data
    return {
        "object_transform": tuple(round(float(value), 10) for row in obj.matrix_local for value in row),
        "vertices": tuple(tuple(round(float(value), 10) for value in vertex.co) for vertex in mesh.vertices),
        "edges": tuple(tuple(edge.vertices) for edge in mesh.edges),
        "polygons": tuple(tuple(polygon.vertices) for polygon in mesh.polygons),
        "materials": tuple(material.name if material else None for material in mesh.materials),
        "uv_layers": tuple(
            (layer.name, tuple((round(float(loop.uv.x), 10), round(float(loop.uv.y), 10)) for loop in layer.data))
            for layer in mesh.uv_layers
        ),
    }


def _apply_external_region_revision(obj, revision):
    axis_index = {"X": 0, "Y": 1, "Z": 2}[revision["axis"]]
    threshold = revision["threshold"]
    selected = [
        vertex for vertex in obj.data.vertices
        if (vertex.co[axis_index] <= threshold if revision["side"] == "MIN" else vertex.co[axis_index] >= threshold)
    ]
    if not selected or len(selected) == len(obj.data.vertices):
        raise ValueError(f"revision region must select some but not all vertices: {obj[ROLE_KEY]}")
    for vertex in selected:
        vertex.co[axis_index] += revision["delta"]
    obj.data.update(calc_edges=True)
    if any(polygon.area <= 1e-12 for polygon in obj.data.polygons):
        raise ValueError(f"external revision created a zero-area face: {obj[ROLE_KEY]}")
    return [vertex.index for vertex in selected]


def revise_external_glb(request, *, authorized=False):
    if not authorized:
        raise ValueError("authorized=true is required for persistent external GLB revision")
    validated = validate_external_revision_request(request)
    normalized = validated["request"]
    scene = bpy.data.scenes.get(normalized["scene_name"])
    if scene is None or scene != bpy.context.scene:
        raise ValueError("scene_name must identify the active Blender Scene")
    source = Path(normalized["source_file"])
    if not source.is_file() or source.is_symlink():
        raise ValueError("source_file must be an existing regular, non-symbolic GLB file")
    source_bytes = source.read_bytes()
    actual_sha = hashlib.sha256(source_bytes).hexdigest()
    if actual_sha != normalized["source_sha256"]:
        raise ValueError(f"source SHA-256 mismatch: expected {normalized['source_sha256']}, got {actual_sha}")
    if bpy.data.collections.get(normalized["source_collection_name"]) or bpy.data.collections.get(normalized["collection_name"]):
        raise ValueError("source_collection_name and collection_name must both be unused")
    occupied_source = [item["object_name"] for item in normalized["part_roles"] if bpy.data.objects.get(item["object_name"])]
    result_names = [f"{normalized['asset_name']} {item['semantic_role']}" for item in normalized["part_roles"]]
    occupied_result = [name for name in result_names if bpy.data.objects.get(name) or bpy.data.meshes.get(name + " Mesh")]
    if occupied_source or occupied_result:
        raise ValueError(f"requested source/result names are occupied: {occupied_source + occupied_result}")

    before = _snapshot_import_data()
    before_names = {name: {block.name for block in getattr(bpy.data, name)} for name in _IMPORT_DATASETS}
    selected = list(bpy.context.selected_objects)
    active = bpy.context.view_layer.objects.active
    active_layer_collection = bpy.context.view_layer.active_layer_collection
    source_token, result_token = uuid.uuid4().hex, uuid.uuid4().hex
    try:
        source_collection = bpy.data.collections.new(normalized["source_collection_name"])
        source_collection[EXTERNAL_SOURCE_OWNER_KEY] = source_token
        source_collection[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
        scene.collection.children.link(source_collection)
        layer_collection = bpy.context.view_layer.layer_collection.children.get(source_collection.name)
        if layer_collection is None:
            raise RuntimeError("external source collection is unavailable in the active View Layer")
        bpy.context.view_layer.active_layer_collection = layer_collection
        result = bpy.ops.import_scene.gltf(filepath=str(source))
        if "FINISHED" not in result:
            raise RuntimeError(f"Blender glTF importer did not finish: {sorted(result)}")

        delta = _import_delta(before)
        imported_objects = delta["objects"]
        meshes = [obj for obj in imported_objects if obj.type == "MESH"]
        empties = [obj for obj in imported_objects if obj.type == "EMPTY"]
        unsupported = sorted(obj.name for obj in imported_objects if obj.type not in {"MESH", "EMPTY"})
        if unsupported or delta["cameras"] or delta["lights"] or delta["armatures"] or delta["actions"]:
            raise ValueError(f"GLB contains unsupported non-static data: {unsupported}")
        for data_kind in ("objects", "meshes", "materials"):
            for block in delta[data_kind]:
                head, separator, suffix = block.name.rpartition(".")
                if separator and len(suffix) == 3 and suffix.isdigit() and head in before_names[data_kind]:
                    raise ValueError(f"import name collision: {data_kind[:-1]} {head}")
        role_map = {item["object_name"]: item["semantic_role"] for item in normalized["part_roles"]}
        imported_names = {obj.name for obj in meshes}
        missing, unmapped = sorted(set(role_map) - imported_names), sorted(imported_names - set(role_map))
        if missing or unmapped:
            raise ValueError(f"part role mapping must cover every imported Mesh; missing={missing}, unmapped={unmapped}")
        imported_set = set(imported_objects)
        for obj in meshes:
            if obj.library or obj.data.library or obj.modifiers or obj.vertex_groups or obj.data.shape_keys:
                raise ValueError(f"unsupported external Mesh dependencies: {obj.name}")
            if obj.parent is not None and (obj.parent not in imported_set or obj.parent.type != "EMPTY"):
                raise ValueError(f"external Mesh parent must be an imported Empty: {obj.name}")
        for empty in empties:
            if empty.parent is not None and (empty.parent not in imported_set or empty.parent.type != "EMPTY"):
                raise ValueError(f"external Empty hierarchy is unsupported: {empty.name}")

        result_root_names = [
            f"{normalized['asset_name']} Root {index + 1}"
            for index in range(len(empties))
        ]
        occupied_roots = [name for name in result_root_names if bpy.data.objects.get(name)]
        if occupied_roots:
            raise ValueError(f"requested result root names are occupied: {occupied_roots}")

        for obj in imported_objects:
            for owner in list(obj.users_collection):
                if owner != source_collection:
                    owner.objects.unlink(obj)
            if source_collection.objects.get(obj.name) is None:
                source_collection.objects.link(obj)
            obj[EXTERNAL_SOURCE_OWNER_KEY] = source_token
            obj[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
        for extra in list(delta["collections"]):
            if extra != source_collection and extra.users == 0:
                bpy.data.collections.remove(extra)
        for obj in meshes:
            obj.data[EXTERNAL_SOURCE_OWNER_KEY] = source_token
            obj.data[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
            obj[ROLE_KEY] = role_map[obj.name]
        source_snapshots = {obj[ROLE_KEY]: _external_mesh_snapshot(obj) for obj in meshes}

        result_collection = bpy.data.collections.new(normalized["collection_name"])
        result_collection[EXTERNAL_RESULT_OWNER_KEY] = result_token
        result_collection[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
        scene.collection.children.link(result_collection)
        copies = {}
        for index, source_empty in enumerate(sorted(empties, key=lambda value: value.name.casefold())):
            copied = source_empty.copy()
            copied.name = result_root_names[index]
            if copied.name != result_root_names[index]:
                raise ValueError(f"result root name collision: {result_root_names[index]}")
            copied[EXTERNAL_RESULT_OWNER_KEY] = result_token
            result_collection.objects.link(copied)
            copies[source_empty] = copied
        result_by_role = {}
        for source_obj in sorted(meshes, key=lambda value: value.name.casefold()):
            role = source_obj[ROLE_KEY]
            copied_mesh = source_obj.data.copy()
            copied_mesh.name = f"{normalized['asset_name']} {role} Mesh"
            copied_mesh[EXTERNAL_RESULT_OWNER_KEY] = result_token
            copied_mesh[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
            copied = source_obj.copy()
            copied.name = f"{normalized['asset_name']} {role}"
            copied.data = copied_mesh
            copied[EXTERNAL_RESULT_OWNER_KEY] = result_token
            copied[EXTERNAL_SOURCE_SHA_KEY] = actual_sha
            copied[ROLE_KEY] = role
            result_collection.objects.link(copied)
            copies[source_obj] = copied
            result_by_role[role.casefold()] = copied
        for source_obj, copied in copies.items():
            copied.parent = copies.get(source_obj.parent)
            copied.matrix_parent_inverse = source_obj.matrix_parent_inverse.copy()

        revision_facts = []
        for revision in normalized["revisions"]:
            obj = result_by_role[revision["semantic_role"].casefold()]
            before_snapshot = _external_mesh_snapshot(obj)
            selected_indices = _apply_external_region_revision(obj, revision)
            after_snapshot = _external_mesh_snapshot(obj)
            if before_snapshot["vertices"] == after_snapshot["vertices"]:
                raise RuntimeError("external revision did not change Mesh vertices")
            if before_snapshot["edges"] != after_snapshot["edges"] or before_snapshot["polygons"] != after_snapshot["polygons"]:
                raise RuntimeError("external revision changed topology")
            if before_snapshot["materials"] != after_snapshot["materials"] or before_snapshot["uv_layers"] != after_snapshot["uv_layers"]:
                raise RuntimeError("external revision changed materials or UV data")
            revision_facts.append({
                "semantic_role": revision["semantic_role"], "object": obj.name,
                "operation": revision["operation"], "axis": revision["axis"], "side": revision["side"],
                "threshold": revision["threshold"], "delta": revision["delta"],
                "selected_vertex_count": len(selected_indices), "selected_vertex_indices": selected_indices,
            })

        if hashlib.sha256(source.read_bytes()).hexdigest() != actual_sha:
            raise RuntimeError("external source file changed during revision")
        for source_obj in meshes:
            if _external_mesh_snapshot(source_obj) != source_snapshots[source_obj[ROLE_KEY]]:
                raise RuntimeError(f"imported external source changed: {source_obj.name}")
        parts = []
        revised_roles = {item["semantic_role"].casefold() for item in normalized["revisions"]}
        for role, obj in sorted(result_by_role.items()):
            obj.data.calc_loop_triangles()
            parts.append({
                "semantic_role": obj[ROLE_KEY], "object": obj.name, "mesh": obj.data.name,
                "vertices": len(obj.data.vertices), "triangles": len(obj.data.loop_triangles),
                "materials": [material.name for material in obj.data.materials],
                "uv_layers": [layer.name for layer in obj.data.uv_layers],
                "modified": role in revised_roles, "independent_mesh": obj.data.users == 1,
            })
        receipt = {
            "status": "created", "operation": "external_glb_region_revision",
            "asset_name": normalized["asset_name"], "source_collection_name": source_collection.name,
            "collection_name": result_collection.name, "source_file": str(source),
            "source_sha256": actual_sha, "provenance": normalized["provenance"],
            "request_sha256": validated["request_sha256"], "parts": parts,
            "revisions": revision_facts, "source_file_preserved": True,
            "imported_source_preserved": True, "topology_preserved": True,
            "materials_preserved": True, "uv_layers_preserved": True,
            "object_transforms_preserved": True, "native_owned_revision_compatibility": "NOT_APPLICABLE",
        }
        receipt["receipt_sha256"] = hashlib.sha256(_canonical(receipt).encode()).hexdigest()
        return receipt
    except Exception:
        _rollback_import_delta(before)
        raise
    finally:
        _restore_context(selected, active, active_layer_collection)
