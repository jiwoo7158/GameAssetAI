# Blender MCP Environment Evidence

## Read-only connection check — 2026-09-16

User-provided configuration (not independently verified from installed source or socket configuration):

- implementation: `ahujasid/blender-mcp`
- source: https://github.com/ahujasid/blender-mcp
- Blender socket: `localhost:9876`

Observed in the current Codex session:

- Blender MCP tools are exposed under `mcp__blender__`.
- `get_scene_info` completed successfully against live Blender.
- `get_addon_status` completed successfully; reported Blender `5.0.1`, addon version
  `[1, 7]`, protocol version `7`, expected protocol version `7`, and `up_to_date: true`.
  The addon version/protocol are not a verified repository release or commit identifier.
- Status also reported `telemetry_consent: true`; no telemetry setting was changed.

Scene result: `Scene`, `object_count: 3`.

| Object | Type |
| --- | --- |
| Cube | MESH |
| Light | LIGHT |
| Camera | CAMERA |

Only the two read-only tools above were called. No Blender code, object creation,
selection change, transform change, save, import, or export was requested.
Object inventory is MCP-reported; independent viewport/native-data confirmation was
not performed. No production workflow is considered stable from this connection check.

## Subsequent authorized development verification — 2026-09-16

The earlier read-only restriction was superseded by the user's explicit development/test
request. Native code execution, viewport capture, and harmless missing-object errors were
verified. Original Scene inventory matched native data and screenshot.
Inspection and static diagnostics synthetic suites passed 36 + 73 checks, also using
helpers loaded from development ZIPs. Fixtures were separate invocation-owned Scenes/IDs;
all tracked IDs and original-scene fingerprint were restored. No original asset was
saved, replaced, imported, or exported. Fixture setup may affect the file dirty flag.

One viewport-evaluation preservation failure was found, corrected, and retested:
see `docs/static-mesh-validation.md`. This evidence does not validate arbitrary Python
execution or third-party addon callbacks as side-effect-free.

## Still unverified

- actual Codex profile reading/switching
- other Blender versions, viewport visibility variations, and every dependency callback
- imported mesh/rig/animation preservation, Mixamo, and Unity/Unreal preparation/export

Continue with `docs/blender-verification.md` and the latest user authorization.
