# Project recovery audit — 2026-10-25

> **Historical recovery decision.** This document records the 2026-10-25 correction and is no
> longer the current Repository-wide assessment. Use
> `docs/audits/2026-11-02-repository-review.md` for current capability, Skill-portfolio and
> architecture decisions. Retain this file as evidence of why the earlier priority changed.

## Why this audit exists

The repository drifted away from the user's stated product order. The original proposal
assumed a working Blender 3D asset-creation layer and then added a Blender-local 2D/pixel
conversion layer. Development instead concentrated on narrow validators, synthetic fixtures,
render passes and Unity-facing checks. Those pieces are not worthless, but they do not replace
asset creation or the requested Blender Add-on.

At the time, this file was the corrective source of truth. It does not delete or invalidate
historical evidence, but its then-current counts and continuation point are now historical.

## Authoritative inputs

Priority order when documents disagree:

1. `AGENTS.md` and the user's explicit instructions.
2. The original `blender_pixel_pipeline_plan.md` supplied by the user.
3. `docs/requirements.md` and `docs/architecture.md` where they preserve the above intent.
4. This recovery audit and the current section at the top of `docs/roadmap.md`.
5. Historical validation documents and archived session logs as evidence only.

The old interpretation in `docs/2d-pixel-pipeline-plan.md` that treated the existing collection
of narrow 3D Skills as equivalent to the proposed 3D asset-generation layer was incorrect.
The decision in `docs/2d-blender-addon-evaluation.md` to defer the Add-on is superseded.

## Intended product architecture

```text
natural-language asset request
  -> creation orchestrator
  -> Blender-native modeling / material / rig / animation modules
  -> inspect and non-destructively revise
  -> Blender Add-on preview and preset controls
  -> 2D pixel / cel / toon render and export
  -> optional Unity export/import validation
```

The layers are complementary. A renderer cannot stand in for a model generator, an animation
validator cannot stand in for an authored rig or Action, and Unity validation is downstream of
having an asset.

The Blender Add-on is also a retained core product layer. Priorities may temporarily move from UI
to modeling, rigging, animation or Mixamo, but implemented UI must be maintained and deferred UI
must remain recorded in `docs/IMPLEMENTATION_MEMORY.md` and `docs/roadmap.md`. A priority change is
not authorization to abandon the Add-on.

## Implementation inventory

| Area | Status | Evidence | Correction |
| --- | --- | --- | --- |
| Natural-language character/weapon/enemy/prop creation | **Routing only** | `blender-create-game-asset` selects narrow specialists but has no end-to-end implementation | Do not promote the router until selected specialists produce reviewable assets |
| Blender-native modeling modules | **Partial** | Primitive static assembly and a humanoid blockout exist | Add controlled semantic revision and representative visual acceptance |
| Character base-mesh creation | **Connected blockout; deformation topology missing** | V1 volumes remain; voxel v2 is rejected; v3 Boolean fixes fusion and passes its current manifold/clearance checks but has 43 ngons and 324 poles. A 2026-10-26 isolated QuadriFlow/ReQuad experiment found direct-solver failures/invalid boundaries and semantic damage after voxel preparation | First improve the semantic source/preconditions without whole-body voxel bridging, then repeat the native topology gate before rigging |
| Rig creation / adaptation | **Generated-fixture only** | An 18-bone rig works mechanically on owned fixtures; no deformation-ready source or arbitrary existing-mesh adaptation | Keep as backend evidence; resume product routing only after deformation topology exists |
| Mixamo workflow | **Preflight only** | No Mixamo character was downloaded, uploaded, auto-rigged or imported | Do not claim Mixamo support until a real round trip succeeds |
| Animation creation/editing | **Partial low-level support** | Action copy/range/root/retarget primitives were tested on synthetic rigs | Add authored animation and cleanup workflows using a real armature |
| Blender Add-on | **Persistently installed and lifecycle-tested** | 0.1.5 is source-aligned; transactional update/restore passes; a fresh Blender 5.0.1 process automatically registered the installed module and panel | Maintain it while core asset work proceeds |
| Static asset cleanup/export | **Partial and usable** | Inspection, copy-only cleanup, pivot/scale, LOD copy and narrow FBX export exist | Keep; use after creation rather than as the main product |
| 2D pixel rendering | **Substantially implemented** | Static/Action renders, palette, outline, sprite sheet and batch paths pass tests | Integrate behind Add-on controls; stop proliferating pass-only Skills |
| Auxiliary 2D passes | **Implemented narrowly** | masks, normal, depth, object ID and impostor bundle exist | Treat as advanced downstream outputs, not current priority |
| Unity integration | **Early validation only** | Sprite/static import checks and an in-memory LODGroup probe exist | Pause new Unity work until Blender creation and Add-on foundations are usable |

## What the Cube tests actually proved

The gray/white Cube images proved plumbing properties: camera framing, RGBA encoding, alpha,
palette reduction, masks, pass encodings, atomic publication and cleanup. They did **not** prove
that GameAssetAI can create a character, weapon, enemy, useful prop, rig or production animation.
Future tests must use the smallest representative asset for the capability being claimed.
A Cube remains acceptable only for low-level geometry or render plumbing where semantic shape is
irrelevant.

## Semantic acceptance rule

Structural evidence is necessary but cannot certify an asset's meaning or visible usability.
The rejected connected character demonstrated this failure: one component, closed manifold
topology, full weights and improved edge-stretch metrics all passed while the thighs, lower legs
or feet were visibly fused in an unacceptable way.

For modeling, rigging and animation stages:

1. define the visible/semantic invariant before implementation (for a humanoid: left/right limb
   clearance, intended joint connectivity, no unintended bridges and a readable silhouette);
2. run structural checks, including topology, ownership, normalization and cleanup;
3. inspect representative front, side and three-quarter views in the actual Blender Scene;
4. record explicit accept/reject evidence before routing the candidate downstream;
5. treat every downstream result from a rejected source as non-product evidence, even if its own
   algorithm and tests pass.

`one component`, `watertight`, `all vertices weighted`, lower numerical error or successful file
publication are never substitutes for visible asset acceptance. A failed visible gate stops
rigging, weight refinement, animation, 2D output and engine export for that candidate.

## Product exposure rule

The 43 Skill folders are implementation modules, not 43 user-facing product commands. Keep the
user-facing surface centered on five workflows: static creation/revision, character
creation/revision, existing-character rig/animation work, engine export and optional 3D-to-2D
output. Inspection, Action manipulation, masks, auxiliary passes, collider and LOD helpers remain
internal or opt-in stages selected by the router/Add-on. Do not expand optional stages while a
core workflow lacks a representative accepted asset.

## Recovery sequence

### R0 — restore trustworthy project state

- Preserve the former append-only session log under `docs/session-history/`.
- Keep `docs/SESSION_STATE.md` concise and actionable.
- Mark historical checks as evidence, not product-completion claims.
- Do not delete existing Skills during recovery.

### R1 — Blender Add-on foundation

- Installable `blender_addon/gameassetai` package.
- Scene Preset Builder with an owned camera/light rig, orthographic framing and exact cleanup.
- Blender sidebar panel exposing explicit settings and setup/remove actions.
- Next: Compositor Node Preset Builder, material presets and export operator that call the proven
  render helpers rather than duplicating them.

### R2 — asset creation family

- One routing Skill for creation requests, backed by separate static, character, rig and
  animation workflows rather than one catch-all implementation.
- First representative workflow: create and revise a recognizable native Blender static asset
  with multiple parts and materials from an explicit design brief.
- Next: character blockout/base mesh, then rig adaptation/creation, then animation authoring.
- External generation may be an optional provider, never the only path and never silently paid.

### R3 — representative end-to-end proof

- Create a non-Cube asset in Blender.
- Apply style/material decisions.
- Use the Add-on preview setup.
- Produce static and, after rig work exists, animated 2D output.
- Export to Unity only after the Blender result is validated.

## Work explicitly paused

Until R1 and the first R2 vertical slice pass, do not add new collider, LODGroup, Unity import,
auxiliary render-pass or synthetic retarget Skills. Existing work stays available and tested.

## Anti-drift rule

Before starting a new capability family, compare it with the active gaps and retained UI backlog
in `docs/IMPLEMENTATION_MEMORY.md`. If it does not advance a listed gap or an explicit current user
request, do not let it displace asset creation, rig adaptation, Mixamo or rigged export work.

## Deletion policy

No existing Skill or evidence document is removed by this recovery. Later consolidation must
first identify callers and retained capability, archive superseded material, and obtain explicit
review before any deletion.
