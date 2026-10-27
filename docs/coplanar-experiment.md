# Synthetic coplanar copy experiment — 2026-09-18

## Verified environment and boundary

Blender connection restored. Live addon status: Blender 5.0.1, addon [1,7], protocol 7,
up to date. Current Scene Cube/Light/Camera, one material (new process; do not force
historical two-material count). External MCP remains user-identified ahujasid/blender-mcp;
no installation, socket/config or telemetry changes. Native runtime documentation confirms
`bmesh.ops.dissolve_limit` parameters including angle_limit, boundary option, verts, edges,
delimit. No installed Skill or reusable apply helper was created.

## Failure → investigation → correction

Initial continuous-plane test failed: requested 1e-6 radians left counts 4/5/2/2 unchanged.
Exact fixture teardown ran on failure. In-memory BMesh probes isolated delimiters and
vertex arguments: neither explained it. Angle sweep on identical coplanar faces (native
face angle 0): 1e-6 and 1e-4 did not dissolve, 0.001 and 0.01 did. Use 0.001 radians only
as explicit experiment input; this evidence does not prove the internal implementation
cause or justify a universal/game default tolerance. Source code is not independently
verified. No forced fallback collapse or original edits.

## Live outcomes

The original capability run passed 60 native checks plus 4 injected-failure
preservation checks passed. Exact UUID-owned synthetic Scenes/Objects/Meshes/materials
removed. Copies were independent. Source unchanged, boundary coordinates, area and
corner UV/material data retained. Original fingerprint and tracked ID names restored:
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.

- Continuous affine UV plane: vertices/edges/faces/triangles 4/5/2/2 → 4/4/1/2.
- UV split, material boundary, Seam, Sharp, noncoplanar cases: remain 4/5/2/2.
- Continuous but nonaffine UV: native dissolve also produces 4/4/1/2. A UV delimiter
  does NOT independently guarantee interpolation preservation after retriangulation.
  Corner equality alone is insufficient. This intentionally unguarded synthetic probe
  exposes the hazard; it is not authorization to apply to such user data.
- Synthetic failures immediately after copy or after write remove exact owned IDs and
  preserve the original. This is fixture teardown evidence, not reusable apply rollback.

Triangle count remained two: structural simplification, NOT triangle-budget reduction.

## Additional development guard

`scripts/check_affine_uv.py` is a pure development-only predicate for finite xyz/UV corner
pairs and explicitly supplied absolute tolerance. It fits one planar affine mapping,
refuses degenerate/noncoplanar/nonaffine/discontinuous input and arithmetic overflow.
No modification authorized, no implicit game tolerance or general UV-quality claim.
Same tolerance is used for source and UV residuals in this prototype; general production
work needs scale-aware separate unit policies and per-island/candidate-edge handling.

All seven native source cases fed this guard: continuous affine/material/seam/sharp
are affine, nonaffine/split/noncoplanar blocked. Five offline tests cover planar/rotated
maps, nonlinear/discontinuous UV, nonplanarity, degeneracy/invalid types/nonfinite values,
finite-input overflow and immutable input/no authorization.

## Repeatable execution

```powershell
python -B scripts/prepare_blender_check.py --suite coplanar-experiment
```

Pass printed JSON `code` to the live MCP Python tool with the actual user request.
The builder separately compiles exact inspector, preservation fingerprint, affine guard
and experiment sources in one globals/locals dictionary and records hashes. This suite
is intentionally separate from `all` (three installed Skill regressions); no untested
experiment quietly becomes an installed workflow. Requires authorized synthetic work,
Object-mode window, no mode forcing or original save. Setup can dirty a clean file.

Next: guard-enforced preview on supported simple inputs, relevant UV/material/edge-flag
fingerprint, explicit unused output names, independent copy and output validation/rollback.
Only then consider a narrow structural-simplification Skill. Broad decimation/LOD, rig,
transforms and engine export remain unimplemented. No silhouette/UV-quality/engine
certification follows from these synthetic numerical checks.

Subsequent preview unit implemented and tested: see `coplanar-preview.md`. The expanded
same suite now passes 107 normal + 4 teardown checks. Original 60/4 above describes the
capability checkpoint, not current suite count. Installed Skills remain unchanged.
