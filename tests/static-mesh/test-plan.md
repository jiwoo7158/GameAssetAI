# Static diagnostics regression

Use live Blender, loading inspection helper/fingerprint support and static diagnostics
in separate helper namespaces. Execute `run_diagnostics_tests()` from `run_diagnostics.py`.
Fixture data is native, synthetic, exact-ID owned, and removed after restoring user context.

Verify: base closed cube; explicit triangle/material/UV/edge-closure constraints; unrequested
constraints unknown; invalid rules/names/types; open planes; loose/wire/degenerate/coincident
geometry; edge winding/overconnection; negative/singular transforms; Subdivision base versus
viewport evaluation; evaluated-mesh release including failure; Shape Keys/Action preservation;
nonfinite data without invalid JSON; edit-mode uncertainty without changing user mode.

Source/current-scene fingerprints and tracked datablock names must match after teardown.
Passing diagnostics is not engine import/export certification. Record actual live failures
and corrections in `docs/static-mesh-validation.md`.
