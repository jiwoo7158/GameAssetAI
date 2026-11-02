# Roadmap

## Current product gate -- authoritative from 2026-11-02

The Repository-wide code audit is `docs/audits/2026-11-02-repository-review.md`. It supersedes the
recovery-era work order below without deleting its history.

Decision: retain the Repository and its proven safety, installation, animation, Generic Unity
export and optional 2D foundations, but redesign the core creation/revision/style layer. Do not
start another narrow validator, render pass or export variant before this gate is resolved.

The user selected **B: retain proven infrastructure and redesign the core production layer**.
The official active sequence is B1 through B8 below. A stage is not a blanket approval of the
next stage; each implementation still needs a bounded work package, representative Blender asset,
visible/semantic acceptance and explicit non-goals.

### Completed work package: static production v3 -- 2026-11-02

- Requirements: `REQ-STATIC`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`, bounded `REQ-WORKFLOW`.
- Reuse: `blender-create-static-asset`, its v1/v2 validator and ownership/rollback mechanics,
  material creation, semantic roles, copy-only revision, router and Artifact Lifecycle.
- Gap: native creation stops at four primitives and revision changes whole-part transforms rather
  than an authored silhouette.
- Implementation boundary: one explicit Blender-native profile-extrusion geometry operation,
  copy-only profile replacement for an owned semantic part, enforceable low-poly style facts and
  a minimal router/contract update. No character, texture painting, arbitrary imported-Mesh edit,
  general text-to-3D, new external dependency or new Skill.
- Validation asset: a Stylized Low-Poly Fantasy Axe whose blade uses an authored profile, plus a
  copy revision that widens and sharpens that profile. A second non-weapon profile part checks that
  the operation is not axe-hardcoded.
- Acceptance: actual Mesh vertices change rather than Object scale; source coordinates/materials
  remain exact; unchanged parts remain exact; budget/material/flat-shading rules are enforced;
  induced failure rolls back only owned data; Blender 5.0.1 saves/reopens the result; front, side
  and three-quarter evidence is recorded for explicit visual review.
- Non-goals: automatic prompt parsing, arbitrary Mesh semantic discovery, UV/texture authoring,
  Boolean/sweep framework, character work, Add-on expansion and Unity revalidation.
- Approval already supplied by the user: implement this bounded first B-plan production path and
  safely update the installed Skill after focused validation.

Result: accepted within the bounded contract. `PROFILE_EXTRUSION` creates real authored silhouette
geometry; revision v2 replaces one owned semantic part's Mesh on an independent copy. A six-part
stylized axe, its wider/sharper blade revision and a non-weapon shield passed preservation,
rollback, budget/material/flat-shading, multi-view visual review and fresh-process Blend reopen.
Both changed Skills are hash-aligned with their backed-up Workspace installations. Evidence:
`D:/Blender/MCP_Test/GameAssetAI/runs/B1-static-production-v3/`
`20261102T041656Z-stylized-axe-profile-61d8ca68`.

### Completed work package: B1.1 static profile correctness -- 2026-11-02

- Requirements: `REQ-STATIC`, `REQ-COST`, `REQ-SAFE`, bounded `REQ-WORKFLOW`.
- Reuse: static assembly v1/v2/v3 contracts, `PROFILE_EXTRUSION`, owned semantic revision,
  Artifact Lifecycle, the accepted axe/shield requests and existing Workspace deployment tools.
- Concrete gap: the v3 side-face winding has not been proven outward, the offline polygon guard
  misses non-adjacent repeated vertices, endpoint-on-edge contact and collinear overlap, and the
  B1 original/revision renders use independent framing that weakens size comparison.
- Affected files: the shared and packaged static creation/validation scripts, focused request and
  Blender workflow tests, the existing static Skill contract, router only if status text changes,
  and the active roadmap/memory/session documents.
- Validation assets: regenerate the B1 stylized axe, wider/sharper revision and profile shield;
  add convex and concave profile mesh-quality probes and same-camera comparison views.
- Acceptance: outward cap/side normals, positive signed volume, closed manifold geometry, no
  zero-area faces or duplicate coordinates, actual triangle count/spec consistency, strict
  rejection of repeated/contacting/overlapping invalid profiles, preservation/rollback/reopen,
  and recorded visual review using identical cameras for original/revision pairs.
- Non-goals: B2 modeling operators, arbitrary polygon libraries, external-mesh editing, character,
  animation, Unity, Add-on expansion, external dependencies or broad Skill consolidation.
- Skill cleanup boundary: reassess the one deprecated and eight consolidate candidates against
  current callers/installations. Remove only evidence-proven dead exposure; retain unique or
  package-required implementations and record the deferred consolidation reason.
- User approval: supplied by the current B1.1 request, including focused Repository/Workspace
  cleanup and hash-checked installation of changed Skills.

Result: accepted within the bounded correctness contract. Side winding is outward; cap and side
normals, closed-manifold edges, positive expected signed volume, non-zero faces, unique vertices
and actual triangle/spec consistency are enforced at creation. The validator rejects repeated,
touching, overlapping and backtracking profiles while accepting a valid concave profile. The
original/revised axe comparison uses one immutable camera frame per view with Backface Culling;
preservation, rollback, legacy v1/v2, save/reopen and installed-Skill execution passed. Evidence:
`D:/Blender/MCP_Test/GameAssetAI/runs/B1.1-static-profile-correctness/`
`20261102T085327Z-final-axe-shield-profile-quality-d6053ce7`.

## Official B-plan production sequence

### B1 -- Foundation static production (complete)

Legacy primitive assembly, explicit semantic parts, `PROFILE_EXTRUSION`, independent geometry
replacement, bounded low-poly style constraints, ownership and rollback are implemented. Accepted
axe/shield evidence proves only this bounded profile-based workflow, not general modeling.

### B1.1 -- Profile mesh correctness (complete)

Correct and prove cap/side winding, strict rejection of degenerate/self-contacting profiles,
closed-manifold and positive-volume output, actual triangle/spec consistency, and identical-camera
original/revision comparison. Completion requires regenerated axe, wide/sharp axe and shield
evidence plus legacy v1/v2/v3 regression, preservation, rollback and fresh-process reopen.

### B2 -- Expand static shape production (complete in bounded profile-beveled scope)

Add only the shape operations demanded by representative assets: section variation/taper,
bounded bevel/chamfer, inset/extrude, improved profile solids and, only when justified, sweep or
Boolean and real part joins. Completion requires creation and semantic revision of at least two
asset types that profile extrusion alone cannot express. B1.1 correctness is the entry gate.

#### Completed work package: B2 profile-beveled solids -- 2026-11-02

- Requirements: `REQ-STATIC`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`, bounded `REQ-WORKFLOW`.
- Reuse: Static Asset v1-v3, B1.1 profile validation and mesh-quality checks, semantic metadata,
  copy-only geometry replacement, ownership/rollback, shared-camera review, Artifact Lifecycle and
  hash-checked Workspace update.
- Concrete gap: constant-depth profile prisms cannot represent a real cutting bevel, a machined
  crate perimeter or a raised/recessed panel transition.
- Implementation boundary: add creation v4/revision v3 and one reusable
  `PROFILE_BEVELED_EXTRUSION` geometry kind. It lofts an explicit outer silhouette ring at the
  center plane to matching explicit core-profile rings at the front/back depth, producing real
  sloped faces. No general bevel modifier, inset/extrude operator family, Boolean, sweep, UV or
  external dependency.
- Validation assets: a stylized fantasy axe with a real beveled cutting solid and copy revision
  that widens the bevel/thins the tip; a reinforced supply crate whose chamfered body and front
  panel use the same operation, plus a copy revision changing body corner treatment and panel
  depth.
- Acceptance: both assets are recognizable and not mere overlapping boxes; actual Mesh vertices
  and cross-sections change without Object scale; core/outer correspondence is valid; output is
  closed, outward, positive-volume and within triangle/material budgets; source/unrelated parts
  and materials remain exact; invalid correspondence and induced failure roll back; shared-camera
  front/side/three-quarter images receive explicit hash-bound visual review; save/reopen and
  installed-Skill execution pass while v1-v3 remain compatible.
- Visual-review closeout: reuse the existing hash-bound review receipt pattern; render success
  remains separate from reviewer decision and cannot mark the run accepted by itself.
- Non-goals: B3 arbitrary external-Mesh revision, B4 UV/textures or broad styles, new asset-noun
  Skills, characters, animation, Unity, Add-on UI, external packages or a general modeling DSL.
- User approval: supplied by the current B2 request, including focused Workspace installation
  after successful representative validation.

Result: creation v4/revision v3 add `PROFILE_BEVELED_EXTRUSION`, a matched outer/core profile
solid with real sloped bands. The same operation produced and copy-revised an accepted fantasy
axe cutting solid and reinforced crate body/panel. Closed-manifold, outward-normal,
positive-volume, budget, preservation, rollback, shared-camera visual review and fresh-process
reopen passed. This completes B2 only for bounded matched-profile bevel/chamfer and panel forms;
general Blender Bevel, arbitrary inset/extrude, sweep, Boolean and connected-part authoring remain
unsupported. B3 is next.

### B3 -- Revise existing Blender/external static assets

Accept explicit `.blend`/`.glb` and Object-to-semantic-part mappings, preserve the source, create
an independent copy, modify selected real geometry and retain unrelated parts/materials. Do not
claim automatic semantic inference. Completion requires one representative non-GameAssetAI
multi-object asset.

#### Completed work package: B2 correspondence hardening and B3 external-region revision -- 2026-11-02

- Requirements: `REQ-STATIC`, `REQ-SAFE`, bounded `REQ-WORKFLOW`; preserve B2 `REQ-STYLE` and
  `REQ-COST` evidence.
- Reuse: Static Asset v1-v4, Kiln GLB hash/import delta inventory, explicit role maps, copy-only
  ownership/rollback, Blender Mesh copying, Artifact Lifecycle, hash-bound visual review and
  Workspace update.
- Confirmed starting B2 gap: individually valid nested profiles could use a shifted/twisted
  correspondence; the pre-B3 validator accepted the supplied square counterexample although its
  connectors crossed.
- B2 boundary: reject crossing connectors, core edges leaving a concave outer polygon and a
  non-minimal cyclic correspondence. Do not add a general polygon library or new Validator Skill.
- B3 boundary: one explicit external `.glb` path/hash; exact Mesh Object-to-role mapping; import to
  an isolated source Collection; independently copy mapped Mesh Objects; apply one declared local
  axis-aligned region transform to selected vertices of mapped roles; retain topology, unchanged
  vertices, UV layers, material references, Object transforms and imported Empty-only hierarchy.
  Refuse modifiers, Shape Keys, vertex groups, linked data and shared mutable result Meshes.
- Representative evidence: the existing licensed/evaluated Kiln field-cannon GLB as an
  `EXTERNAL_INPUT`; lengthen the explicitly mapped left/right trail end regions while preserving
  the body, barrel, wheels and other parts. The Skill must not depend on this private path or Kiln
  runtime.
- Acceptance: original file/hash and imported source data remain exact; output Mesh data is
  independent; only the declared role/vertex region changes; unrelated objects/materials/UVs and
  transforms remain exact; unsupported input/name conflicts and induced failure leave no owned
  residue; shared-camera images receive explicit review; save/reopen and installed execution pass.
- Non-goals: automatic semantics, arbitrary free-form editing, `.blend` ingestion in this first
  path, topology replacement, UV generation, modifier/Shape Key support, B4 style/texture work,
  new Skill, Add-on UI or external packages.
- User approval: supplied by the current B3 request, including use of an existing local external
  asset and focused Workspace installation after validation.

Result: the shifted-square counterexample was reproduced and is now refused. V4 additionally
requires strictly nested profiles, nearest cyclic index alignment, internal core edges,
non-crossing connectors and stable bevel width; the accepted B2 axe/crate requests still pass.
External-revision v1 imports an explicit hash-pinned static `.glb`, requires a complete unique
Mesh Object/role map, copies every result Mesh independently and applies only
`LOCAL_AXIS_END_OFFSET` to an explicitly bounded vertex region. The 13-part Kiln evaluation field
cannon passed source/hash preservation, two-trail end extension, unrelated-part/material/UV/
transform preservation, name/hash refusal, induced rollback, shared-camera visual acceptance and
fresh-process reopen. This completes B3 only for that bounded GLB/static/no-modifier contract;
`.blend`, automatic semantics, arbitrary selection/topology edits, modifiers, Shape Keys, vertex
groups and linked data remain unsupported. B4 is next.

### B4 -- Game-specific art direction, materials and textures

Connect Workspace Profile and explicit request decisions to silhouette, proportion, shape
language, material/shading, UV/texture policy and polygon/texture budgets. Completion requires the
same class of asset in two visibly different styles through geometry and surface treatment, not a
color-only variant. Stylized Low-Poly is evidence, not a global default.

### B5 -- Broaden static asset domains

Reuse common operations across weapons/armor, props/furniture, machinery/devices,
architecture/structures and natural environment assets instead of adding one Skill per noun.
Completion requires creation and follow-up revision in at least three different domains.

### B6 -- Redesign character, clothing and creature production

Develop style-aware character shapes, hair/clothing/equipment, varied proportions,
deformation-conscious topology, non-humanoid routes and partial revision. Reuse the proven bounded
M2-M4 rig/animation/export path where eligible; do not equate the CC0 human template with general
character generation. Completion requires an accepted styled character and components with a
real downstream handoff where supported.

### B7 -- Natural-language integrated production and Blender Add-on

Turn requests into explicit creation specifications, route internal production modules, present
actual Blender previews, apply user revisions and invoke output Skills. Earlier stages retain
minimal natural-language routing; B7 is the full create-review-revise-output user experience.
Completion requires a fresh Codex session to execute a representative end-to-end workflow.

### B8 -- Real-project proof and product-surface consolidation

Validate actual Unity-project use, game-specific budgets, 2D/animation integration, a smaller
user-facing Skill surface, internal-helper consolidation, packaging-copy management and practical
Add-on use. Safe removal of a proven dead Skill may happen earlier; B8 is not an excuse to keep
known misleading exposure. Completion requires representative real-project workflows and aligned
Repository/Workspace documentation and installation.

## Recovery priority — authoritative from 2026-10-25

> Historical implementation sequence. Retained for traceability; it no longer sets priority.

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
- [x] representative explicit-landmark A-pose rig fitting and weight-adaptation workflow
- [x] generated-character 18-bone rig and deterministic first-pass region weights
- [x] first live six-bone pose/deformation review on the retained character
- [x] experimental shoulder/hip copy mechanics tested; product evidence invalidated by rejected input topology
- [x] add backward-compatible v2 two-bone transition weights and live six-bone pose smoke test
- [x] real Mixamo `IN_PLACE` round-trip validation on an actual M2 humanoid asset
- [x] installable hash-pinned Mixamo-style FBX import and explicit pose-space retarget workflow
  with rollback, saved/reopened Action and visibly deformed M2 target evidence
- [x] replace the rejected global rest-delta bake with parent-local chain collapse plus
  swing/twist rest-basis alignment; real Walking passed 32-frame and multi-view acceptance
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
- [x] rig/deformation review on the compact and lanky canonical-template outputs with installed-Skill proof
- [x] real Mixamo-downloaded Walking FBX import and bounded `IN_PLACE` retarget proof
- [ ] M2-character upload/download service round trip and `TRANSFER` root-motion proof
- [x] bounded single-Mesh/single-Armature/single-Action animated FBX export and Unity Generic
  import/playback proof (`IN_PLACE`, non-loop)
- [x] representative imported/existing Action range/FPS preparation with evaluated-pose baking,
  exact redundant-key cleanup, source preservation and saved/reopened real Walking evidence
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
- M2 result: `blender-rig-character-base` schema v3 now fits the retained 18-bone hierarchy from
  explicit object-local A-pose landmarks and generates normalized, same-side, four-influence
  envelope weights. Compact/Lanky shoulder, elbow, hip and knee probes passed structural,
  visual, rollback and saved/reopened gates. Lanky knee minimum face-area ratio improved from
  0.052 to 0.732. This is accepted for the explicit-landmark/template scope, not arbitrary
  automatic humanoid rigging.
- M3 result: `blender-import-humanoid-animation` performs hash-pinned FBX import, exact 17-role
  mapping, parent-local swing/twist conversion and a new bound Action with owned rollback. The
  real Adobe Mixamo Walking FBX passed 32-frame structure/direction/clearance checks, save/reopen
  and explicit Front/Side/Three-quarter acceptance on M2 Compact for `IN_PLACE`.
- M3.4 result: `blender-prepare-game-action` creates an independent unbound game clip from one
  explicit Armature Action using evaluated-pose range/FPS sampling. It supports Bezier/missing
  boundary keys beyond the strict extractor, preserves source references, bounds sampled-pose
  error and reports loop/root facts without automatic repair. Real Walking frames 1-24 passed
  representative Mesh comparison and reopen; the partial range is explicitly not a seamless loop.
- M4 result: `blender-export-animated-fbx` stages one selected Action on owned temporary rig data,
  preserves an unbound prepared Action/source state, emits an Action-named FBX take and passed
  fresh Blender 5.0.1 skin/pose comparison plus Unity 6000.3.9f1 Generic clip playback. Humanoid
  Avatar, root-motion conversion, loop repair and Animator Controllers remain separate gaps.
- Next implementation boundary: return to broader native static modeling/semantic revision unless
  a concrete Unity Humanoid or root-motion requirement is explicitly selected.

### Artifact lifecycle gate -- 2026-10-28

- [x] make Repository source independent of private validation-output directories
- [x] add unique run manifests, verification and manifest-gated dry-run/apply cleanup
- [x] separate external inputs and Workspace state from cleanup-owned outputs
- [x] require explicit reviewer/time/image hashes/findings for M3 visual acceptance receipts
- [x] use the standard run structure for imported-Action cleanup validation

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
- [x] bounded Mixamo animation-FBX rig import and 17-role `IN_PLACE` retarget on M2 Compact
- [ ] M2-character Mixamo upload/download round trip and `TRANSFER` root-motion approval
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
