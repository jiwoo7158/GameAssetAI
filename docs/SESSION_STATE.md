# Current Session State — 2026-10-27

This is the active continuation checkpoint. The former 2,994-line append-only log is preserved
unchanged at `docs/session-history/SESSION_STATE-through-2026-10-25.md` (SHA-256
`be14c705251cab3f2643ed65483b2e2b4bfef7e9ae799e41139435c3b37b3039`).

Read `docs/IMPLEMENTATION_MEMORY.md` for the durable capability/backlog view. The Add-on/UI backlog
is retained there even when the immediate continuation moves to modeling, rigging or Mixamo.

## Current objective

Recover the repository around its actual purpose: reusable Blender game-asset creation and
editing Skills, a Blender-native Add-on execution/UI layer, downstream 2D pixel/cel conversion,
and optional Unity validation.

Read `docs/PROJECT_AUDIT.md` before choosing work. It supersedes the prior assumption that the
existing narrow inspection/modification Skills constitute the missing 3D generation layer.

## Current priority

1. M3 local implementation is complete for explicit hash-pinned Mixamo-signature FBX import,
   17-role pose-space retargeting and an independent bound Action. A real Adobe Mixamo download
   remains the next acceptance gate; do not call the service round trip complete from synthetic
   evidence.
2. Keep automatic mapping, existing-rig replacement, clothing/hair and corrective deformation
   outside the M3 proof.
3. Keep the completed Kiln GLB Adapter intact; refreshed-session discovery/use remains its only
   operational gate and imported data must not enter native v2.1 revision without proof.
4. After the Mixamo proof, perform imported-Action cleanup and then rigged/animated export plus
   Unity import validation.

## M3 Humanoid animation import and retarget implementation -- 2026-10-27

- Added `blender-import-humanoid-animation` with schema
  `gameassetai.humanoid-animation-import-request.v1`. It verifies an explicit FBX path and SHA-256,
  imports into a temporary Scene, reuses exact Mixamo and Humanoid inspectors, requires explicit
  17-role source/target mappings, samples pose-space rest deltas, creates a new bound Action and
  keeps the imported source in an owned Collection. `IN_PLACE` and explicit masked `TRANSFER`
  root policies are supported; varying Armature-object transforms, non-unit mapped scale, occupied
  targets and ambiguous imports are refused.
- Added a bounded Mixamo-handoff exporter for one explicit Mesh and Armature. Its Blender 5.0.1
  re-import has one Mesh, one 18-bone Armature, a valid Armature modifier and one UV layer.
- Focused evidence is under
  `D:/Blender/MCP_Test/GameAssetAI_HumanoidAnimation_M3_20261027`: an external synthetic
  Mixamo-signature FBX was imported through the real FBX API, retargeted to the M2 Compact Mesh,
  visibly changed the evaluated Mesh at frames 1/6/12, rendered front/side evidence, saved and
  reopened with its Action and retained source Collection. An induced post-import mapping failure
  restored the exact original datablock and animation baseline, including removal of fake-user
  imported Actions.
- This is implementation and local representative mechanics evidence, not Adobe Mixamo service
  evidence. No user-owned Mixamo FBX was found in the checked paths, and no upload/login/download
  occurred. Exact continuation: run the installed Skill once with a real Mixamo-downloaded FBX,
  inspect the visible motion, then perform Action cleanup before M4 animated engine export.
- Portable bundle: `.local/source-bundles/blender-import-humanoid-animation-m3.2-20261027.zip`,
  SHA-256 `27027305098a690ed064ef7c1cc37c4a291314e8c80cd923f0bb37d0f5b8cd3d`.
  The new Skill and updated router are source/Workspace hash-aligned; the installed Skill itself
  repeated the full background run and saved/reopened successfully. Router backup:
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-create-game-asset-20261027-pre-m3-router`.

### Real Mixamo Walking compatibility check -- 2026-10-28

- User-supplied Adobe Mixamo `Walking.fbx` (SHA-256
  `6411f45c8a6461c3e83a61d8884d4a4970cbd9b3f0c5a1f3de308d5f34c6e677`) imports as one
  `Armature`, one `Armature|mixamo.com|Layer0` Action over frames 1–32 and a complete required
  17-role Mixamo mapping. The installed M3 Skill created and bound `GAA M3 Mixamo Walking`, kept
  the source Armature/Action, preserved target geometry/UV/rest data and saved/reopened normally.
- Structural results and comparison renders are under
  `D:/Blender/MCP_Test/GameAssetAI_Mixamo_Walking_20261028`. The source character shows an
  ordinary walk with arms at its sides, while the M2 target folds both arms across the torso and
  over-crosses the legs. This is a **visual rejection**, not accepted Mixamo compatibility.
- The evidence strongly indicates a rest-pose/bone-basis retarget defect: the current global
  armature-space rest-delta method does not correctly reconcile the source and target rest poses.
  Extra animated shoulders, `Spine1`, fingers and toes are reported, but the exact contribution of
  those omitted roles has not yet been isolated.
- Exact continuation: correct the existing M3 pose-space conversion with parent-local rest-basis
  alignment, then rerun only this real 32-frame FBX and compare Source/Target views. Do not start
  M4 export or mark the Mixamo round trip accepted until that visible gate passes.

## M2 Humanoid rig fitting and weight adaptation -- 2026-10-27

- `blender-rig-character-base` schema v3 adds `EXPLICIT_LANDMARKS` for a local, non-empty,
  single Humanoid A-pose Mesh with `-Y` front and no existing modifier, vertex groups, Shape Keys,
  linked data or animation. It requires 22 object-local landmarks; unreliable joints are refused
  rather than inferred.
- The existing 18-bone hierarchy is fitted to those points. `LANDMARK_ENVELOPE_V3` assigns at most
  four normalized deform influences using bone-segment distance, excludes opposite-side limb
  bones, reports missing/cross-side/sum-error facts and preserves vertex coordinates and active UV.
  Failure removes only the new groups, modifier, Armature Object and Armature data.
- Compact and Lanky M1 v4 characters were recreated and tested in Blender 5.0.1 under
  `D:/Blender/MCP_Test/GameAssetAI_RigAdaptation_M2_20261027`. Both have zero missing and
  cross-side influences, maximum four influences and maximum sum error `3.33e-16`. An induced
  failure after weight creation restored the exact target state; both saved `.blend` files reopen.
- Knee minimum local face-area ratio improved Compact `0.114 -> 0.718` and Lanky
  `0.052 -> 0.732`. Multi-view rest/pose review found no tear, unintended bilateral connection or
  severe elbow/knee/shoulder/hip collapse. Elbow minima are `0.251`/`0.477`; their neighborhoods
  are broader than M1, so those values are not directly equivalent to the old probe.
- Existing v1/v2 rig regression remains 13/13. The Workspace installation is hash-aligned and an
  independent installed-script Compact run passed. Bundle:
  `.local/source-bundles/blender-rig-character-base-v3-m2-20261027.zip`, SHA-256
  `11fe27bbd1e45e4e1615cf44c6de8ee446242c589b2c72ae54eede7f668b3501`.
  Previous installation backup:
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-rig-character-base-20261027-pre-m2-v3`.
- Decision: M2 is accepted for the explicit-landmark, single-body local A-pose scope. It is not
  general automatic rigging. M3 may proceed with one M2-supported character and a real Mixamo
  round trip.

## Character canonical-template v4 result -- 2026-10-27

- `blender-create-character-base` now has optional schema v4 `DEFORMATION_TEMPLATE`. It duplicates
  an explicit absolute, non-symlink `.blend` Mesh after exact SHA-256 verification, requires
  declared `CC0-1.0` provenance and `-Y` front, applies bounded `SMOOTH_REGIONAL_V1` proportions,
  preserves connectivity/UV loops, assigns four materials and uses the existing owned rollback.
  Native v1/v3 paths are unchanged; no asset is vendored or required.
- Representative Blender 5.0.1 evidence is under
  `D:/Blender/MCP_Test/GameAssetAI_DeformationReady_20261027/{compact,lanky}`. Each saved/reopened
  result has 12,502 vertices, 12,500 quads, one closed component and 50,000 UV loops. Source SHA
  `3c121505651140ceb4d69fd1d8923f7788ffadd81672f5be14845a5f2c75c137` remained unchanged;
  an induced bad-hash request restored the exact Blender datablock baseline.
- Both Armature probes exercised elbow, knee, shoulder and hip. Compact visual continuity is
  usable as representative evidence. Lanky knee compression reached a 0.052 minimum local
  face-area ratio, and the existing blockout-oriented rig required validation-only arm refitting.
  Therefore implementation/structure passed, but `deformation-ready` visual acceptance did not.
  Do not route v4 to product animation, Mixamo or export until rig fitting and weight adaptation
  pass the repeated multi-view gate.
- Portable experimental bundle:
  `.local/source-bundles/blender-create-character-base-v4-experimental-20261027.zip`, SHA-256
  `5a081c027f943f9cdf159f719aa0ee184fed9b1972b335a8c5e1661c5a35a9f3`.
  The personal Workspace installation is hash-aligned with repository source. The previous
  installation is preserved at
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-create-character-base-20261027-pre-v4-experimental`.
  Client discovery in a refreshed Codex session remains unverified; deployment alignment is not
  discovery evidence.

## Static semantic revision work package — 2026-10-27

### Optional Kiln GLB Adapter result

- `blender-create-static-asset` now also accepts
  `gameassetai.kiln-glb-import-request.v1` for an already generated, explicitly named GLB.
- It verifies an exact lowercase SHA-256 and complete Mesh Object/semantic-role map, uses Blender's
  native glTF importer, moves the imported hierarchy into one new Collection, records Kiln
  provenance and inventories every created Object/Mesh/Material.
- Import ownership is separate from native assembly ownership. The receipt states
  `native_revision_compatibility: NOT_VALIDATED`; existing v2.1 revision behavior is unchanged.
- Blender 5.0.1 validation used the Kiln 1.5.0 field cannon. Invalid hash failed before import; an
  omitted role failed after import and restored the exact baseline; normal import produced 13
  mapped Mesh Objects, 10 Mesh datablocks and 4 Materials. Receipt cleanup restored the baseline.
- Reviewable result:
  `D:/AI/GameAssetAI-Kiln-Evaluation-20261027/adapter-output/kiln-field-cannon-adapter-check.blend`
  (SHA-256 `7fc86daea8eb26f4c6a2b335326ce9a1d7373cbdf5d63a644eca0e227206c511`).
- Receipt JSON SHA-256:
  `72901c86cad2d0d7dbb82c68c764d127985abe78fd99ce1a7c195ad1ef959533`.
- Native regression and repository structure validation passed. Cleanup now also refuses when a
  referenced imported Mesh or Material no longer carries the verified import owner token. Bundle:
  `.local/source-bundles/blender-create-static-asset-kiln-adapter-v2.2.1.zip`, SHA-256
  `ebacd94decc4143775c9198970d7d89b7955d6380436b0a99e2cb9bffaeeea17`.
- Workspace source is hash-aligned; its prior copy is preserved at
  `.agents/skill-backups/blender-create-static-asset-20261027-pre-kiln-adapter-v2.2.1`.

- `blender-create-static-asset` now keeps creation v1 and adds creation v2 semantic roles plus
  `gameassetai.static-asset-revision-request.v1` copy-only transform revision.
- The target gets independent Collection/Object/Mesh data; source materials are shared read-only.
  Unowned/non-semantic sources, unknown/duplicate roles and occupied names fail closed.
- Focused Blender 5.0.1 regression passed v1 creation/cleanup, v2 creation, exact source
  preservation, body/handle revision and deliberate mid-copy rollback.
- Representative run 03:
  `.local/validation/static-asset-lantern-20261027-run-03/` contains compact and tall eight-part
  lanterns, a wide-body/wide-handle copy revision, nine review PNGs and the reviewable `.blend`.
  Front, side and three-quarter views were inspected. Runs 01/02 remain rejected evidence for
  disconnected-handle corrections.
- Independent reopen confirmed all three Collections contain the same eight semantic roles. Body
  dimensions are compact `(1.30, 1.30, 1.25)`, tall `(0.95, 0.95, 1.80)` and revised
  `(1.55, 1.55, 1.05)`.
- Kiln 1.5.0 was later installed only in the approved isolated evaluation folder and produced the
  preserved field-cannon GLB. It remains optional and outside the repository/Workspace runtime.
- Repository structure validation passed. `skill-creator` quick validation could not start because
  global Python lacks PyYAML; the repository contract validator did validate the Skill metadata.
- Final bundle: `.local/source-bundles/blender-create-static-asset-semantic-revision-v2.1.zip`,
  SHA-256 `a7a968a21a840e9e6b1a6605f60fa5590e2734b755840b748ec2e0eb963662e7`.
- Installed source is hash-aligned at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-create-static-asset`; the prior installation
  is preserved at `.agents/skill-backups/blender-create-static-asset-20261027-pre-semantic-revision-v2`;
  the intermediate update is retained at the corresponding `pre-semantic-revision-v2.1` path.
- Full unrelated offline tests were inconclusive under the managed sandbox because their standard
  Windows temp directories were denied. The focused Blender regression is the relevant passing
  evidence. Next operational gate: refreshed-session discovery and one normal Workspace call.

Candidate visibility is not a user prohibition on restarting Blender. The prior statement that
the current character “had to be maintained” was an incorrect attribution. Preserve recoverable
work through verified checkpoints, but do not convert that safety choice into a claimed user
constraint.

## Current environment facts

- Repository: `D:/GitHub/GameAssetAI`.
- Repository has no `.git` directory in the current workspace, so Git status/history is
  unavailable here.
- Blender 5.0.1 is connected through MCP.
- Blender MCP Add-on protocol is 13 while the server expects 15; execution fallback works.
- Current Blender file: `D:/Blender/MCP_Test/MCPTest.blend`.
- Original Blender Scene `Scene` remains preserved with `Cube`, `Camera`, `Light`. The active
  Scene is the separate character Workbench described below.
- The Add-on is installed and enabled in saved Blender 5.0 Preferences. A fresh Blender 5.0.1
  process proved automatic enablement and panel/property registration.
- External asset libraries and 3D generators reported by MCP are disabled.
- Unity workbench exists but new Unity work is paused by the recovery audit.

## Completed capability groups retained

- Read-only Blender asset/static/humanoid/animation inspection.
- Guarded copy-only cleanup, transform, pivot and static LOD operations.
- Narrow texture-free static FBX export and validation.
- Low-level Action copy/range/root-motion/retarget composition primitives.
- Static and Action pixel PNG rendering, palette/value/outline processing, sprite sheets and
  batches.
- Material/object/silhouette masks, normal/depth/object-ID passes and impostor bundles.

These are supporting capabilities. They are not evidence of general asset generation, rigging,
Mixamo completion or animation authoring.

## Known missing product capabilities

- A routing-only natural-language character/weapon/enemy/prop Skill now exists in source; it still
  requires installed-client host validation and the specialist creation Skills remain narrow.
- A guarded v3 connected character candidate now exists and passes structural/agent multi-view
  gates; user visual acceptance, production topology, weights and animation polish remain incomplete.
- No completed Mixamo round trip.
- The Add-on now has Scene, Compositor, material, single PNG, Action sequence and sprite-sheet
  controls. A live non-Cube Blender-created character -> Cel style -> 2D sheet proof exists.
- Rigged/animated export and Unity import proof remain missing.

The first narrow static-asset and character blockout workflows exist. The old voxel-connected
character is rejected; its rig/weight results remain algorithm evidence only. The replacement v3
Boolean candidate preserves bilateral clearance but is not yet user-accepted or rigged.

## Validation baseline

- Historical broad baseline: 241 script tests and 47 workspace tests passing, with four Windows
  symlink skips.
- Latest focused Unity request validator: 5 tests passing.
- Development-tool regression: 75 tests passing, including opt-in Skill contract acceptance and
  malformed-contract refusal.
- Repository structure and all opted-in Skill contracts pass `scripts/validate_repo.py`.
- Do not rerun the entire historical suite for every small edit. Run focused tests, repository
  validation, and one representative Blender test for significant Blender behavior.

## Exact continuation point

The active Scene is `GameAssetAI_Character_Topology_v3_Workbench`, showing only
`GAA Scout v3 Boolean Current`. It is one recoverable review fixture, not a requirement to keep
that Scene or process open and not the project objective. After implementation approval, use a
disposable copy or regenerate a representative blockout for the topology/revision work; do not rig
the current Boolean Mesh as a product target and do not reuse the rejected voxel candidate's
rig/weights. The Add-on
installation, source alignment, transactional update/restore and fresh-process survival gates are
complete; maintain them while returning priority to accepted asset work.

The bounded topology follow-up and canonical-template evaluation are complete. Automatic
retopology remains rejected. Blender Studio Human Base Meshes v1.4.1 is the provisional preferred
CC0 topology source; MakeHuman v1.3.0 data remains a viable optional proportion provider and MPFB
2.0.18 remains an uninstalled external authoring candidate. No provider is integrated and no
experimental output may be routed to product rigging yet.

## Development-system stabilization -- 2026-10-26

- Added stable requirement IDs and an incremental `gameassetai.skill-contract.v1` connecting a
  revised Skill to requirements, implementation/dependency choice, preservation and completion
  evidence. Historical Skills are not mass-rewritten.
- Repository packaging now validates the contract only for Skills that opt in. The first adopter
  is `blender-create-character-base`; its current evidence remains `representative` for blockout
  creation and does not claim deformation readiness.
- Added the native -> existing GameAssetAI -> reviewed open source -> bounded custom decision
  order. External installation and integration remain separately approved actions.
- Recorded a research-only evaluation queue in `docs/IMPLEMENTATION_MEMORY.md` and a bounded next
  work package in `docs/roadmap.md`. No external dependency or new Skill was added.

## Isolated QuadriFlow/ReQuad experiment -- 2026-10-26

- Requirements exercised: `REQ-CHAR`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`; existing
  `blender-create-character-base` creation/material/preservation behavior was reused unchanged.
- Blender 5.0.1 native QuadriFlow and official ReQuad 0.11.3 for Windows x64 were run in
  `--factory-startup` background processes on two different humanoid proportions. ReQuad remained
  a temporary module under `D:/Blender/MCP_Test`; it was not installed, enabled in saved
  Preferences, copied into repository source, or added as a runtime dependency.
- Final direct-input evidence is under
  `D:/Blender/MCP_Test/GameAssetAI_Retopology_Experiment_20261026/run-10-direct-final`.
  QuadriFlow refused both dense Boolean-derived inputs. ReQuad completed both at 1,986 and 2,055
  all-quad faces and transferred all four material roles plus finite, non-zero-area UV layers, but
  produced 10 and 16 boundary/non-manifold edges. The compact ReQuad result also had five detected
  non-adjacent triangle-overlap pairs.
- Controlled normalized-input evidence is under `.../run-07`. Both tools produced one-component,
  all-quad, zero-boundary outputs; however the shared whole-body voxel preparation visibly bridged
  or merged foot/lower-body forms. One compact ReQuad output had one overlap pair and one lanky
  QuadriFlow output had one zero-area UV face.
- Front, side and three-quarter topology renders and non-overwriting `.blend` files were visually
  inspected. Both methods produced general quad grids, but neither established explicit
  deformation-oriented shoulder/elbow/hip/knee loops or passed all semantic and structural gates.
- Decision: **C for current integration**. The technologies are useful experimental baselines,
  especially fast native QuadriFlow on a clean surface, but neither currently satisfies the Skill
  contract. Do not replace the generator, add a Skill, or promote evidence. The next proposal is
  semantic source cleanup plus a repeat of the native gate, not automatic large custom retopology.

## Minimal topology-source cleanup and rerun -- 2026-10-26

- Blender's QuadriFlow wrapper rejects edges whose endpoints compare equal at `1e-4`; the original
  compact Boolean source contained eight such edges despite having no zero-area faces, boundary
  edges or ordinary non-manifold evidence. This explains the earlier generic input-refusal message.
- `blender-create-character-base` now performs one bounded `dissolve_degenerate` cleanup at that
  tolerance immediately after its owned Boolean union, recalculates normals, and refuses the result
  if a preflight micro edge remains. The receipt records before/after counts. This is source cleanup,
  not retopology and adds no dependency.
- Blender 5.0.1 focused validation now passes 22 checks. Development-tool regression passes 75
  tests and repository validation passes.
- The final disposable evidence is under
  `D:/Blender/MCP_Test/GameAssetAI_Retopology_Experiment_20261026/run-12-minimal-fix` with two
  non-overwriting `.blend` files and front/side/three-quarter renders for both methods.
- QuadriFlow completed both cleaned sources as closed all-quad meshes, but produced 1,390/1,318
  zero-area UV faces, 43/51 non-adjacent triangle-overlap candidates, and generic uniform grids
  without explicit shoulder/elbow/hip/knee deformation loops.
- ReQuad completed both sources with finite non-zero-area UVs, but its own engine OBJ outputs
  already contained open boundary/non-manifold edges; the Blender import and material/UV transfer
  were not their cause. Final outputs retained 14/16 boundary/non-manifold edges and likewise did
  not establish deformation-oriented joint loops.
- Whole-body voxel normalization remains rejected because it fuses or bridges semantically separate
  legs/feet. The limited cleanup preserves those separations, but the lanky source still has one
  detected head/neck overlap candidate and was not treated as clean production input.
- Decision: **alternative transition**. Keep the useful source cleanup, but do not integrate either
  automatic retopology result or promote the Skill beyond representative blockout evidence. Stop
  this approach and, only after approval, evaluate a canonical topology template before considering
  a separately license-verified MakeHuman CC0 base mesh.

## Canonical topology source evaluation -- 2026-10-26

- Requirements exercised: `REQ-CHAR`, `REQ-STYLE`, `REQ-COST`, `REQ-SAFE`. Repository search found
  no existing reusable humanoid canonical mesh asset, so no internal template was silently assumed.
- Evaluated in isolated Blender 5.0.1 background processes without modifying the live Scene,
  repository Skill, Add-on, or installed Workspace Skill. Final evidence is under
  `D:/Blender/MCP_Test/GameAssetAI_CanonicalTopology_Evaluation_20261026/run-03-final`.
- Blender Studio Human Base Meshes v1.4.1: official CC0 asset bundle, Blender 4.2+; tested the
  stylized male body at compact and lanky affine stress proportions. Both remained one-component,
  closed all-quad meshes with 12,502 vertices, 12,500 faces and a valid non-zero-area UV map.
  The `-Y` front convention required no rotation. The common elbow/knee bend produced no increase
  in the audit's existing overlap candidates and passed visual front/side/three-quarter review.
- MakeHuman v1.3.0: pinned CC0 `hm08` base body plus pinned CC0 min/max-height target data; application
  code remains AGPL and was not copied. Body-only extraction produced 13,380 vertices and 13,378
  quads, one closed component and a valid UV map. Target application reproducibly produced 1.2995 m
  and 2.3884 m extremes after axis/unit conversion. Rest meshes had zero overlap candidates, but
  the shared evaluation-only bend produced 98/102 candidates, so the data alone is not a proven
  rigging handoff without proper weights/correctives.
- MPFB 2.0.18 was reviewed but not installed. It is GPL-3.0-or-later code, supports Blender 4.2+
  and exposes scripting-oriented workflows; its bundled MakeHuman assets are separately CC0.
  Headless automation and actual MPFB rig/weight output remain untested.
- Failed harness outputs before the final result are retained at the experiment root and `run-02`.
  They are rejected test-harness evidence: incomplete limb selection caused visible spikes and was
  corrected before `run-03-final`; those artifacts do not count against either source mesh.
- Decision: **limited project-owned integration is promising, not yet approved**. Prefer the
  Blender Studio stylized body as the first canonical-topology source because it is CC0, directly
  appendable, visually deformation-oriented, UV-complete and has no runtime add-on dependency.
  Keep MakeHuman/MPFB as an optional future provider for richer phenotype targets and rigging, not
  as a required dependency. The next gate must prove semantic non-affine proportions plus actual
  Armature weights and representative elbow/knee/shoulder/hip deformation before integration.

## First live authored Action and review correction — 2026-10-25

- Created and then revised `GAA Scout Ready Loop` on the retained `GAA Scout Rig`.
- 12 FPS, inclusive frames 1–36, Blender 5 layered Action slot `OBGAA Scout Rig`.
- User review found that upper- and lower-body motion read as opposite. A first contralateral
  phase swap still looked wrong in side view, so the final v3 Ready Loop keeps the lower body
  stable and animates only both upper arms, forearms, hands and head.
- Final v3 has 21 F-Curves and 84 Bezier/AUTO_CLAMPED keys across 7 pose bones.
- Frames 1 and 36 are identical; frames 12 and 24 alternate upper-body guard poses.
- Front 1/12/24/36 and right-side 12/24 frame strips were visually checked.
- The active Workbench Scene remains visible at frame 12; nothing was cleaned up.
- Original v1 checkpoint remains available for recovery:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_Animated.blend`, 123,917 bytes,
  SHA-256 `fb24f8e8b4835c49797020de5e67bb933c87d9bb4531217bed87375a68b92e76`.
- Corrected v3 checkpoint:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_ReadyLoop_v3.blend`, 123,062 bytes,
  SHA-256 `9469b9b7f7bd54526adff472bf61e767cb4eef17bf005ab5d9515890e78afe8e`.

User review then identified the actual issue: evaluated hands were on `+Y` while feet defined the
character front as `-Y`. V4 reverses the arm rotations and records `-Y` on the Scene, character,
rig and Action. At frames 12/24 both hand tails and foot tails evaluate in negative Y, and the
right-side frame strip confirms matching orientation. V4 checkpoint:
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_ReadyLoop_v4.blend`, 123,335 bytes,
SHA-256 `97852e97630597768c5ab59438aadcfd87169c45772a19cdd771f822d9f8ef3c`.

The reusable `blender-author-pose-action` Skill now enforces matching rig/request front axes,
passes one focused Blender 5.0.1 creation/binding/cleanup fixture, and is packaged and deployed
hash-aligned in the personal Workspace. The next animation is a locomotion Action authored through
this boundary, not another direct ad-hoc key insertion.

That locomotion step is complete. The Skill created and bound `GAA Scout Walk Loop` while
preserving `GAA Scout Ready Loop` as a separate Action. Walk v1 is 12 FPS over frames 1–25 with
8 animated limb bones, 24 F-Curves and 120 keys. The `-Y` front axis was derived from evaluated
bone motion before authoring. Right-side and front frame strips at 1/7/13/19/25 confirm alternating
contact/passing poses and matching frames 1/25. Active Action is now Walk Loop at frame 1.

Non-overwriting walk checkpoint:
`D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_Walk_v1.blend`, 124,301 bytes, SHA-256
`0c44dfa6728c2b08492b213931f0a9a9834bf681f16e2bcc980e523ac76b1540`.

## Walk contact refinement and Action preview controls -- 2026-10-25

- `blender-author-pose-action` now supports schema v2 with explicit local bone-location channels;
  v1 rotation-only requests remain supported.
- Focused Blender 5.0.1 validation passes nine checks. The installed Workspace Skill is updated
  with a hash-bound backup at
  `.agents/skill-backups/blender-author-pose-action-20261025-pre-location-v2`.
- `GAA Scout Walk Loop v2` is active. It retains the `-Y` front axis and adds a root local-Y
  height curve; all 25 mesh samples remain above `-0.001m` penetration.
- Front/right nine-frame strips showed no clear shoulder, elbow, hip or knee tear, so weights were
  not changed.
- `GAA Scout Ready Loop`, `GAA Scout Walk Loop` and `GAA Scout Walk Loop v2` are all preserved as
  separate fake-user Actions.
- Non-overwriting checkpoint:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_Walk_v2.blend`, 127,732 bytes, SHA-256
  `a3d7fc6d40d0e53e62ccd052fd572833ada246525ec54219aa7b9ca364cb169b`.
- The Add-on now exposes explicit Armature/Action selectors and a Preview Action operator. Its
  focused factory test passes four checks, and the live panel selects Walk v2.
- Updated Add-on archive: `.local/source-bundles/gameassetai-blender-addon-0.1.1.zip`, SHA-256
  `40592570c5d17110d441f23a5dd9bd0134d5c665cc954167eb6092d010945880`.

## Reversible material preview and single PNG export -- 2026-10-25

- The Add-on now provides `Flat Lit`, `Cel Banded` (2--6 bands) and `Emission Unlit` presets.
  It replaces only slots on an explicit Mesh with Add-on-owned materials and records the exact
  original material names. Restore refuses partial, edited or ownership-mismatched state.
- Focused Blender 5.0.1 material validation passes nine checks. Live apply, restore and reapply
  succeeded on all four `GAA Scout Current` material slots without changing polygon indices or
  original materials.
- The live Workbench remains on Walk v2 frame 1 with the three-band Cel preview applied and its
  Remove control available.
- Cel checkpoint: `D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_CelPreview_v1.blend`,
  127,687 bytes, SHA-256
  `92ac1064b4362172d89386cc0c6ea09ad676174c9a3d609afa574d9f97343d06`.
- The Add-on single-PNG operator uses a same-directory stage, refuses overwrite, verifies the PNG
  signature and restores render settings. Focused validation passes five checks.
- Live 64x64 output: `D:/Blender/MCP_Test/GAA_Scout_Cel_Walk_Frame01.png`, 4,337 bytes, SHA-256
  `173a56a208779ccdffd8f1b7816a009224c10972b26fd755cc9e7d135a50b1a0`.

## Portable Add-on preset -- 2026-10-25

- Camera/view, lighting, pixel and material-style controls can now be saved to and loaded from a
  strict `gameassetai.blender-addon-preset.v1` JSON document. Scene Object/Action bindings and
  output paths are not serialized.
- Focused round-trip validation passes five checks.
- Live preset created at `D:/Blender/MCP_Test/GAA_Scout_Cel64_Preset.json`; the character remains
  visible with Walk v2 and the reversible Cel preview active.
- Preset SHA-256: `b61f27e179a5fd40e0987bbb7878b2b81fc393e22a6aaf9b8f534415fe29a517`.
- Add-on 0.1.3 archive: `.local/source-bundles/gameassetai-blender-addon-0.1.3.zip`, 49,374 bytes,
  SHA-256 `da949a78885fb2c26781b126af5cec6945954a195708abc2c9e3e1a6964a0031`.

## User-reviewed forward walk correction -- 2026-10-25

- User review: Walk v2 looked like backward walking; reverse playback looked forward.
- Created `GAA Scout Walk Forward Loop` by reversing the reviewed v2 time progression while
  preserving every source pose, the root-height curve and the recorded `-Y` front axis.
- The Action has 27 F-Curves and 243 keys over frames 1--25 at 12 FPS. Frames 1/25 still match;
  sampled ground penetration remains below 1mm.
- `GAA Scout Ready Loop`, Walk v1 and Walk v2 remain preserved. The new Forward Action is active,
  selected in the Add-on and left visible at frame 1 with the reversible Cel preview applied.
- Non-overwriting checkpoint:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Workbench_WalkForward_v1.blend`, 129,669 bytes,
  SHA-256 `11990d18cc7be0d05560d1fbdda34054ecc049f00d10350aabf21d1217a93199`.

## Add-on background Action-sequence bridge -- 2026-10-25

- The Add-on now exposes helper-root, output-directory, filename-prefix, step and padding controls
  for the selected Mesh/Rig/Action.
- It loads the existing `blender-render-action-png-sequence` validation, candidate, framing,
  stage and job helpers, then invokes the existing renderer in a separate Blender process.
  Sequence renderer logic is not duplicated in the Add-on.
- The first live attempt correctly rolled back because `SOURCE_COPY` was outside the renderer's
  contract. The bridge was corrected to `OWNED_NEUTRAL`; no target or temporary file remained from
  the failed attempt.
- The successful Forward Walk run rendered source frames 1/5/9/13/17/21/25 to seven new 64x64
  RGBA PNGs named `GAA_Scout_WalkForward_00.png` through `_06.png` in
  `D:/Blender/MCP_Test`.
- Publication status: `created`, count 7, receipt SHA-256
  `5528efce83a16096fb4188720f825104249f442129acd0754b82d2d45affb0a8`; stage/job residue: none.
- The interactive Workbench retains the Forward Action, reversible Cel material preview and all
  prior Actions.
- Add-on 0.1.4 archive: `.local/source-bundles/gameassetai-blender-addon-0.1.4.zip`, 59,740 bytes,
  SHA-256 `fc7f1d1d7be3dbb70e6015d01cd73e6654466afb4c01d2a19acf6a333e88ca98`.

## Pixel label correction and sprite-sheet handoff -- 2026-10-25

- The panel heading `Pixel Preview` was misleading: that section configures the pixel Scene but
  does not provide live preview. It is now `Pixel Scene Setup` and displays the explicit Mesh
  target instead of the active Rig.
- The Add-on can pass the last verified sequence receipt to the existing
  `assemble-png-sprite-sheet` validator/assembler with explicit columns, rows, padding and output
  paths; assembler logic is not duplicated.
- Focused bridge validation passes four checks.
- Live result: seven Forward Walk frames, 4x2 top-left row-major cells, 1px padding, 259x129 RGBA8.
- Sheet: `D:/Blender/MCP_Test/GAA_Scout_WalkForward_Sheet.png`, SHA-256
  `c6a1ac680dbfb604660abdbf34cd0ef7348910fd309de6946b7fdeaeb4d960cd`.
- Metadata: `D:/Blender/MCP_Test/GAA_Scout_WalkForward_Sheet.json`, SHA-256
  `2785394157aa5f2a138debe2c88fc739f290578fb5dd01d7f875511d72c818cf`.
- Receipt SHA-256: `fad6d6a72099b994da088c4f7658780f26704b4df79549a2520e81fa44cd9fad`.
- Add-on 0.1.5 archive: `.local/source-bundles/gameassetai-blender-addon-0.1.5.zip`, 66,167 bytes,
  SHA-256 `1bb82d28f898fafa4cd55fc480a141c3d2b59dc514171dbfbb53ae9563a4bc90`.

## Existing Skill reuse audit and creation router -- 2026-10-25

- Reviewed all 41 pre-existing Skill folders by their declared scope and validation evidence.
- No Skill was deleted. They are now classified as creation spine, inspection, non-destructive
  revision, existing-animation adaptation, downstream 2D output or optional static/engine support
  in `docs/SKILL_REUSE_AUDIT.md`.
- Added routing-only `blender-create-game-asset`. It sends natural-language asset requests to the
  existing static, character, rig or pose-Action Skill and exposes downstream stages only after a
  reviewable source exists. It contains no duplicate Blender implementation.
- Corrected `skills/README.md` so `blender-author-pose-action` reflects its v2 local-location
  support instead of the obsolete rotation-only description.
- Router archive: `.local/source-bundles/blender-create-game-asset.zip`, 2,801 bytes, SHA-256
  `a22c2b0f347cd9232ed9277da491e2860d81cd56a52678f61caa2acb935a1286`.
- Deployed source and installed copies are hash-aligned at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-create-game-asset`; refreshed-client
  discovery and one realistic routed host request remain the next validation gate.

## Documentation consolidation -- 2026-10-25

- Added `docs/IMPLEMENTATION_MEMORY.md` as the durable source for implemented capabilities, active
  gaps, evidence boundaries and deferred-but-retained Add-on/UI work.
- `PROJECT_AUDIT.md`, `SKILL_REUSE_AUDIT.md` and `roadmap.md` now explicitly preserve the Add-on as
  a core product layer even when asset creation has higher immediate priority.
- The next session must not infer that postponed batch/live-preview/Profile UI work was cancelled.

## Rejected connected-character experiment (historical evidence) -- 2026-10-25

- `blender-create-character-base` now accepts backward-compatible schema v2 with explicit
  `VOLUME_ISLANDS` or `VOXEL_CONNECTED` topology modes. V1 behavior is unchanged.
- The connected path voxel-remeshes the semantic volumes, restores material roles from the nearest
  source surface, verifies exactly one component and reports before/after component counts.
- Focused Blender 5.0.1 validation passes 13 checks across both topology modes. The source Skill
  was hash-bound updated in the personal Workspace, with its previous version backed up at
  `.agents/skill-backups/blender-create-character-base-20261025-pre-connected-v2`.
- The active live Scene is now `GameAssetAI_Character_Topology_Workbench`; the prior animated
  `GameAssetAI_Character_Workbench` and original default Scene remain preserved.
- The then-visible candidate was `GAA Scout Connected Current`, 3,738 vertices / 3,738 quads, one
  closed component, zero boundary/non-manifold edges and four material roles. It was later rejected
  by the visual review recorded below.
- `GAA Scout Connected Rig` adds 18 bones, 17 deform groups and one Armature modifier; all 3,738
  vertices are weighted. A temporary six-limb-bone pose smoke test was visually checked and then
  restored to rest pose.
- Non-overwriting recovery copy:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Connected_v1.blend`, 261,739 bytes, SHA-256
  `8eca5a47b3924d976e1b1a3621683a8d9c018d0c207494268abae09f5d78adc2`.
- Portable Skill bundle: `.local/source-bundles/blender-create-character-base-v2.zip`, 6,535
  bytes, SHA-256 `8972ee4b01c9827df788accc8e3ba3bb3d31c259b841b243a771924c148adfaf`.
- Current limitation is explicit: topology is watertight but voxel-based with many poles and no
  UVs. Rigid `REGION_ASSIGNMENT_V1` was replaced on the live candidate by v2 two-bone
  transition weights: 1,206 of 3,738 vertices have two influences and every vertex weight sum is
  within floating-point tolerance of 1.0. The six-bone pose smoke test passed and was restored.
- Focused Blender 5.0.1 rig validation now passes 13 checks across rigid v1 and blended v2. The
  installed Skill was hash-bound updated with backup
  `.agents/skill-backups/blender-rig-character-base-20261025-pre-blended-v2`.
- Latest non-overwriting recovery copy:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Connected_BlendedWeights_v2.blend`, 272,885 bytes,
  SHA-256 `b3f890ec33a529c7a5fde46df1f729ff5423e09f676a5ddcc15c80a7d6d8690b`.
- Portable rig Skill bundle: `.local/source-bundles/blender-rig-character-base-v2.zip`, 5,382
  bytes, SHA-256 `5d82a81a0cf7323f1b3d00081d5f6b472fa6018cc98f956efafed8061b53e57a`.
- This section records implementation history only; its connected candidate is not a continuation
  target.

## Copy-only shoulder/hip weight refinement -- 2026-10-25

- Added and deployed `blender-adjust-character-joint-weights-copy`. It uses an exact preview and
  fingerprint-bound apply, never overwrites the source, duplicates Object/Mesh independently,
  shares only the verified owned Armature/materials and rolls back owned output on failure.
- Focused Blender 5.0.1 validation passes eight checks; source and installed copies are hash-aligned.
- Live shoulder refinement affected 456 vertices; target-pair edge delta maximum changed from
  `0.539509` to `0.523474`. Live hip refinement affected 200 vertices; maximum changed from
  `0.562104` to `0.373643`.
- Under the same six-bone review pose, shoulder p95/max absolute edge stretch improved from
  `0.216139/0.918174` to `0.201798/0.762483`; hip improved from
  `0.721259/3.204531` to `0.463600/3.163987`.
- Active visible object is `GAA Scout Connected Joint Refined Current` in
  `GameAssetAI_Character_Topology_Workbench`, restored to rest pose. The original and shoulder-only
  intermediate are hidden, not deleted, so the Blender viewport shows one current character.
- Checkpoint: `D:/Blender/MCP_Test/GameAssetAI_Character_JointRefined_v3.blend`, 310,580 bytes,
  SHA-256 `f3970f052f370634856da4492382cfc98245fc7b44131de5d3aca950be8123ed`.
- Skill bundle: `.local/source-bundles/blender-adjust-character-joint-weights-copy.zip`, 6,840
  bytes, SHA-256 `b11cc05fe556dd9a4a2e4bb8970901e20fc05c8fc0c66e2461adfc666d496f93`.
- This implementation preserved its source and reduced its selected numerical metrics, but the
  input topology was later rejected by user visual review. Therefore this section is backend
  algorithm evidence only, not product-quality character progress.

## Visual rejection and corrected continuation -- 2026-10-25

- User review showed that the thighs/lower legs/feet were visibly fused or bridged incorrectly.
  The cause is the character v2 whole-body voxel remesh, not the later weight redistribution.
- Previous structural checks (`one component`, closed manifold, no boundary edges, full normalized
  weights) and deformation metrics did not detect the semantic geometry failure.
- `GameAssetAI_Character_JointRefined_v3.blend` is retained only as a rejected diagnostic
  checkpoint. Do not continue rigging, animation, 2D rendering or export from it.
- `blender-create-character-base` `VOXEL_CONNECTED` and
  `blender-adjust-character-joint-weights-copy` on that topology are suspended from default routing.
- At that historical point the Add-on was only session-registered. This lifecycle defect is now
  resolved by the persistent installation and fresh-process proof recorded below.
- The request validator now refuses `VOXEL_CONNECTED`; focused character, rig and weight-copy
  regressions pass without using that mode. Exact next implementation is to replace global voxel
  remeshing with a connected humanoid construction that keeps left/right
  limbs and feet separated except through intended anatomy. Before rigging, require
  clearance/bridge/self-intersection checks plus user-visible front, side and three-quarter
  acceptance. After that, persist/install the Add-on and resume rig adaptation.
- Current suspension bundle:
  `.local/source-bundles/blender-create-character-base-suspended-20261025.zip`, SHA-256
  `e4bea3ad99cbe569ce10856a34d91bacfd00ab9bd414f4723fa4254aa9e0b3a2`. The installed Skill is
  hash-aligned and its pre-suspension version is backed up under
  `.agents/skill-backups/blender-create-character-base-20261025-validator-suspension`.

## Guarded Boolean-connected character v3 -- 2026-10-25

- Added schema `gameassetai.character-base-request.v3` with the single explicit topology mode
  `BOOLEAN_CONNECTED`. It exact-unions the deliberately overlapping semantic volumes rather than
  remeshing the whole body.
- Corrected the boot/ankle construction gap and added enforced gates for one component, zero
  non-manifold edges, positive foot/lower-leg centerline clearance and zero cross-side edges below
  the knee. The rejected v2 `VOXEL_CONNECTED` mode remains refused.
- Focused Blender 5.0.1 validation passes 20 checks, including exact requested Mesh naming,
  semantic gates, cleanup and full state restoration. `scripts/validate_repo.py` also passes.
- Live candidate `GAA Scout v3 Boolean Current` remains visible in
  `GameAssetAI_Character_Topology_v3_Workbench`: 369 vertices, 373 polygons, one component,
  zero non-manifold edges and 0.024138 m foot/lower-leg clearance.
- Agent multi-angle material review passed front/three-quarter/right/back for bilateral leg/foot
  separation and intended joint connections. Treat this as engineering evidence, not user visual
  acceptance; do not rig it until the visible candidate is accepted.
- Installed `blender-create-character-base` and `blender-create-game-asset` were hash-bound updated.
  Backups are `blender-create-character-base-20261025-pre-boolean-v3` and
  `blender-create-game-asset-20261025-pre-boolean-v3` under the Workspace Skill backup directory.
- Final v3.1 also restores the prior Blender Scene/selection/active Object on Boolean failure.
  Portable bundle: `.local/source-bundles/blender-create-character-base-v3.1-20261025.zip`,
  SHA-256 `f3fca1a0912aff7545f364cd950d719189a5e007eb1777a90abf212a408a774a`.
  Installed backup immediately before this hardening is
  `blender-create-character-base-20261025-pre-v3-context-restore`.
- Exact continuation: obtain user visual acceptance of the visible v3 candidate, then resume
  clean-copy rig/deformation work. The Add-on lifecycle gate is complete.

## Persistent Blender Add-on installation -- 2026-10-25

- Installed `.local/source-bundles/gameassetai-blender-addon-0.1.5.zip` into Blender 5.0's user
  Add-ons directory, enabled module `gameassetai` and saved Blender Preferences.
- Runtime verification resolves the module from the installed user path and confirms version
  `0.1.5`, `Scene.gameassetai` and `GAA_PT_pixel_pipeline` are registered. All 14 source files
  excluding generated `__pycache__` hash-match the installed copies.
- Fresh-process survival and guarded update/version work were subsequently completed below.
- Saved one non-overwriting recovery checkpoint for the new candidate:
  `D:/Blender/MCP_Test/GameAssetAI_Character_Boolean_v3.blend`, 327,067 bytes, SHA-256
  `811154202f70d1cd53a7f515f43ee60c6c45c98ffdc3f3375bec46fb9de01b18`.

## Blender Add-on installation inspector -- 2026-10-25

- Added `scripts/inspect_blender_addon_installation.py`, schema
  `gameassetai.blender-addon-installation.v1`.
- It reads literal `bl_info`, checks an explicit Blender version, ignores generated Python caches,
  and reports missing/extra/changed files with complete source and installed SHA-256 manifests.
- Five focused offline tests pass. Repository validation passes. The current Blender 5.0.1 user
  installation reports `aligned`, compatible, version `0.1.5`, with 14 files and no differences.
- Added `scripts/update_blender_addon.py` with hash-bound plan, atomic apply and recoverable
  restore. It preserves the prior installation, retains the replaced version on restore and
  refuses post-plan source/installation drift. Four focused tests pass; the current 0.1.5 plan is
  `already_aligned`, so no installed files were changed.
- The active v3 character Scene was not modified. Character rigging remains gated on user visual
  acceptance of the visible v3 candidate.

## Add-on fresh-process survival proof -- 2026-10-25

- Added `tests/blender_addon/run_persistent_addon_startup.py` and launched a separate Blender
  5.0.1 process using saved user Preferences.
- Five checks passed: enabled preference, installed user-path import, version 0.1.5, registered
  `Scene.gameassetai`, and registered `GAA_PT_pixel_pipeline`.
- This completes the persistent installation/restart lifecycle gate without closing or modifying
  the interactive character Workbench. The next product gate is user visual acceptance of
  `GAA Scout v3 Boolean Current`, followed by deformation-topology/revision work.

## Comprehensive Skill direction audit -- 2026-10-25

- All 43 Skill folders remain related to Blender game-asset work; none requires deletion solely
  for being off-topic. The problem was priority and exposure, not total irrelevance.
- Core creation remains partial: router, primitive static assembly, character blockout, fixture
  rigging and explicit pose authoring. Existing-asset inspection and Action adaptation helpers are
  reusable but must be orchestrated internally rather than exposed as dozens of product commands.
- Advanced 2D passes, impostors, collider and LOD tooling are valid optional downstream tools but
  are frozen at maintenance-only until creation, deformation, Mixamo and animated export mature.
- `blender-adjust-character-joint-weights-copy` and every result based on rejected voxel topology
  remain suspended from product claims.
- Critical correction: v3 fixes bilateral fusion but its live topology is 118 quads, 212 triangles,
  43 ngons and 324 poles. It is a connected visual blockout, not deformation-ready topology.
  User shape approval must lead to a topology/revision stage with edge-flow, self-intersection,
  UV and representative pose-deformation gates, not directly to product rigging.
- Updated and hash-bound deployed `blender-create-character-base`,
  `blender-rig-character-base` and `blender-create-game-asset`; pre-audit installed copies are
  retained under matching `*-20261025-pre-direction-audit` backup directories.
