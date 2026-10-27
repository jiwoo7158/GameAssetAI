# GameAssetAI implementation memory

This document preserves product direction across long sessions. It is not an append-only activity
log. Update it when a capability changes status or when priorities move; do not remove deferred
work merely because another workstream becomes temporarily more important.

## Product order

```text
natural-language asset request
  -> creation router
  -> Blender-native modeling / material / rig / animation specialists
  -> inspection and reversible revision
  -> Blender Add-on UI for repeatable preview/setup/export work
  -> Pixel/Cel/Toon outputs
  -> optional Unity export/import validation
```

The Add-on and 2D pipeline complement asset creation. They must not replace it. Conversely, moving
back to modeling, rigging or Mixamo work must not cause the Add-on UI work to be forgotten.

## Implemented and retained

### Creation spine

- `blender-create-game-asset`: routing-only natural-language entry. Do not host-promote it until
  the selected creation specialist passes a representative visible acceptance gate.
- `blender-create-static-asset`: explicit primitive-based low-poly props/weapons/environment parts.
- `blender-create-character-base`: V1 separate-volume and guarded v3 Boolean blockout paths remain
  intact. Experimental v4 `DEFORMATION_TEMPLATE` duplicates an explicit hash-pinned Blender
  Studio Human Base Meshes v1.4.1 CC0 Mesh, applies two tested non-affine proportion ranges,
  preserves all-quad topology/UV loops, assigns materials and records provenance with owned
  rollback. Lanky knee compression and generated-fixture rig mismatch prevent an accepted
  deformation-ready claim. `VOXEL_CONNECTED` remains suspended after leg/foot fusion.
- `blender-rig-character-base`: 18-bone generated-fixture rig mechanics are retained, but the
  rejected connected candidate is not valid product evidence.
- `blender-adjust-character-joint-weights-copy`: the copy/preservation algorithm is retained as
  experimental backend evidence only. Its live metrics came from the rejected topology and must
  not be presented as character-quality progress.
- `blender-author-pose-action`: explicit key-pose Action authoring with front-axis and optional
  root/pelvis location channels.

### Existing-asset support

Retain the inspection, static cleanup/copy preparation, animation inventory/copy/range/loop/root,
retarget-readiness/bake/composition and binding/replacement Skills. They are specialist stages for
existing assets, rigs and animations. They are not substitutes for creation. The detailed grouping
and limitations are in `docs/SKILL_REUSE_AUDIT.md`.

### Blender Add-on 0.1.5

Implemented UI/execution modules:

- owned orthographic camera and neutral-light setup/removal;
- compositor pixel graph setup/removal;
- explicit Armature and Action selection/preview binding;
- reversible Flat Lit, Cel Banded and Emission Unlit material previews;
- current-frame atomic PNG export;
- portable camera/lighting/pixel/material JSON presets;
- background Action PNG-sequence dispatch through the existing Skill helpers;
- last-sequence sprite-sheet handoff through the existing atomic assembler.

The former `Pixel Preview` label was corrected to `Pixel Scene Setup`: there is no true live pixel
preview yet.

The Add-on is installed and enabled in saved Blender 5.0 Preferences. Runtime registration,
source/installed hash alignment, transactional update/restore and fresh-process survival are
verified.

### Downstream 2D capabilities

Retain static/Action rendering, batch coordination, equal-cell sheets, silhouette/material/object
masks, normal/depth/object-ID passes and impostor bundles. Principal static/Action/sheet paths are
integrated into the Add-on; advanced passes remain explicit opt-in tools.

## Active product gaps, in order

1. Adapt/fit a rig and weights to an explicit template-derived or existing humanoid Mesh; the
   current 18-bone generated-fixture rig is not a general adapter.
2. Repeat representative elbow/knee/shoulder/hip visual gates and only then decide whether v4 may
   advance from experimental structural evidence to accepted deformation-ready output.
3. Complete user-visible acceptance without treating one test character as the product objective.
4. Complete one real Mixamo import/round-trip/retarget validation.
5. Implement rigged/animated FBX or GLB export and verify it in Unity.
6. Broaden native static modeling and controlled semantic revision beyond primitive assembly.

Do not insert new collider, LODGroup, auxiliary pass or Unity-only work ahead of these gaps unless
a concrete user request requires it.

## Open-source evaluation queue -- research only

No candidate below is installed or part of the required runtime. Integration requires a separate
user-approved work package and representative isolated validation.

| Priority | Candidate | Possible reuse | Current decision |
| --- | --- | --- | --- |
| 1 | Blender native QuadriFlow and ReQuad | topology baseline for the character deformation-topology gap | isolated Blender 5.0.1 experiment completed 2026-10-26; neither is integration-ready: direct inputs failed topology gates and voxel-prepared inputs failed semantic preservation |
| 2 | RetopoFlow | optional human-guided topology correction | manual review aid only unless deterministic automation is demonstrated |
| 3 | Blender Agent Skills | modeling/UV/QA procedure comparison | inspect individual procedures and tests; do not install wholesale or duplicate GameAssetAI Skills |
| 4 | Kiln 1.5.0 | broader procedural static props/environment provider | tested only in the approved isolated evaluation folder; an existing field-cannon GLB passed the optional hash-verified Blender 5.0.1 Adapter. Kiln remains non-required, and imported semantic revision compatibility is not validated |
| 5 | Rigify then GameRig | control rig and game-oriented deform/export rig | evaluate only after a deformation-ready Mesh exists; preserve suitable existing rigs |
| 6 | Rokoko Blender Plugin | imported-animation mapping/retarget reference | defer to the real imported-animation work package; Blender 5 compatibility must be proven locally |
| 7 | MakeHuman | optional humanoid base-mesh provider | defer; separate CC0 asset evaluation from AGPL application-code integration and do not replace style-neutral creation by default |

Research snapshot: Kiln and Blender Agent Skills advertise MIT licensing; ReQuad is GPL-3.0-or-
later; RetopoFlow code is GPL with separate non-code asset terms; GameRig is GPL-2.0 and built on
Rigify; Rokoko's repository advertises MIT but its install may download libraries; MakeHuman code
is AGPL while bundled base assets are CC0. Recheck exact version, license and Blender compatibility
at the time of any proposed integration.

The optional canonical-template work package is implemented in the existing
`blender-create-character-base`; no new Skill or required dependency was added. The v3 and v4
compact/lanky outputs are evidence fixtures, not product requirements. Automatic
QuadriFlow/ReQuad integration remains rejected. The next core gate is existing-mesh rig fitting
and weight adaptation, not another topology provider.

## Deferred but retained Add-on/UI backlog

These items are intentionally postponed, not cancelled:

- true live Pixel/Cel preview viewport or dedicated preview workspace;
- multi-item static/Action batch queue UI backed by `blender-render-2d-batch`;
- progress and cancellation feedback for background rendering;
- active Workspace Profile picker, refresh and fingerprint display;
- richer Action comparison, timeline and loop-review controls;
- sprite-sheet preview, cell inspection and export-history display;
- camera presets beyond Front/Side/Quarter/Top, including isometric and portrait variants;
- additional lighting presets and explicit rim/fill controls;
- richer material presets, palette controls, value bands and outline settings in the UI;
- persistent Preferences installation/update workflow for the Add-on;
- UI bridges for normal/depth/mask/impostor outputs after core asset workflows are stable.

When an Add-on task is deferred, keep it here and in `docs/roadmap.md`. Do not silently delete it
from both documents.

## Evidence boundaries

- The earlier separate-volume character proves a visible creation/rig/Action/Cel/sequence/sheet
  vertical slice, not production character quality.
- The voxel-connected candidate is rejected: structural checks missed unintended bridges between
  nearby limb/foot geometry. It must not feed later product claims.
- Shoulder/hip copy metrics prove only that the weight-copy algorithm executed and preserved its
  source. Because the input topology is rejected, they are not character-quality evidence.
- The sword proves explicit low-poly assembly, not arbitrary natural-language modeling.
- Animation adaptation primitives are tested, but no real Mixamo round trip is complete.
- Static FBX export is tested; rigged/animated Unity export is not.
- The v3 Boolean candidate fixes bilateral fusion and is suitable for blockout review, but its
  43 ngons and 324 poles mean it is not yet evidence of deformation topology.
- Add-on 0.1.5 is installed and enabled in Blender Preferences, and its 14 source files are
  hash-aligned with the repository. Hash-bound transactional update/restore is implemented, and a
  fresh Blender 5.0.1 process loaded the saved preference, installed module, Scene property and
  panel successfully.
- The new creation router is source/installed hash-aligned; client discovery is not yet proven.

## Candidate retention decision

“Keep one visible current candidate” prevents the old extremes of showing only the default Cube
or accumulating every iteration. It does not mean the user required that Object, Scene or Blender
process to remain open. A verified non-overwriting checkpoint permits restart/lifecycle testing;
candidate retention is an agent workflow choice unless the user explicitly says otherwise.

## Documentation roles

- `AGENTS.md`: development rules and boundaries.
- `docs/PROJECT_AUDIT.md`: why the project direction was corrected.
- `docs/IMPLEMENTATION_MEMORY.md`: durable current capability and deferred-work memory.
- `docs/SKILL_REUSE_AUDIT.md`: how existing Skills are reused and where they stop.
- `docs/roadmap.md`: actionable checked/unchecked backlog.
- `docs/SESSION_STATE.md`: concise exact continuation point for the next session.
- `docs/session-history/`: historical evidence only, never the active plan.
