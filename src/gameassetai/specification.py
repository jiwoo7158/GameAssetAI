from __future__ import annotations

from pathlib import Path
from typing import Any

from .catalog import load_catalogs, validate_style_ids
from .errors import ValidationError
from .filesystem import read_json_object, validate_identifier


SCHEMA = "gameassetai.asset-specification.v1"
BUILTIN_REFERENCE_ROLES = frozenset({
    "concept", "front", "side", "back", "three-quarter", "source",
})
REFERENCE_ROLE_MAX_LENGTH = 64
OUTPUT_FORMAT_ARTIFACTS: dict[str, dict[str, frozenset[str]]] = {
    "blend": {"model": frozenset({".blend"})},
    "fbx": {"export": frozenset({".fbx"})},
    "png": {
        "preview": frozenset({".png"}),
        "sprite": frozenset({".png"}),
    },
    "sprite-sheet": {"sprite": frozenset({".png"})},
    "png-sequence": {"sprite": frozenset({".png"})},
}
OUTPUT_FORMATS = set(OUTPUT_FORMAT_ARTIFACTS)


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ValidationError(f"{label} must be a list of nonempty strings")
    return list(value)


def validate_asset_specification(
    document: dict[str, Any], catalog_root: Path | None = None,
) -> dict[str, Any]:
    required = {
        "schema", "asset_id", "name", "game", "operation", "asset_type", "description",
        "style", "references", "generation", "source", "rig_animation", "outputs",
    }
    unknown = set(document) - required - {"metadata"}
    missing = required - set(document)
    if missing or unknown:
        raise ValidationError(f"Asset specification fields mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")
    if document.get("schema") != SCHEMA:
        raise ValidationError(f"Unsupported asset specification schema: {document.get('schema')}")
    validate_identifier(document.get("asset_id"), "asset_id")
    validate_identifier(document.get("game"), "game")
    for field in ("name", "description"):
        if not isinstance(document.get(field), str) or not document[field].strip():
            raise ValidationError(f"{field} must be a nonempty string")
    operation = document.get("operation")
    if operation not in {"create", "modify"}:
        raise ValidationError("operation must be create or modify")

    registries = load_catalogs(catalog_root)
    registries["asset-types"].get(document.get("asset_type"))

    style = document.get("style")
    if not isinstance(style, dict) or set(style) != {"three_d", "two_d", "overrides"}:
        raise ValidationError("style must contain three_d, two_d, and overrides")
    validate_style_ids(style["three_d"], style["two_d"], catalog_root, label="style")
    if not isinstance(style["overrides"], dict):
        raise ValidationError("style.overrides must be an object")

    references = document.get("references")
    if not isinstance(references, list):
        raise ValidationError("references must be a list")
    for index, reference in enumerate(references):
        if not isinstance(reference, dict) or set(reference) != {"path", "role", "sha256"}:
            raise ValidationError(f"references[{index}] has an invalid contract")
        if not isinstance(reference["path"], str) or not reference["path"].strip():
            raise ValidationError(f"references[{index}].path must be nonempty")
        role = reference["role"]
        if isinstance(role, str) and len(role) > REFERENCE_ROLE_MAX_LENGTH:
            raise ValidationError(
                f"references[{index}].role must be at most {REFERENCE_ROLE_MAX_LENGTH} characters"
            )
        validate_identifier(role, f"references[{index}].role")
        digest = reference["sha256"]
        if digest is not None and (
            not isinstance(digest, str) or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)
        ):
            raise ValidationError(f"references[{index}].sha256 is invalid")

    generation = document.get("generation")
    if not isinstance(generation, dict) or set(generation) != {"provider", "options"}:
        raise ValidationError("generation must contain provider and options")
    if generation["provider"] != "auto":
        registries["generation-providers"].get(generation["provider"])
    if not isinstance(generation["options"], dict):
        raise ValidationError("generation.options must be an object")

    source = document.get("source")
    if operation == "modify" and not isinstance(source, dict):
        raise ValidationError("modify operations require a source object")
    if operation == "create" and source is not None:
        raise ValidationError("create operations must set source to null")
    if source is not None:
        if set(source) != {"path", "object", "preserve_original"}:
            raise ValidationError("source has an invalid contract")
        if not isinstance(source["path"], str) or not source["path"].strip():
            raise ValidationError("source.path must be nonempty")
        if source["object"] is not None and not isinstance(source["object"], str):
            raise ValidationError("source.object must be null or a string")
        if source["preserve_original"] is not True:
            raise ValidationError("source.preserve_original must be true")

    rig = document.get("rig_animation")
    if not isinstance(rig, dict) or set(rig) != {"rig", "actions"}:
        raise ValidationError("rig_animation must contain rig and actions")
    if rig["rig"] not in {"none", "existing", "humanoid", "asset-specific", "undecided"}:
        raise ValidationError("rig_animation.rig is invalid")
    _strings(rig["actions"], "rig_animation.actions")

    outputs = document.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise ValidationError("outputs must be a nonempty list")
    for index, output in enumerate(outputs):
        if not isinstance(output, dict) or set(output) != {"format", "options"}:
            raise ValidationError(f"outputs[{index}] has an invalid contract")
        if output["format"] not in OUTPUT_FORMATS or not isinstance(output["options"], dict):
            raise ValidationError(f"outputs[{index}] is invalid")
    return document


def load_asset_specification(path: Path, catalog_root: Path | None = None) -> dict[str, Any]:
    document = read_json_object(path)
    return validate_asset_specification(document, catalog_root)
