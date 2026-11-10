from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Iterable

from .errors import ValidationError
from .filesystem import is_link, read_json_object, validate_identifier


REGISTRY_SPECS = {
    "asset-types": ("gameassetai.asset-types.v1", "asset_types"),
    "styles": ("gameassetai.styles.v1", "styles"),
    "generation-providers": ("gameassetai.generation-providers.v1", "providers"),
}
IMPLEMENTATION_STATES = {"not-implemented", "bounded", "available"}
EVIDENCE_STATES = {"none", "tested", "representative", "accepted", "engine-proven"}


@dataclass(frozen=True)
class Registry:
    kind: str
    entries: dict[str, dict[str, Any]]
    sources: tuple[str, ...]

    def get(self, identifier: str) -> dict[str, Any]:
        try:
            return self.entries[identifier]
        except KeyError as exc:
            raise ValidationError(f"Unknown {self.kind} identifier: {identifier}") from exc


def default_catalog_root() -> Path:
    packaged = resources.files("gameassetai").joinpath("data", "catalog")
    try:
        path = Path(str(packaged))
    except TypeError as exc:
        raise ValidationError("Packaged catalog is not filesystem-accessible") from exc
    if not path.is_dir():
        raise ValidationError("No packaged catalog is available; pass an explicit catalog root")
    return path


def _documents(root: Path, kind: str) -> Iterable[Path]:
    directory = root / kind
    if is_link(directory) or not directory.is_dir():
        raise ValidationError(f"Missing real catalog directory: {directory}")
    files = sorted(directory.glob("*.json"))
    if not files:
        raise ValidationError(f"Catalog directory contains no JSON documents: {directory}")
    for path in files:
        if is_link(path) or not path.is_file():
            raise ValidationError(f"Catalog document must be a real file: {path}")
        yield path


def _validate_common(entry: dict[str, Any], source: Path) -> str:
    identifier = validate_identifier(entry.get("id"), f"catalog id in {source.name}")
    for field in ("label", "description"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{identifier}.{field} must be a nonempty string")
    if entry.get("implementation_status") not in IMPLEMENTATION_STATES:
        raise ValidationError(f"{identifier}.implementation_status is invalid")
    if entry.get("evidence") not in EVIDENCE_STATES:
        raise ValidationError(f"{identifier}.evidence is invalid")
    if entry["evidence"] != "none" and entry["implementation_status"] == "not-implemented":
        raise ValidationError(f"{identifier} cannot have evidence for an unimplemented capability")
    return identifier


def load_registry(root: Path | None, kind: str) -> Registry:
    if kind not in REGISTRY_SPECS:
        raise ValidationError(f"Unknown registry kind: {kind}")
    root = (root or default_catalog_root()).expanduser().absolute()
    schema, list_field = REGISTRY_SPECS[kind]
    entries: dict[str, dict[str, Any]] = {}
    sources: list[str] = []
    for path in _documents(root, kind):
        document = read_json_object(path)
        if document.get("schema") != schema or set(document) != {"schema", list_field}:
            raise ValidationError(f"Invalid {kind} document contract: {path}")
        rows = document[list_field]
        if not isinstance(rows, list) or not rows:
            raise ValidationError(f"{path} must contain a nonempty {list_field} list")
        for row in rows:
            if not isinstance(row, dict):
                raise ValidationError(f"{path} contains a non-object entry")
            identifier = _validate_common(row, path)
            if identifier in entries:
                raise ValidationError(f"Duplicate {kind} id: {identifier}")
            entries[identifier] = row
        sources.append(path.name)

    if kind == "asset-types":
        for identifier, entry in entries.items():
            category = entry.get("category")
            if category not in {"character", "equipment-prop", "environment", "vfx-mesh"}:
                raise ValidationError(f"{identifier}.category is invalid")
            parent = entry.get("parent")
            if parent is not None and parent not in entries:
                raise ValidationError(f"{identifier}.parent does not exist: {parent}")
            if entry.get("rig_policy") not in {
                "not-applicable", "asset-specific", "humanoid-optional", "existing-or-custom"
            }:
                raise ValidationError(f"{identifier}.rig_policy is invalid")
            if not isinstance(entry.get("dynamic"), bool):
                raise ValidationError(f"{identifier}.dynamic must be boolean")
    elif kind == "styles":
        for identifier, entry in entries.items():
            if entry.get("dimension") not in {"3d", "2d"}:
                raise ValidationError(f"{identifier}.dimension is invalid")
            specification = entry.get("specification")
            if not isinstance(specification, dict) or not specification:
                raise ValidationError(f"{identifier}.specification must be a nonempty object")
    else:
        for identifier, entry in entries.items():
            if entry.get("cost") not in {"local", "optional-external"}:
                raise ValidationError(f"{identifier}.cost is invalid")
            capabilities = entry.get("capabilities")
            if not isinstance(capabilities, list) or not all(
                isinstance(value, str) and value for value in capabilities
            ):
                raise ValidationError(f"{identifier}.capabilities must be a string list")
    return Registry(kind=kind, entries=entries, sources=tuple(sources))


def load_catalogs(root: Path | None = None) -> dict[str, Registry]:
    return {kind: load_registry(root, kind) for kind in REGISTRY_SPECS}


def validate_catalog(root: Path | None = None) -> dict[str, Any]:
    registries = load_catalogs(root)
    return {
        "status": "valid",
        "registries": {
            kind: {"entries": len(registry.entries), "sources": list(registry.sources)}
            for kind, registry in registries.items()
        },
    }
