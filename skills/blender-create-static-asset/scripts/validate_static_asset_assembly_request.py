import hashlib
import json
import math
import re
from pathlib import Path


CREATE_SCHEMAS = {
    "gameassetai.static-asset-assembly-request.v1",
    "gameassetai.static-asset-assembly-request.v2",
}
REVISION_SCHEMA = "gameassetai.static-asset-revision-request.v1"
KILN_IMPORT_SCHEMA = "gameassetai.kiln-glb-import-request.v1"
PRIMITIVES = {"BOX", "CYLINDER", "ICOSPHERE", "WEDGE"}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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


def validate_request(request):
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    expected = {"schema", "scene_name", "asset_name", "collection_name", "materials", "parts", "policy"}
    if set(request) != expected:
        raise ValueError(f"request fields must be exactly {sorted(expected)}")
    if request["schema"] not in CREATE_SCHEMAS:
        raise ValueError(f"schema must be one of {sorted(CREATE_SCHEMAS)}")
    for key in ("scene_name", "asset_name", "collection_name"):
        _name(request[key], key)

    materials = request["materials"]
    if not isinstance(materials, list) or not 1 <= len(materials) <= 16:
        raise ValueError("materials must contain 1 to 16 entries")
    material_names = set()
    for index, material in enumerate(materials):
        if not isinstance(material, dict) or set(material) != {"name", "base_color", "metallic", "roughness"}:
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

    parts = request["parts"]
    if not isinstance(parts, list) or not 1 <= len(parts) <= 64:
        raise ValueError("parts must contain 1 to 64 entries")
    part_names = set()
    semantic_roles = set()
    for index, part in enumerate(parts):
        fields = {"name", "primitive", "dimensions", "location", "rotation_degrees", "material", "segments"}
        if request["schema"].endswith(".v2"):
            fields.add("semantic_role")
        if not isinstance(part, dict) or set(part) != fields:
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
        if part["primitive"] not in PRIMITIVES:
            raise ValueError(f"parts[{index}].primitive must be one of {sorted(PRIMITIVES)}")
        part["dimensions"] = _finite_vector(part["dimensions"], 3, f"parts[{index}].dimensions", positive=True)
        part["location"] = _finite_vector(part["location"], 3, f"parts[{index}].location")
        part["rotation_degrees"] = _finite_vector(part["rotation_degrees"], 3, f"parts[{index}].rotation_degrees")
        if not isinstance(part["material"], str) or part["material"].casefold() not in material_names:
            raise ValueError(f"parts[{index}].material must name a declared material")
        segments = part["segments"]
        if part["primitive"] in {"BOX", "WEDGE"}:
            if segments is not None:
                raise ValueError("BOX/WEDGE segments must be null")
        elif isinstance(segments, bool) or not isinstance(segments, int) or not 3 <= segments <= 64:
            raise ValueError("CYLINDER/ICOSPHERE segments must be an integer from 3 to 64")

    policy = request["policy"]
    required_policy = {
        "existing_names": "REFUSE",
        "source_scene": "PRESERVE",
        "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
        "failure": "ROLL_BACK_OWNED_DATA",
    }
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
    if request["schema"] != REVISION_SCHEMA:
        raise ValueError(f"schema must be {REVISION_SCHEMA}")
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
        if not isinstance(revision, dict) or set(revision) != fields:
            raise ValueError(f"revisions[{index}] has invalid fields")
        role = _name(revision["semantic_role"], f"revisions[{index}].semantic_role")
        if role.casefold() in roles:
            raise ValueError("revision semantic roles must be case-insensitively unique")
        roles.add(role.casefold())
        changed = False
        for key, positive in (("dimensions", True), ("location", False), ("rotation_degrees", False)):
            value = revision[key]
            if value is not None:
                revision[key] = _finite_vector(value, 3, f"revisions[{index}].{key}", positive=positive)
                changed = True
        if not changed:
            raise ValueError(f"revisions[{index}] must change at least one transform field")

    required_policy = {
        "existing_names": "REFUSE",
        "source": "PRESERVE",
        "revision": "NEW_COLLECTION_OBJECTS_MESHES_SHARED_MATERIALS",
        "failure": "ROLL_BACK_OWNED_DATA",
    }
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


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("request")
    args = parser.parse_args()
    payload = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if payload.get("schema") == REVISION_SCHEMA:
        validator = validate_revision_request
    elif payload.get("schema") == KILN_IMPORT_SCHEMA:
        validator = validate_kiln_import_request
    else:
        validator = validate_request
    print(json.dumps(validator(payload), indent=2, ensure_ascii=False))
