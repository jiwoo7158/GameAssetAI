# Roadmap

## Recovery priority — authoritative from 2026-10-25

The detailed checklist below is retained as implementation history, but it no longer determines
work order. See `docs/PROJECT_AUDIT.md` for the evidence and scope correction.

Durable capability status and deferred UI work are maintained in
`docs/IMPLEMENTATION_MEMORY.md`. An unchecked deferred UI item remains part of the product even
when character, rigging or export work has higher priority.

- [x] preserve the former append-only session log without deleting it
- [x] establish a concise active continuation checkpoint
- [x] reverse the unsupported Blender Add-on deferral
- [x] Blender Add-on Scene Preset Builder, panel and exact cleanup
- [x] Blender Add-on Compositor Node Preset Builder
- [x] package Add-on 0.1.0 and register its panel/operators in the live Blender session
- [x] Blender Add-on reversible material/shader preset module
- [x] Blender Add-on single PNG, Action-sequence and sprite-sheet export bridges backed by proven helpers
- [x] creation-request router separating static, character, rig and animation workflows
- [x] native recognizable static prop/weapon creation foundation with a four-part sword fixture
- [x] live viewport review and wedge-tip revision of a created non-Cube sword asset
- [x] representative low-poly character base-mesh creation foundation
- [x] visible live Workbench character creation and multi-angle review
- [x] replace rejected global-voxel character connection with guarded v3 Boolean topology that preserves bilateral limb/foot clearance
- [ ] representative rig creation/adaptation workflow
- [x] generated-character 18-bone rig and deterministic first-pass region weights
- [x] first live six-bone pose/deformation review on the retained character
- [x] experimental shoulder/hip copy mechanics tested; product evidence invalidated by rejected input topology
- [x] add backward-compatible v2 two-bone transition weights and live six-bone pose smoke test
- [ ] real Mixamo round-trip validation on an actual humanoid asset
- [x] reusable authored pose Action creation workflow on a real Armature
- [x] user-reviewed 36-frame upper-body Ready Loop v3 with stable lower body
- [x] package and focused-test the front-axis-guarded pose Action authoring Skill
- [x] author and visually inspect the first `-Y`-consistent Walk Loop through that Skill
- [x] refine walk foot contact and root height
- [x] end-to-end non-Cube Blender creation -> style -> 2D output proof
- [ ] resume Unity import/configuration work using that representative asset

### Next asset-system work

- [x] suspend `VOXEL_CONNECTED` and its weight refinement in default routing instructions
- [x] enforce the suspension in the character request validator and regression tests
- [x] implement guarded v3 Boolean-connected topology with component, manifold and bilateral-clearance gates
- [ ] complete user-visible multi-view acceptance of the v3 blockout
- [x] implement an optional hash-pinned CC0 canonical-template path that preserves all-quad
  topology and UVs across two non-affine proportions, with rollback and saved-file evidence
- [ ] pass representative visual deformation acceptance; lanky knee compression and the
  blockout-rig mismatch prevent promotion to accepted deformation-ready output
- [x] install and enable the Blender Add-on in saved Blender 5.0 Preferences
- [x] add guarded read-only Add-on source/installed version, compatibility and hash checking
- [x] verify saved Preferences load and register the Add-on in a fresh Blender 5.0.1 process
- [x] add hash-bound transactional Add-on update/rollback with preserved prior/replaced versions
- [ ] rig/deformation review on accepted deformation topology, then existing-character rig adaptation
- [ ] real Mixamo import/round-trip/retarget proof
- [ ] rigged/animated FBX or GLB export and Unity import proof
- [ ] reviewed existing-Action copy editing and motion-template workflow
- [ ] broader native static modeling and controlled semantic revision

### Proposed planning boundary for the next implementation

The first isolated technology experiment for the deformation-topology/revision stage inside the
existing `blender-create-character-base` Skill is complete. Production integration has not been
approved.

- Requirements: `REQ-CHAR`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`.
- Reuse: current proportion/material/front-axis/ownership/rollback code, generic mesh diagnostics,
  existing rig only as a later deformation probe, and the Add-on for review.
- [x] Evaluate native QuadriFlow and ReQuad 0.11.3 on disposable copies of two humanoid
  proportions in Blender 5.0.1. Neither was installed or integrated.
- Follow-up result: the direct-input refusal was traced to Blender's `1e-4` QuadriFlow micro-edge
  preflight. A bounded post-Boolean cleanup is now part of the existing generator and lets native
  QuadriFlow run on both representative proportions. This does not make the outputs acceptable:
  QuadriFlow produced widespread zero-area UV faces, intersection candidates and generic joint
  grids; ReQuad's engine OBJ output itself retained open boundary/non-manifold edges. The shared
  voxel preparation remains rejected because it damages foot/lower-body separation.
- Decision: current candidates are **C / not integration-ready**. RetopoFlow remains only a
  possible human-guided aid; do not proceed to it or install anything without a separate request.
- Expected project-owned gap: semantic joint-loop contract, self-intersection checks,
  deterministic UV policy and representative pose-deformation acceptance.
- Non-goals: arbitrary-mesh automatic retopology, Mixamo round trip, new rig system, export,
  additional render passes or a new Skill.
- Completion: preserved source; connected manifold output; no ngons; bilateral clearance; no
  unintended self-intersection; explicit elbow/knee/shoulder/hip loop evidence; valid UVs; and
  accepted front/side/three-quarter representative rest and bent-joint views.
- Failure: source mutation, semantic bridging, invalid topology/UV, unacceptable silhouette or
  deformation, or reliance on an unapproved dependency. Roll back only owned output.
- [x] Implement the confirmed bounded micro-edge cleanup and repeat the native/open-source gate on
  compact and lanky inputs without whole-body voxel fusion.
- [x] Evaluate a reusable canonical topology source with two proportions and common elbow/knee
  bends: Blender Studio Human Base Meshes v1.4.1 and pinned MakeHuman v1.3.0 CC0 body/height targets.
- Result: Blender Studio's stylized body is the provisional preferred source. It is directly
  appendable, one-component/closed/all-quad, UV-complete and visually survived the bounded bend;
  MakeHuman offers stronger target breadth but its raw data did not prove a rigging handoff, and
  MPFB 2.0.18 remains uninstalled/unverified as an automation dependency.
- Implemented decision: schema v4 `DEFORMATION_TEMPLATE` is an explicit optional path inside the
  existing Skill. It duplicates a hash-pinned Blender Studio v1.4.1 CC0 Mesh, retains topology and
  UV loops, applies bounded regional proportions, records provenance and preserves v1/v3 native
  paths. Compact and lanky Blender 5.0.1 Armature probes pass structural/reopen checks, but visual
  acceptance remains open because the lanky knee reached a 0.052 local face-area ratio and the
  generated-fixture rig does not fit this template without probe-only refitting.
- Next implementation boundary: adapt/fit the existing rig and weights to an explicit existing
  humanoid Mesh, then repeat elbow/knee/shoulder/hip visual gates. Do not add another topology
  provider or call v4 product-ready until that gate passes.

### Retained Add-on/UI work

- [ ] true live Pixel/Cel preview viewport or dedicated preview workspace
- [ ] multi-item static/Action batch queue UI using the existing batch coordinator
- [ ] background progress/cancel surface
- [ ] active Profile picker with refresh and fingerprint display
- [ ] richer Action comparison/timeline/loop review controls
- [ ] sprite-sheet preview and cell inspection
- [ ] additional camera, lighting, material, palette, shading and outline controls
- [x] persistent Blender Preferences installation plus read-only installed/source verification
- [x] transactional Add-on update/rollback
- [x] fresh-process restart-survival verification
- [ ] advanced-pass UI bridges after core asset workflows stabilize

Until the first Add-on and creation vertical slices pass, do not expand collider, Unity
LODGroup, auxiliary render-pass or synthetic retargeting scope.

## Historical implementation ledger

This roadmap is intentionally capability-oriented rather than a fixed list of five skills.
Current active target is Unity and local use in GameAssetAI-Workspace. Unreal-specific
work and external/public distribution were removed from scope on 2026-09-21;
existing projects, historical tests and local Skill installation are preserved.

## Foundation

- [x] offline repository/template validation and workspace creation regression tests
- [x] document and test the minimal profile/project-mapping file contract
- [x] verify Blender MCP (native inspection, screenshot, scratch change/restore, error behavior on 5.0.1)
- [x] explicit workspace-profile reading/switching to live diagnostics in current session
- [x] fresh Workspace Profile A/B/null switching and exact restoration (user-reported)
- [x] document current Blender / Unity versions used in testing
- [x] define synthetic Blender inspection/static diagnostics fixtures

Synthetic fixtures exist under `tests/workspace/`, `tests/blender-scene/`, and
`tests/static-mesh/`. Imported production fixtures remain unverified; explicit current-session
switching and user-reported fresh Workspace Profile A/B/null behavior passed.

Profile evidence: `docs/profile-workflow-validation.md`. Installed Skill session exposure
and explicit calls, three read-only natural-language outcomes and synthetic apply/restore
were confirmed by the user. Raw routing traces remain
packaging evidence gaps. See `docs/skill-session-validation.md`.

## Asset inspection

- [x] scene inventory (read-only native helper, Blender 5.0.1)
- [x] mesh statistics (base mesh, not final export topology)
- [x] material inventory (referenced datablocks/node types)
- [x] armature inventory (rest bones/parent/deform flags)
- [x] Action / animation inventory (bindings/slots/NLA, not keyframe editing)

Evidence: `docs/inspection-validation.md`. Source helper/fixture tests passed;
raw client routing traces and imported production assets still require validation.

## Static assets

### Active work package: optional Kiln GLB import boundary (2026-10-27)

- Requirements: `REQ-STATIC`, `REQ-COST`, `REQ-SAFE`.
- Reuse: the existing `blender-create-static-asset` validator/helper, ownership receipts and
  rollback discipline, plus Blender 5.0.1's native glTF importer.
- Gap: an already generated Kiln GLB can be inspected manually, but cannot enter the Skill's
  guarded Blender workflow with a verified source hash and explicit semantic-role mapping.
- Change: add one optional import mode to the existing Skill. It imports an explicit GLB into a
  new owned Collection, records Kiln provenance, identifies all created data and rolls back the
  synchronous import delta on any failure.
- Non-goals: running Kiln, prompt routing, replacing native v1/v2.1, semantic revision of imported
  topology, general GLB framework, Add-on, character, animation, 2D or Unity work.
- Affected files: the existing static-asset Skill and its two mirrored helper scripts, one focused
  Blender test, this active record/session checkpoint and the existing static validation record.
- Representative evidence: the preserved Kiln 1.5.0 field-cannon GLB at
  `D:/AI/GameAssetAI-Kiln-Evaluation-20261027/field-cannon-base.glb`.
- Acceptance: exact SHA-256 and complete unique role mapping are required; import preserves all
  prior Scene/Object/Mesh/Material state; invalid hash fails before import; incomplete mapping
  fails after import and removes only the newly created delta; successful receipt accounts for
  imported meshes/materials; native v1/v2.1 focused regression remains passing.
- [x] bounded schema/validator and Blender-native import adapter
- [x] Kiln 1.5.0 field-cannon positive import, invalid-hash refusal and post-import rollback
- [x] native v1/v2.1 focused regression and hash-aligned Workspace deployment
- [ ] imported-topology semantic revision compatibility (explicitly not validated)

### Active work package: copy-only semantic assembly revision (2026-10-27)

- Requirements: `REQ-STATIC`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`.
- Reuse: `blender-create-static-asset`, its strict request validator, owned-data tags,
  rollback/receipt cleanup and Blender-native primitive/material construction.
- Gap: creation v1 has meaningful part names but no machine-stable semantic roles and cannot
  revise an existing generated assembly without mutating it.
- Change: add backward-compatible creation v2 semantic roles and a copy-only geometry-transform
  revision mode in the same Skill. Preserve v1 and share source materials read-only.
- Non-goals: characters, rigs, animation, UV authoring, 2D, Unity, Add-on changes, arbitrary mesh
  editing, general text-to-3D and mandatory external dependencies.
- Affected files: the existing static-asset Skill instructions and its two helper scripts, their
  focused Blender fixture, this roadmap/session record and the existing static validation record.
- Representative evidence: two proportionally different multi-part low-poly lanterns plus a
  copied revision that changes body and handle roles while preserving the source exactly.
- Acceptance: v1 regression passes; v2 supports unique roles; revision refuses unowned/ambiguous
  sources and occupied names; induced failure leaves no owned residue; Blender 5.0.1 results pass
  structural checks and front/side/three-quarter visual review.
- External decision: Kiln is research-only in this package. Installing or integrating it remains
  approval-gated; the native path is sufficient for the bounded revision gap.
- [x] backward-compatible semantic creation v2 and copy-only revision v1
- [x] legacy creation, source preservation and induced rollback Blender 5.0.1 regression
- [x] two proportion variants plus one body/handle revision with multi-view review (run 03)
- [ ] arbitrary imported-mesh semantic revision, UV authoring and free-form topology

- [x] static mesh diagnostics (read-only, base/guarded viewport, not engine certification)
- [x] limited existing mesh loose-geometry cleanup on a copy (not general surface repair)
- [ ] non-destructive optimization
- [x] advisory optimization preflight from base diagnostics and explicit target (no edit method)
- [x] synthetic coplanar copy experiment and UV affine guard (not triangle reduction/apply Skill)
- [x] guard-enforced coplanar preview with bounded fingerprint and no persistent IDs
- [x] planar structural-simplification copy apply/rollback and self-contained source Skill
- [x] fourth Skill installed-client exposure/synthetic apply/restore (user-reported)
- [x] separate geometry/UV absolute tolerances, legacy compatibility and parameter hash tests
- [x] disconnected planar components, retained seam and incompatible UV-island refusal tests
- [ ] pivot / transform preparation
- [x] read-only mesh pivot/transform snapshot, native preservation/refusal tests
- [x] analytic positive-scale copy preview/fingerprint/freshness tests (development-only, no apply)
- [x] positive-scale independent-copy apply/output validation/rollback and narrow self-contained Skill
- [x] fifth Skill host use and instruction-led synthetic scale-apply/restore (user-reported)
- [x] representative tilted-face normal/tangent directions and isolated scale-preview overflow probes
- [x] final linked positive-scale output UV/channel/Mesh validation and rollback regression
- [x] explicit local-point pivot preview/freshness and independent-copy apply experiment (development-only)
- [x] narrow self-contained explicit-pivot source Skill, ZIP and installed-helper native regression
- [x] sixth Skill actual client exposure/instruction-led synthetic use and exact restore (user-reported)
- [ ] collider / LOD workflow
- [x] split collider inspection, collider generation, LOD inspection and LOD generation boundaries
- [x] offline explicit existing-collider candidate request contract
- [x] read-only Blender existing-collider candidate and representative fixture
- [x] package, install and regression-test a narrow existing-collider inspection Skill
- [x] refreshed-client discovery and no-candidate refusal for collider inspection
- [x] natural-language synthetic existing-collider host inspection and exact teardown
- [x] explicit existing-LOD-chain read-only inspection workflow
- [x] offline exact existing-LOD-chain request contract
- [x] read-only Blender existing-LOD-chain candidate and representative fixture
- [x] package, install and regression-test a narrow existing-LOD-chain inspection Skill
- [x] refreshed-client discovery and no-chain refusal for LOD inspection
- [x] natural-language synthetic existing-LOD-chain host inspection and exact teardown
- [ ] non-destructive independent-copy LOD generation workflow
- [x] development-only independent-copy Decimate capability experiment
- [x] explicit independent-copy LOD generation request contract
- [x] transient independent-copy LOD candidate preview, collision/dependency guards and teardown fixture
- [x] persistent independent-copy LOD apply guards and representative rollback fixtures
- [x] package/install narrow independent-copy LOD Skill and run source/installed-helper regressions
- [ ] refreshed-client LOD-copy discovery and no-candidate refusal
- [x] synthetic live Blender LOD-copy preview/apply receipt and exact teardown
- [x] development-only Unity PreviewScene LODGroup capability experiment
- [x] explicit offline Unity prefab LODGroup request contract
- [ ] Unity LODGroup request/configuration/import validation
- [x] narrow texture-free static Mesh Unity export workflow (not textured/rigged/animated)
- [x] development-only static export context and live FBX/glTF operator RNA preflight
- [x] isolated synthetic FBX file export and Blender re-import (not Unity import)
- [x] observed native FBX overwrite hazard; tested single-file no-overwrite publication
- [x] isolated synthetic FBX import and in-memory prefab instantiation in Unity 6000.3.9f1 (not production export)
- [x] explicit static FBX request preflight with fail-closed offline tests (not export)
- [x] request-hash-bound read-only Blender FBX candidate review and dependency refusal (not export)
- [x] texture-free request-bound staged FBX publication with collision/late-meta guards
- [x] staged static FBX import with identity-root fixture verification in Unity 6000.3.9f1
- [x] narrow texture-free static FBX source Skill, ZIP and installed-helper native regression
- [x] explicit hash-bound Unity static FBX import validator with positive/failure live checks

Cleanup evidence: `docs/loose-cleanup-validation.md`. Unity import evidence:
`docs/unity-import-validation.md`. Broad optimization and engine
preparation remain separate tasks; no production rig cleanup was performed.

## Character / rig

- [x] explicit-mapping read-only humanoid inspection with synthetic Blender regression
- [x] humanoid inspection source/ZIP/installed-helper regression and no-overwrite local deployment
- [ ] existing rig preservation
- [x] read-only exact-signature Mixamo preparation preflight (not upload/retarget)
- [ ] Mixamo rig import workflow
- [ ] deform-bone export policy
- [ ] Unity Humanoid compatibility checks

## Animation

- [x] read-only Action/binding/NLA/driver/F-Curve inventory Skill with explicit root mapping; source/ZIP/installed-helper Blender regression
- [x] non-destructive whole-Action copy to an explicit name with source/reference preservation
- [x] strict exact-key linear frame-range extraction into an unbound Action copy
- [x] explicit range-copy frame rebasing to frame 0 or 1, including handles/pose markers
- [ ] synthesized boundaries and source Action renaming
- [x] stored F-Curve endpoint loop-candidate inspection with explicit range/tolerance
- [x] evaluated local-basis pose endpoint comparison for an explicit complete bone list
- [x] bounded evaluated finite-difference translation/rotation/scale seam-velocity comparison
- [x] native fractional-frame pose evaluation and exact-restore capability probe
- [ ] subframe extrema, deformation and visual loop validation
- [x] explicit Object/Bone stored-translation root-motion inspection with no name guessing
- [ ] Unity/engine root-motion policy validation
- [x] read-only explicit-mapping retarget-readiness inspection with source Action coverage
- [x] strict aligned-rig name-only Action remap copy with unbound result and stale guards
- [x] differing-rest rotation-only local-basis quaternion bake on temporary rig copies
- [x] evaluated integer-frame root-motion paths in local-basis/Armature/world space
- [x] explicit-scaled root translation transfer and in-place policy into a location-only Action
- [x] strict rotation/root-translation Action composition into an unbound result
- [x] empty-target explicit Action binding with hash-bound receipt rollback
- [x] exact current-Action replacement with hash-bound receipt rollback
- [ ] retarget workflow
- [ ] animation editing
- [ ] attack / dodge / skill refinement

## Local Skill operation and validation

- [x] refreshed-session exposure and bounded call/no-target behavior for the first 13 installed Skills (user-reported)
- [x] refreshed-session exposure/no-target behavior for the retarget-readiness Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the aligned Action-copy Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the rotation-bake Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the evaluated-root-motion Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the root-translation-bake Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the retarget-composition Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the empty-target Action-binding Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the current-Action replacement Skill (user-reported)
- [x] refreshed-session exposure/no-target behavior for the Action-range extraction Skill (user-reported)
- [x] refreshed-session visibility of updated frame-rebase policies (user-reported)
- [x] refreshed-session exposure/no-target behavior for evaluated-pose-loop Skill (user-reported)
- [x] refreshed-session visibility of evaluated-pose-loop v2 velocity inputs (user-reported)
- [x] instruction-led synthetic cleanup apply/restore (user-reported)
- [x] three independent read-only natural-language outcomes (user-reported; raw traces absent)
- [ ] ambiguous removal/refusal behavior and raw routing evidence
- [x] ambiguous Cube cleanup inspection-only triage and declared Skill selection (user-reported)
- [x] seventh static-FBX Skill refreshed-session exposure and missing-policy refusal (user-reported)
- [x] seventh static-FBX Skill host-driven disposable candidate/apply/Unity-validate cleanup
- [x] hash-bound local Skill installation/update/restore tooling with isolated rollback tests
- [ ] remaining raw routing/refusal evidence for local client use

Historical package/release checklist evidence remains in `docs/`, but completing a
public release, GitHub distribution or Unreal exporter is no longer a roadmap goal.

## Planned 3D-to-2D pixel / stylized pipeline

This is an additive downstream pipeline. Existing 3D creation, inspection, Rig, Animation,
Mixamo and Unity work remains in scope and must not be replaced or duplicated. The detailed
adapted plan and safety boundary are in `docs/2d-pixel-pipeline-plan.md`.

- [x] verify Blender 5.x render/compositor/color-management/image-save capabilities through MCP
- [x] verify an isolated staged render/write and exact temporary-data/file teardown
- [x] define explicit Profile-aware view, lighting, style/pixel and output request schemas
- [x] bind static request/source/setup/output fingerprints and preview orthographic framing
- [x] isolated temporary camera/framing preview for one explicit synthetic static Mesh
- [x] isolated temporary neutral lighting/background proof with source Scene preservation
- [x] single-view Pixel render experiment with repeatable decoded low-resolution pixels
- [x] explicit fixed-palette quantization with alpha preservation and no game defaults
- [x] deterministic explicit-count automatic palette reduction with no game-specific defaults
- [x] explicit one-pixel outer silhouette validation with no game-specific defaults
- [x] explicit HSV-value step shading validation with no game-specific defaults
- [x] representative live Blender fixture with multiple observed value-step bands
- [x] staged no-overwrite single PNG workflow and narrow reusable Skill
- [x] explicit Action PNG-sequence output using existing animation inspection contracts
- [x] offline explicit Action PNG-sequence request/frame-plan contract
- [x] read-only Blender Action/slot/Mesh candidate and evaluated range-bounds fingerprint
- [x] stable union framing, isolated Mesh/Armature/Action stage and hash-bound sequence job
- [x] reopened-stage verification of binding, modifier, fractional FPS and frame deformation
- [x] staged no-overwrite PNG-sequence renderer with all-or-nothing publication
- [x] stable per-frame dimensions, alpha bounds, anchor and filename validation
- [x] refreshed-client Skill discovery and exact supported-boundary report (user-reported)
- [x] one natural-language synthetic Action render with restore/teardown evidence (user-reported)
- [x] sprite-sheet assembly with explicit layout/order metadata
- [x] refreshed-client sprite-sheet Skill discovery and natural-language call (user-reported)
- [x] optional exact Profile-backed 2D preset extraction/validation contract
- [x] integrate fresh Profile preset hashes into static/sequence/sprite-sheet Skills
- [x] explicit mixed direction/Action batch contract, hash-bound job and guarded sequential
  all-or-nothing coordinator
- [x] refreshed-client 2D batch Skill discovery and one natural-language synthetic call
- [x] evaluate optional Blender panel/operator add-on; deferred until a concrete interactive
  workflow proves value beyond the stable Skill/background-job contracts
- [x] explicit alpha-derived RGBA8 silhouette mask postprocess
- [x] explicit static base-Mesh material-slot mask with visible-surface occlusion
- [x] explicit static target-Object visibility mask with named occluders
- [x] define explicit static camera-basis normal-pass axes and RGBA8 encoding contract
- [x] read-only tilted-face normal candidate and camera-basis RGB reference probe
- [x] isolated flat/smooth shader-to-PNG probe; documented face-forward flip and byte drift
- [x] owned float OpenEXR normal stage plus deterministic CPU RGBA8 encoding
- [x] implement, package, install and regression-test the static normal pass
- [x] refreshed-client discovery and natural-language host-test the static normal pass
- [x] define, implement, package, install and regression-test a static camera-linear depth pass
- [x] refreshed-client discovery and natural-language host-test the static depth pass
- [x] define, implement, package, install and regression-test a multi-Object color-ID pass
- [x] refreshed-client discovery and natural-language host-test the Object-ID pass
- [x] define impostor support as shared-framing orchestration over existing pass Skills
- [x] define and offline-test an exact multi-pass impostor bundle request
- [x] implement and test its read-only shared-framing preview and result-manifest validator
- [x] implement atomic multi-pass staging, coordination, rollback and manifest publication
- [x] package, install and regression-test `blender-render-impostor-bundle`
- [x] refreshed-client discovery of `blender-render-impostor-bundle`
- [x] natural-language host-test the impostor bundle
- [x] offline exact Unity Sprite import/slicing request and generated-check contract
- [x] live Unity Sprite import/slicing validation on one explicit equal-cell fixture
