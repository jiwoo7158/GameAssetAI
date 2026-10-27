"""Validate an explicit static multi-pass impostor bundle without writing files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import stat

from validate_2d_depth_pass_request import (SCHEMA as DEPTH_SCHEMA,
                                            validate_2d_depth_pass_request)
from validate_2d_normal_pass_request import (SCHEMA as NORMAL_SCHEMA,
                                             validate_2d_normal_pass_request)
from validate_2d_static_render_request import (SCHEMA as COLOR_SCHEMA,
                                               validate_2d_static_render_request)


SCHEMA = "gameassetai.2d-impostor-bundle-request.v1"
TOP_FIELDS = frozenset(("schema", "items", "manifest", "policy"))
ITEM_FIELDS = frozenset(("id", "view_id", "pass_kind", "request"))
MANIFEST_FIELDS = frozenset(("target_file", "overwrite"))
POLICY_FIELDS = frozenset(("execution_order", "publication", "on_failure",
                           "framing_mismatch"))
PASS_KINDS = ("COLOR", "NORMAL", "DEPTH")
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
MAX_VIEWS = 32
MAX_ITEMS = MAX_VIEWS * len(PASS_KINDS)
PASS_SCHEMAS = {"COLOR": COLOR_SCHEMA, "NORMAL": NORMAL_SCHEMA, "DEPTH": DEPTH_SCHEMA}


def _exact(value, fields, label, errors):
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        errors.append(f"{label} must be an object with string keys")
        return False
    missing, unknown = sorted(fields - value.keys()), sorted(value.keys() - fields)
    if missing:
        errors.append(f"{label} missing fields: " + ", ".join(missing))
    if unknown:
        errors.append(f"{label} unknown fields: " + ", ".join(unknown))
    return not missing and not unknown


def _hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _path_key(value):
    return str(Path(value).resolve(strict=False)).casefold()


def _link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _valid_stem(value):
    if (not isinstance(value, str) or not value or value != value.strip()
            or value.startswith(".") or value.endswith(".")
            or re.search(r'[\x00-\x1f/\\:*?"<>|]', value)):
        return False
    base = value.split(".", 1)[0].upper()
    return base not in {"CON", "PRN", "AUX", "NUL",
                        *[f"COM{i}" for i in range(1, 10)],
                        *[f"LPT{i}" for i in range(1, 10)]}


def _valid_manifest(value, errors):
    if not _exact(value, MANIFEST_FIELDS, "manifest", errors):
        return None
    if value.get("overwrite") is not False:
        errors.append("manifest.overwrite must be false")
    text = value.get("target_file")
    if not isinstance(text, str) or not text or text != text.strip() or "\x00" in text:
        errors.append("manifest.target_file must be a nonempty absolute path")
        return None
    target, meta = Path(text), Path(text + ".meta")
    try:
        if (not target.is_absolute() or target.suffix.lower() != ".json"
                or not _valid_stem(target.stem) or ".." in target.parts):
            errors.append("manifest.target_file must be an absolute .json path")
        elif (not target.parent.is_dir()
              or any(_link(parent) for parent in (target.parent, *target.parent.parents))):
            errors.append("manifest parent must exist and contain no link/reparse path")
        elif target.exists() or _link(target) or meta.exists() or _link(meta):
            errors.append("manifest target or its .meta already exists")
    except OSError:
        errors.append("manifest path could not be inspected")
    return text


def _child_validation(kind, child):
    if kind == "COLOR":
        return validate_2d_static_render_request(child)
    if kind == "NORMAL":
        return validate_2d_normal_pass_request(child)
    if kind == "DEPTH":
        return validate_2d_depth_pass_request(child)
    return {"ready_for_blender_inspection": False, "request_sha256": None,
            "errors": ["unsupported pass kind"]}


def validate_2d_impostor_bundle_request(request):
    """Return a deterministic cross-pass plan; never inspect Blender or write files."""
    report = {"schema": SCHEMA, "status": "error", "errors": [],
              "ready_for_shared_framing_preview": False, "request_sha256": None,
              "view_count": 0, "item_count": 0, "pass_kinds": [], "items": [],
              "outputs": [], "manifest": None}
    errors = report["errors"]
    try:
        if not _exact(request, TOP_FIELDS, "request", errors):
            return report
        if request.get("schema") != SCHEMA:
            errors.append("schema mismatch")
        policy = request.get("policy")
        if _exact(policy, POLICY_FIELDS, "policy", errors):
            expected = {"execution_order": "LIST_ORDER", "publication": "ALL_OR_NOTHING",
                        "on_failure": "ROLL_BACK_BUNDLE_OUTPUTS",
                        "framing_mismatch": "REJECT"}
            for key, value in expected.items():
                if policy.get(key) != value:
                    errors.append(f"policy.{key} must be {value}")
        manifest = _valid_manifest(request.get("manifest"), errors)

        items = request.get("items")
        if not isinstance(items, list) or not 2 <= len(items) <= MAX_ITEMS:
            errors.append(f"items must contain 2 through {MAX_ITEMS} entries")
            items = []
        ids, output_keys, output_parents = set(), set(), set()
        view_order, view_data, view_keys, planned, outputs = [], {}, {}, [], []
        scene_object = None
        for index, item in enumerate(items):
            label = f"items[{index}]"
            if not _exact(item, ITEM_FIELDS, label, errors):
                continue
            item_id, view_id, kind, child = (item.get("id"), item.get("view_id"),
                                              item.get("pass_kind"), item.get("request"))
            valid_identifiers = {}
            for field, value in (("id", item_id), ("view_id", view_id)):
                valid_identifiers[field] = isinstance(value, str) and bool(ID_PATTERN.fullmatch(value))
                if not valid_identifiers[field]:
                    errors.append(f"{label}.{field} must be a safe 1-64 character identifier")
            if isinstance(item_id, str):
                key = item_id.casefold()
                if key in ids:
                    errors.append("item ids must be case-insensitively unique")
                ids.add(key)
            if kind not in PASS_KINDS:
                errors.append(f"{label}.pass_kind must be COLOR, NORMAL or DEPTH")
                continue
            validation = _child_validation(kind, child)
            if validation.get("ready_for_blender_inspection") is not True:
                errors.append(f"{label}.request is invalid: "
                              + "; ".join(validation.get("errors", [])))
                continue
            if child.get("schema") != PASS_SCHEMAS[kind]:
                errors.append(f"{label}.request must use current {kind} schema {PASS_SCHEMAS[kind]}")
            if kind == "COLOR":
                profile = child.get("profile")
                if not isinstance(profile, dict) or any(value is not None for value in profile.values()):
                    errors.append(f"{label} COLOR request must use explicit null Profile provenance")
                if child.get("lighting", {}).get("transparent_background") is not True:
                    errors.append(f"{label} COLOR request requires a transparent background")
                style = child.get("style", {})
                if style.get("anti_aliasing") != "DISABLED" or style.get("nearest_neighbor") is not True:
                    errors.append(f"{label} COLOR request requires fixed nearest-neighbor sampling")
            pair = (child.get("scene_name"), child.get("object_name"))
            if scene_object is None:
                scene_object = pair
            elif pair != scene_object:
                errors.append("all bundle children must use one exact Scene and Object")
            view, style = child.get("view"), child.get("style")
            framing = {"view": view, "resolution": style.get("resolution")}
            view_key = view_id.casefold() if valid_identifiers["view_id"] else f"invalid-{index}"
            if view_key in view_keys and view_keys[view_key] != view_id:
                errors.append("view ids must use one case-exact spelling")
            else:
                view_keys[view_key] = view_id
            if view_id not in view_data:
                view_order.append(view_id)
                view_data[view_id] = {"framing": framing, "passes": []}
            elif view_data[view_id]["framing"] != framing:
                errors.append(f"view {view_id} children must use identical view and resolution")
            if kind in view_data[view_id]["passes"]:
                errors.append(f"view {view_id} contains duplicate {kind} pass")
            view_data[view_id]["passes"].append(kind)
            output = child["output"]["target_file"]
            output_key = _path_key(output)
            if output_key in output_keys:
                errors.append("bundle output paths must be case-insensitively unique")
            output_keys.add(output_key)
            output_parents.add(str(Path(output).parent.resolve(strict=False)).casefold())
            outputs.append(output)
            planned.append({"position": index, "id": item_id, "view_id": view_id,
                            "pass_kind": kind, "request_schema": child.get("schema"),
                            "request_sha256": validation.get("request_sha256"),
                            "target_file": output, "framing": framing})

        if not 1 <= len(view_order) <= MAX_VIEWS:
            errors.append(f"bundle must contain 1 through {MAX_VIEWS} explicit views")
        pass_order = view_data[view_order[0]]["passes"] if view_order else []
        if len(pass_order) < 2:
            errors.append("each view must contain at least two distinct semantic passes")
        for view_id in view_order:
            if view_data[view_id]["passes"] != pass_order:
                errors.append("every view must use the same explicit pass order")
        if len(output_parents) > 1:
            errors.append("every bundle output must share one directory")
        if manifest is not None:
            manifest_key = _path_key(manifest)
            if manifest_key in output_keys:
                errors.append("manifest path must differ from every PNG output")
            if output_parents and str(Path(manifest).parent.resolve(strict=False)).casefold() not in output_parents:
                errors.append("manifest and PNG outputs must share one directory")
        if errors:
            return report
        report.update(status="ready", ready_for_shared_framing_preview=True,
                      request_sha256=_hash(request), view_count=len(view_order),
                      item_count=len(planned), pass_kinds=pass_order, items=planned,
                      outputs=outputs, manifest=manifest, policy=policy,
                      scene_name=scene_object[0], object_name=scene_object[1],
                      views=[{"view_id": view_id,
                              "framing": view_data[view_id]["framing"]}
                             for view_id in view_order],
                      limitations=["Validation does not inspect Blender or calculate framing",
                                   "Object-ID and animated impostors are outside v1"])
    except (TypeError, KeyError, OSError, OverflowError, ValueError) as exc:
        errors.append(str(exc))
    return report
