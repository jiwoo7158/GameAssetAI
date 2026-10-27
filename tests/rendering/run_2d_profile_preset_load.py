"""Load packaged Profile-preset helpers and verify fresh provenance without writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import uuid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--helper-root", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    args = parser.parse_args()
    helper_root = args.helper_root.resolve(strict=True)
    artifact_root = args.artifact_root.resolve(strict=True)
    sys.path.insert(0, str(helper_root))
    from extract_2d_profile_preset import PRESET_SCHEMA
    from resolve_2d_profile_preset import resolve_2d_profile_preset
    from validate_2d_static_render_request import (
        SCHEMA as STATIC_SCHEMA, validate_2d_static_render_request)

    preset = {
        "schema": PRESET_SCHEMA,
        "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                 "up": [0, 0, 1], "framing_margin": 0.1},
        "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
        "style": {"mode": "PIXEL", "resolution": [32, 32],
                  "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                  "palette_mode": "NONE", "palette": [], "max_colors": None,
                  "outline_mode": "NONE", "outline_color": None, "outline_width": 0,
                  "shading_mode": "NONE", "value_steps": None},
        "sequence": {"playback_fps": 12},
        "sprite_sheet": {"padding": 1, "order": "ROW_MAJOR_TOP_LEFT"},
    }
    context = {"schema": "gameassetai.profile-context.v1", "profile": "TestGame",
               "path": str(artifact_root / "TestGame.md"),
               "reference_sha256": "1" * 64, "profile_sha256": "2" * 64,
               "markdown": "```gameassetai-2d-preset\n" + json.dumps(preset) + "\n```\n",
               "rules": "explicit only"}
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    static = resolve_2d_profile_preset(context, "STATIC_RENDER")
    action = resolve_2d_profile_preset(context, "ACTION_SEQUENCE")
    sheet = resolve_2d_profile_preset(context, "SPRITE_SHEET")
    check("static_resolved", static["status"] == "resolved")
    check("action_fps_resolved", action["settings"]["playback_fps"] == 12)
    check("sheet_layout_resolved", sheet["settings"]["padding"] == 1)
    fresh = resolve_2d_profile_preset(context, "STATIC_RENDER", static["binding"])
    check("fresh_binding_accepted", fresh["status"] == "resolved")
    changed = dict(context); changed["profile_sha256"] = "3" * 64
    check("changed_binding_refused", resolve_2d_profile_preset(
        changed, "STATIC_RENDER", static["binding"])["status"] == "error")
    absent = dict(context); absent.update(profile=None, path=None, profile_sha256=None,
                                          markdown=None)
    check("absence_not_reused", resolve_2d_profile_preset(
        absent, "STATIC_RENDER", static["binding"])["status"] == "absent")
    request = {"schema": STATIC_SCHEMA, "scene_name": "Scene", "object_name": "Cube",
               **static["settings"],
               "output": {"target_file": str(artifact_root / (
                   "profile-load-" + uuid.uuid4().hex + ".png")),
                          "color_mode": "RGBA", "color_depth": 8, "overwrite": False}}
    check("resolved_request_valid", validate_2d_static_render_request(
        request)["ready_for_blender_inspection"])
    check("no_artifact_written", not Path(request["output"]["target_file"]).exists())
    print(json.dumps({"status": "passed", "check_count": len(checks),
                      "checks": checks, "helper_root": str(helper_root)}, sort_keys=True))


if __name__ == "__main__":
    main()
