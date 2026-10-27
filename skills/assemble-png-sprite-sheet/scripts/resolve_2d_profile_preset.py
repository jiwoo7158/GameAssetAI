"""Resolve one complete Profile 2D preset and enforce fresh provenance before use."""
from __future__ import annotations

from extract_2d_profile_preset import extract_2d_profile_preset


RESOLUTION_SCHEMA = "gameassetai.2d-profile-preset-resolution.v1"
PURPOSES = {"STATIC_RENDER", "ACTION_SEQUENCE", "SPRITE_SHEET"}
_BINDING_FIELDS = {"name", "reference_sha256", "profile_sha256", "preset_sha256"}


def resolve_2d_profile_preset(context, purpose, expected_binding=None):
    """Resolve exact purpose settings; never merge partial explicit values or read files."""
    report = {"schema": RESOLUTION_SCHEMA, "status": "error", "errors": [],
              "settings_source": "ACTIVE_PROFILE_PRESET"}
    try:
        if purpose not in PURPOSES:
            raise ValueError("purpose must be STATIC_RENDER, ACTION_SEQUENCE or SPRITE_SHEET")
        extracted = extract_2d_profile_preset(context)
        if extracted.get("status") == "absent":
            report.update(status="absent", reason=extracted.get("reason"), purpose=purpose,
                          settings_source=None)
            return report
        if extracted.get("status") != "ready":
            raise ValueError("Active Profile 2D preset is unavailable: "
                             + "; ".join(extracted.get("errors", [])))
        binding = {"name": extracted["profile"],
                   "reference_sha256": extracted["reference_sha256"],
                   "profile_sha256": extracted["profile_sha256"],
                   "preset_sha256": extracted["preset_sha256"]}
        if expected_binding is not None:
            if not isinstance(expected_binding, dict) or set(expected_binding) != _BINDING_FIELDS:
                raise ValueError("expected_binding fields must be exact")
            if expected_binding != binding:
                raise ValueError("Active Profile or 2D preset changed; preview is stale")
        preset = extracted["preset"]
        if purpose == "STATIC_RENDER":
            settings = {"profile": {key: binding[key] for key in
                                     ("name", "reference_sha256", "profile_sha256")},
                        "view": preset["view"], "lighting": preset["lighting"],
                        "style": preset["style"]}
        elif purpose == "ACTION_SEQUENCE":
            settings = {"profile": {key: binding[key] for key in
                                     ("name", "reference_sha256", "profile_sha256")},
                        "view": preset["view"], "lighting": preset["lighting"],
                        "style": preset["style"],
                        "playback_fps": preset["sequence"]["playback_fps"]}
        else:
            settings = {"profile": binding,
                        "padding": preset["sprite_sheet"]["padding"],
                        "order": preset["sprite_sheet"]["order"]}
        report.update(status="resolved", purpose=purpose, binding=binding,
                      settings=settings,
                      limitations=["Complete preset only; partial merge with explicit settings is forbidden",
                                   "Reread Profile context and pass binding again before mutation/output"])
    except (ValueError, TypeError, KeyError) as exc:
        report["errors"].append(str(exc))
    return report

