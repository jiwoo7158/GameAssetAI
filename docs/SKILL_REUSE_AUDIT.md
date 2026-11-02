# Existing Skill reuse audit -- 2026-10-25

> **Historical 43-Skill snapshot.** The Repository now has 46 Skill folders and later M1-M4
> evidence. Current per-Skill recommendations are maintained in
> `docs/audits/2026-11-02-skill-assessment.tsv`; use this document only for the recovery-era
> reasoning it preserves.

## Decision

No existing Skill is deleted. There are 43 Skill folders; 42 contain executable helpers and the
remaining `blender-create-game-asset` is intentionally routing-only. This does not mean 43
separate product features. The router/Add-on should expose a small workflow surface and treat most
Skills as internal or opt-in stages. None is wholly unrelated to Blender game-asset work, but
several were implemented too early or split too narrowly relative to the unfinished creation,
deformation and engine round-trip spine. Those Skills are retained without further expansion.

The current v3 Boolean character corrects the rejected left/right fusion, but it is still a
blockout surface: the live Mesh has 118 quads, 212 triangles, 43 ngons and 324 poles. Structural
closure plus a readable silhouette does not make it deformation-ready. Default routing must not
jump from visual acceptance directly to product rigging until topology/UV/deformation criteria are
defined and passed.

## Current creation spine

| Skill | Use now | Required improvement |
| --- | --- | --- |
| `blender-create-static-asset` | Low-poly props, weapons and simple environment assemblies | more native part types and revision operations; not arbitrary text-to-mesh |
| `blender-create-character-base` | V1 separated blockout plus guarded v3 Boolean-connected blockout | add a deformation-topology/revision stage; visual acceptance alone does not permit product rigging |
| `blender-rig-character-base` | Generated-fixture rig mechanics | keep for algorithm evidence; require a deformation-ready source contract before product routing |
| `blender-adjust-character-joint-weights-copy` | Removed deprecated experiment | removed from active source/Workspace on 2026-11-02; Git history retains the rejected-input evidence |
| `blender-author-pose-action` | Explicit reviewed key-pose Actions | reusable motion templates and safer editing of an existing Action copy |

## Reusable supporting groups

### Inspect before modifying

`blender-inspect-asset`, `blender-validate-static-mesh`, `blender-inspect-humanoid`,
`blender-inspect-animation` and `blender-inspect-mixamo-preflight` remain useful entry checks.
They must not be presented as creation completion.

### Non-destructive revision and preparation

`blender-cleanup-loose-geometry`, `blender-simplify-coplanar`,
`blender-prepare-positive-scale`, `blender-relocate-pivot-copy` and
`blender-create-static-lod-copy` are usable after a source asset exists. Their narrow copy-only
contracts are appropriate and should remain separate from generation.

### Existing-animation adaptation

The Action inventory/copy/range/binding/replacement, loop/root/evaluated-pose inspection,
retarget-readiness, aligned remap, rotation bake, root bake and composition Skills form a coherent
adaptation chain. They are useful for imported or existing animation, but they do not create a
rig, choose a bone mapping or prove a Mixamo round trip. Route them only after explicit inspection.

### Downstream output

Static/Action pixel rendering, mixed 2D batch, sprite-sheet assembly, silhouette/material/object
masks, normal/depth/object-ID passes and impostor bundles are reusable after creation. The Add-on
now exposes the principal style, sequence and sheet paths. Advanced passes remain opt-in.

### Optional engine/static preparation

`blender-export-static-fbx` is usable only for its texture-free static contract. Collider and LOD
inspectors are diagnostics for explicit existing candidates. None is a character generator or a
rigged Unity exporter.

## Product exposure classification

- **Core workflow entry:** router, static creation, character creation, rig/adaptation, Action
  authoring/editing, static/rigged export and the Add-on.
- **Internal backend primitives:** inspection, Action copy/range/bind/replace, loop/root-motion,
  retarget/bake/compose, cleanup, scale and pivot Skills. Retain them, but do not require users to
  choose among them manually.
- **Core optional 2D output:** static PNG, Action sequence and sprite-sheet assembly. Batch is an
  internal coordinator.
- **Advanced opt-in only:** masks, normal/depth/object-ID passes, impostors, collider and LOD
  diagnostics/copies. Preserve but stop expanding them until core asset workflows pass.
- **Suspended from product routing:** character `VOXEL_CONNECTED` and joint-weight refinement on
  that topology. Their code/evidence remains for diagnosis, not default use.

## Keep, consolidate, freeze, or suspend

### Keep and actively develop

- `blender-create-game-asset`, `blender-create-static-asset`,
  `blender-create-character-base`, `blender-rig-character-base` and
  `blender-author-pose-action` form the creation spine.
- The Add-on remains the repeatable UI layer, not a replacement for those capabilities.
- Inspection of an existing asset/humanoid/animation remains first-class because the product must
  work with assets that were not generated by GameAssetAI.

### Keep but consolidate behind workflows

- Action copy/range/bind/replace, loop/root-motion checks and retarget/bake/compose helpers are
  technically useful. They should appear as one imported-animation adaptation workflow rather
  than a menu of micro-Skills.
- Cleanup, positive-scale and pivot-copy helpers should appear as one static preparation workflow.
- Static PNG, Action sequence, sprite sheet and batch remain the core optional 3D-to-2D workflow.

### Freeze at maintenance-only

- Material/object/silhouette masks, normal/depth/object-ID passes and impostor bundles are valid
  downstream tools, but no additional pass-only Skills should be added before core asset work.
- Collider and LOD inspection/copy are relevant optional preparation, but must not consume current
  creation, rigging, Mixamo or animated-export priority.
- The narrow static-only FBX exporter is useful as-is; extend export through a separate reviewed
  rigged/animated path rather than distorting its contract.

### Suspend from product claims

- `blender-adjust-character-joint-weights-copy` was removed from the active Skill surface after
  confirming that it had no current caller and only rejected-source evidence. Restore from Git
  history only if a future accepted character requires that exact bounded operation.
- `VOXEL_CONNECTED` is rejected historical code inside the character Skill.
- Generated-rig and Action results produced from rejected topology are not character-quality
  evidence even when their individual mechanics passed.

## Gaps requiring new or expanded implementation

1. turn the v3 connected blockout into, or replace it with, deformation-suitable topology with
   explicit edge-flow, self-intersection, UV and pose-deformation gates;
2. controlled semantic revision of generated and existing Meshes rather than regeneration only;
3. accepted-topology rig/deformation validation followed by existing-character rig adaptation;
4. actual Mixamo import/round-trip validation;
5. editing/polishing an existing Action through a reviewed copy;
6. rigged/animated FBX or GLB export plus Unity import verification;
7. broader native static modeling beyond primitive assembly.

Persistent Add-on installation, hash/version inspection, transactional update/restore and
fresh-process survival are complete and move to maintenance rather than remaining a product gap.

Development should expand these gaps in that order before adding more auxiliary render-pass or
Unity-only Skills.

## Relationship to the Add-on

The Add-on is the repeatable UI/execution layer over these Skills, not a competing implementation.
Scene/compositor setup, material preview, Action selection, single PNG, sequence dispatch and
sprite-sheet handoff already exist. Multi-item batch UI and true live Pixel/Cel preview remain
deliberately deferred and are retained in `docs/IMPLEMENTATION_MEMORY.md`. When a Skill gains a
stable repeatable workflow, prefer a thin Add-on bridge to copying its implementation into UI code.

## Deployment evidence

The routing Skill is packaged at `.local/source-bundles/blender-create-game-asset.zip` (2,801
bytes, SHA-256 `a22c2b0f347cd9232ed9277da491e2860d81cd56a52678f61caa2acb935a1286`) and deployed hash-aligned
to `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-create-game-asset`. Client discovery still
requires a refreshed Codex session and is not inferred from file deployment.
