import hashlib
import json
import math
from pathlib import Path


SCHEMAS = {
    "gameassetai.character-base-request.v1",
    "gameassetai.character-base-request.v2",
    "gameassetai.character-base-request.v3",
    "gameassetai.character-base-request.v4",
    "gameassetai.character-base-request.v5",
}
REVISION_SCHEMAS = {"gameassetai.character-base-revision-request.v1"}
POSES = {"A_POSE", "T_POSE"}
MATERIAL_KEYS = ("skin", "primary", "secondary", "boots")
REGION_LIMITS = {
    "head_scale": (0.85, 1.35),
    "head_width_scale": (0.8, 1.35),
    "head_depth_scale": (0.8, 1.3),
    "torso_width_scale": (0.8, 1.25),
    "arm_length_scale": (0.75, 1.15),
    "arm_thickness_scale": (0.75, 1.25),
    "leg_length_scale": (0.85, 1.15),
    "hand_scale": (0.8, 1.4),
    "foot_scale": (0.8, 1.4),
}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _number(value, label, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number")
    value = float(value)
    if not low <= value <= high:
        raise ValueError(f"{label} must be in [{low}, {high}]")
    return value


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    schema = request.get("schema")
    expected = {"schema", "scene_name", "character_name", "collection_name", "object_name", "mesh_name", "pose", "proportions", "colors", "policy"}
    if schema in {"gameassetai.character-base-request.v2", "gameassetai.character-base-request.v3", "gameassetai.character-base-request.v4", "gameassetai.character-base-request.v5"}:
        expected.add("topology_mode")
    if schema in {"gameassetai.character-base-request.v4", "gameassetai.character-base-request.v5"}:
        expected.add("template")
    if schema == "gameassetai.character-base-request.v5":
        expected.update({"art_direction", "regions"})
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if schema not in SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(SCHEMAS)}")
    if schema.endswith(".v2") and request["topology_mode"] not in {"VOLUME_ISLANDS", "VOXEL_CONNECTED"}:
        raise ValueError("topology_mode must be VOLUME_ISLANDS or VOXEL_CONNECTED")
    if schema.endswith(".v2") and request["topology_mode"] == "VOXEL_CONNECTED":
        raise ValueError("VOXEL_CONNECTED is suspended after unintended humanoid limb/foot fusion")
    if schema.endswith(".v3") and request["topology_mode"] != "BOOLEAN_CONNECTED":
        raise ValueError("v3 topology_mode must be BOOLEAN_CONNECTED")
    if schema in {"gameassetai.character-base-request.v4", "gameassetai.character-base-request.v5"} and request["topology_mode"] != "DEFORMATION_TEMPLATE":
        raise ValueError("v4/v5 topology_mode must be DEFORMATION_TEMPLATE")
    for key in ("scene_name", "character_name", "collection_name", "object_name", "mesh_name"):
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    if len({request[k].casefold() for k in ("collection_name", "object_name", "mesh_name")}) != 3:
        raise ValueError("collection_name, object_name and mesh_name must be distinct")
    if request["pose"] not in POSES:
        raise ValueError(f"pose must be one of {sorted(POSES)}")
    if schema in {"gameassetai.character-base-request.v4", "gameassetai.character-base-request.v5"} and request["pose"] != "A_POSE":
        raise ValueError("v4/v5 template creation currently requires A_POSE")

    if schema in {"gameassetai.character-base-request.v4", "gameassetai.character-base-request.v5"}:
        template = request["template"]
        template_fields = {
            "source_file", "source_sha256", "mesh_name", "source_name",
            "source_version", "license", "front_axis",
        }
        if not isinstance(template, dict) or set(template) != template_fields:
            raise ValueError(f"template fields must be exactly {sorted(template_fields)}")
        source_file = template["source_file"]
        if not isinstance(source_file, str) or not Path(source_file).is_absolute() or Path(source_file).suffix.casefold() != ".blend":
            raise ValueError("template.source_file must be an absolute .blend path")
        digest = template["source_sha256"]
        if (not isinstance(digest, str) or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)):
            raise ValueError("template.source_sha256 must be a lowercase SHA-256")
        for key in ("mesh_name", "source_name", "source_version"):
            value = template[key]
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise ValueError(f"template.{key} must be a non-empty string up to 128 characters")
        if template["license"] != "CC0-1.0":
            raise ValueError("v4 currently accepts only an explicitly identified CC0-1.0 template")
        if template["front_axis"] != "-Y":
            raise ValueError("template.front_axis must be -Y")

    if schema == "gameassetai.character-base-request.v5":
        regions = request["regions"]
        if not isinstance(regions, dict) or set(regions) != set(REGION_LIMITS):
            raise ValueError(f"regions fields must be exactly {sorted(REGION_LIMITS)}")
        for key, limits in REGION_LIMITS.items():
            regions[key] = _number(regions[key], f"regions.{key}", *limits)

        art = request["art_direction"]
        art_fields = {"style_family", "silhouette", "shape_language", "palette", "polygon_budget", "provenance", "unsupported"}
        if not isinstance(art, dict) or set(art) != art_fields:
            raise ValueError(f"art_direction fields must be exactly {sorted(art_fields)}")
        if art["style_family"] not in {"STYLIZED_LOW_POLY_SD", "CUSTOM"}:
            raise ValueError("art_direction.style_family must be STYLIZED_LOW_POLY_SD or CUSTOM")
        for key in ("silhouette", "shape_language"):
            if not isinstance(art[key], str) or not art[key].strip() or len(art[key]) > 256:
                raise ValueError(f"art_direction.{key} must be a non-empty string up to 256 characters")
        palette = art["palette"]
        if not isinstance(palette, list) or not 2 <= len(palette) <= 8:
            raise ValueError("art_direction.palette must contain 2 to 8 RGBA colors")
        for index, color in enumerate(palette):
            if not isinstance(color, list) or len(color) != 4:
                raise ValueError(f"art_direction.palette[{index}] must be RGBA")
            palette[index] = [_number(value, f"art_direction.palette[{index}]", 0.0, 1.0) for value in color]
            if palette[index][3] != 1.0:
                raise ValueError("art_direction palette must be opaque")
        art["polygon_budget"] = int(_number(art["polygon_budget"], "art_direction.polygon_budget", 10000, 100000))
        provenance = art["provenance"]
        if not isinstance(provenance, dict) or set(provenance) != {"source", "source_ref", "profile_sha256"}:
            raise ValueError("art_direction.provenance fields must be source, source_ref and profile_sha256")
        if provenance["source"] not in {"USER_REQUEST", "WORKSPACE_PROFILE", "USER_AND_PROFILE"}:
            raise ValueError("art_direction.provenance.source is unsupported")
        if not isinstance(provenance["source_ref"], str) or not provenance["source_ref"].strip():
            raise ValueError("art_direction.provenance.source_ref must be non-empty")
        digest = provenance["profile_sha256"]
        if digest is not None and (not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("art_direction.provenance.profile_sha256 must be null or lowercase SHA-256")
        if not isinstance(art["unsupported"], list) or any(not isinstance(item, str) or not item.strip() for item in art["unsupported"]):
            raise ValueError("art_direction.unsupported must be a list of non-empty strings")

    proportions = request["proportions"]
    fields = {"height", "shoulder_width_ratio", "hip_width_ratio", "body_depth_ratio", "limb_thickness_ratio", "head_height_ratio"}
    if not isinstance(proportions, dict) or set(proportions) != fields:
        raise ValueError(f"proportions fields must be exactly {sorted(fields)}")
    proportions["height"] = _number(proportions["height"], "height", 0.5, 4.0)
    proportions["shoulder_width_ratio"] = _number(proportions["shoulder_width_ratio"], "shoulder_width_ratio", 0.18, 0.42)
    proportions["hip_width_ratio"] = _number(proportions["hip_width_ratio"], "hip_width_ratio", 0.12, 0.32)
    proportions["body_depth_ratio"] = _number(proportions["body_depth_ratio"], "body_depth_ratio", 0.08, 0.25)
    proportions["limb_thickness_ratio"] = _number(proportions["limb_thickness_ratio"], "limb_thickness_ratio", 0.025, 0.09)
    proportions["head_height_ratio"] = _number(proportions["head_height_ratio"], "head_height_ratio", 0.12, 0.22)

    colors = request["colors"]
    if not isinstance(colors, dict) or set(colors) != set(MATERIAL_KEYS):
        raise ValueError(f"colors fields must be exactly {list(MATERIAL_KEYS)}")
    for key in MATERIAL_KEYS:
        color = colors[key]
        if not isinstance(color, list) or len(color) != 4:
            raise ValueError(f"colors.{key} must be RGBA")
        colors[key] = [_number(component, f"colors.{key}", 0.0, 1.0) for component in color]
        if colors[key][3] != 1.0:
            raise ValueError("character base materials must be opaque")

    required_policy = {
        "existing_names": "REFUSE",
        "source_scene": "PRESERVE",
        "creation": "NEW_SINGLE_MESH_CHARACTER",
        "failure": "ROLL_BACK_OWNED_DATA",
        "rigging": "NOT_INCLUDED",
    }
    if request["policy"] != required_policy:
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
        "schema", "scene_name", "source_collection_name", "source_object_name",
        "character_name", "collection_name", "object_name", "mesh_name",
        "regional_adjustments", "policy",
    }
    if set(request) != expected:
        raise ValueError(f"revision request fields must be exactly {sorted(expected)}")
    if request["schema"] not in REVISION_SCHEMAS:
        raise ValueError(f"revision schema must be one of {sorted(REVISION_SCHEMAS)}")
    for key in expected - {"schema", "regional_adjustments", "policy"}:
        if not isinstance(request[key], str) or not request[key].strip() or len(request[key]) > 128:
            raise ValueError(f"{key} must be a non-empty string up to 128 characters")
    adjustments = request["regional_adjustments"]
    if not isinstance(adjustments, dict) or not adjustments or not set(adjustments) <= set(REGION_LIMITS):
        raise ValueError(f"regional_adjustments must contain supported keys from {sorted(REGION_LIMITS)}")
    changed = False
    for key in list(adjustments):
        adjustments[key] = _number(adjustments[key], f"regional_adjustments.{key}", *REGION_LIMITS[key])
        changed = changed or abs(adjustments[key] - 1.0) > 1.0e-8
    if not changed:
        raise ValueError("regional_adjustments must include at least one non-identity value")
    required_policy = {
        "existing_names": "REFUSE",
        "source": "PRESERVE",
        "revision": "NEW_COLLECTION_OBJECT_MESH_SHARED_MATERIALS_PRESERVE_UV_TOPOLOGY",
        "failure": "ROLL_BACK_OWNED_DATA",
        "rigging": "NOT_INCLUDED",
    }
    if request["policy"] != required_policy:
        raise ValueError(f"policy must be exactly {required_policy}")
    normalized = json.loads(_canonical(request))
    return {
        "status": "ready",
        "request": normalized,
        "request_sha256": hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest(),
    }

