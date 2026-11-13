import hashlib
import json
import math
import re
from pathlib import Path


CREATE_SCHEMAS = {
    "gameassetai.static-asset-assembly-request.v1",
    "gameassetai.static-asset-assembly-request.v2",
    "gameassetai.static-asset-assembly-request.v3",
    "gameassetai.static-asset-assembly-request.v4",
    "gameassetai.static-asset-assembly-request.v5",
}
REVISION_SCHEMAS = {
    "gameassetai.static-asset-revision-request.v1",
    "gameassetai.static-asset-revision-request.v2",
    "gameassetai.static-asset-revision-request.v3",
    "gameassetai.static-asset-revision-request.v4",
}
KILN_IMPORT_SCHEMA = "gameassetai.kiln-glb-import-request.v1"
EXTERNAL_REVISION_SCHEMA = "gameassetai.external-static-revision-request.v1"
PRIMITIVES = {"BOX", "CYLINDER", "ICOSPHERE", "WEDGE"}
GEOMETRY_KINDS = {"PRIMITIVE", "PROFILE_EXTRUSION", "PROFILE_BEVELED_EXTRUSION"}
STYLE_FAMILIES = {"STYLIZED_LOW_POLY", "CUSTOM"}
SURFACE_STYLES = {"ANGULAR_LOW_POLY", "PAINTED_LOOK_STYLIZED", "CUSTOM"}
TEXTURE_PATTERNS = {"WOOD_GRAIN", "PAINTED_METAL"}
UV_ROTATIONS = {0, 90, 180, 270}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PROFILE_RELATIVE_EPSILON = 1e-7


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _finite_vector(value, length, label, *, positive=False):
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{label} must contain exactly {length} numbers")
    result = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
            raise ValueError(f"{label} must contain finite numbers")
        if positive and item <= 0:
            raise ValueError(f"{label} values must be greater than zero")
        result.append(float(item))
    return result


def _name(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 128:
        raise ValueError(f"{label} must be a non-empty string up to 128 characters")
    return value


def _profile_points(value, label):
    if not isinstance(value, list) or not 3 <= len(value) <= 32:
        raise ValueError(f"{label} must contain 3 to 32 [x, z] points")
    points = [_finite_vector(point, 2, f"{label}[{index}]") for index, point in enumerate(value)]
    span = max(
        max(point[0] for point in points) - min(point[0] for point in points),
        max(point[1] for point in points) - min(point[1] for point in points),
    )
    tolerance = max(1e-9, span * PROFILE_RELATIVE_EPSILON)

    def distance_squared(a, b):
        return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

    for first in range(len(points)):
        for second in range(first + 1, len(points)):
            if distance_squared(points[first], points[second]) <= tolerance ** 2:
                raise ValueError(f"{label} must not reuse or nearly duplicate a vertex")
    if any(
        distance_squared(points[index], points[(index + 1) % len(points)]) <= tolerance ** 2
        for index in range(len(points))
    ):
        raise ValueError(f"{label} must not contain zero-length or unstable edges")
    area2 = sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )
    if area2 <= max(1e-12, tolerance * tolerance):
        raise ValueError(f"{label} must be counter-clockwise with non-zero area")

    def orientation(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    for index in range(len(points)):
        previous = points[index - 1]
        current = points[index]
        following = points[(index + 1) % len(points)]
        incoming = (current[0] - previous[0], current[1] - previous[1])
        outgoing = (following[0] - current[0], following[1] - current[1])
        if (
            abs(orientation(previous, current, following)) <= tolerance
            and incoming[0] * outgoing[0] + incoming[1] * outgoing[1] <= 0
        ):
            raise ValueError(f"{label} must not backtrack or overlap at a vertex")

    def sign(value):
        if value > tolerance:
            return 1
        if value < -tolerance:
            return -1
        return 0

    def on_segment(a, b, point):
        return (
            abs(orientation(a, b, point)) <= tolerance
            and min(a[0], b[0]) - tolerance <= point[0] <= max(a[0], b[0]) + tolerance
            and min(a[1], b[1]) - tolerance <= point[1] <= max(a[1], b[1]) + tolerance
        )

    def intersects_or_touches(a, b, c, d):
        first_c = sign(orientation(a, b, c))
        first_d = sign(orientation(a, b, d))
        second_a = sign(orientation(c, d, a))
        second_b = sign(orientation(c, d, b))
        if first_c * first_d < 0 and second_a * second_b < 0:
            return True
        return (
            (first_c == 0 and on_segment(a, b, c))
            or (first_d == 0 and on_segment(a, b, d))
            or (second_a == 0 and on_segment(c, d, a))
            or (second_b == 0 and on_segment(c, d, b))
        )

    count = len(points)
    for first in range(count):
        a, b = points[first], points[(first + 1) % count]
        for second in range(first + 1, count):
            if second in {first, (first + 1) % count} or (second + 1) % count == first:
                continue
            c, d = points[second], points[(second + 1) % count]
            if intersects_or_touches(a, b, c, d):
                raise ValueError(f"{label} must not self-intersect, self-touch, or overlap")
    return points


def _orientation_2d(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_on_segment_2d(point, a, b, tolerance):
    return (
        abs(_orientation_2d(a, b, point)) <= tolerance
        and min(a[0], b[0]) - tolerance <= point[0] <= max(a[0], b[0]) + tolerance
        and min(a[1], b[1]) - tolerance <= point[1] <= max(a[1], b[1]) + tolerance
    )


def _segments_intersect_or_touch_2d(a, b, c, d, tolerance):
    values = (
        _orientation_2d(a, b, c), _orientation_2d(a, b, d),
        _orientation_2d(c, d, a), _orientation_2d(c, d, b),
    )
    signs = tuple(1 if value > tolerance else -1 if value < -tolerance else 0 for value in values)
    if signs[0] * signs[1] < 0 and signs[2] * signs[3] < 0:
        return True
    return (
        (signs[0] == 0 and _point_on_segment_2d(c, a, b, tolerance))
        or (signs[1] == 0 and _point_on_segment_2d(d, a, b, tolerance))
        or (signs[2] == 0 and _point_on_segment_2d(a, c, d, tolerance))
        or (signs[3] == 0 and _point_on_segment_2d(b, c, d, tolerance))
    )


def _point_profile_location(point, profile, tolerance):
    inside = False
    for index, first in enumerate(profile):
        second = profile[(index + 1) % len(profile)]
        if _point_on_segment_2d(point, first, second, tolerance):
            return "boundary"
        if ((first[1] > point[1]) != (second[1] > point[1])):
            crossing_x = first[0] + (point[1] - first[1]) * (second[0] - first[0]) / (second[1] - first[1])
            if crossing_x > point[0]:
                inside = not inside
    return "inside" if inside else "outside"


def _validate_profile_correspondence(outer, core, label):
    count = len(outer)
    span = max(
        max(point[0] for point in outer) - min(point[0] for point in outer),
        max(point[1] for point in outer) - min(point[1] for point in outer),
    )
    tolerance = max(1e-9, span * PROFILE_RELATIVE_EPSILON)
    if any(_point_profile_location(point, outer, tolerance) != "inside" for point in core):
        raise ValueError(f"{label} core profile points must lie strictly inside the outer profile")

    def cost(offset):
        return sum(
            (outer[index][0] - core[(index + offset) % count][0]) ** 2
            + (outer[index][1] - core[(index + offset) % count][1]) ** 2
            for index in range(count)
        )

    current_cost = cost(0)
    best_cost = min(cost(offset) for offset in range(count))
    if current_cost > best_cost + max(tolerance * tolerance * count, best_cost * 1e-9):
        raise ValueError(f"{label} outer/core indices do not use the nearest cyclic correspondence")

    connectors = list(zip(outer, core))
    if any(math.dist(first, second) <= tolerance for first, second in connectors):
        raise ValueError(f"{label} bevel width is numerically unstable")
    for first in range(count):
        for second in range(first + 1, count):
            if _segments_intersect_or_touch_2d(*connectors[first], *connectors[second], tolerance):
                raise ValueError(f"{label} outer/core connector segments must not cross or touch")

    for index in range(count):
        core_edge = (core[index], core[(index + 1) % count])
        for outer_index in range(count):
            outer_edge = (outer[outer_index], outer[(outer_index + 1) % count])
            if _segments_intersect_or_touch_2d(*core_edge, *outer_edge, tolerance):
                raise ValueError(f"{label} core edges must remain inside the outer profile")
        connector = connectors[index]
        for outer_index in range(count):
            if outer_index in {index, (index - 1) % count}:
                continue
            outer_edge = (outer[outer_index], outer[(outer_index + 1) % count])
            if _segments_intersect_or_touch_2d(*connector, *outer_edge, tolerance):
                raise ValueError(f"{label} connector crosses the outer profile")
        for core_index in range(count):
            if core_index in {index, (index - 1) % count}:
                continue
            core_edge = (core[core_index], core[(core_index + 1) % count])
            if _segments_intersect_or_touch_2d(*connector, *core_edge, tolerance):
                raise ValueError(f"{label} connector crosses the core profile")


def _geometry(value, label, *, allow_beveled=False):
    allowed = GEOMETRY_KINDS if allow_beveled else GEOMETRY_KINDS - {"PROFILE_BEVELED_EXTRUSION"}
    if not isinstance(value, dict) or value.get("kind") not in allowed:
        raise ValueError(f"{label}.kind must be one of {sorted(allowed)}")
    if value["kind"] == "PRIMITIVE":
        if set(value) != {"kind", "primitive", "dimensions", "segments"}:
            raise ValueError(f"{label} PRIMITIVE fields are invalid")
        if value["primitive"] not in PRIMITIVES:
            raise ValueError(f"{label}.primitive must be one of {sorted(PRIMITIVES)}")
        value["dimensions"] = _finite_vector(value["dimensions"], 3, f"{label}.dimensions", positive=True)
        segments = value["segments"]
        if value["primitive"] in {"BOX", "WEDGE"}:
            if segments is not None:
                raise ValueError(f"{label} BOX/WEDGE segments must be null")
        elif isinstance(segments, bool) or not isinstance(segments, int) or not 3 <= segments <= 64:
            raise ValueError(f"{label} CYLINDER/ICOSPHERE segments must be an integer from 3 to 64")
    elif value["kind"] == "PROFILE_EXTRUSION":
        if set(value) != {"kind", "profile_points", "depth"}:
            raise ValueError(f"{label} PROFILE_EXTRUSION fields are invalid")
        value["profile_points"] = _profile_points(value["profile_points"], f"{label}.profile_points")
        depth = value["depth"]
        if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not math.isfinite(depth) or depth <= 0:
            raise ValueError(f"{label}.depth must be a finite number greater than zero")
        value["depth"] = float(depth)
    else:
        fields = {"kind", "outer_profile_points", "core_profile_points", "depth"}
        if set(value) != fields:
            raise ValueError(f"{label} PROFILE_BEVELED_EXTRUSION fields are invalid")
        outer = _profile_points(value["outer_profile_points"], f"{label}.outer_profile_points")
        core = _profile_points(value["core_profile_points"], f"{label}.core_profile_points")
        if len(outer) != len(core):
            raise ValueError(f"{label} outer and core profiles must have the same point count")
        if all(math.dist(first, second) <= 1e-9 for first, second in zip(outer, core)):
            raise ValueError(f"{label} core profile must differ from the outer profile")
        _validate_profile_correspondence(outer, core, label)
        depth = value["depth"]
        if isinstance(depth, bool) or not isinstance(depth, (int, float)) or not math.isfinite(depth) or depth <= 0:
            raise ValueError(f"{label}.depth must be a finite number greater than zero")
        value["outer_profile_points"] = outer
        value["core_profile_points"] = core
        value["depth"] = float(depth)
    return value


def _style(value, material_count):
    fields = {
        "family", "shape_language", "silhouette_strategy", "shading",
        "material_strategy", "max_materials", "triangle_budget",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"style fields must be exactly {sorted(fields)}")
    if value["family"] not in STYLE_FAMILIES:
        raise ValueError(f"style.family must be one of {sorted(STYLE_FAMILIES)}")
    _name(value["shape_language"], "style.shape_language")
    if value["silhouette_strategy"] != "EXPLICIT_PART_GEOMETRY":
        raise ValueError("style.silhouette_strategy must be EXPLICIT_PART_GEOMETRY")
    if value["shading"] != "FLAT":
        raise ValueError("static v3 currently supports FLAT shading only")
    if value["material_strategy"] != "DECLARED_LIMITED":
        raise ValueError("style.material_strategy must be DECLARED_LIMITED")
    maximum = value["max_materials"]
    if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 16:
        raise ValueError("style.max_materials must be an integer from 1 to 16")
    if material_count > maximum:
        raise ValueError("declared materials exceed style.max_materials")
    budget = value["triangle_budget"]
    if isinstance(budget, bool) or not isinstance(budget, int) or not 4 <= budget <= 100000:
        raise ValueError("style.triangle_budget must be an integer from 4 to 100000")
    return value


def _art_direction(value):
    fields = {
        "provenance", "surface_style", "silhouette", "proportion",
        "geometry_detail", "palette", "unsupported",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"art_direction fields must be exactly {sorted(fields)}")
    provenance = value["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"source", "source_ref", "profile_sha256"}:
        raise ValueError("art_direction.provenance fields are invalid")
    if provenance["source"] not in {"USER_REQUEST", "WORKSPACE_PROFILE"}:
        raise ValueError("art_direction.provenance.source is invalid")
    _name(provenance["source_ref"], "art_direction.provenance.source_ref")
    profile_sha = provenance["profile_sha256"]
    if provenance["source"] == "WORKSPACE_PROFILE":
        if not isinstance(profile_sha, str) or not SHA256_PATTERN.fullmatch(profile_sha):
            raise ValueError("Workspace Profile art direction requires profile_sha256")
    elif profile_sha is not None:
        raise ValueError("USER_REQUEST art direction profile_sha256 must be null")
    if value["surface_style"] not in SURFACE_STYLES:
        raise ValueError(f"art_direction.surface_style must be one of {sorted(SURFACE_STYLES)}")
    for key in ("silhouette", "proportion", "geometry_detail"):
        _name(value[key], f"art_direction.{key}")
    palette = value["palette"]
    if not isinstance(palette, list) or not 2 <= len(palette) <= 8:
        raise ValueError("art_direction.palette must contain 2 to 8 RGBA colors")
    value["palette"] = [
        _finite_vector(color, 4, f"art_direction.palette[{index}]")
        for index, color in enumerate(palette)
    ]
    if any(component < 0 or component > 1 for color in value["palette"] for component in color):
        raise ValueError("art_direction.palette components must be in [0, 1]")
    if not isinstance(value["unsupported"], list) or any(
        not isinstance(item, str) or not item.strip() for item in value["unsupported"]
    ):
        raise ValueError("art_direction.unsupported must contain non-empty strings")
    return value


def _appearance(value):
    fields = {
        "uv_policy", "texture_policy", "texture_output_directory",
        "max_texture_resolution", "max_texture_bytes", "pack_images",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"appearance fields must be exactly {sorted(fields)}")
    if value["uv_policy"] != "LOCAL_BOX_PROJECT":
        raise ValueError("appearance.uv_policy must be LOCAL_BOX_PROJECT")
    if value["texture_policy"] != "OPTIONAL_GENERATED_PNG":
        raise ValueError("appearance.texture_policy must be OPTIONAL_GENERATED_PNG")
    directory = value["texture_output_directory"]
    if not isinstance(directory, str) or not Path(directory).is_absolute():
        raise ValueError("appearance.texture_output_directory must be absolute")
    resolution = value["max_texture_resolution"]
    if isinstance(resolution, bool) or not isinstance(resolution, int) or resolution not in {32, 64, 128, 256, 512}:
        raise ValueError("appearance.max_texture_resolution must be 32, 64, 128, 256 or 512")
    byte_budget = value["max_texture_bytes"]
    if isinstance(byte_budget, bool) or not isinstance(byte_budget, int) or not 1024 <= byte_budget <= 16 * 1024 * 1024:
        raise ValueError("appearance.max_texture_bytes must be an integer from 1024 to 16777216")
    if value["pack_images"] is not True:
        raise ValueError("appearance.pack_images must be true")
    return value


def _texture(value, label, appearance):
    if value is None:
        return None
    fields = {"kind", "image_name", "file_name", "resolution", "palette", "scale", "seed"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields must be exactly {sorted(fields)}")
    if value["kind"] not in TEXTURE_PATTERNS:
        raise ValueError(f"{label}.kind must be one of {sorted(TEXTURE_PATTERNS)}")
    _name(value["image_name"], f"{label}.image_name")
    file_name = value["file_name"]
    if (not isinstance(file_name, str) or not file_name or Path(file_name).name != file_name
            or Path(file_name).suffix.casefold() != ".png"):
        raise ValueError(f"{label}.file_name must be a plain PNG file name")
    resolution = value["resolution"]
    if (isinstance(resolution, bool) or not isinstance(resolution, int)
            or resolution not in {32, 64, 128, 256, 512}
            or resolution > appearance["max_texture_resolution"]):
        raise ValueError(f"{label}.resolution exceeds the allowed texture resolution")
    palette = value["palette"]
    if not isinstance(palette, list) or not 2 <= len(palette) <= 4:
        raise ValueError(f"{label}.palette must contain 2 to 4 RGBA colors")
    value["palette"] = [_finite_vector(color, 4, f"{label}.palette[{index}]") for index, color in enumerate(palette)]
    if any(component < 0 or component > 1 for color in value["palette"] for component in color):
        raise ValueError(f"{label}.palette components must be in [0, 1]")
    scale = value["scale"]
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or not math.isfinite(scale) or not 1 <= scale <= 32:
        raise ValueError(f"{label}.scale must be a finite number from 1 to 32")
    value["scale"] = float(scale)
    seed = value["seed"]
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= 2147483647:
        raise ValueError(f"{label}.seed must be an integer from 0 to 2147483647")
    return value


def _uv_mapping(value, label):
    fields = {"rotation_degrees", "mirror_u", "mirror_v"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} fields must be exactly {sorted(fields)}")
    if isinstance(value["rotation_degrees"], bool) or value["rotation_degrees"] not in UV_ROTATIONS:
        raise ValueError(f"{label}.rotation_degrees must be one of {sorted(UV_ROTATIONS)}")
    for key in ("mirror_u", "mirror_v"):
        if not isinstance(value[key], bool):
            raise ValueError(f"{label}.{key} must be boolean")
    return value


def _estimated_triangles(geometry):
    if geometry["kind"] == "PROFILE_EXTRUSION":
        return 4 * len(geometry["profile_points"]) - 4
    if geometry["kind"] == "PROFILE_BEVELED_EXTRUSION":
        return 6 * len(geometry["outer_profile_points"]) - 4
    primitive = geometry["primitive"]
    if primitive == "BOX":
        return 12
    if primitive == "WEDGE":
        return 8
    if primitive == "CYLINDER":
        return 4 * geometry["segments"] - 4
    return 20 if geometry["segments"] <= 12 else 80


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = {"schema", "scene_name", "asset_name", "collection_name", "materials", "parts", "policy"}
    if request.get("schema") in {
        "gameassetai.static-asset-assembly-request.v3",
        "gameassetai.static-asset-assembly-request.v4",
        "gameassetai.static-asset-assembly-request.v5",
    }:
        expected.add("style")
    if request.get("schema") == "gameassetai.static-asset-assembly-request.v5":
        expected.update({"art_direction", "appearance"})
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in CREATE_SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(CREATE_SCHEMAS)}")
    for key in ("scene_name", "asset_name", "collection_name"):
        _name(request[key], key)

    is_v5 = request["schema"] == "gameassetai.static-asset-assembly-request.v5"
    if is_v5:
        request["art_direction"] = _art_direction(request["art_direction"])
        request["appearance"] = _appearance(request["appearance"])
    materials = request["materials"]
    if not isinstance(materials, list) or not 1 <= len(materials) <= 16:
        raise ValueError("materials must contain 1 to 16 entries")
    material_names = set()
    for index, material in enumerate(materials):
        material_fields = {"name", "base_color", "metallic", "roughness"}
        if is_v5:
            material_fields.update({"material_role", "texture"})
        if not isinstance(material, dict) or set(material) != material_fields:
            raise ValueError(f"materials[{index}] has invalid fields")
        name = material["name"]
        if not isinstance(name, str) or not name.strip() or name.casefold() in material_names:
            raise ValueError("material names must be non-empty and case-insensitively unique")
        material_names.add(name.casefold())
        material["base_color"] = _finite_vector(material["base_color"], 4, f"materials[{index}].base_color")
        if any(component < 0 or component > 1 for component in material["base_color"]):
            raise ValueError("base_color components must be in [0, 1]")
        for key in ("metallic", "roughness"):
            value = material[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"materials[{index}].{key} must be in [0, 1]")
            material[key] = float(value)
        if is_v5:
            _name(material["material_role"], f"materials[{index}].material_role")
            material["texture"] = _texture(
                material["texture"], f"materials[{index}].texture", request["appearance"]
            )

    if is_v5:
        texture_specs = [material["texture"] for material in materials if material["texture"] is not None]
        image_names = [item["image_name"].casefold() for item in texture_specs]
        file_names = [item["file_name"].casefold() for item in texture_specs]
        if len(image_names) != len(set(image_names)) or len(file_names) != len(set(file_names)):
            raise ValueError("texture image names and file names must each be unique")
        if request["art_direction"]["surface_style"] == "PAINTED_LOOK_STYLIZED" and not texture_specs:
            raise ValueError("PAINTED_LOOK_STYLIZED requires at least one generated texture")

    parts = request["parts"]
    if not isinstance(parts, list) or not 1 <= len(parts) <= 64:
        raise ValueError("parts must contain 1 to 64 entries")
    part_names = set()
    semantic_roles = set()
    estimated_triangles = 0
    for index, part in enumerate(parts):
        if request["schema"] in {
            "gameassetai.static-asset-assembly-request.v3",
            "gameassetai.static-asset-assembly-request.v4",
            "gameassetai.static-asset-assembly-request.v5",
        }:
            fields = {"name", "semantic_role", "geometry", "location", "rotation_degrees", "material"}
        else:
            fields = {"name", "primitive", "dimensions", "location", "rotation_degrees", "material", "segments"}
            if request["schema"].endswith(".v2"):
                fields.add("semantic_role")
        if not isinstance(part, dict):
            raise ValueError(f"parts[{index}] has invalid fields")
        if is_v5:
            if not fields.issubset(part) or set(part) - (fields | {"uv_mapping"}):
                raise ValueError(f"parts[{index}] has invalid fields")
            part["uv_mapping"] = _uv_mapping(
                part.get("uv_mapping", {"rotation_degrees": 0, "mirror_u": False, "mirror_v": False}),
                f"parts[{index}].uv_mapping",
            )
        elif set(part) != fields:
            raise ValueError(f"parts[{index}] has invalid fields")
        name = part["name"]
        if not isinstance(name, str) or not name.strip() or name.casefold() in part_names:
            raise ValueError("part names must be non-empty and case-insensitively unique")
        part_names.add(name.casefold())
        if "semantic_role" in part:
            role = _name(part["semantic_role"], f"parts[{index}].semantic_role")
            if role.casefold() in semantic_roles:
                raise ValueError("semantic roles must be case-insensitively unique")
            semantic_roles.add(role.casefold())
        if "geometry" in part:
            part["geometry"] = _geometry(
                part["geometry"], f"parts[{index}].geometry",
                allow_beveled=request["schema"].endswith((".v4", ".v5")),
            )
            estimated_triangles += _estimated_triangles(part["geometry"])
        else:
            if part["primitive"] not in PRIMITIVES:
                raise ValueError(f"parts[{index}].primitive must be one of {sorted(PRIMITIVES)}")
            part["dimensions"] = _finite_vector(part["dimensions"], 3, f"parts[{index}].dimensions", positive=True)
        part["location"] = _finite_vector(part["location"], 3, f"parts[{index}].location")
        part["rotation_degrees"] = _finite_vector(part["rotation_degrees"], 3, f"parts[{index}].rotation_degrees")
        if not isinstance(part["material"], str) or part["material"].casefold() not in material_names:
            raise ValueError(f"parts[{index}].material must name a declared material")
        if "geometry" not in part:
            segments = part["segments"]
            if part["primitive"] in {"BOX", "WEDGE"}:
                if segments is not None:
                    raise ValueError("BOX/WEDGE segments must be null")
            elif isinstance(segments, bool) or not isinstance(segments, int) or not 3 <= segments <= 64:
                raise ValueError("CYLINDER/ICOSPHERE segments must be an integer from 3 to 64")

    if request["schema"] in {
        "gameassetai.static-asset-assembly-request.v3",
        "gameassetai.static-asset-assembly-request.v4",
        "gameassetai.static-asset-assembly-request.v5",
    }:
        request["style"] = _style(request["style"], len(materials))
        if estimated_triangles > request["style"]["triangle_budget"]:
            raise ValueError(
                f"estimated triangles {estimated_triangles} exceed style.triangle_budget "
                f"{request['style']['triangle_budget']}"
            )

    policy = request["policy"]
    required_policy = (
        {
            "existing_names": "REFUSE",
            "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS_IMAGES",
            "external_files": "NO_OVERWRITE_OWNED_PNG",
            "failure": "ROLL_BACK_OWNED_DATA_AND_FILES",
        }
        if is_v5 else
        {
            "existing_names": "REFUSE",
            "source_scene": "PRESERVE",
            "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        }
    )
    if policy != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")

    normalized = json.loads(_canonical(request))
    return {
        "status": "ready",
        "request": normalized,
        "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest(),
    }


def validate_revision_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = {
        "schema", "scene_name", "source_collection_name", "asset_name", "collection_name",
        "revisions", "policy",
    }
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in REVISION_SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(REVISION_SCHEMAS)}")
    for key in ("scene_name", "source_collection_name", "asset_name", "collection_name"):
        _name(request[key], key)
    if request["source_collection_name"] == request["collection_name"]:
        raise ValueError("source_collection_name and collection_name must differ")

    revisions = request["revisions"]
    if not isinstance(revisions, list) or not 1 <= len(revisions) <= 64:
        raise ValueError("revisions must contain 1 to 64 entries")
    roles = set()
    for index, revision in enumerate(revisions):
        fields = {"semantic_role", "dimensions", "location", "rotation_degrees"}
        if request["schema"].endswith((".v2", ".v3", ".v4")):
            fields = {"semantic_role", "geometry", "location", "rotation_degrees"}
        if not isinstance(revision, dict) or set(revision) != fields:
            raise ValueError(f"revisions[{index}] has invalid fields")
        role = _name(revision["semantic_role"], f"revisions[{index}].semantic_role")
        if role.casefold() in roles:
            raise ValueError("revision semantic roles must be case-insensitively unique")
        roles.add(role.casefold())
        changed = False
        if "geometry" in revision and revision["geometry"] is not None:
            revision["geometry"] = _geometry(
                revision["geometry"], f"revisions[{index}].geometry",
                allow_beveled=request["schema"].endswith((".v3", ".v4")),
            )
            changed = True
        vector_fields = (("location", False), ("rotation_degrees", False))
        if "dimensions" in revision:
            vector_fields = (("dimensions", True), *vector_fields)
        for key, positive in vector_fields:
            value = revision[key]
            if value is not None:
                revision[key] = _finite_vector(value, 3, f"revisions[{index}].{key}", positive=positive)
                changed = True
        if not changed:
            raise ValueError(f"revisions[{index}] must change at least one transform field")

    required_policy = (
        {
            "existing_names": "REFUSE",
            "source": "PRESERVE",
            "revision": "NEW_COLLECTION_OBJECTS_MESHES_REGENERATED_UV_SHARED_MATERIALS_IMAGES",
            "failure": "ROLL_BACK_OWNED_DATA",
        }
        if request["schema"].endswith(".v4") else
        {
            "existing_names": "REFUSE",
            "source": "PRESERVE",
            "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
            "failure": "ROLL_BACK_OWNED_DATA",
        }
    )
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")

    normalized = json.loads(_canonical(request))
    return {
        "status": "ready",
        "request": normalized,
        "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest(),
    }


def validate_kiln_import_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = {
        "schema", "scene_name", "asset_name", "collection_name", "source_file",
        "source_sha256", "part_roles", "provenance", "policy",
    }
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] != KILN_IMPORT_SCHEMA:
        raise ValueError(f"schema must be {KILN_IMPORT_SCHEMA}")
    for key in ("scene_name", "asset_name", "collection_name"):
        _name(request[key], key)

    source = request["source_file"]
    if not isinstance(source, str) or not Path(source).is_absolute() or Path(source).suffix.casefold() != ".glb":
        raise ValueError("source_file must be an absolute .glb path")
    if not isinstance(request["source_sha256"], str) or not SHA256_PATTERN.fullmatch(request["source_sha256"]):
        raise ValueError("source_sha256 must be a lowercase SHA-256")

    mappings = request["part_roles"]
    if not isinstance(mappings, list) or not 1 <= len(mappings) <= 128:
        raise ValueError("part_roles must contain 1 to 128 entries")
    object_names = set()
    semantic_roles = set()
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict) or set(mapping) != {"object_name", "semantic_role"}:
            raise ValueError(f"part_roles[{index}] has invalid fields")
        object_name = _name(mapping["object_name"], f"part_roles[{index}].object_name")
        semantic_role = _name(mapping["semantic_role"], f"part_roles[{index}].semantic_role")
        if object_name.casefold() in object_names:
            raise ValueError("part object names must be case-insensitively unique")
        if semantic_role.casefold() in semantic_roles:
            raise ValueError("semantic roles must be case-insensitively unique")
        object_names.add(object_name.casefold())
        semantic_roles.add(semantic_role.casefold())

    provenance = request["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"producer", "version", "program_ref"}:
        raise ValueError("provenance fields must be producer, version and program_ref")
    if provenance["producer"] != "Kiln":
        raise ValueError("provenance.producer must be Kiln")
    _name(provenance["version"], "provenance.version")
    if provenance["program_ref"] is not None:
        _name(provenance["program_ref"], "provenance.program_ref")

    required_policy = {
        "existing_names": "REFUSE",
        "source_file": "READ_ONLY",
        "import": "NEW_COLLECTION_OWNED_DATA",
        "failure": "ROLL_BACK_IMPORT_DELTA",
    }
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")

    normalized = json.loads(_canonical(request))
    return {
        "status": "ready",
        "request": normalized,
        "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest(),
    }


def validate_external_revision_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = {
        "schema", "scene_name", "asset_name", "source_collection_name", "collection_name",
        "source_file", "source_sha256", "part_roles", "revisions", "provenance", "policy",
    }
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] != EXTERNAL_REVISION_SCHEMA:
        raise ValueError(f"schema must be {EXTERNAL_REVISION_SCHEMA}")
    for key in ("scene_name", "asset_name", "source_collection_name", "collection_name"):
        _name(request[key], key)
    if request["source_collection_name"] == request["collection_name"]:
        raise ValueError("source_collection_name and collection_name must differ")
    source = request["source_file"]
    if not isinstance(source, str) or not Path(source).is_absolute() or Path(source).suffix.casefold() != ".glb":
        raise ValueError("source_file must be an absolute .glb path")
    if not isinstance(request["source_sha256"], str) or not SHA256_PATTERN.fullmatch(request["source_sha256"]):
        raise ValueError("source_sha256 must be a lowercase SHA-256")

    mappings = request["part_roles"]
    if not isinstance(mappings, list) or not 1 <= len(mappings) <= 128:
        raise ValueError("part_roles must contain 1 to 128 entries")
    object_names, semantic_roles = set(), set()
    for index, mapping in enumerate(mappings):
        if not isinstance(mapping, dict) or set(mapping) != {"object_name", "semantic_role"}:
            raise ValueError(f"part_roles[{index}] has invalid fields")
        object_name = _name(mapping["object_name"], f"part_roles[{index}].object_name")
        role = _name(mapping["semantic_role"], f"part_roles[{index}].semantic_role")
        if object_name.casefold() in object_names or role.casefold() in semantic_roles:
            raise ValueError("part object names and semantic roles must each be case-insensitively unique")
        object_names.add(object_name.casefold())
        semantic_roles.add(role.casefold())

    revisions = request["revisions"]
    if not isinstance(revisions, list) or not 1 <= len(revisions) <= len(mappings):
        raise ValueError("revisions must contain 1 entry up to the mapped part count")
    revised_roles = set()
    for index, revision in enumerate(revisions):
        fields = {"semantic_role", "operation", "axis", "side", "threshold", "delta"}
        if not isinstance(revision, dict) or set(revision) != fields:
            raise ValueError(f"revisions[{index}] has invalid fields")
        role = _name(revision["semantic_role"], f"revisions[{index}].semantic_role")
        if role.casefold() not in semantic_roles:
            raise ValueError(f"revisions[{index}].semantic_role is not mapped")
        if role.casefold() in revised_roles:
            raise ValueError("revision semantic roles must be case-insensitively unique")
        revised_roles.add(role.casefold())
        if revision["operation"] != "LOCAL_AXIS_END_OFFSET":
            raise ValueError("external revision operation must be LOCAL_AXIS_END_OFFSET")
        if revision["axis"] not in {"X", "Y", "Z"} or revision["side"] not in {"MIN", "MAX"}:
            raise ValueError("external revision axis/side must be X/Y/Z and MIN/MAX")
        for key in ("threshold", "delta"):
            value = revision[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"revisions[{index}].{key} must be a finite number")
            revision[key] = float(value)
        if revision["delta"] == 0:
            raise ValueError(f"revisions[{index}].delta must be non-zero")

    provenance = request["provenance"]
    if not isinstance(provenance, dict) or set(provenance) != {"producer", "version", "source_ref", "license"}:
        raise ValueError("provenance fields must be producer, version, source_ref and license")
    for key in ("producer", "version", "source_ref", "license"):
        _name(provenance[key], f"provenance.{key}")

    required_policy = {
        "existing_names": "REFUSE", "source_file": "READ_ONLY",
        "import": "NEW_COLLECTION_OWNED_SOURCE",
        "revision": "NEW_COLLECTION_INDEPENDENT_MESHES_SHARED_MATERIALS",
        "failure": "ROLL_BACK_OPERATION_DELTA",
    }
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")
    normalized = json.loads(_canonical(request))
    return {"status": "ready", "request": normalized,
            "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    args = parser.parse_args()
    payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if payload.get("schema") in REVISION_SCHEMAS:
        validator = validate_revision_request
    elif payload.get("schema") == KILN_IMPORT_SCHEMA:
        validator = validate_kiln_import_request
    elif payload.get("schema") == EXTERNAL_REVISION_SCHEMA:
        validator = validate_external_revision_request
    else:
        validator = validate_request
    print(json.dumps(validator(payload), indent=2, ensure_ascii=False))
# Retained bounded Blender capability; product support remains evidence-scoped.
