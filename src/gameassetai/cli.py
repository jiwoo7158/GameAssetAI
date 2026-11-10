from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .catalog import REGISTRY_SPECS, load_registry, validate_catalog
from .distribution import (
    build_product_bundle,
    install_product_bundle,
    update_product_bundle,
    validate_product_bundle,
    write_bundle_zip,
)
from .errors import GameAssetAIError
from .outputs import begin_output_run, validate_output_run
from .specification import load_asset_specification
from .workspace import (
    create_or_connect_workspace,
    create_profile,
    default_template_root,
    list_profiles,
    read_active_profile,
    select_profile,
    update_workspace,
    validate_workspace,
)


def _print(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gameassetai", description="GameAssetAI product foundation CLI")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="group", required=True)

    catalog = sub.add_parser("catalog")
    catalog_sub = catalog.add_subparsers(dest="action", required=True)
    catalog_validate = catalog_sub.add_parser("validate")
    catalog_validate.add_argument("--root", type=Path)
    catalog_list = catalog_sub.add_parser("list")
    catalog_list.add_argument("kind", choices=sorted(REGISTRY_SPECS))
    catalog_list.add_argument("--root", type=Path)

    workspace = sub.add_parser("workspace")
    workspace_sub = workspace.add_subparsers(dest="action", required=True)
    for action in ("create", "connect", "update"):
        command = workspace_sub.add_parser(action)
        command.add_argument("path", type=Path)
        command.add_argument("--template", type=Path)
    workspace_validate = workspace_sub.add_parser("validate")
    workspace_validate.add_argument("path", type=Path)
    workspace_validate.add_argument("--require-profile", action="store_true")

    profile = sub.add_parser("profile")
    profile_sub = profile.add_subparsers(dest="action", required=True)
    create = profile_sub.add_parser("create")
    create.add_argument("workspace", type=Path)
    create.add_argument("profile_id")
    create.add_argument("--name", required=True)
    create.add_argument("--description", required=True)
    create.add_argument("--three-d-style")
    create.add_argument("--two-d-style", action="append", default=[])
    select = profile_sub.add_parser("select")
    select.add_argument("workspace", type=Path)
    select.add_argument("profile_id")
    clear = profile_sub.add_parser("clear")
    clear.add_argument("workspace", type=Path)
    listing = profile_sub.add_parser("list")
    listing.add_argument("workspace", type=Path)
    show = profile_sub.add_parser("show")
    show.add_argument("workspace", type=Path)

    spec = sub.add_parser("spec")
    spec_sub = spec.add_subparsers(dest="action", required=True)
    spec_validate = spec_sub.add_parser("validate")
    spec_validate.add_argument("path", type=Path)
    spec_validate.add_argument("--catalog-root", type=Path)

    outputs = sub.add_parser("outputs")
    outputs_sub = outputs.add_subparsers(dest="action", required=True)
    begin = outputs_sub.add_parser("begin")
    begin.add_argument("workspace", type=Path)
    begin.add_argument("--game", required=True)
    begin.add_argument("--category", required=True)
    begin.add_argument("--asset", required=True)
    begin.add_argument("--run-id")
    begin.add_argument("--summary", default="")
    validate_run = outputs_sub.add_parser("validate")
    validate_run.add_argument("path", type=Path)

    package = sub.add_parser("package")
    package_sub = package.add_subparsers(dest="action", required=True)
    build = package_sub.add_parser("build")
    build.add_argument("repo", type=Path)
    build.add_argument("destination", type=Path)
    validate = package_sub.add_parser("validate")
    validate.add_argument("bundle", type=Path)
    archive = package_sub.add_parser("zip")
    archive.add_argument("bundle", type=Path)
    archive.add_argument("target", type=Path)
    install = package_sub.add_parser("install")
    install.add_argument("bundle", type=Path)
    install.add_argument("skills_dir", type=Path)
    update = package_sub.add_parser("update")
    update.add_argument("bundle", type=Path)
    update.add_argument("skills_dir", type=Path)
    update.add_argument("--backup", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.group == "catalog":
            if args.action == "validate":
                result = validate_catalog(args.root)
            else:
                registry = load_registry(args.root, args.kind)
                result = {"kind": args.kind, "entries": list(registry.entries.values())}
        elif args.group == "workspace":
            if args.action in {"create", "connect"}:
                result = create_or_connect_workspace(args.template, args.path)
            elif args.action == "update":
                result = update_workspace(args.template, args.path)
            else:
                result = validate_workspace(args.path, require_profile=args.require_profile)
        elif args.group == "profile":
            if args.action == "create":
                result = create_profile(
                    args.workspace, args.profile_id, args.name, args.description,
                    three_d_style=args.three_d_style, two_d_styles=args.two_d_style,
                )
            elif args.action == "select":
                result = select_profile(args.workspace, args.profile_id)
            elif args.action == "clear":
                result = select_profile(args.workspace, None)
            elif args.action == "list":
                result = {"profiles": list_profiles(args.workspace)}
            else:
                result = {"profile": read_active_profile(args.workspace)}
        elif args.group == "spec":
            result = {"status": "valid", "specification": load_asset_specification(args.path, args.catalog_root)}
        elif args.group == "outputs":
            if args.action == "begin":
                result = begin_output_run(
                    args.workspace, game=args.game, asset_category=args.category,
                    asset_id=args.asset, run_id=args.run_id, request_summary=args.summary,
                )
            else:
                result = {"status": "valid", "manifest": validate_output_run(args.path)}
        else:
            if args.action == "build":
                result = build_product_bundle(args.repo, args.destination)
            elif args.action == "validate":
                result = validate_product_bundle(args.bundle)
            elif args.action == "zip":
                result = write_bundle_zip(args.bundle, args.target)
            elif args.action == "install":
                result = install_product_bundle(args.bundle, args.skills_dir)
            else:
                result = update_product_bundle(args.bundle, args.skills_dir, args.backup)
    except (GameAssetAIError, OSError, UnicodeError, ValueError) as exc:
        print(f"GameAssetAI failed: {exc}", file=sys.stderr)
        return 1
    _print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
