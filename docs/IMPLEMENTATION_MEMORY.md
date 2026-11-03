# GameAssetAI implementation memory

This document preserves product direction across long sessions. It is not an append-only activity
log. Update it when a capability changes status or when priorities move; do not remove deferred
work merely because another workstream becomes temporarily more important.

## Repository-wide audit decision -- 2026-11-02

The code-based audit in `docs/audits/2026-11-02-repository-review.md` supersedes older broad
completion interpretations. Preserve the proven installation, safety, animation, Generic FBX,
Unity and optional 2D foundations, but redesign the core production layer rather than adding more
narrow validators or render passes.

Current product facts:

- static creation retains four legacy primitives, bounded v3 profile extrusion, accepted v4
  matched-profile beveled solids and v5 explicit art-direction/UV/generated-image material
  production plus copy-only owned semantic geometry replacement;
- character creation is blockout or a hash-pinned CC0 human-template proportion workflow, not a
  general character/style generator;
- M2/M3/M3.4/M4 evidence is valid only for its documented A-pose, 17-role `IN_PLACE`, single-Action
  and Unity Generic scopes;
- the Add-on is persistently installable, but its implemented UI is primarily 2D
  preview/setup/export rather than the complete creation workflow;
- v3 style facts enforce explicit silhouette geometry, flat shading, material count and triangle
  budget; v5 adds a bounded two-style static art-direction/UV/image-texture path, not a general
  style or texturing engine.

Before another feature milestone, select one bounded production domain and representative art
direction, then improve actual creation/revision quality through visible Blender acceptance. Do
not treat the former 46 (now 45 after one deprecated removal) Skill folders as separate
user-facing product commands. Use the per-Skill disposition table in
`docs/audits/2026-11-02-skill-assessment.tsv` when planning consolidation.

The user selected the official B-plan sequence maintained in `docs/roadmap.md`: B1 foundation,
B1.1 profile correctness, B2 shape-production breadth, B3 explicit external-asset revision, B4
art direction/material/texture, B5 static-domain breadth, B6 character/clothing/creature redesign,
B7 integrated natural-language/Add-on production, and B8 real-project proof plus product-surface
consolidation. This sequence supersedes the earlier suggestion to jump directly from B1 to
external-asset revision.

Focused Skill cleanup on 2026-11-02 removed the deprecated
`blender-adjust-character-joint-weights-copy` source/test/installed exposure after confirming no
Router, M2, M3 or packaging caller and only rejected-source evidence. The eight `CONSOLIDATE`
animation/2D modules remain installable implementation modules because current preparation,
validation and package regressions call them directly; they are not promoted as the default
user workflow. The ten `FREEZE` modules remain optional explicit downstream tools and are not
selected ahead of core production work.

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
- `blender-create-static-asset`: legacy primitive assemblies plus accepted v3 profile extrusion
  for authored low-poly silhouettes. V3 records complete geometry metadata and mechanically
  enforces flat shading, limited declared materials and triangle budget. Revision v2 replaces one
  owned semantic part's actual Mesh geometry in an independent copy while preserving Object scale,
  source data and unrelated parts. The representative axe/shield evidence does not imply arbitrary
  prompt-to-mesh, imported-Mesh editing, UV/textures or broad art-style generation.
  V4 adds `PROFILE_BEVELED_EXTRUSION`: explicit matching outer/core rings form a closed solid with
  real sloped cross-section bands. Revision v3 replaces that geometry on a copy. An axe and a
  reinforced crate passed explicit visual acceptance, manifold/normal/volume checks, preservation,
  rollback and reopen. The B3 hardening rejects shifted/twisted correspondence, core edges that
  escape a concave outer profile, crossing connectors and unstable near-zero bevel widths. This is
  not a general Bevel/inset/extrude/sweep/Boolean system.
- Static external-revision v1 accepts one explicit hash-pinned static `.glb`, a complete unique
  Mesh Object/semantic-role map and bounded `LOCAL_AXIS_END_OFFSET` edits. It preserves the source
  file and imported source, creates independent result Mesh datablocks, shares materials read-only,
  retains topology/UV/Object transforms and Empty-only hierarchy, and rolls back its full import/
  result delta on failure. A 13-part Kiln evaluation field cannon passed accepted two-trail
  extension evidence. This does not support `.blend`, semantic inference, arbitrary regions,
  modifiers, vertex groups, Shape Keys, linked data, topology, material or UV editing.
- Static creation v5 resolves a complete explicit art-direction decision from the user or a hash-
  recorded Workspace Profile, then applies style-specific geometry parameters, deterministic
  `LOCAL_BOX_PROJECT` UVs and optional `WOOD_GRAIN`/`PAINTED_METAL` PNG base-color textures. Images
  are connected to Principled materials, packed, externally hash-recorded, budget checked and
  rolled back with owned files/data. Accepted Angular Low-Poly and Painted-Look crate evidence
  proves visible geometry and surface differences, not general UV unwrap, texture painting, PBR
  maps, arbitrary material revision or broad art-style generation.
- `blender-create-character-base`: V1 separate-volume and guarded v3 Boolean blockout paths remain
  intact. Experimental v4 `DEFORMATION_TEMPLATE` duplicates an explicit hash-pinned Blender
  Studio Human Base Meshes v1.4.1 CC0 Mesh, applies two tested non-affine proportion ranges,
  preserves all-quad topology/UV loops, assigns materials and records provenance with owned
  rollback. Lanky knee compression and generated-fixture rig mismatch prevent an accepted
  deformation-ready claim. `VOXEL_CONNECTED` remains suspended after leg/foot fusion.
- `blender-rig-character-base`: v1/v2 generated-fixture mechanics remain intact. V3 adds a bounded
  existing/template Mesh path: explicit object-local A-pose landmarks fit the retained 18-bone
  hierarchy; landmark-envelope weighting normalizes at most four influences, prevents opposite-
  side limb weights, preserves coordinates/UVs and rolls back owned groups/modifier/Armature.
  Compact and lanky canonical-template characters passed representative multi-view deformation,
  save/reopen and installed-Skill execution. This does not imply automatic landmark detection or
  support for arbitrary clothing, Shape Keys or existing rigs.
- The deprecated `blender-adjust-character-joint-weights-copy` Skill was removed from the active
  source and Workspace surface on 2026-11-02. It had no Router/M2/M3 caller, supported only the
  rejected generated-character topology and duplicated a future weight-adaptation responsibility.
  Its implementation and failed evidence remain recoverable from Git history and the Repository
  audit; do not restore it as a user-facing Skill without a new representative accepted target.
- `blender-author-pose-action`: explicit key-pose Action authoring with front-axis and optional
  root/pelvis location channels.
- `blender-import-humanoid-animation`: explicit hash-pinned Mixamo-style FBX import, exact
  17-role source/target mapping, parent-local chain collapse, direction swing/local-Y twist
  transfer through `Bone.convert_local_to_pose()`, independent bound Action, owned Source
  Collection and rollback. A real Adobe Mixamo Walking FBX passed 32-frame automatic checks and
  explicit multi-view acceptance on the M2 Compact rig for `IN_PLACE`.
  Automatic results remain structurally qualified until a separate review receipt records an
  explicit reviewer, review time, decision and exact image hashes. Generated failed/intermediate
  runs are disposable; the Repository implementation/tests and minimal accepted evidence are the
  durable baseline.
- `blender-prepare-game-action`: user-facing non-destructive clip preparation for one explicit
  Armature Action. It evaluates an explicit range at explicit source/target FPS, rebases to frame
  0 or 1, bakes sign-continuous quaternion pose channels, optionally removes only exact redundant
  scalar samples, reports loop/root metrics and returns an independent unbound Action. A real
  accepted Mixamo-retargeted Walking range passed Mesh-pose comparison, save/reopen and multi-frame
  preview evidence. It does not repair loops, convert root motion, edit NLA or approximately reduce
  keys.
- `blender-export-animated-fbx`: engine-proven bounded Unity Generic export for one explicit local
  skinned Mesh, Armature and Object-slot pose Action. It stages without overwrite, binds only
  owned temporary data, emits one Action-named non-loop `IN_PLACE` take, and has passed fresh
  Blender reimport plus live Unity 6000.3.9f1 sampled-skin playback. Humanoid Avatar, root-motion
  conversion, loop repair and Animator Controller authoring are not included.

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

1. Execute B6 character/clothing/creature production redesign while reusing eligible M2-M4
   rig/animation/export foundations.
2. Continue B7-B8 in the official roadmap order unless a concrete user request justifies a
   documented bounded dependency.

Unity Humanoid Avatar/root-motion work remains a separate optional gate only when a concrete game
requires it; Generic animated FBX is already engine-proven and must not displace B2.

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
| 4 | Kiln 1.5.0 | broader procedural static props/environment provider | tested only in the approved isolated evaluation folder; an existing field-cannon GLB passed optional hash-verified import and the bounded B3 explicit-map/end-region revision. Kiln remains non-required; this is not native-owned or arbitrary imported-Mesh compatibility |
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
- The initial real Mixamo global-rest-delta result is retained as rejected evidence. The corrected
  parent-local swing/twist conversion passed the same real Walking FBX, all 32-frame numerical
  checks and explicit Source/Target multi-view review on M2 Compact. Acceptance is limited to the
  17-role `IN_PLACE` scope; root transfer and omitted finger/toe/facial motion remain unproven.
- Static FBX export is tested. Rigged/animated FBX is engine-proven for one local Mesh/Armature,
  one explicit Action, Unity Generic, `IN_PLACE` and non-loop clips; Humanoid Avatar and converted
  root motion remain unproven.
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

## B4 hardening and B5 static-domain breadth -- 2026-11-03

Creation v5 texture publication now uses a unique same-directory staged PNG, signature validation
and atomic no-overwrite hard-link publication. Rollback records staged ownership before saving and
deletes final files only when path identity and SHA-256 still match. Focused Blender probes covered
failure before save, a partial staged file, post-save packing, the second of two textures, a
publication race won by a simulated user file, and geometry failure after Material creation.

Revision schema `gameassetai.static-asset-revision-request.v4` is limited to an owned creation-v5
assembly. Every result Mesh is independent. Selected replacement geometry receives a fresh
deterministic local-box UV layer using the source part's recorded quarter-turn/mirror mapping;
Materials and packed Images remain shared read-only. Style, art-direction, applied-fact and
appearance provenance persist, and the original triangle budget is rechecked. This does not edit
texture pixels, Material nodes or arbitrary external assets.

Accepted Blender 5.0.1 evidence:

`D:/Blender/MCP_Test/GameAssetAI/runs/B5/20261103T040438Z-static-domain-breadth-81459f66`

One shared implementation created and revised a painted fantasy shield, an angular fantasy
lantern and a modular stone doorway. Triangle counts are 168, 148 and 182 respectively for both
original and revision. All six results retained one valid UV layer per part; the shield retained
two hashed/packed 128px textures. Eighteen immutable-pair-camera renders were explicitly reviewed
and accepted after correcting a hidden wood surface and a revised doorway connection gap. A fresh
Blender process reopened the Blend and verified semantic roles, independent Meshes, shared
Materials, packed Images and external texture hashes. This closes B5 only for these representative
static domains. It is not evidence of arbitrary noun-to-mesh generation, general unwrap, texture
painting, material revision or character/creature production.
