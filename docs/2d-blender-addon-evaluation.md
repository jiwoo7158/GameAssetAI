# Blender panel/operator decision — superseded 2026-10-25

## Current decision

This superseding decision remains authoritative: keep the Add-on as a core UI/execution layer.
The Add-on is installed and enabled in saved Blender 5.0 Preferences. Runtime registration,
source/installed alignment, transactional update/restore and fresh-process survival are verified.

Build the Blender Add-on as a core execution and UI layer. Keep the proven hash-bound background
jobs for publication and rollback, but expose repeatable Blender-local scene, compositor,
material and export setup through owned operators and panels.

The earlier deferral below was based on treating the background render contracts as the whole
product. That contradicted the supplied plan, which explicitly called for a Skill + Blender
Add-on architecture, and it left the requested Blender-local workflow unimplemented.

Initial implementation order:

1. owned Scene Preset Builder with exact cleanup;
2. Compositor Node Preset Builder;
3. material/shader presets;
4. export operator backed by the existing render helpers;
5. preset loading and animation/batch controls.

## Historical decision (no longer authoritative)

## Evidence considered

The stabilized 2D path now covers static PNG, Action sequences, sprite-sheet assembly,
Profile-backed settings, mixed static/Action batches and Unity Sprite validation. Its
write operations deliberately run from reviewed, hash-bound stage/job files in isolated
background Blender processes. Existing host tests confirm natural-language Skill routing,
no-overwrite publication, rollback and restoration without needing persistent Blender UI.

The active Workspace Profile and output destinations live outside Blender by design. A
panel would either duplicate that configuration or need its own synchronization and stale-
state rules. Long Action/batch renders would still need the existing background process,
receipt and rollback implementation; wrapping them in `bpy.types.Operator` would not remove
that machinery. Registration, hot reload, Blender-version compatibility, UI layout state
and add-on upgrade/uninstall behavior would add a second lifecycle that has not solved a
demonstrated user blocker.

## Re-evaluation triggers

An add-on spike becomes justified only if at least one of these is demonstrated:

- artists need repeated interactive camera/framing preview without a Codex round trip;
- a Blender-local progress/cancel surface is required for long background jobs;
- Profile presets need a read-only Blender picker with an explicit refresh/fingerprint UI;
- a tested operator materially reduces context fragility compared with direct `bpy` helpers.

Any future spike must remain an optional execution/UI layer. It must not install or own
Blender MCP, replace Skills or Profiles, store game defaults in Blender, mutate the active
Scene merely to display a preview, or bypass request fingerprints, no-overwrite publication,
receipts and rollback. Until a trigger has representative evidence, an add-on tree would be
speculative duplication rather than production convenience.
