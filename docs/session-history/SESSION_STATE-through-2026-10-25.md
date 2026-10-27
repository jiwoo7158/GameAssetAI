# Session State — 2026-09-29

## 2D render Phase 0 capability checkpoint — 2026-09-29

- Added the read-only `scripts/inspect_2d_render_capabilities.py` helper and
  `tests/rendering/run_2d_render_capabilities.py` live harness. Registered the
  `2d-render-capabilities` suite in payload preparation and repository validation.
- Blender 5.0.1 passes **10 checks** through MCP for render operator access, PNG/RGBA,
  orthographic camera controls, resolution/alpha/output properties, Image save RNA,
  compositor access and color-management controls. No render or file was created.
- The first live probe exposed invalid Python type-level checks. Blender RNA confirms
  `Camera.ortho_scale`, `Image.save` and `Image.save_render`; the helper now uses
  `bl_rna.properties/functions` and passes on rerun.
- Blender 5.0.1 uses `Scene.compositing_node_group` rather than legacy
  `Scene.node_tree`. Legacy `CompositorNodeComposite`/`CompositorNodeValToRGB` type names
  are absent; render-layer, scale, pixelate and file-output node types are present.
- Color-management enum metadata under-reports the current `AgX` value as only `NONE`.
  Future code must not hard-code or infer the complete preset catalog from this metadata.
- The original Scene remained Cube/Light/Camera with one material and the captured state
  was identical before/after. Blender MCP is still addon 1.7 protocol 7 against expected
  protocol 11; execution fallbacks remain functional.
- Validation evidence and limitations are in
  `docs/2d-render-capability-validation.md`. No 2D Skill or Blender add-on has been
  created yet.
- Added `gameassetai.2d-static-render-request.v1` and its read-only validator. The exact
  nested contract covers optional hash-bound Profile provenance, orthographic view,
  explicit lighting/style/palette policy and a collision-free absolute PNG target; it
  never fills game defaults or authorizes rendering.
- Seven offline contract tests pass; the full scripts suite is now **111 pass** after the
  later palette and receipt additions.
- Added `tests/rendering/run_2d_background_render.py` so write-capable testing cannot
  overwrite the interactive Blender's global Render Result. A separate Blender 5.0.1
  `--background --factory-startup` process passed **8 checks** for 32x24 RGBA8 rendering,
  staged publication, collision refusal and exact file teardown. No test PNG remained,
  and the interactive Cube/Light/Camera Scene stayed unchanged.
- This initial render probe was subsequently extended by the candidate, framing, pixel,
  palette and receipt work recorded below.
- Added that read-only candidate and framing layer. Blender 5.0.1 passes **19 checks** for
  request/source/setup/output fingerprint binding, world bounds, square/portrait/landscape framing,
  stale state and dependency refusal, no file/Camera creation, context preservation and
  exact synthetic teardown.
- The first candidate supports PIXEL + NONE or opaque FIXED palette + disabled anti-aliasing
  + nearest intent + owned neutral lighting. CEL/FLAT_TOON, AUTO palette and copied source
  lighting remain explicit request vocabulary but fail closed until implemented.
- The interactive Cube/Light/Camera Scene and its one material remained unchanged. The
  reviewed framing plan was then applied in a separate factory-startup Blender process.
- Updated the separate background probe to load the exact repository request/candidate/
  framing helpers. Blender 5.0.1 passes **11 checks** from v1 request through candidate,
  plan-driven owned Camera/light, 32x24 RGBA8 stage, collision-safe publication and exact
  file teardown. The result reports request/source/setup/output/plan and artifact hashes.
- This completes the synthetic camera/framing and neutral-light isolation gates. The next
  priority is a narrow Pixel render configuration and structural pixel/alpha validation;
  palette, outlines, CEL/FLAT_TOON and production user-Mesh transfer remain unimplemented.
- Corrected a real framing defect found by pixel validation: Blender `ortho_scale` follows
  horizontal span in landscape and vertical span in portrait, rather than always being a
  vertical span. Square, portrait and landscape live regressions now pass.
- The isolated render now passes **18 checks** with filter size 0, decoded RGBA8 pixels,
  nonempty alpha bounds `[6, 2, 25, 21]`, visible margins, zero partial-alpha pixels and
  exact teardown. Two consecutive renders have identical decoded pixels but different PNG
  container bytes; byte-level PNG determinism is therefore explicitly not claimed.
- Added deterministic fixed-palette RGBA8 quantization/PNG encoding (**5 offline tests**).
  The live probe reduces 39 source RGBA values to 3 while preserving alpha exactly.
- Added a read-only final artifact receipt (**4 offline tests**) binding PNG path/size/SHA
  and pixel facts to request/source/setup/output/plan hashes. Live receipt binding passes;
  no receipt file or PNG is retained by the test.
- Next priority is a reusable staged single-PNG workflow boundary. AUTO palette,
  outline/shading, CEL/FLAT_TOON and production user-Mesh transfer remain later work.

## Action-range frame-rebase update checkpoint — 2026-09-28

## Evaluated pose-loop endpoint checkpoint — 2026-09-28

- The user confirmed the updated `blender-extract-action-range` Skill exposes all three
  frame policies (`KEEP_FRAMES`, `REBASE_TO_ZERO`, `REBASE_TO_ONE`) without changing the
  Scene; that host gate is complete.
- Added and installed the twenty-third Skill, `blender-inspect-evaluated-pose-loop`. It
  compares evaluated local-basis translation, quaternion rotation and scale at two exact
  frames for an explicit complete list of animated pose bones.
- It evaluates only an independent Armature Object/data copy in an owned temporary Scene.
  Parented Armature Objects, constraints, drivers, Object/custom-property curves,
  unsupported pose channels and omitted animated bones fail closed. It does not claim
  tangent, velocity, deformation, visual or Unity loop continuity.
- The user confirmed refreshed-session exposure and correct no-input refusal, completing
  the original host gate. The Skill was then updated in place to request schema v2, adding
  bounded start-forward/end-backward finite-difference translation, rotation-vector and
  scale velocity seam comparison without creating another Skill.
- Blender 5.0.1 passes **16 checks** from repository source, updated portable ZIP and
  updated installed Workspace helpers. Matching endpoint poses, matching root velocity,
  mismatching child angular velocity, bounded refusals, source preservation and exact
  teardown pass. Original Scene remains Cube/Light/Camera with the current one-material
  inventory unchanged.
- Updated through the hash-bound workflow at `D:/AI/GameAssetAI-Workspace/.agents/skills/
  blender-inspect-evaluated-pose-loop`. The endpoint-only version is retained at
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
  blender-inspect-evaluated-pose-loop-20260928-pre-velocity`. Updated archive SHA-256:
  `0b06e3bce184d4190c9dbbef937da4a6e5104acd3635573c32ede76b42eb7e0d`.
- Final validation: repository and Workspace structure OK; scripts **95 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **23** source/installations
  are byte-aligned, and the retained endpoint-only backup matches the update plan exactly.
  `skill-creator` quick validation is unavailable because optional
  PyYAML is absent; compilation, repository validation, packaging and live regressions
  pass without installing it.
- The user confirmed refreshed-session schema v2 and all four velocity inputs, completing
  the update host gate without Blender changes or test data.
- A separate seven-check Blender 5.0.1 development probe confirmed deterministic LINEAR
  pose evaluation at fractional frames 1.25 and 1.75, unchanged Action keys, exact fixture
  teardown and original Scene restoration. This establishes capability only; sampling
  density, Bezier extrema, deformation and visual loop validation remain future work.
- With the reported daily quota at 27%, do not begin the larger deformation/visual phase
  until a later continuation. Unity is not required for the next Blender-only experiment.
- Integrated the user-provided `blender_pixel_pipeline_plan.md` as future planning only.
  `SKILL_3D_ASSET.md` is interpreted as the existing `skills/` 3D system; no replacement
  Skill, duplicate 3D generator, add-on tree or runtime feature was created. The adapted
  downstream Pixel/Cel/Toon phases, Profile boundaries, isolated setup and no-overwrite
  output contract are recorded in `docs/2d-pixel-pipeline-plan.md` and the roadmap.

## Action-range frame-rebase update checkpoint — 2026-09-28

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-extract-action-range`; the twenty-second Skill's original host gate is complete.
- Updated that Skill in place rather than adding another Skill. The existing strict
  exact-boundary LINEAR contract now accepts `KEEP_FRAMES`, `REBASE_TO_ZERO`, or
  `REBASE_TO_ONE`.
- Rebasing changes only the copied Action and applies one reviewed integer offset to key,
  handle and retained pose-marker times. Source content and current/NLA references remain
  unchanged; synthesized boundaries and Bezier curves remain refused.
- Blender 5.0.1 passes **17 checks** from repository source, updated portable ZIP and
  updated installed Workspace helpers, including both rebase origins, unknown-policy
  refusal, source preservation and exact teardown.
- Updated through the hash-bound deployment workflow. The previous installed version is
  retained at `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
  blender-extract-action-range-20260928-pre-rebase`. Updated archive SHA-256:
  `ce5e41a44daaaa7f7a1c62b781baeee105d106f86f6befd655c86abe4fb54560`.
- Blender MCP remains `ahujasid/blender-mcp` on `localhost:9876`; the original
  Cube/Light/Camera Scene and its two-material inventory remained unchanged. Unity was not
  required.
- Final validation: repository and Workspace structure OK; scripts **94 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **22** current
  source/installations are byte-aligned. The retained previous-version backup hashes match
  the update plan exactly. `skill-creator` quick validation remains unavailable because
  optional PyYAML is absent; repository validation, compilation, packaging and live
  regressions pass without installing it.
- Refreshed-client visibility of all three policies is now user-confirmed. Synthesized
  boundaries, Bezier-safe cutting, source renaming, production animation data and Unity
  animation import remain open.

## Strict Action-range extraction checkpoint — 2026-09-28

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-replace-current-action`; the twenty-first Skill's host gate is complete.
- Added and installed the twenty-second Skill, `blender-extract-action-range`. It copies
  one explicit integer frame interval to an independent fake-user-protected unbound Action
  while preserving the source Action and every current/NLA reference.
- The bounded `KEEP_FRAMES` policy requires every F-Curve to have unique key times, exact
  start/end keys, LINEAR interpolation only, and no samples or modifiers. It retains only
  in-range pose markers and never synthesizes boundaries or rebases frames.
- Blender 5.0.1 passes **12 checks** from repository source, portable ZIP and installed
  Workspace helpers: authorization, missing-boundary, nonlinear, modifier, stale and
  collision refusal; exact key/marker range; source/reference preservation and teardown.
- The first live run found a missing `_curves` provider before fixture creation. After
  adding `inspect_animation.py`, the next run exposed Blender invalidating cached Keyframe
  references after collection removal. Reverse-index reacquisition fixed it; all three
  final origins pass and no synthetic data remains.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-extract-action-range`.
  Archive SHA-256:
  `bf2d0aa87e1f4a3be3d85e68da2da078ce95b156b4b0707c0ddb2f67a96fd67b`.
- Blender MCP remains `ahujasid/blender-mcp` on `localhost:9876`; the original
  Cube/Light/Camera Scene remained unchanged. Unity was not required.
- Final validation: repository and Workspace structure OK; scripts **94 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **22** source/installations
  are byte-aligned. `skill-creator` quick validation remains unavailable because optional
  PyYAML is absent; repository validation, compilation, packaging and live regressions
  pass without installing it.
- Remaining host gate: refresh the client and verify the twenty-second Skill is exposed
  and refuses the current no-Action Scene. Frame rebasing, synthesized Bezier boundaries,
  source renaming, production animation data and Unity animation import remain open.

## Current-Action replacement checkpoint — 2026-09-27

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-bind-action-empty`; the twentieth Skill's host gate is complete.
- Added and installed the twenty-first Skill, `blender-replace-current-action`. It swaps
  only one exact current Armature Action for one exact protected/unbound Action under the
  `CURRENT_ONLY` policy, preserving both Actions.
- The current Action must be bound only to the named Armature; the replacement must be
  unbound. Both require one exact Object slot and fake-user protection. NLA, Object/data
  drivers, extra references, stale content, wrong current binding and missing authorization
  are refused.
- Apply returns a hash-bound receipt containing both Action fingerprints and slots.
  Rollback requires that exact receipt, unchanged Actions and the exact replacement
  binding before restoring the previous Action. Neither Action is deleted.
- Blender 5.0.1 passes **16 checks** from repository source, portable ZIP and installed
  Workspace helpers, including NLA/driver/stale/wrong-current/tampered/changed-source
  refusal, reference swaps, exact restoration and teardown.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-replace-current-action`.
  Archive SHA-256:
  `13032bbc4fb267a770e2055ae2fc5a38c37935e42de4f16fa7eaf98efe058a82`.
- Blender MCP remains `ahujasid/blender-mcp` on `localhost:9876`; the original
  Cube/Light/Camera Scene remained unchanged and all synthetic data was removed. Unity
  was not required.
- Final validation: repository and Workspace structure OK; scripts **93 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **21** source/installations
  are byte-aligned. `skill-creator` quick validation remains unavailable because optional
  PyYAML is absent; repository validation, compilation, packaging and live regressions
  pass without installing it.
- Remaining host gate: refresh the client and verify the twenty-first Skill is exposed and
  refuses the current no-Armature/no-Action Scene. Production Action compatibility,
  deformation, representative Mixamo data and Unity animation import remain open.

## Empty-target Action binding checkpoint — 2026-09-27

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-compose-retarget-actions`; the nineteenth Skill's host gate is complete.
- Added and installed the twentieth Skill, `blender-bind-action-empty`. It binds one
  explicit protected/unbound/single-Object-slot Action only to an explicit Armature with
  no current Action, NLA tracks or Object/data drivers (`EMPTY_ONLY`).
- Preview binds request, Action content and target state hashes. Apply requires explicit
  authorization and returns a hashed receipt. Rollback requires that exact receipt,
  unchanged Action content and exact current binding; it never deletes the Action and
  restores whether an empty animation-data block existed before apply.
- Blender 5.0.1 passes **14 checks** from repository source, portable ZIP and installed
  Workspace helpers: authorization/stale/occupied/tampered refusal, exact binding,
  content/reference preservation, both rollback state branches and exact teardown.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bind-action-empty`.
  Archive SHA-256:
  `6e4259f71baa1afb34851a332273eb724aa3818bd79a44af7cf2e95ff07e5c3a`.
- Blender MCP remains `ahujasid/blender-mcp` on `localhost:9876`; Blender 5.0.1 add-on
  1.7 reports protocol 7 against server expectation 11, while compatible execution
  fallbacks pass. The original Cube/Light/Camera Scene remained unchanged and every
  synthetic ID was removed. Unity was not required.
- Final validation: repository and Workspace structure OK; scripts **92 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **20** source/installations
  are byte-aligned. `skill-creator` quick validation remains unavailable because optional
  PyYAML is absent; repository validation, compilation, packaging and live regressions
  pass without installing it.
- Remaining host gate: refresh the client and verify the twentieth Skill is exposed and
  refuses the current no-Armature/no-Action Scene. Occupied-target replacement policy is
  deliberately still unimplemented; production rig/Action fixtures and Unity animation
  import remain later validation work.

## Retarget Action composition checkpoint — 2026-09-27

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-bake-root-translation-copy`; the eighteenth Skill's host gate is complete.
- Added and installed the nineteenth Skill, `blender-compose-retarget-actions`. It accepts
  only one unbound fake-user quaternion-rotation Action and one unbound fake-user
  root-location Action with matching explicit integer ranges, then retains one independent
  unbound composite Action.
- Inputs must be single Object-slot Actions with linear integer keys and no samples or
  modifiers. Rotation channels must be target-bone quaternions; translation must be exactly
  XYZ location on the explicit target root. Arbitrary Actions, overlap, constraints,
  malformed ranges, stale previews and missing authorization are refused.
- Blender 5.0.1 passes **9 checks** from repository source, portable ZIP and installed
  Workspace helpers: preview/auth/stale/nonlinear refusal, seven-curve output, combined
  paths, source/target preservation and exact teardown.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-compose-retarget-actions`.
  Archive SHA-256:
  `df25084157cc4415d78595fc369282c557bf703e502234b82cdf43b21eea2340`.
- Final validation: repository and Workspace structure OK; scripts **91 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **19** source/installations
  are byte-aligned. `skill-creator` quick validation remains unavailable because optional
  PyYAML is absent; repository validation, compilation, packaging and live regressions
  pass without installing it. Unity was off and not required. The original
  Cube/Light/Camera Scene remained unchanged and every synthetic ID was removed.
- The result remains unbound. Remaining host gate: refresh the client and verify the
  nineteenth Skill is exposed and refuses the current no-Armature/no-Action Scene. Only
  after that should explicit binding/replacement/rollback policy be designed separately.

## Root translation bake checkpoint — 2026-09-26

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-inspect-evaluated-root-motion`; the seventeenth Skill's host gate is complete.
- Added and installed the eighteenth Skill, `blender-bake-root-translation-copy`. It
  creates one independent fake-user, unbound, location-only Action for an explicitly
  mapped parentless root bone.
- The request must explicitly choose `TRANSFER` or `IN_PLACE`, Armature-space XYZ axis
  mask and scalar. No root, axes, target proportion or Unity policy is inferred.
  `TRANSFER` maps absolute sampled source basis location through source Armature space and
  the target rest orientation. `IN_PLACE` writes zero location per sampled frame.
- It refuses parents, nonidentity Armature transforms, constraints, drivers, Object-motion
  channels, ambiguous slots, invalid mask/scale, collisions, stale previews and missing
  authorization. It does not copy rotation/scale, compose Actions, bind, export or save.
- Blender 5.0.1 passes **12 checks** from repository source, portable ZIP and installed
  Workspace helpers. Two fixture defects (sorting Blender objects and using an invalidated
  EditBone reference after mode exit) were corrected before the successful regression.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bake-root-translation-copy`.
  Archive SHA-256:
  `a1180b71d260ae52878e126142478fdf1d05a51f92741d7159fab32ea711b451`.
- Final validation: repository and Workspace structure OK; scripts **90 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **18** source/installations
  are byte-aligned. `skill-creator` quick validation could not start because optional
  PyYAML remains absent; repository validation, compilation, packaging and live regressions
  passed without installing it. Unity was off and not required. Blender's original
  Cube/Light/Camera Scene remained unchanged and all synthetic data was removed.
- Remaining host gate: refresh the client and verify the eighteenth Skill is exposed and
  refuses the current no-Armature/no-Action Scene without creating data. The next bounded
  design is rotation/root-translation Action composition and optional result binding;
  production Mixamo/deformation and Unity policy remain later validation stages.

## Evaluated root-motion checkpoint — 2026-09-26

- The user confirmed refreshed-session exposure and correct no-input refusal for
  `blender-bake-rotation-retarget-copy`. The sixteenth Skill's host gate is complete;
  no Blender data was created or modified.
- Added and installed the seventeenth Skill,
  `blender-inspect-evaluated-root-motion`. It requires exact Scene, Armature, Action,
  parentless root-bone, Action-slot, frame-range and tolerance inputs. It evaluates the
  Action only on an owned temporary Scene/independent Armature copy and reports sampled
  `LOCAL_BASIS`, `ARMATURE` and `WORLD` positions without retaining an output.
- The report separates endpoint displacement (`net_translation_evidence`) from sampled
  travel (`path_translation_evidence`), so a returning loop can have zero net movement
  and a nonzero path. Metrics include endpoints, net vector/distance, path length, maximum
  distance from start and bounds.
- The workflow refuses parented root bones/Armatures, Object or pose-bone constraints,
  Object/Armature-data drivers, Object-transform Action channels, ambiguous slots,
  missing root-location curves, non-unit frame steps and ranges over 10001 frames. It does
  not infer roots, transfer motion, choose in-place policy or configure Unity.
- Blender 5.0.1 passed **11 checks** from repository Skill source, portable ZIP and
  installed Workspace helpers. The fixture demonstrates a zero-net/nonzero-path loop and
  static Object-scale contribution to world distance, plus refusal, source preservation
  and exact teardown.
- The first native run exposed a false preservation failure caused by comparing evaluated
  `matrix_world`/`matrix_basis` caches as stored state. The guard now compares stored
  transform/pose properties, Action content and references and restores the original
  Scene frame before verifying.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-evaluated-root-motion`.
  Archive SHA-256:
  `3d32271de279fc31df46135ea5566b105dac1b2212d04c0753aa25e35fb3b131`.
- Final validation: repository and Workspace structure OK; scripts **89 pass**;
  Workspace **47 pass / 4 explicit Windows symlink skips**; all **17** source/installations
  are byte-aligned. `skill-creator` quick validation could not start because optional
  PyYAML is absent; repository validation, compilation, packaging and live regressions
  passed without installing it.
- Unity was off and not required. The original Blender Scene remains Cube/Light/Camera;
  all synthetic Scene/Object/Armature/Action data was removed.
- Remaining host gate: refresh the client and verify the seventeenth Skill is exposed and
  refuses the current no-Armature/no-Action Scene without creating data. After that, use
  the three-space evidence to design target-scaled root translation and explicit
  in-place/root-motion policy as a separate guarded unit.

## Differing-rest rotation bake checkpoint — 2026-09-26

- User confirmed refreshed-session exposure and correct no-input refusal for
  `blender-retarget-aligned-action-copy`. The fifteenth Skill's host gate is complete;
  no Blender data was created or modified.
- Added and installed the sixteenth Skill, `blender-bake-rotation-retarget-copy`. It
  evaluates only owned temporary source/target rig copies, samples mapped source
  `matrix_basis` rotations at each integer frame, and retains one independent,
  fake-user-protected, unbound quaternion Action on target bone paths.
- Unlike the strict aligned path copy, source and target mapped rest matrices may differ.
  The workflow remains rotation-only local-basis transfer: it refuses location, scale,
  root/Object motion, non-bone channels, unmapped animated bones, parents, non-identity
  Object transforms, Object/pose-bone constraints, Object drivers, differing inherit-scale
  modes, multiple slots, non-unit frame step, ranges over 10001 frames, collisions, stale
  previews and missing explicit authorization.
- The owned Blender 5.0.1 fixture passes **12 checks** from repository source, portable
  ZIP and installed Workspace helpers. Its source uses Euler rotation on a vertical-rest
  rig while the target has horizontal rest directions; output is a three-frame linear
  quaternion Action. The first run found and fixed validation ordering: the temporary
  source binding is now cleared before original Action references are compared.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bake-rotation-retarget-copy`.
  Archive SHA-256:
  `3718075d937d050fd6cd47a07390125ef9ab335d7b20aceb721313ed45edf612`.
- Final validation: repository structure OK; scripts **88 pass**; Workspace **47 run / 4
  explicit Windows symlink skips**; all **16** source/installations are byte-aligned.
  Unity was off and was not required. Blender's original Cube/Light/Camera Scene remained
  unchanged and every synthetic Scene/Object/Armature/Action was removed.
- This is not world-space or normalized-humanoid retargeting and does not prove visual or
  deformation quality. Hip translation/proportion scaling, root-motion policy, result
  binding, production Mixamo fixtures, visual/deformation validation and Unity animation
  import remain open.
- Remaining host gate: refresh the client and verify the sixteenth Skill is exposed and
  refuses the current no-Armature/no-Action Scene without creating data. Only after that
  should translation/root-motion design begin as a separate explicit-policy unit.

## Strict aligned Action-copy retarget checkpoint — 2026-09-26

- User confirmed refreshed-session exposure and correct no-input refusal for
  `blender-inspect-retarget-readiness`. The fourteenth Skill's host gate is complete;
  it did not create test data or modify Blender.
- Added and installed the fifteenth Skill,
  `blender-retarget-aligned-action-copy`. It supports only strict name-only F-Curve path
  remapping when explicit source/target humanoid rigs already have matching mapped rest
  matrices, Object transforms and animated rotation modes. It creates one independent,
  fake-user-protected, unbound Action and preserves source/current/NLA references and both
  Armatures.
- The workflow refuses missing/inferred mappings, extra animated bones, non-bone channels,
  differing rest matrices/transforms/rotation modes, parented rigs, relevant constraints
  or drivers, multiple Action slots, collisions, stale previews and missing authorization.
  It does not perform pose-space conversion, constraint retargeting, binding, baking,
  root-motion policy, deformation validation, export or save.
- The owned Blender 5.0.1 fixture passes **16 checks** using repository source, portable
  ZIP and installed Workspace helpers. Native iteration found and fixed a stale
  `matrix_world` cache assumption by comparing raw transforms without a dependency refresh;
  it also confirmed that a rest edit/restoration invalidates the old preview and requires
  a fresh one.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-retarget-aligned-action-copy`.
  Archive SHA-256:
  `dc3812b76355d122a53c093b35f1d0be0fda63dc60947385769f1b677214565e`.
- Final validation: repository structure OK; scripts **87 pass**; Workspace **47 run / 4
  explicit Windows symlink skips**; all **15** source/installations are byte-aligned.
  Unity was not running or required. Blender's original Cube/Light/Camera Scene was
  preserved, and all synthetic rigs/Actions/Scenes were removed.
- The MCP addon remains 1.7/protocol 7 while the server now expects protocol 11. Verified
  fallback execution still works, so no addon update was performed. `skill-creator` quick
  validation remains unavailable because optional PyYAML is absent; repository validation,
  Python compile, packaging and live helper regressions pass without installing it.
- Remaining host gate: refresh the client and verify the fifteenth Skill is exposed and
  refuses the current no-Armature/no-Action Scene without creating data. After that, the
  next retarget unit is pose-space conversion/bake design for genuinely differing rigs;
  it must remain separate from this strict aligned-copy path.

## Retarget-readiness checkpoint — 2026-09-23

- The user reported about 30% daily usage remaining and asked to prioritize that daily
  figure rather than the weekly figure. This bounded unit was completed without starting
  an actual retarget mutation workflow.
- Added the fourteenth Skill, `blender-inspect-retarget-readiness`. It compares two
  explicitly mapped humanoid Armatures and one bound source Action without inferring bone
  names or changing Blender. It reports mapping completeness, mapped/unmapped animation
  coverage, Action ownership/slot, Armature Object transforms, existing target animation,
  and per-role rest-bone length/direction metrics.
- A positive `retarget_candidate` is intentionally not a quality or write certificate.
  Rest-pose alignment, bone roll/axes, constraints, weights, deformation, root-motion
  policy, visual quality, Mixamo compatibility, Unity behavior and actual bake remain
  outside this Skill.
- The owned Blender 5.0.1 fixture passes 11 checks from repository source, portable ZIP,
  and installed Workspace helpers. It covers a complete candidate, both humanoid reports,
  rest metrics, mapped and extra-bone Action coverage, preservation reviews, same-rig,
  incomplete-map, unbound-Action and invalid-slot behavior, read-only inventory and exact
  teardown. The first run found and fixed two fixture-only defects: EditBone name lifetime
  and an overly strict float assertion.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-retarget-readiness`.
  Archive SHA-256:
  `76b8c48517d44aaf83b3c64b65fe44ec560ef8926f204eb707334115fb7d13a0`.
- Final validation: repository structure OK; scripts **86 pass**; Workspace **47 run / 4
  explicit Windows symlink skips**; all **14** source/installations are byte-aligned.
  `skill-creator` quick validation remains unavailable because optional PyYAML is absent;
  repository packaging/frontmatter/compile and all live helper paths pass without it.
- Blender remained the original `Scene` with `Cube`, `Light`, `Camera` and one material;
  no user asset, Profile, Unity project or existing installed Skill was changed. The MCP
  addon remains version 1.7/protocol 7 against expected protocol 9; verified fallback
  execution still works, so no update was performed.
- Remaining gate: a refreshed client must expose the fourteenth Skill and, because the
  current file has no two Armatures or Action, report the missing inputs without creating
  test data. After that, design an actual retarget workflow only as a separate guarded
  unit; do not silently create constraints, change rest poses, rename bones or bake Actions.

## Root-motion host gate and continuation point — 2026-09-23

- User confirmed refreshed-session exposure of `blender-inspect-root-motion`. The current
  Blender file has neither Action nor Armature, so the host correctly refused execution
  without creating test data or modifying Blender. The thirteenth Skill's discovery and
  no-target behavior gate is complete.
- Read-only repository validation still passes, and all **13** source Skills remain
  byte-aligned with the 13 personal Workspace installations. No Blender, Unity, Profile,
  project or installed-Skill file was changed in this checkpoint.
- The user-visible quota screenshot now shows 22% weekly remaining and 33% in the current
  five-hour window. Per the project continuation policy, do not open the next substantial
  retargeting unit in this session. The current atomic unit is complete and consistent.
- Next session must begin with a read-only retarget-readiness contract and synthetic
  source/target Armature inspection. It must reuse explicit humanoid mappings, compare
  required roles/rest hierarchy/scale and Action ownership, and must not yet retarget,
  rename bones, change rest poses, bake Actions or require Unity. Only after that evidence
  passes should a retarget mutation design be considered.

## Explicit root-motion checkpoint — 2026-09-23

- User confirmed refreshed-session exposure of `blender-inspect-animation-loop`. With no
  Action in the current file, the host correctly did not execute, create test data or edit
  Blender. The twelfth Skill's discovery/no-target gate is complete.
- Added and installed the thirteenth Skill, `blender-inspect-root-motion`. It reads stored
  XYZ translation evidence for one explicitly named Object or Armature bone, exact Action
  slot/range and explicit tolerance. It does not guess the root, interpret root rotation,
  select in-place policy, evaluate poses or change animation.
- The owned Blender 5.0.1 fixture passes ten checks for explicit Root movement, axis span,
  non-root exclusion, rotation review, Object/Bone distinction, bad mapping/range/slot
  refusal, read-only preservation and exact teardown. Repository source, portable ZIP and
  installed Workspace helpers all pass. ZIP SHA-256:
  `8d7ab1e164b4a00c0305bedc293d8a65658cf83780d92dc58a1e00c580092e11`.
- Final validation: repository structure OK, scripts **85 pass**, Workspace **47 run /
  4 explicit Windows symlink skips**, and all **13** source/installed Skills are
  byte-aligned. Blender remains Scene with Cube/Light/Camera and one material.
  `skill-creator` quick validation remains unavailable because optional PyYAML is absent;
  packaging/frontmatter/compile and live helper tests pass without installing it.
- Refreshed-client exposure/no-Action behavior remains for the thirteenth Skill. The
  user-visible quota screenshot showed 25% weekly remaining, so after completing this
  atomic unit no new retargeting/editing unit was opened. Next priority after the host
  gate is retarget-readiness design, not automatic retarget or animation editing.

## Animation loop endpoint checkpoint — 2026-09-23

- User confirmed refreshed-session exposure of `blender-copy-action`. With no Action in
  the current file, the host correctly did not run the copy, fabricate test data or edit
  Blender. The eleventh Skill's discovery/no-target gate is complete.
- Added and installed the twelfth Skill, `blender-inspect-animation-loop`. It compares
  stored F-Curve scalar values at explicit start/end frames using an explicit value
  tolerance, reports boundary keys and Cycles modifiers, and never changes the current
  frame. It deliberately does not claim evaluated-pose or visual loop certification.
- The owned Blender 5.0.1 fixture passes nine checks for match/mismatch, explicit relaxed
  tolerance, boundary coverage, invalid/missing input refusal, inventory/frame preservation
  and exact teardown. Repository source, portable ZIP and installed Workspace helpers all
  pass. ZIP SHA-256:
  `101d1df1cfacd66a3c97a23ddda2ec8510f5cb7c0614196a37e6318b8aad5ec1`.
- Final validation: repository structure OK, scripts **84 pass**, Workspace **47 run /
  4 explicit Windows symlink skips**, and all **12** source/installed Skills are
  byte-aligned. Blender remains Scene with Cube/Light/Camera and one material.
  `skill-creator` quick validation remains unavailable because optional PyYAML is absent;
  packaging/frontmatter/compile and live helper tests pass without installing it.
- Refreshed-client exposure/no-Action behavior is the remaining gate for the twelfth
  Skill. After that, the next independent roadmap unit is explicit root-motion inspection.
  Evaluated-pose/tangent/visual loop validation remains open rather than overstated.

## Action organization checkpoint — 2026-09-23

- User confirmed refreshed-session exposure and a real read-only call of
  `blender-inspect-animation`: Scene targets Camera/Cube/Light, no Actions, bindings,
  drivers, NLA strips or root-motion channels, no root-name inference, and identical
  before/after state. The tenth Skill's discovery/no-data behavior gate is complete.
- Added an explicit read-only Action-copy plan. It binds one exact Scene/source/target
  request to inventory, preserves source and references, requires an unbound fake-user
  copy, rejects unknown policy fields/collisions and refuses target names over Blender
  5.0.1's observed 255-byte UTF-8 ID-name limit. Its owned fixture passes nine checks.
- Added and installed the eleventh Skill, `blender-copy-action`. Its apply requires a
  fresh detailed content fingerprint plus explicit authorization, copies one whole Action
  to an unused name, leaves current/NLA references unchanged and keeps the copy unbound.
  Source, ZIP and installed-helper Blender runs each pass eight checks with exact teardown.
  ZIP SHA-256: `591f467ea20487baf28ba0289194798f98ccbcc22c7e772e41695bc3428f155d`.
- One initial fixture correctly failed stale after keyframe-value restoration because
  Blender had also moved its handles; the fixture now uses a fully reversible F-Curve mute
  toggle. This demonstrated that the detailed content guard detects hidden curve changes.
- Final validation: repository structure OK, scripts **83 pass**, Workspace **47 run /
  4 explicit Windows symlink skips**, and all **11** source/installed Skills are
  byte-aligned. Blender remains Scene with Cube/Light/Camera and one material. The
  `skill-creator` quick validator again could not start because optional PyYAML is absent;
  repository packaging/frontmatter/compile tests passed and no dependency was installed.
- Refreshed-client exposure is the only remaining gate for `blender-copy-action`. Because
  the current Scene has no Action, the host should confirm exposure and safely refuse to
  fabricate source data. After that, the next roadmap unit is read-only loop-validation
  design; frame-range extraction/take splitting/source renaming remain deliberately open.

## Animation inventory Skill checkpoint — 2026-09-23

- Promoted the bounded animation inventory into the tenth source Skill,
  `blender-inspect-animation`. It remains strictly read-only: file-wide Actions plus
  scoped bindings, slots, drivers, NLA strips, F-Curves/keyframes and only explicitly
  supplied root-bone location channels. It does not import, extract/name, evaluate,
  judge loops, retarget or edit animation.
- Expanded the owned Blender 5.0.1 fixture from eight to 11 checks by adding NLA-strip,
  driver and unused-Action inventory. Repository source, portable ZIP and installed
  personal-Workspace helper all pass the same 11 checks with exact fixture teardown;
  original Scene remains Cube/Light/Camera with one material.
- Installed only the new Skill without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-animation`. All ten source
  and installed Skills are byte-aligned. Portable ZIP SHA-256:
  `30f93ff4fa2ff78596ec8ef10493508352a430920310df4c0a782c2aef484085`.
- Final validation: repository structure OK, scripts **78 pass**, Workspace **47 run /
  4 explicit Windows symlink skips**. Sandboxed temp creation is blocked by Windows ACL,
  so both suites were rerun successfully with the established non-sandboxed test path.
  `skill-creator` quick validation could not start because optional PyYAML is absent;
  repository packaging/frontmatter/compile tests passed and no dependency was installed.
- Refreshed-client automatic discovery is the only remaining gate for this Skill. In a
  new/refreshed Workspace session, ask for `blender-inspect-animation` on the current
  Scene without creating test data. If no Actions exist, it must report that bounded
  result and make no Blender changes. After that, the next independent roadmap unit is
  read-only Action extraction/naming design, not extraction or mutation itself.

## Completed host-driven static FBX / Unity gate — 2026-09-22

- The refreshed personal Workspace client completed the full
  `blender-export-static-fbx` protocol on `Scene / Cube`: formal
  `candidate_for_review`, no blockers, matching fingerprint, `created` publication,
  no overwrite, stage cleanup, and unchanged unsaved Blender Scene/Object state.
- Published test artifact was exactly 15,020 bytes with SHA-256
  `c88378061c4b1de95bb0cc9d38e5344ce59ebcd1a2fdaff279ebaea291294136`
  at the user-authorized Unity `Assets/Blender` path. The development session
  independently verified both values before running Unity.
- Unity 6000.3.9f1 imported that exact hash and the request-bound validator passed all
  12 checks: one Mesh, 24 imported vertices, 12 triangles, 24 UV coordinates, one
  submesh/material slot, zero animation clips, identity root, `2 x 2 x 2` Preview
  Scene bounds and active-Scene preservation. The source Cube's eight control vertices
  becoming 24 imported vertices is expected vertex splitting at hard normal/UV corners,
  not added surface topology.
- Unity `AssetDatabase.DeleteAsset` then removed only that exact FBX and generated
  `.meta`. `Assets/Blender` returned to only `Blender.unity` and its `.meta`, with the
  established hashes unchanged. The active Scene remains `Blender.unity`, not dirty,
  two roots, null selection; Blender remains Cube/Light/Camera with one material.
- This closes the seventh Skill's host apply and Unity import/cleanup gate. Texture
  sidecars, rigs/animation, colliders/LOD and visual material fidelity remain outside
  this narrow static export claim. Unreal/public distribution remain out of scope.
- Added `scripts/update_skill.py` as the next bounded foundation unit. It separates a
  read-only exact-manifest plan from apply, retains the prior installation at an unused
  backup path, rolls back an injected promotion failure, and restores without deletion by
  retaining the replaced new version. Isolated tests cover drift/collision/refusal and
  CLI use; the real personal Workspace was not updated. Client refresh remains separate.
- Final regression passes: repository structure OK, scripts **77 pass**,
  Workspace **47 run / 4 explicit Windows symlink skips**. The actual personal Workspace
  contract passes and all nine installed Skills are byte-aligned with repository sources;
  these were read-only checks and do not imply a refreshed client catalog.
- Completed the next single source/install capability after that checkpoint: read-only humanoid Armature
  inspection with explicit role mapping and no name guessing. A Blender 5.0.1 owned
  synthetic fixture passes 11 checks for mapping/hierarchy/refusals/deform/animation and
  exact teardown. Repository-source, ZIP and installed-Workspace helper runs all pass;
  only the new eighth Skill was deployed without overwrite. ZIP SHA-256 is
  `3139659171020e101f72ec73767d9dae1a8e3f73674cda760bba2f91bf94d00e`.
  Refreshed-client discovery and a real/synthetic explicit-mapping host call remain the
  next user-session gate. See
  `docs/humanoid-inspection-validation.md`.
- User subsequently confirmed refreshed-session automatic exposure. With only
  Cube/Light/Camera and no Armature, the host correctly did not invoke humanoid analysis,
  fabricate a mapping or modify Blender. Discovery and missing-target refusal pass; an
  explicit-mapping host call remains separate and does not block repository development.
- Completed the next narrow Mixamo foundation: `blender-inspect-mixamo-preflight` detects
  one exact naming signature, derives the explicit mapping and reviews bound Mesh groups,
  transform and existing animation without edits. Source/ZIP/installed-helper Blender
  runs each pass eight checks with teardown. ZIP SHA-256 is
  `9a42ec2d372221b36ae78ec324ae27e47bbcea392cfb1065d32224022b6c97c3`;
  only the new ninth Skill was deployed no-overwrite. Refreshed-client exposure remains.
- User then confirmed refreshed-session automatic exposure of the Mixamo preflight. With
  no Armature, it correctly did not run, create a test rig or modify Blender. Discovery
  and missing-target refusal pass.
- Added the next bounded animation foundation without a new Skill deployment:
  `scripts/inspect_animation.py` inventories stored Actions, slots/bindings, NLA,
  F-Curves/keyframes and only explicitly mapped root-bone location channels. The owned
  Blender 5.0.1 fixture passes eight checks with frame/context/ID teardown. Import,
  extraction/naming, loop judgment, retarget and editing remain separate.
- Final regression after this unit: repository structure OK, scripts **77 pass** and
  Workspace **47 run / 4 explicit Windows symlink skips**. Current personal Workspace
  still has nine aligned Skills; animation inventory was intentionally not packaged or
  installed yet. Next session should first extend its synthetic evidence to NLA strip,
  unused Action and driver inventory before deciding whether to create the tenth Skill.

## Latest staged static FBX and Unity checkpoint

- User confirmed refreshed-client automatic exposure of `blender-export-static-fbx` and
  read-only Cube preflight. With no Profile/absolute target/axes/scale, it correctly kept
  authorization false and did not fabricate a formal candidate or write a file. Host
  discovery and information-missing refusal pass; host-driven disposable apply is separate.
- Added `scripts/prepare_unity_static_fbx_check.py` and six offline tests. An explicit
  request binds project/Assets path and SHA-256 to topology, UV, material, clip, root
  transform, world-bounds and Scene-preservation expectations; optional import refresh
  is explicit. Generated C# is no-overwrite and fails on any mismatch.
- Live Unity positive check passed 12 named comparisons on a new installed-Skill-exported
  quad; an intentional 3-vs-2 triangle expectation failed closed with the exact check.
  The first generated C# caught a Windows backslash escaping bug at compile time; it was
  fixed, regression-tested and rerun. Exact fixture FBX/meta were deleted afterward.
  See `docs/unity-static-fbx-validation.md`.
- Final validation: repository structure OK, scripts **66 pass**, Workspace **47 run /
  4 skipped**, actual personal Workspace validation passes, and no staged directories
  remain. Unity target folder contains only the original Scene/meta with unchanged hashes;
  Unity Scene is not dirty with two roots, and Blender is Cube/Light/Camera.
- The host-driven disposable export, Unity validator and exact deletion described here
  were subsequently completed; the newer section above is authoritative.

- Promoted the proven narrow path into source Skill `blender-export-static-fbx` after
  removing its accidental dependency on the test-only `source_fingerprint`. The Skill's
  own export fingerprint tracks geometry, material and relevant reported state; native
  `export-context` now passes **34 checks** including geometry/material change detection.
- Source-Skill, ZIP-helper and installed-helper Blender runs each pass the same **10**
  staged checks. ZIP SHA-256 is
  `0434A3C73264895C21812651EE10A9ED87633DCE7120FB072FCBF33BAF83104F`.
  No-overwrite deployment added only the seventh Skill under
  `D:/AI/GameAssetAI-Workspace/.agents/skills`; alignment has no changed/missing/extra
  files. Discovery was initially unverified because the session was already open;
  the later refreshed-session gate above passed. See
  `docs/static-fbx-skill-validation.md`.

- Added development-only `scripts/export_static_fbx_staged.py` and
  `tests/static-mesh/run_fbx_staged_export.py`, wired as `--suite fbx-staged`.
  It requires explicit authorization and a fresh request-bound candidate, exports one
  texture-free Mesh to a unique same-directory stage, verifies binary/Object/source,
  then atomically publishes without overwrite. It never removes a published target.
- Native Blender 5.0.1 staged suite passes **10 checks**, including missing authorization,
  stale candidate, existing target and injected late `.meta` refusal, source/ID/original
  preservation and exact artifact cleanup. `export-context` later reached **34 checks**
  after the self-contained export fingerprint regression was added.
- Extended the explicit request contract with `apply_scale_options`,
  `use_space_transform` and `bake_space_transform`; current Blender RNA identifiers are
  checked rather than assumed. Repository structure OK; scripts **59 pass**. Workspace
  suite remains **47 run / 4 skipped** from this session's approved rerun.
- In the authorized Unity-only folder, compared four synthetic unit/axis variants.
  `FBX_SCALE_NONE` yielded compensating root scale 100; `FBX_SCALE_UNITS` yielded scale
  one but an axis-correction rotation; Unity Bake Axis Conversion did not eliminate it.
  Static-only Blender `bake_space_transform=true` plus `FBX_SCALE_UNITS` imported with
  identity root and expected `2 x 0 x 1` world bounds. Blender marks that option
  experimental, so this result must not be reused for rigs/animation without new tests.
- Final request-bound staged Unity import: one Mesh, 4 vertices, 2 triangles, 4 UVs,
  one submesh/material, zero clips; Preview Scene only. Active `Blender.unity` remained
  not dirty with two roots. Unity deleted exact test FBX/meta files. Target folder
  returned to only `Blender.unity` and `.meta`, whose SHA-256 values still match
  `D3E92CB4E393601199E0D0C870706A3A80377429F5C6117D7A944CD75F21D8FB` and
  `0D9695875929209775B5E8E37206FFFD02588306055B133BE79DF694AC248603`.
- Blender MCP implementation remains `ahujasid/blender-mcp` at `localhost:9876`.
  Blender is 5.0.1; exposed addon 1.7/protocol 7 is behind the tool's expected protocol
  9, but current calls succeeded through compatibility fallback. No update was installed.
- The earlier next gates—refreshed discovery/refusal and the narrow Unity validator—are
  complete above. Remaining host gate is one disposable explicitly configured apply and
  Unity validation/cleanup. Textured `.fbm`, rigs, animation, colliders and LOD remain
  separate; Unreal and public distribution remain out of scope.

## Latest FBX sidecar checkpoint

- A test-only Blender 5.0.1 textured static FBX export with `path_mode=COPY`,
  `embed_textures=False` produced owned `output/probe.fbx` plus
  `output/probe.fbm/source.png` copied from owned `source/source.png`.
  Source/copied PNG SHA-256 matched. The one-off fixture's Scene/context and
  tracked data-name lists restored; original Scene remains Cube/Light/Camera.
- Inspected the exact six-entry temporary tree, then removed only its three
  files and empty directories. No Unity project, original Blender asset,
  Workspace/Profile or Skill installation changed. Evidence and limitation:
  `docs/unity-export-contract.md`.
- `COPY` remains refused by the request preflight; single-file hardlink
  publication is not a complete `.fbm` transaction. Next safe development unit
  is multi-artifact ownership/collision/rollback design or a narrower
  texture-free export path. No production export is authorized yet.

## Latest static FBX candidate checkpoint

- Continued the Unity-only/local-use plan. Added explicit `scene_name` and SHA-256
  of a valid static FBX request to the offline preflight. Added development-only
  `scripts/inspect_static_fbx_candidate.py`, loaded by `export-context`, to bind
  that request to a live named Blender Scene/Object and current FBX RNA/poll.
- Native Blender 5.0.1 `export-context` now **29 checks pass**: no-dependency
  candidate remains non-authorized, stale/missing preflight, invalid axes/scale,
  inactive Scene, shared Mesh, modifier and direct texture-node paths refuse.
  Exact synthetic ID cleanup and original fingerprint
  `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`
  restored. An initial assertion compared context-sensitive fingerprints from
  different temporary contexts; the comparison was corrected and rerun.
- No Blender/Unity user asset, Profile or Workspace changes; no export, Skill or
  installation. Next independent risk is staged artifact and material/texture
  sidecar behavior. A production destination or engine result is still not
  authorized by either read-only preflight.

## Current scope decision

- User removed Unreal-specific support and external/public distribution from the
  active plan. Preserve existing Unreal project paths/data and historical evidence;
  do not build Unreal export, release automation or public packaging. Local Skill
  installation/update and tests remain necessary for the personal Workspace.
- Updated root instructions/README and architecture, requirements, workflow,
  roadmap. The Unity import result below remains the latest engine evidence.
- Next bounded work: define a conservative Unity export contract with explicit
  per-game/user choices and fail-closed checks; do not infer defaults from the
  one synthetic Unity import. Then verify it offline before any production export.
- That bounded unit is complete: `docs/unity-export-contract.md`, read-only
  `scripts/validate_static_fbx_request.py` and six new offline tests. Blender 5.0.1
  FBX axis enums and scale RNA range were read via MCP without scene changes.
  No export, Skill installation, Workspace/Profile or Unity project file change.
  The next task is Blender-side Object/state verification and staged-artifact/
  sidecar policy, still requiring explicit per-game choices for any real export.
- Latest validation: repository structure OK, script suite **59 pass**,
  Workspace suite **47 run / 4 skipped** (Windows symlink privilege skips).
  Initial sandboxed test run failed because the OS temp directory was inaccessible;
  approved non-sandboxed rerun passed. No Git metadata is present in this checkout.
- Extended `inspect_static_export_context.py` to report live FBX axis enums and
  scale RNA hard range. The `export-context` native fixture now passes **19** checks
  with original Scene fingerprint and ID lists restored. Matched the offline
  request guard's minimum to Blender's observed float hard minimum
  `0.0010000000474974513`; no export or original-scene change occurred.
- Static FBX request guard also rejects Windows-reserved/invalid destination names,
  unknown/missing fields, invalid axes/flags, copy-mode sidecars and existing
  `.fbx`/`.meta`; path inspection failures refuse. Final repository structure OK,
  scripts **59 pass**, Workspace **47 run / 4 skipped**.

## Latest Unity import checkpoint

- User authorized testing only inside
  `C:\Users\jiwoo\UnityProject\GameEngineering\Assets\Blender`; the existing
  `Blender.unity` and `.meta` were not edited. Unity MCP was not exposed, but the
  installed Unity CLI connected to the running 6000.3.9f1 Editor after an
  approved non-sandboxed status check. Blender 5.0.1/MCP 1.7/protocol 7 was
  connected. No Unity package, scene, project setting or Workspace Profile changed.
- A unique synthetic FBX exported from a separate Blender-owned quad was imported
  as a ModelImporter asset: 4 vertices, 2 triangles, UV, normals, tangents,
  material/renderer. Tested -Z/Y axis conversion gave expected world positions
  and upward normals. In-memory Unity Preview Scene prefab instantiation passed;
  it was closed without saving. Built-in pipeline Standard shader reference was
  supported, but material appearance and production assets were not tested.
- Unity removed only the test FBX and generated `.meta`; exact repo staging FBX
  was removed. Unity Blender folder again has only the original scene and meta,
  with pre/post SHA-256 matches. Unity Scene remained active, two roots, not dirty;
  Blender Scene remained Cube/Light/Camera with no test-owned IDs. Full methods,
  observed importer defaults and limitations: `docs/unity-import-validation.md`.
- Initial one-off Blender teardown halted because the owned Mesh still held its
  owned material. The exact tagged Mesh, then material, then Scene were removed
  after ownership/user verification; no test ID remained. Repeatable fixtures
  must use this order. Repository validator passed; offline script suite **52
  pass** and Workspace suite **47 run / 4 skipped**.
- Next priority: define an explicit Profile/user export contract (format, axes,
  units, selection, destination, material/sidecar handling and no-overwrite policy)
  before a reusable export Skill. Do not generalize this one test to rigs,
  animations or different render pipelines. No user action needed merely to
  preserve or inspect this synthetic result.

## Latest sixth-Skill host outcome and next development boundary

- Native FBX export overwrote only an owned sentinel when explicitly targeting its path
  (`check_existing=False`). Added `scripts/promote_export_artifact.py`: same-directory
  absolute regular stage and non-linked parent, atomic `os.link` to absent destination,
  existing target collision refusal, no copy/replace fallback, stage kept for caller.
  Offline promotion tests cover success, existing target, invalid paths and mocked
  unsupported hardlink failure; development-tools suite now **52 pass**.
- Expanded `fbx-probe` to **23 Blender checks**: own sentinel overwrite hazard, published
  new target, existing published target preserved, all three exact owned files removed.
  Synthetic Blender IDs, original Scene context/fingerprint/ID lists restored. Raw
  `.local/validation/fbx-no-overwrite-20260919.json`. Helper is development-only,
  single-file and not a production export Skill; cannot certify Unity/material appearance.
- Next safe boundary needs explicit game export contract and a real Unity version/import
  target before claiming a supported Unity export workflow. Current active Profile is
  null and Workspace project mappings contain zero entries. Do not infer axes, unit
  conversion, destination or format from test-only values. User input is needed to
  identify an existing disposable Unity import target and authorize test-owned files
  there; never move the project or write under it based solely on this repository.
  Additional Blender-only tests can continue, but must not be labeled engine validation.

- Continued static export foundation: verified FBX operator `poll`, then added
  `tests/static-mesh/run_fbx_export_probe.py` and `--suite fbx-probe`. It uses a new
  synthetic Scene/Object/Mesh/material and one unique FBX under ignored
  `.local/validation/`, explicit test-only -Z/Y axes, scale1/no unit conversion,
  selection-only Mesh/no animation. Blender 5.0.1 exporter created one binary file;
  own FBX importer loaded one Mesh into a separate owned Scene. **19 checks pass** for
  model record scope, vertices/face/UV/material reference, world residual
  2.384185791015625e-07 <= test-only 1e-5, original context/fingerprint/ID list and
  exact artifact cleanup. No remaining gameassetai-fbx-* temp directory. Raw result:
  `.local/validation/fbx-roundtrip-20260919.json`.
- Initial naive substring scope check hit FBX `DefaultCamera` metadata; changed to actual
  model-record matching and retested. No original Scene object was exported as a model.
  No Unity engine import or material appearance claim; explicit test axis values are
  not defaults. No new Skill, production path write or external project change.
- Next bounded task: decide whether additional Blender-only glTF or roundtrip refusal
  probes materially reduce export risk; then define a conservative no-overwrite export
  workflow only with explicit game Profile/user format, axes, units and destination.
  Actual Unity project/version/import validation remains separately unverified.

- Following host outcome, built development-only read-only
  `scripts/inspect_static_export_context.py` and synthetic
  `tests/static-mesh/run_export_context.py`; added `--suite export-context` payload,
  offline source-count and repo-required-path checks. Blender 5.0.1 native **17 checks
  pass**. FBX/glTF RNA option names were observed without operator call; original Scene
  Cube/Light/Camera and fingerprint restored. Workspace active Profile is null, so format,
  axes, unit conversion, destination, selection and Unity behavior remain unknown.
  Evidence: `docs/static-export-preflight.md` and ignored
  `.local/validation/export-context-20260919.json`.
- Next boundary: synthetic FBX export in an exactly owned temporary directory, artifact
  inspection and cleanup, with explicit test-only settings. This is not a production
  exporter/Skill and must not touch original Scene, Unity projects or mapped paths.

- User confirmed actual Workspace client selected `blender-relocate-pivot-copy` for an
  instruction-led synthetic UV triangle. Preview local (0.25,0.25,0) predicted world
  (1.25,2.25,3), verify fingerprint matched, apply returned `created` on independent
  copy. Original Mesh/UV/topology retained, world/pivot errors 0 <= explicit 0.00001;
  only test-owned IDs removed and start/end state matched. This host gate is complete
  by user report, not raw client/MCP traces. Do not request repeat of any of six passed
  synthetic host outcomes. No source or installation change from this report.
- Next independent development unit: static asset export preflight, initially read-only
  and Profile-aware without assuming engine axes, units, output path or FBX/GLB behavior.
  Verify Blender operator/API availability in the live 5.0.1 environment before coding;
  no save/export/Unity-project mutation until a separately tested workflow exists.


## Latest pivot multisurface/dependency checkpoint

- Skill Creator was read/used after 61-check multi-surface evidence. Extracted pivot
  file-wide blocker/surface checks into development apply helper, removing dependency on
  scale-apply; retested 61 live checks. Added self-contained sixth source Skill
  `blender-relocate-pivot-copy` with four mirrored helpers, concise authorization/policy/
  rollback instructions, source-equality offline regression and `pivot-skill` payload.
- Creator quick validation, source and actual ZIP native runs passed 61 initially, then
  source/ZIP/installed runs each passed **63** after adding a second owned Object sharing
  the source Mesh. Copy remained independent, both original users and coordinates intact,
  exact fixture cleanup/fingerprint restored. Only the harness changed; Skill ZIP/install
  bytes unchanged. Latest raw results: `.local/validation/pivot-shared-source-20260919.json`.
  ZIP SHA-256
  `96ddaab497944146fd468b87950ac5eee0a4ace87c231df31b0a1f3281456e7d` under
  `.local/source-bundles/pivot-skill-20260919/`. New no-overwrite deployment added only
  sixth Skill to `D:/AI/GameAssetAI-Workspace/.agents/skills`; initial installed native
  run also passed 61. Earlier responses: `.local/validation/pivot-skill-20260919.json`.
  All six source/install byte comparisons align; personal config/Profiles/projects and
  previous five Skill installations unchanged. Actual client discovery is not verified.
- Offline scripts **49 pass**, Workspace **43 pass/4 Windows privilege skips**; repo and
  actual Workspace validators pass. No Git metadata/release, quota estimate, engine
  certification, original save/export. Original Blender fingerprint/ID lists restored.
- Next host-only gate: actual Workspace client exposure and instruction-led synthetic
  sixth-Skill preview/apply/restore. Do not demand repeats of first five host tests. In
  this development session direct installed helper calls are complete; catalog routing
  cannot be inferred from them. Copyable host prompt in docs/pivot-copy-validation.md.
  Continue repository work where independent checks remain.

- Read root AGENTS/README/current state and repository; no `.git` metadata, so no Git
  status/commit claim. Blender MCP 5.0.1/addon [1,7]/protocol 7 is connected, original
  Scene initially Cube/Light/Camera and one material. No quota API or usage estimate.
- Expanded only the development pivot native harness: two-face/two-material/two-UV
  independent-copy checks and owned source animation, constraint, modifier, vertex-group
  plus file-wide Scene animation refusal/recovery. **61 Blender checks pass**; exact
  synthetic ID teardown and original fingerprint match. Raw response/source hashes:
  `.local/validation/pivot-multisurface-20260919.json`. No source/apply helper change,
  new Skill, Workspace installation/config change, original save or export.
- At that checkpoint the next task was packaging; completed in the newer bullets above.


## Latest explicit-pivot development checkpoint

- Continued after fifth host confirmation and final-state safety correction below; added
  development-only scripts/preview_pivot_copy.py and apply_pivot_copy.py, native harness
  tests/static-mesh/run_pivot_preview.py, docs/pivot-copy-validation.md. No sixth Skill,
  pivot installation, personal settings/Profile/project or architecture changes.
- Explicit finite local point and tolerance; no automatic center/bottom/engine policy.
  Predict B*T(p), vertices v-p; apply on independent tagged copies with authorization,
  unused name, fresh snapshot, file-wide dependency guards and before/after-link checks.
  Source scale/rotation retained, world positions unchanged, copied origin relocates.
  Retains vertex count/topology/UV/material refs; safe exact-owned rollback only.
- Native Blender 5.0.1 suite **49 pass**, including malformed parameters, stale snapshot,
  scope/tolerance/candidate binding, delta/reflection refusal, collision/no-change, UV/world/
  channels/independence/source checks and injected write/link/linked UV/scale/Mesh/vertex
  failures. Exact original fingerprint/ID lists restored. Raw response/source hashes:
  .local/validation/pivot-copy-20260918.json. Earlier 32-check preview count is historical.
- Payload --suite pivot-preview now eight separately compiled sources, including dev scale
  helpers as dependencies; compile/source-count offline regression and validator updated.
  This helper is NOT standalone/installable; do not deploy it separately as a Skill.
- Next first task: representative multi-face/material/two-UV pivot fixtures and dependency
  refusal/rollback guards, then decide narrowly self-contained packaging based on evidence.
  Do not request repeat fifth-Skill or Profile gates. No user action required currently.
- Final offline scripts 48 pass; Workspace 43 pass/4 explicit Windows privilege skips.
  Repo/Workspace validators pass. Installed five Skill versions remain aligned; latest
  installed native counts below remain 421, pivot is separately development-only 49.
  No original save/export, release, quota estimate or external service introduced.

## Previous fifth Skill host outcome and final-state safety checkpoint

- User confirmed fifth Skill preview/verify/apply, independent copy, unit scale, zero world/
  pivot error and exact synthetic restore on Blender 5.0.1. Host outcome complete; do not
  request repeat, reinstall, Profile or previous four Skill gate checks. Raw routing/client
  build remains a separate release evidence gap, not a repository development blocker.
- Expanded native transform harness: tilted-face world normal/tangent directions and
  bitangent signs (synthetic only), isolated overflow refusal and tiny-positive preview.
  Tiny-positive apply not attempted; numerical conditioning/engine shading not certified.
- Reproduced old apply helper accepting post-link UV mutation. Mirrored development/Skill
  helpers now recheck linked Object/Mesh, exact scale, topology/UV/material surface,
  non-scale channels and parent-inverse. Linked UV/scale/Mesh reassignment refuse and
  roll back completely. Unexpected successful fixture copies are tracked before assertions.
- Old reproduction left only owned synthetic IDs: inspected exact owner tokens, users and
  references, removed exact Object/Mesh/material/Scene. Final native runs restore original
  fingerprint f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d and ID lists.
  No original Scene save/export; synthetic setup may dirty file, clean flag not certified.
- Source/new ZIP/actual installed transform suites each 90 pass. Existing installed suites
  169 + 162 pass; distinct latest installed total 421. Offline scripts 48 pass, Workspace
  43 pass/4 Windows symlink privilege skips. Repo/Workspace/Creator validators pass;
  all five installations byte aligned. No live quota API; no exhaustion estimate invented.
- Approved hash-guarded patch changed only installed apply_scale_copy.py. Exact original
  bytes stored as base64+SHA in .local/deployment-backups/scale-postlink-20260918/.
  Latest fifth archive .local/source-bundles/scale-postlink-20260918/ SHA
  4a0035da669209d6bc9f510dce913f50838c43e6f8139e2cca1db264e731c1a7.
  Raw responses/hashes .local/validation/scale-postlink-20260918.json. Earlier ZIP obsolete.
- Changed mirrored apply helpers, native transform harness, README/skills/tests docs,
  transform evidence, roadmap/release/host evidence and this state. Architecture and
  personal Workspace configuration/Profiles/projects/MCP unchanged; no new Skill/release.
- At that checkpoint next bounded task was explicit-target read-only pivot candidate analysis,
  distinguishing pivot relocation from mesh centering without choosing a game-specific
  policy. Continue via existing transform snapshot; no original pivot/mesh mutation.
  Broader export, reflected/dependent sources and production rigs remain unverified.

## Historical positive-scale apply / fifth Skill checkpoint

- Implemented scripts/apply_scale_copy.py: fresh preview, explicit authorization and unused
  <=63 UTF-8 byte name, file-wide animation data/drivers/constraints refusal, independent
  Object/Mesh copies, positive scale baked only into copied vertices. Exact unit output
  scale; original location/rotation/pivot, topology/edge flags/UV activity/material refs,
  source hash/surface/reported-world matrix checked. No dependency graph refresh/save/export.
- Native failures fixed and retested: copied cached matrix_world remained scaled after
  channel assignment -> validation refused and rolled back completely; setting only the
  new copy's world matrix fixes it. Rotated matrix decomposition introduced sub-unit scale
  rounding -> restore exact unit scale and source location/Euler channels then validate.
  NaN residual comparisons explicitly fail, not silently pass. No original/Scene update.
- Preview additionally binds parent-inverse and active/render UV state; older preview hashes
  require re-preview. Positive XYZ/static restriction unchanged, reflection/zero/delta/rig/
  parent/custom-normal cases deferred; evaluated geometry/normals/tangents/procedural material
  appearance/numerical conditioning/concurrent callbacks are NOT certified.
- Transform harness now 82 checks: prior 56 + 26 apply/refusal/rollback checks. Source,
  actual ZIP and installed helper versions each pass. Two UV layers/activity, rotated/
  translated/nonuniform output positions/pivot, independent Mesh and source preservation,
  auth/hash/name/empty unrelated animation/Constraint guards, stale no-change and injected
  write/wrong-coordinate/NaN/post-link rollback tested. Exact fixture teardown restores
  original fingerprint/IDs. Raw ZIP/installed responses/hashes in ignored
  .local/validation/scale-apply-20260918.json.
- Used Skill Creator after native evidence to create ONLY blender-prepare-positive-scale
  with three self-contained mirrored helpers and source-equality regression. UTF-8 Creator
  quick validation passes. Actual archive .local/source-bundles/scale-copy-20260918/
  blender-prepare-positive-scale.zip SHA
  3bafd45ed790168308068760d67ac7e87c995195783e62679c1fac3b7d7a1671.
  Directory includes inspector ZIP for harness, not full five-bundle set. Native Skill
  needs no other installed Skill.
- Confirmed destination absent; approved no-overwrite deploy added only new Skill to
  existing D:/AI/GameAssetAI-Workspace/.agents/skills. All FIVE installations byte aligned.
  Existing four Skills, personal Profiles/settings/projects/MCP unchanged. No publication.
- Final existing installed regressions 169 + 162 = 331 pass; new installed suite 82 pass,
  total separate latest suites 413 pass. No cumulative/doubled source+ZIP count. Offline
  tools 48 pass, Workspace 43 pass/4 Windows symlink privilege skips, repo validator passes.
- Changes: apply helper, preview hash, native harness, payload source origin/suite routing,
  required-file validator, offline counts/source equality, new source Skill/helpers,
  transform/roadmap/release docs, repo/skills/scripts/tests READMEs and this state.
- Current highest host gate: fifth Skill exposure/instruction-led synthetic preview/apply/
  restore in an actual catalog-exposing Workspace conversation. This session already ran
  actual installed code; do NOT ask for reinstall/source-folder/MCP/Profile/previous four
  Skill gate repetition. Exact one synthetic request is in docs/transform-preflight.md,
  Remaining host-only check. Supplied current catalog lacks new Skill, so automatic host
  selection remains unverified, not a failing helper or inaccessible Workspace.
- After client outcome: record provenance, test output normal/tangent/appearance limits and
  numerical edge cases before expanding transform/engine preparation. No current live quota
  API; do not reuse earlier 20%/22% screenshot as a new reading or invent remaining credits.

## Historical positive-scale preview checkpoint

- Read root AGENTS/README and prior state/helpers/harness. MCP live Blender 5.0.1/addon
  [1,7]/protocol 7 verified; no MCP configuration/telemetry changes. User supplied screen
  shows 5h 20%/week 22%; no programmatic live quota available and no credit/time estimate.
  Kept work to a validated preview unit instead of starting a large apply/Skill phase.
- Added scripts/preview_scale_copy.py: analytic positive-scale simple-mesh preview, explicit
  tolerance, XYZ rotation and no dependent/delta/custom-normal/unsupported-attribute input.
  Predicts scaled vertices/unit scale/location-rotation matrix basis, validates local-basis
  coordinate residual. No copy/IDs/operator/graph refresh/authorization/export certificate.
  Negative or zero scale refused; earlier native reflection experiment does not authorize it.
- Fingerprint binds Scene/Object/Mesh/raw transform/basis/ordered geometry/edge flags/UV/
  material slot links/references/effective tolerance. verify_scale_preview recomputes it,
  refuses missing/stale hash and gives snapshot-only freshness on match. No deep material
  backup, evaluated-world/normal/tangent/engine or concurrency guarantee.
- Expanded separate transform-preflight payload to 5 sources; compile/source-count offline
  invariant updated. Native suite 56 pass (24 previous snapshot + 6 native copy capability
  + 26 preview tests). Stale geometry/transform/UV/seam/Scene/tolerance, NaN UV, no-change,
  invalid tolerance, reflection/zero/delta/parent/Edit Mode/no IDs and restoration tested.
  Exact owned fixture teardown restores original fingerprint and ID lists. Raw evidence:
  ignored .local/validation/scale-preview-20260918.json. No original save/export.
- Changed preview helper, transform test, payload generator, repo required-file validator,
  offline source-count assertion, transform docs, roadmap and repo/scripts/tests READMEs,
  this state. No Skill/deployment/Profile/project/architecture changes.
- Final offline scripts 47 pass + Workspace 43 pass = 90 pass/4 explicit Windows symlink
  privilege skips (approved OS-temp access). Repository and actual Workspace validators pass.
- Next first task: implement narrow independent-copy positive-scale apply consuming fresh
  preview hash, explicit caller authorization/name and file-wide dependency safety guard;
  validate actual copied local/world geometry/UV/material/transforms before link, inject
  write/validation/link failures and exact rollback. Do not package fifth Skill before
  that live evidence. No user action, reinstall or repeat client gate needed.

## Historical ambiguous triage / transform-preflight checkpoint

Subsequent same-turn capability checkpoint: extended only synthetic harness with independent
copy-scale experiment (6 checks): normalized copied scale, matrix-basis positions preserved
within explicit test-only 1e-6, UV/material/topology preserved, source/edit independence.
Not evaluated-world/normals/engine certification or reusable apply function. First run
stopped material cleanup because copied Mesh still referenced it; inspected exact token
df6049f5cb9c44b7b07a292261428f9a and remaining IDs/users, recovered only owned Mesh/material/
empty Scene. Fixed harness to remove all Meshes before materials. Rerun 30 pass, full
teardown and original fingerprint restored. Current total separate native suites 361,
not 355; earlier 24-count bullet below is the prior snapshot-only checkpoint. Raw successful
MCP/hash evidence in ignored .local/validation/transform-preflight-20260918.json.
Next: scale-copy preview/freshness guard and output matrix/geometry validation plus failures,
only then an apply helper/Skill. No user action or repeated client check currently required.

- User provided Cube cleanup inspection-only result and screenshot declaring inspection/
  diagnostics Skills. Cube 8/12/6/12, no relevant structural cleanup, coplanar planar-only
  workflow correctly excluded, null Profile rules not invented; no copies/edits and state
  matched by user report. Specific read-only triage gate complete; raw call traces absent.
  Do NOT repeat this Cube/client setup/Profile/exposure/helper test as a user gate.
- Chose next roadmap foundation: development-only inspect_static_transform.py, explicit
  named mesh/Scene, raw/reported transform matrices, exact determinant/scale reviews, base
  local bounds and parent/binding risks. No graph refresh/operator/pivot change/apply/export.
  Numerical results withheld for invalid target/Scene, Edit Mode and nonfinite raw/matrix/
  vertex values. Snapshot-only; reported matrices may be stale, no near-singularity or
  engine certificate, bounds center is NOT a guessed pivot target.
- Added run_transform_preflight.py and separate --suite transform-preflight (4 sources),
  payload offline compile/source-count coverage and required repo files. Native 24 checks
  pass on Blender 5.0.1/addon [1,7]/protocol 7: identity/offset bounds, mirrored/nonuniform/
  singular transforms, parent/Constraint/groups, nonfinite vertex/raw Euler, explicit
  names, Edit Mode retained; owned fixture teardown restores original fingerprint/IDs.
- Final installed helper regressions rerun: earlier-three 169 + fourth 162 = 331 pass;
  new development snapshot 24 pass, total 355 separate native checks. Exact fixture teardown.
- Offline scripts first failed because sandbox denied Windows OS temp access, not a source
  assertion failure. Approved rerun: 47 pass. Workspace approved run: 43 pass/4 explicit
  symlink privilege skips. Repository validator passes. No quota estimate; screenshot
  percentages are user-supplied historical information, not a programmatic live reading.
- Changes: scripts/inspect_static_transform.py, tests/static-mesh/run_transform_preflight.py,
  scripts/prepare_blender_check.py, scripts/validate_repo.py, tests/scripts/test_development_tools.py,
  docs/transform-preflight.md, client/release/roadmap docs, README, scripts/tests README and
  this state. No fifth Skill, installation/Profile/project/MCP/original file changes.
- Next development priority: define/test independent-copy scale preparation with explicit
  caller operation and matrix/world-geometry/UV/material preservation before packaging.
  Do not infer pivot or engine units from null Profile. Full rotation/origin/parent/rig/
  Shape Key/animation handling remains deferred. No user reinstall or repeated gate needed.

## Historical direct installed-source checkpoint

- Corrected overly broad claim that a separate conversation was required for installed
  helper tests. Actual session cwd remains D:/GitHub/GameAssetAI; Workspace is readable,
  Blender MCP callable. Four Skills absent from the supplied automatic catalog is only
  an implicit-selection limitation, not a repository/installed-source testing blocker.
- Read repo root instructions/README, this state, actual Workspace AGENTS, installed cleanup
  SKILL and active-profile.json (null). No inferred budgets or Workspace configuration writes.
- Added read-only --installed-skills-dir to prepare_blender_check.py: exact installed helper
  sources, validated resources/linked-path refusal, no repository/ZIP fallback, mutually
  exclusive origins, existing harness sources and shared namespace compile semantics.
  Six offline tests cover actual modified installation, preservation, missing Skill/helper,
  mixed origins, linked ancestor and CLI from another cwd. Tools now 47 pass.
- Strengthened cleanup harness: existing-copy state preserved on name collision, stale
  apply preserves changed synthetic source/ID lists, exact coordinate restoration.
  Actual installed helpers: 36 + 73 + 60 = 169 checks; fourth 158 + 4 = 162; total 331 pass.
  Raw MCP responses and source hashes in ignored .local/validation/installed-safety-20260918.json.
  Direct explicit execution evidence, NOT automatic discovery/implicit selected-Skill trace.
- Exact fixture teardown restored original fingerprint/ID names. Source Skills, installed
  Skills, Profiles, projects and MCP unchanged; no original save/export. Prior user gates
  remain complete. Do NOT request another stale/name-collision helper run from the user.
- Next host-only evidence: ambiguous natural-language cleanup selects an appropriate Skill
  and establishes categories before apply. Current catalog lacks GameAssetAI Skills; a
  conversation actually exposing them is needed only for that automatic-selection test.
  Repository development is otherwise not blocked. Broader optimization/rig/export and
  conservative installation/update/recovery policy remain separate priorities.
- Finished conservative development policy in skill-packaging.md: first-install only,
  exact owned rollback versus interruption/cleanup/concurrency limits, preserve drift/
  personal backups, fresh preview after version changes; no automatic updater/uninstall
  claim. Corrected historical bundle paths/Profile claims. No broad architecture changes.
- Final offline: tools 47 pass + Workspace 43 pass = 90 pass, 4 explicit Windows symlink
  skips; repository validator passed. Actual installed helper result remains 331 live
  checks, exact teardown. Automatic ambiguous routing requires a catalog-exposing host
  conversation; this is the only next client action, not a repeat of helper regression.

## Historical Profile/client and scope/failure checkpoint

- User confirmed independent Workspace Profile A/B/null rereads: Cube 12 > 10 exceeded,
  12 <= 20 within budget, null leaves game rules unjudged without stale reuse. Settings
  byte-exact restored, existing Profile hashes unchanged, only two synthetic Profiles
  removed; Blender state unchanged. User-reported, raw traces/build absent. Do NOT repeat.
- Added seven native checks for disconnected planar components: global affine UV allows
  both internal edges, a seam protects one, independent copy retains seam, different
  island offset blocks whole-mesh preview/apply with no new IDs; restored synthetic state.
  Actual current fourth ZIP helpers: 158 normal + 4 failure = 162 checks pass, exact
  owned fixture teardown, original fingerprint/ID lists restored. No Skill/helper changes,
  no source/archive/install/Profile/MCP changes or original save/export.
- Added offline deployment partial-write/readback-corruption tests: owned paths removed,
  source unchanged and sibling personal Skill retained. Tools 41 pass. This is first
  deployment rollback evidence, not concurrent-write or automatic update support.
- Final validation: repository and actual Workspace validators passed; tools 41 pass,
  Workspace 43 pass/4 Windows symlink privilege skips; all four installed sources aligned
  by read-only hash check. Earlier-three actual ZIP helper regression 166 pass plus
  current fourth 162 pass = 328 native checks. All owned fixtures removed and original
  fingerprint/ID lists restored. No original asset/config/Profile modification.
- Updated README, roadmap, release/client/Profile/workflow evidence, coplanar scope docs,
  test plan/README and this checkpoint. Historical checkpoints below retain old counts.
- Next client gate: ambiguous removal must establish target/categories before applying,
  then stale-preview/name-collision refusals in the actual Workspace client. Native
  helpers already refuse these; this catalog cannot open/refresh that independent client.
  Do not repeat exposure/read-only/synthetic apply/Profile gates. Raw routing/build and
  installation/update/recovery policy remain release gaps. No stable release/Git publish.
  Exact next synthetic-only stale-preview/name-collision request is recorded under
  `docs/skill-session-validation.md`, Remaining client checks. No quota estimate made.

## Historical client-pass/separate-tolerances checkpoint

- User confirmed fourth Skill exposure + actual synthetic preview/fingerprint-bound copy
  apply/validation/teardown/restore, source unchanged and starting-state differences none.
  4/5/2/2 → 4/4/1/2; NO triangle reduction. Marked client gate complete by user report,
  raw call/client-build details absent. Do not request new-Skill exposure/apply test again.
- Used Skill Creator for a narrow backward-compatible update: separate geometry_tolerance
  and uv_tolerance in guard/preview/apply. Legacy tolerance explicitly sets both; mixed
  style or missing separate bounds refuse. Effective normalized parameters bound into
  hash, geometry-derived area bound, no hidden game or scale default.
- Added three offline tests and native equivalence, UV-bound hash/stale apply and native
  strict UV with loose geometry tests. Also tested local size ×1000, two affine UV layers
  through apply, layer names retained, second-layer nonaffinity blocked and source restored.
  Current actual fourth ZIP helpers **155 checks pass**,
  original fingerprint/ID lists restored, exact fixture teardown. Offline tools **39 pass**.
- Updated prototype mirrors and packaged helpers consistently. Skill Creator UTF-8 quick
  validation passed. Installed old four-file hashes verified before backup/approved patch;
  `.local/deployment-backups/separate-tolerances/` retains old versions; read-only drift
  validator reports aligned. No earlier Skill/Profile/project/MCP changes.
- Current fourth archive `.local/source-bundles/separate-tolerances-20260918/` SHA
  `8e70b8894e79c56f88aa1befc06790ccd28dfaae5c506aa972ca6a8b76a5a3bd`; directory includes
  inspector ZIP only additionally for harness, NOT a complete all-suite bundle set.
  Earlier-three bundles remain in coplanar-20260918; no archives overwritten.
- Updated client evidence, README, roadmap, release checklist, helpers/tests/Skill and
  this checkpoint. No new Skill, publication/stable-release or quota estimate.
- Repository validator passed; Workspace 43 pass/4 explicit symlink-privilege skips.
- Final earlier-three actual ZIP-helper regression 166 pass; current fourth 155 pass,
  total separate native suites 321 checks pass. Offline tools 39 pass + Workspace 43 pass
  = 82 pass/4 skips. Final MCP inventory Cube/Light/Camera; exact teardown and original
  fingerprint restored. No original save/export/modification or settings change.

Historical next gate (now passed by user report above): fresh Workspace conversation rereads Profile A/B/null without
stale/invented rules. Prior explicit development Profile-switch test is complete; do not
claim that proves independent fresh-client behavior. This development catalog cannot
start/refresh the user's Workspace conversation. User can submit a single synthetic
Profile-switch/diagnostics-only request, preserve original active settings/Profiles exactly
and restore them. No old exposure/read-only/apply test needs repeat. Subsequent repository
priority: explicit candidate/island-scope design before changing whole-mesh restrictions;
do not generalize just because two-UV/scale fixtures passed. Four Skills remain limited
development workflows; no new source-folder/MCP setup is necessary.

## Historical copy-apply/self-contained Skill checkpoint

- Read current root instructions/README/preview checkpoint and live addon status. Blender
  5.0.1/addon [1,7]/protocol 7 connected. No remaining quota estimate/API; latest supplied
  image remains historical 68%/30%, not a current live reading.
- Added `scripts/apply_coplanar.py`, canonical predicted geometry hash to preview,
  independent Object/Mesh copy apply with explicit authorization/name/exact preview hash,
  file-wide dependency guard, actual output/prediction/transform/source validation before
  linking. Exact owned-ID rollback for write, corrupted output and post-link failure.
- Expanded synthetic tests: missing/stale hash, real source transform change, changed
  tolerance, collisions/authorization, group/Shape Key/animation binding refusal and
  unrelated constraint guard; source shared users/materials preserved, copied Mesh edit
  independent. New suite **141 + 4 = 145 live checks pass**; exact teardown restores
  original fingerprint. No triangle reduction claim (4/5/2/2 → 4/4/1/2).
- Used Skill Creator to package only this verified workflow as
  `skills/blender-simplify-coplanar` with four self-contained helper resources. Sources
  do not require another installed Skill. Prototype mirrors retained for development;
  new offline source-equality test prevents divergence. No broad decimation/rig/export.
- Actual ZIP helpers pass same 145 live checks. Versioned bundle directory
  `.local/source-bundles/coplanar-20260918/` contains four archives; old three unchanged.
  New ZIP SHA `6f4e0ce3417f755ae712f177d7f17857393b686b707ad91c4306805b968d9674`.
- Skill Creator quick_validate passed with Python UTF-8 mode after default cp949 decode
  failure. Approved no-overwrite deploy installed ONLY the new Skill into existing
  D:/AI/GameAssetAI-Workspace/.agents/skills; read-only validator reports aligned.
- Final earlier-three ZIP-helper regression **166 pass**. Total separate latest native
  suites 311 checks pass, exact teardown; original fingerprint
  `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d` restored.
  Final MCP Scene Cube/Light/Camera. Offline tools 36 pass, Workspace 43 pass/4 explicit
  symlink-privilege skips; repository validator passed. No original save/export.
- Added `docs/coplanar-apply.md`; updated README/roadmap/payload/validator/scripts docs,
  source/helper/tests and this checkpoint. Global MCP/Profile/projects and earlier three
  Skill installations unchanged. No Git init/commit/upload/stable release.

Current highest-priority user gate: fourth Skill exposure and instruction-led synthetic
preview/apply in existing Workspace session. Dev session cannot refresh its catalog to
verify that client's selection. One exact synthetic request in `coplanar-apply.md`; do
NOT repeat old client tests/reinstall Workspace or touch original Cube. This is a runtime
usability gate, not a claim native helpers failed or all repository development is blocked.
After user outcome: record provenance, separate xyz/UV tolerance policies and validate
candidate/island scope before broadening. New Skill must not be labeled stable until
client behavior and remaining release checklist gates are passed.

## Historical guard-enforced preview checkpoint

- Confirmed live Blender 5.0.1/addon [1,7]/protocol 7 before implementation.
- Added development-only `scripts/preview_coplanar.py`: explicit target/angle/tolerance,
  simple-input refusals, whole-mesh per-UV affine guard, bounded source/parameters hash
  including seam/sharp, in-memory BMesh simulation, predicted counts/retained boundary/
  corner UV/material/smooth/area checks, always mutation_authorized=false. No Object/Mesh
  copies/IDs, to_mesh, link, mode changes, graph refresh, save or export.
- First gate reuse failed on observed native uv_seam. New preview supports only the
  observed BOOLEAN/EDGE built-in; installed cleanup sources/allowlist unchanged.
- Expanded native fixture: preview no IDs/source changes, protected-boundary no-op,
  nonaffine/split/noncoplanar blocking, seam/UV hash changes, invalid parameters/missing
  target refusals, injected operator failure explicitly frees BMesh and preserves IDs.
  Latest separate experiment **107 + 4 = 111 checks pass**, exact fixture teardown,
  original fingerprint restored. Three installed Skill regressions remain separate.
- Updated payload generator and suite offline count to six sources; sources compiled
  separately with shared globals/locals. Added `docs/coplanar-preview.md`, updated
  capability evidence, roadmap/scripts README, required-file validator and this file.
- Final repository validator passed; offline development tools 35 pass and Workspace
  43 pass/4 explicit symlink-privilege skips. Existing installed-workflow live regression
  re-run: 166 checks pass, exact teardown complete. No new Skill/deployment/ZIP/Profile/
  MCP changes. Final MCP inventory retains Cube/Light/Camera.
- User screenshot 5-hour 68% / weekly 30% at that moment; no live quota API/estimate.

Next atomic unit: independent-copy structural simplification apply, explicit preview hash
and unused name, file-wide dependency risk guard, validate predicted output/protected
flags and exact owned-ID rollback on write/validation/link failures. Read
`docs/coplanar-preview.md` first. Whole-mesh restriction and shared xyz/UV tolerance are
prototype boundaries, not broad optimizer or game defaults. No user setup/action required;
do not repeat already-passed client prompts. Installable Skill creation waits for copy
apply/refusal/rollback tests and self-contained packaging.

## Historical restored-connection/coplanar checkpoint

- User started Blender; live addon/Scene/Python connection restored. Blender 5.0.1,
  addon [1,7], protocol 7. Current original Scene Cube/Light/Camera, one material;
  do not restore historical two-material count. No MCP/settings/telemetry changes.
- Implemented synthetic-only `tests/static-mesh/run_coplanar_experiment.py`, separate
  `coplanar-experiment` payload suite, native internal-edge dissolve delimiters and
  failure teardown tests. First tiny-angle test failed; native angle sweep showed
  1e-6/1e-4 no dissolve, 0.001/0.01 dissolve on zero-angle plane. Corrected explicit
  experimental angle to 0.001; do not claim implementation cause or game default.
- Continuous plane: 4/5/2/2 → 4/4/1/2 vertices/edges/faces/triangles. UV split/material/
  seam/sharp/noncoplanar boundaries preserved. NO triangle reduction occurred.
- Added continuous nonaffine UV hazard: native UV delimiter still dissolves. Added
  pure `scripts/check_affine_uv.py` plus five offline tests; checks one planar affine
  map at explicit tolerance, rejects nonaffinity/discontinuity/degeneracy/nonfinite
  values/overflow. Native source cases verify guard decisions. Synthetic hazard probe
  intentionally bypasses guard to demonstrate why future reuse must enforce it.
- Latest final native installed-workflow regression **166 checks pass**; experiment
  **60 + 4 = 64 checks pass**, exact teardown complete. Original fingerprint restored
  `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
  Final Scene inventory Cube/Light/Camera. No original save/cleanup/export occurred.
- Offline tools **35 pass**, Workspace **43 pass/4 symlink-privilege skips**;
  repository validator passed. Sources/installed three Skills and ZIPs unchanged.
- Added `docs/coplanar-experiment.md`; updated test plan, payload generator/offline
  test, affine guard/test, validator, roadmap/scripts README and this file. No new Skill,
  production apply helper, Git init/commit/release or game-profile default introduced.
- User screenshot 5-hour 74% / weekly 31% at that moment; no live quota API/estimate.

Next atomic work: implement guard-enforced structural-simplification PREVIEW only on
supported simple inputs; relevant UV/material/seam/sharp/transforms freshness hash,
no permanent copied IDs, no implicit edit authorization. Then separately design copy
apply/name/validation/rollback before installing any new Skill. Re-read
`docs/coplanar-experiment.md`: one tolerance for xyz and UV is prototype-only; future
scale-aware tolerance policy and candidate/island scope need validation. No user action
is required for these synthetic development steps. Prior connection blocker is resolved;
do not request starting/reinstalling Blender again unless a new live call fails.

## Historical connectivity/experiment-design checkpoint

- Read root instructions/README, latest checkpoint, architecture, skill design, workflow,
  roadmap and optimization preflight. Prior client outcome tests remain complete.
- Current Blender MCP tools ARE exposed, but addon status, Scene inventory and native
  Python capability query all returned "Could not connect to Blender". Their envelope
  says isError=false; text is failure. No current Scene state/capability is verified,
  no synthetic data created and no Blender modification occurred. Do not claim today's
  live tests passed using historical results.
- Completed safe offline work: repository validator passed; development tools 30 pass,
  Workspace 43 pass/4 explicit symlink-privilege skips. No new functionality/Skill installed.
- Added `tests/static-mesh/optimization-test-plan.md`: bounded coplanar-copy experiment,
  continuous vs split UV, material/seam/sharp/noncoplanar boundaries, ownership/freshness/
  rollback gates. Triangle count may remain unchanged despite edge/polygon reduction;
  never mislabel structural simplification as meeting a triangle budget. Updated
  `docs/optimization-preflight.md`, repository validator and this checkpoint.
- Latest user screenshot reports 5-hour 77% / weekly 31% at that moment. No live quota
  API or remaining-credit estimate is claimed. Stop reason is disconnected Blender,
  not quota. No MCP installation/configuration/telemetry or personal data changed.

Current required user action: open Blender and start the existing Blender MCP addon's
server (previous user-provided endpoint localhost:9876). No reinstall/workspace recreation
needed. Then first re-query addon status and Scene, verify native operation capabilities,
implement ONLY the first synthetic experiment and protected-boundary cases, run native
regression/teardown, record evidence before creating a reusable helper/Skill. The test
plan is not implementation or live verification. Original projects stay in place.

## Latest read-only/preflight checkpoint (supersedes earlier client gates)

- User supplied separate natural-language outcomes: inventory Cube/Light/Camera;
  diagnostics Cube 8/12/6, 12 triangles, no findings, no invented null-Profile budgets;
  cleanup preview 0/0, no modification/copy. These three outcome checks are complete;
  do NOT request them again. Selected-Skill/raw MCP traces were not supplied.
- Added development-only `scripts/plan_static_optimization.py` and five tests in
  `tests/scripts/test_optimization_plan.py`. Trusted base diagnostic report + explicit
  target → advisory needs-target/within-target/copy-preview-candidate/review/blocked.
  No new Skill, optimization method, authorization, implicit Profile budgets or edits.
  Failed/incomplete/evaluated inputs refuse; sensitivity/structure issues do not turn
  into automatic decimation. Freshness explicitly unverified, always reinspect before edits.
- Current actual ZIP-helper regression **166 live checks passed**, fixture cleanup and
  original fingerprint restored. Live Cube planner targets None/10/12/20/0 produced the
  expected five decisions with no authorization/method and original fingerprint unchanged.
- Development tools **30 pass**; Workspace **43 pass/4 explicit symlink-privilege skips**;
  repository validator passed. Three installed Skills/helpers/bundles unchanged.
- New `docs/optimization-preflight.md`; updated README, roadmap, release/session evidence,
  scripts README, repository validator and this checkpoint. Architecture/Profiles/MCP and
  existing external projects preserved. No Git init/commit/publication or stable release.
- Latest user screenshot shows 5-hour 21% / weekly 35% at that moment. Live quota API is
  unavailable; no remaining-credit/time estimate or exhaustion warning is claimed.
  Finish this narrow verified unit rather than begin a larger copy-decimation workflow
  under the user's low-usage checkpoint policy.

Next session: first read this checkpoint and `optimization-preflight.md`; design a single
synthetic copy-optimization experiment with explicit test target, UV/material/silhouette
validation and source fingerprint/rollback. Verify native capabilities first. No user
action is needed to start that development unit, and no passed client prompts need repeat.
Remaining release gates (not reasons to block repository development): raw routing traces,
ambiguous removal/refusals, fresh-client Profile freshness, exact client/version/source
provenance, update/recovery policy and release integrity. No original data needs deletion.

## Historical quad/apply checkpoint

- User reported synthetic instruction-led preview → independent-copy apply → validation
  → teardown/restore success: vertices 7→4, edges 5→4, one face/UV retained, source
  unchanged, Mesh independent, zero loose leftovers, starting-state difference none.
  This apply/restore gate is complete; DO NOT request it again. Raw selected-Skill/calls,
  fingerprint/client-version/refusal evidence not supplied; do not invent them.
- Added the corresponding quad fixture and wire-only endpoint-retention regression in
  `tests/static-mesh/run_loose_cleanup.py`. Actual current ZIP helpers: inspection 36,
  diagnostics 73, cleanup 57 = **166 live checks passed**, teardown complete and original
  fingerprint restored. No helper/Skill/bundle/deployment changes needed this turn.
- Updated session evidence, release checklist, roadmap, cleanup evidence, packaging,
  test plan and this file. Existing architecture/personal Profile/projects/MCP retained.
- Final repository validator passed; offline tools 25 pass, Workspace 43 pass/4 explicit
  symlink-privilege skips. Final MCP inventory retains Cube, Light, Camera.
- User's latest screenshot reports 5-hour 25% / weekly 36% at that moment; no live API,
  quota estimate or exhaustion warning claimed. Avoid broad new feature work.
- Next priority: independent analysis-only natural-language prompts 1–3 in
  `skill-session-validation.md` and client authorization/refusal behavior, followed by
  fresh-client Profile freshness. These require the already working Workspace session;
  this dev catalog cannot emulate that client. No reinstall/new source-folder setup.
- Once client analysis/authorization gates pass, select conservative copy optimization
  preflight before any decimation, pivot changes, rig edits or engine export. Do not
  treat user apply summary alone as proof of all read-only routing boundaries.

## Historical namespace checkpoint

- User confirmed installed session exposure and explicit actual calls for all THREE
  Skills: Scene 3 objects, Cube 12 triangles/no findings, cleanup preview 0 targets;
  selection/mode/datablock lists retained. Null Profile: game limits unjudged.
  First namespace error corrected/retested; original traceback/client build not supplied.
- Skill Creator guided a narrow execution-invariant update to the three SKILL.md files:
  same dictionary for exec globals/locals, same-request function call, independent compile.
  Payload builder now explicitly shares globals/locals. New executable regression
  proves helper imports visible inside functions and separately compiled future imports.
- Installed instructions updated only after old hashes verified and exact backups made
  at `.local/deployment-backups/namespace-fix-20260916/`. All three deployments aligned;
  helper code, personal settings, original projects and MCP configuration unchanged.
- Cleanup fixture now applies using an explicit prior-preview fingerprint; added retained
  surface validation failure and owned-ID rollback tests. Final actual ZIP-helper run:
  **36 + 73 + 48 = 157 Blender checks pass**, teardown complete, original fingerprint
  `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d` restored.
- Offline development tools **25 pass**; Workspace **47 tests, 43 pass/4 symlink skips**.
  Windows symlink privilege is unavailable; skips explicit, no failures.
- Final repository/actual Workspace validators and three Skill Creator quick validations
  passed. Final native inventory/viewport retain Cube, Light, Camera; no original save.
- Latest bundles: `.local/source-bundles/namespace-fix-20260916/`; earlier ZIPs/hashes
  below are historical. Added `docs/skill-session-validation.md`, updated evidence,
  release checklist, roadmap, README, repository validator and this continuation point.
- Screenshot supplied by user shows remaining 5-hour 35% / weekly 38% at that moment;
  no live quota API or exhaustion warning is claimed. Kept this unit narrow.

At that checkpoint the remaining gate was independent prompts and instruction-led
synthetic preview/apply in the already working Workspace client. This dev session cannot
refresh its Skill catalog or emulate independent client routing. Do NOT repeat installation,
old-folder removal, session exposure or explicit Profile tests as blockers. Native apply
is verified; implicit client selection is not. Prompts in `skill-session-validation.md`.

## Historical foundation checkpoint

- Independently confirmed user removed old manual Workspace: old path absent. No
  further deletion or previous failed Workspace backup is claimed.
- Added read-only `scripts/read_profile_context.py` and temporary recovery-aware
  `tests/workspace/profile_check_fixture.py`; tests in `test_profile_context.py`.
- Actual new Workspace: A Profile explicit Cube limit 10 → live 12 > 10; re-read B
  limit 20 → no budget finding. Engine/style/other limits unknown. Original active
  config restored byte-for-byte, only exact synthetic Profiles/state removed.
- Next sequential Skill `blender-cleanup-loose-geometry`: preview/no-op or explicitly
  authorized cleanup on independent copy only. Separate isolated/wire flags, unused
  output name, required preview fingerprint, simple-input refusal/rollback guards.
  Source and its shared users preserved; materials intentionally shared.
- Initial future-import payload and default selection-attribute failures were found
  and corrected. Retested nonidentity/nonfinite transforms, source dependencies/mode,
  stale/missing preview, independent copy edits and simulated failure rollback.
- Source bundles: latest combined **36 + 73 + 46 = 155 live Blender checks pass**,
  exact teardown complete and original fingerprint restored. Scene Cube/Light/Camera,
  viewport confirms original objects. No original mesh/rig/Action saved/cleaned/exported.
- Offline Workspace **47 tests: 43 pass, 4 explicit Windows symlink privilege skips**;
  development tools **24 tests: all pass**. Current validators pass.
- Added read-only `scripts/validate_skill_deployment.py`: detect missing/extra/changed
  sources and invalid deployment without writes; all THREE actual deployed Skills aligned.
- New cleanup ZIP SHA-256 `48af864fb00d7675c3bf77b5b7662538a450c5da5b079c357c91837257a8a1a1`;
  helper SHA `0d52721cefdc7de8109eb25533c0e4d168f4fc11f5434875cf0ba72df2edb6f5`;
  SKILL SHA `a0811d2f147253d8ed8670a92602023d5ffdd61df49c0c36e623f72af2390fa4`.
  Skill Creator quick validation passed. Copied/byte-verified new Skill only into
  D:/AI/GameAssetAI-Workspace/.agents/skills; earlier installations/settings preserved.
- Added evidence `docs/profile-workflow-validation.md`, `loose-cleanup-validation.md`,
  and `release-checklist.md`; updated root README, skills/scripts/tests/payload tooling,
  validator, roadmap, workflow, packaging, MCP foundation/location evidence and this file.
- Existing architecture, template, original projects, global MCP settings retained.
  No quota estimate/limit warning, Git initialization, commit, upload or stable release.

At that historical checkpoint Profile data flow was verified and installed discovery,
implicit routing and fresh-client Profile behavior were UNVERIFIED; they did not
invalidate explicit-source development evidence or justify another folder deletion.
See next priorities below and release checklist before claiming client stability.

## Current overall goal

Develop usable reusable Blender game-asset workflows through narrow sequential
design → implementation → live test → correction → regression → documentation cycles.
Preserve the development repo / personal Workspace / existing external projects split.
The user authorized synthetic reversible Blender development tests; the earlier
read-only-connection-only restriction no longer governs this task.

## Completed work

- Existing workspace/repository foundation safety and 40-test regression retained.
- First source Skill: `blender-inspect-asset`, read-only scene/named/selected inventory,
  base meshes, material references, rest bones, Action slots/NLA and file-wide Actions.
- Second, after first live tests passed: `blender-validate-static-mesh`, explicit named
  topology/material/transform diagnostics with optional supplied Profile constraints.
  No game defaults, automatic repair, rig replacement, or engine certification.
- Found actual dependency-graph animation refresh changing a source transform during
  evaluation. Added conservative file-wide animation/constraint evaluation blockers,
  retained base diagnostics, and retested successfully. Do not remove data to bypass.
- Strengthened preservation fingerprint with weights, rest/pose matrices and Action
  curves/keyframe handles; real fixture keyframe modification detection passed.
- Added self-contained MCP test payload generation, repeatable portable source ZIPs,
  and explicit no-overwrite local deployment. No MCP installation or socket client.
- Created `D:/AI/GameAssetAI-Workspace` from the template with approved execution.
  Copied both tested Skills to its `.agents/skills/`, verified every source byte/hash.
  Active Profile remains null, project mappings empty, global settings unchanged.
- Updated roadmap, workflow, evidence and packaging/test instructions.

## Changed repository files in this development stage

- new `skills/blender-inspect-asset/SKILL.md`, `scripts/inspect_asset.py` inside that Skill
- new `skills/blender-validate-static-mesh/SKILL.md`, `scripts/validate_mesh.py` inside it
- new `tests/blender-scene/run_inspection.py`, its `test-plan.md`
- new `tests/static-mesh/run_diagnostics.py`, its `test-plan.md`
- new `scripts/prepare_blender_check.py`, `package_skill.py`, `deploy_skill.py`
- new `tests/scripts/test_development_tools.py`
- new `docs/inspection-validation.md`, `static-mesh-validation.md`, `skill-packaging.md`
- updated `README.md`, `skills/README.md`, `scripts/README.md`, `tests/README.md`
- updated `scripts/validate_repo.py`, `docs/roadmap.md`, `development-workflow.md`,
  `blender-verification.md`, `blender-mcp-environment.md`, this checkpoint
- ignored development ZIP artifacts under `.local/source-bundles/`

Root AGENTS.md and all existing game projects were preserved. No .git metadata exists;
no Git initialization, commit, release, upload, or third-party asset was introduced.

## Earlier verification (before latest continuation)

Windows, Python 3.13.7, Blender 5.0.1. MCP identity supplied by user:
implementation `ahujasid/blender-mcp`, source https://github.com/ahujasid/blender-mcp,
socket `localhost:9876`. Observed addon [1, 7], protocol/expected 7, up_to_date true.
Client build and installed MCP source commit/socket configuration are not independently
known. Telemetry consent reported true and was not changed.

- Offline Workspace suite: **40 tests, 36 pass, 4 explicit skips** (Windows symlink
  privilege 1314). Actual junction and hard-link preservation checks pass.
- Offline development tools suite: **18 tests, all pass**. Byte-preserving repeatable
  ZIPs, source/ZIP payload equality, missing-resource failure without fallback, no-overwrite
  deployment, overlap/link rejection, nested resources, failure cleanup and CLI covered.
- Live Blender: **36 inspection + 73 diagnostics = 109 checks pass** using repository
  helpers, and again using helpers read directly from ZIPs. Exact fixture cleanup complete.
- Original Scene still Cube, Light, Camera. Fingerprint restored:
  `f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
- Native/tool inventory and screenshot agreed; harmless missing-object tool returned
  error text despite isError false. Skill accounts for that result envelope behavior.
- Both SKILL.md files pass bundled skill-creator quick_validate with isolated uv/PyYAML.
  This is authoring validation only; runtime tools remain standard-library-only.
- `validate_repo.py`, template validation, and new actual Workspace validation pass.
  Isolated OS-temp tests required approved execution; no quota estimates were invented.

## Bundles / deployment provenance

ZIP SHA-256 (development artifacts, not stable releases or client-upload certification):

- inspector: `0f192d3d5032a16a86a8dbf2027c8e79980351c9cc87fafb7a55a47548b63aa2`
- diagnostics: `cfe449a9f1fa3c40fcef40a512d15116f4e21423e14d68b9fedf8f55fdc2d17c`

Deployed helper source SHA-256:

- inspector: `f64d98b75f22ca7993d3559444ae5702ad9f145c799db3300f193e39386d49f8`
- diagnostics: `169c172e6e3077494fe788f5e95cac0a305dca0dc618f74471123515e44d8aba`

SKILL.md SHA-256 inspector `a90514ced7a751507b969be2248d07ef2791787342683a074464c304f88fb2e2`,
diagnostics `c497de4ee50d75f1fffb62a30e3f52c0134c6be93d1e2c3d18b99aedd5d92b3f`.
Keep sources here and retest before deliberate redeployment; no overwrite tool provided.

## Known limits / important decisions

- Source-helper tests do not prove client implicit selection or fresh-client Profile
  behavior. User separately confirmed exposure/explicit calls; current Profile flow checked.
- Explicit optional constraints are passed as data; Markdown is not parsed with guessed
  defaults. Missing rules remain unknown; no game-specific rules in reusable sources.
- Evaluation is viewport-only and conservatively blocked even for unrelated animated
  data. Stored transforms are cached; base inspection does not refresh dependencies.
- Fingerprint is bounded, not every datablock property. Temporary test setup may dirty
  a previously clean file. Original unsaved file was not saved or replaced.
- Production imported rigs/actions, skin quality, instance/export topology, UV density,
  self-intersections, retargeting, Mixamo and engine import/export are not certified.
- Local `.agents/skills` exposure/explicit calls were confirmed by the user. Implicit
  routing is next to verify. No global skill folder renamed, no plugin/MCP bundle added.
- Account quota is not programmatically exposed; no usage warning was observed.

## Current blocker / next priorities

Old-path removal and explicit Workspace Profile tests are complete. Do NOT ask the user
to close/delete the old folder again or repeat already-passed Profile file tests as blockers.

1. Next dev capability: conservative copy-based optimization experiment following the
   advisory preflight, then pivot/export prep. Client read-only outcome tests and synthetic
   apply/restore have passed by user report; do not request setup or repeated prompts.
2. Remaining release evidence: raw routing/client version, ambiguous removal/refusals,
   stale-preview/no-overwrite and fresh-session Profile behavior. These do not block
   explicit-source repository development.
3. Follow the narrow optimization boundary in `optimization-preflight.md`.
   Do not broaden loose-geometry cleanup into merge/decimation or untested rig handling.
   Real engine import verification needs separately scoped environment/version evidence.

Current atomic source/test changes are verified. No Blender outage or exhausted quota is
claimed. Latest checkpoint takes precedence over historical manual-gate claims above.

## First reusable static Pixel PNG Skill checkpoint — 2026-09-29

- Added and locally installed `blender-render-static-pixel-png`, the first downstream 2D
  Skill. It accepts one simple reviewed Mesh and creates one new orthographic Pixel RGBA8
  PNG using owned neutral lighting, no palette reduction or an explicit opaque fixed
  palette. It does not duplicate existing 3D creation.
- Added hash-bound source blend staging, render-job creation and background staged
  rendering. Interactive Blender never renders or saves. Target/`.meta` collisions,
  stale request/source/setup/output/plan/job/stage hashes and unsupported dependencies
  fail closed; temporary paths are exact and owned.
- The first live regression exposed and fixed an ownership bug where collision handling
  could delete a pre-existing stage. The corrected path preserves collisions and removes
  only a partial file after an attempted write.
- Blender 5.0.1 passes 9 live staging checks from repository, portable ZIP and installed
  Workspace helpers. The installed full background path passes 12 checks from stage reload
  through PNG/receipt creation, collision refusal and exact file teardown. The earlier
  isolated renderer still passes 18 checks.
- Scripts regression: **116 passed**. Repository validation passes. Portable ZIP SHA-256:
  `d305421141a2a86558e43e2b16f860f58272c85f6b5bf390d2844aefafe47fbb`.
  Installed without overwrite at `D:/AI/GameAssetAI-Workspace/.agents/skills/
  blender-render-static-pixel-png`; source/ZIP/installed helper behavior is verified.
- Interactive Scene remains Cube/Light/Camera with one material; no test-owned blend,
  job or PNG remains. Blender addon remains 1.7/protocol 7 vs expected 11 with working
  fallbacks. Skill Creator quick validation is unavailable because optional PyYAML is
  absent; no dependency was installed only for that check.
- Next gate: refresh the client Skill catalog and confirm natural-language discovery plus
  one reviewed render request. After that, automatic palette and outline/shading research
  are next; CEL/Toon and animation sequences remain later work.

## Static Pixel host gate and CLI correction — 2026-09-29

- The user confirmed automatic Skill exposure and a natural-language 32x32 transparent
  Cube render. Final PNG: 1,201 bytes, SHA-256
  `17e8aa7ff0f0d7fb26d4c79752d421f35ceb3ba6af62c4dfbb49c6970048f00f`,
  alpha bounds `[3,3,28,28]`; receipt SHA-256
  `3d0d736f70243bf5a0a347bfe807cfc8b4a04dd3f56941e000600a985e532d78`.
- The first background call failed before publication because the renderer used `bpy`
  without importing it. The host safely reused the unchanged stage/job fingerprint chain,
  published once, removed its exact temporaries and preserved Cube/Light/Camera.
- Corrected the renderer with an explicit `import bpy`. Strengthened the background test
  so the renderer loads in independent globals and its real CLI `main()`/arguments run;
  installed-helper stage→job→PNG→receipt passes all 12 checks after the fix.
- Corrected bundle SHA-256:
  `67bd349b2a91eafbb40d2389057af432abcd4d5f048e30f8cc0ab507648ed552`.
  Updated installed Skill is byte-aligned. The earlier version is retained at
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
  blender-render-static-pixel-png-20260929-pre-bpy-import`.
- Scripts **116 passed** and repository validation passed. The next independent feature
  priority is deterministic explicit-count AUTO palette processing; do not create a second
  2D Skill for it.

## Static Pixel AUTO palette checkpoint — 2026-09-29

- Extended the existing `blender-render-static-pixel-png` Skill in place; no second 2D
  Skill was created. `AUTO` now uses deterministic frequency-weighted median-cut RGB with
  an explicit `max_colors` in `[2,256]`, preserves all alpha bytes, canonicalizes fully
  transparent RGB and records the derived opaque RGBA8 palette.
- Added 4 focused offline tests for repeatability, bounded colors, alpha behavior,
  no-expansion when unique colors are already below the limit, and invalid/invisible
  refusal. Scripts suite is now **120 passed**.
- Blender 5.0.1 candidate regression is now **20 checks**, including explicit AUTO
  eligibility. The installed Skill's actual CLI stage→job→AUTO PNG→receipt path passes
  **13 checks**, including a four-color bound, collision refusal and exact teardown.
- Current portable ZIP SHA-256:
  `bbfb8937da4618955011ae20a150f60ed1cf3eeea5aa84a1ebcef54aebbc54e5`.
  Installed source is updated. The preceding CLI-fixed version remains at
  `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
  blender-render-static-pixel-png-20260929-pre-auto-palette`.
- AUTO is deterministic engineering output, not a perceptual/art-direction quality claim.
  Next host gate is one natural-language AUTO render after client refresh. Next repository
  feature after that is outline/shading validation, not CEL/Toon or animation yet.

## AUTO host gate and one-pixel outer outline checkpoint — 2026-09-29

- The user confirmed natural-language AUTO max-4 rendering at the new personal test root
  `D:/Blender/MCP_Test`. File facts were independently rechecked: 209 bytes, SHA-256
  `b2d291b3824dedcfa3746c3f4dc02b8a6406c619237c0b5e8d2c075b1fba9bb2`;
  no owned stage/job remained. The reusable Skill does not hard-code this personal path.
  Do not use the unrelated Unity project folder for future 2D development artifacts.
- Added backward-compatible request v2. v1 remains explicit legacy no-outline input; v2
  requires `outline_mode/color/width`. The first implemented option is one opaque
  8-neighbor outer pixel and it never overwrites a source-visible pixel.
- Palette reduction runs before outlining, so an outline may add one color beyond AUTO
  `max_colors`. Added 3 offline contract/postprocess tests. Scripts are now **123 passed**.
- Candidate suite passes **21 checks**. Installed Skill full CLI regression passes
  **14 checks** with AUTO max 4 plus black outline: 84 new outline pixels, alpha bounds
  `[5,1,26,22]`, collision refusal, receipt binding and exact teardown.
- Current ZIP SHA-256:
  `6b89f3e667383cdc8e112496d9b6ea68bbab640fb73186a00af45dba18ac0139`.
  The previous AUTO-only version is retained at `D:/AI/GameAssetAI-Workspace/.agents/
  skill-backups/blender-render-static-pixel-png-20260929-pre-outline`.
- Next host gate is one natural-language v2 outline render in `D:/Blender/MCP_Test`.
  Shading validation is the next repository feature after that; CEL/Toon and animation
  sequences remain later work.

## Outline host stale-session refusal checkpoint — 2026-09-29

- The first natural-language outline request refused safely because that client session
  still described the pre-outline Skill and v1 schema. It created no target PNG or owned
  temporary file and preserved Cube/Light/Camera.
- Read-only disk inspection proves the repository and actual Workspace installation both
  contain the optional one-pixel outline instructions and request v2 fields. Deployment
  hashes remain aligned (`SKILL.md` begins `d3c7c9f6`, validator begins `b5e75760`).
- Treat this as a client Skill-catalog cache issue. Do not duplicate/rename the Skill,
  reinstall MCP, change schema back to v1, or weaken fail-closed behavior.
- Required host action: completely start a new Codex/ChatGPT task from
  `D:/AI/GameAssetAI-Workspace` after closing the stale task, first ask it to report the
  request schema and supported outline modes, then issue the render prompt only if it
  reports v2 and `NONE`/`OUTER`.
- Do not start shading implementation until this refreshed-session outline gate passes;
  this preserves the one-feature-at-a-time evidence cycle.

## Outline host refreshed-session schema gate - 2026-09-29

- A completely new task opened from `D:/AI/GameAssetAI-Workspace` reported
  `gameassetai.2d-static-render-request.v2` and the complete outline contract without
  running or modifying Blender.
- The refreshed task correctly exposes `NONE` with `outline_color: null` and width `0`,
  plus `OUTER` with an opaque normalized RGBA color and width exactly `1`. This resolves
  the earlier stale-session catalog issue; no source, installation, MCP or schema change
  is required.
- The remaining host gate is one natural-language `OUTER` render in that same refreshed
  task, targeting a new file under `D:/Blender/MCP_Test`. Do not begin shading work until
  the render receipt, temporary cleanup and unchanged interactive Scene are confirmed.

## Outline host completion and value-step shading checkpoint - 2026-09-29

- The refreshed host completed the exact 32x32 AUTO-4 plus black one-pixel outer-outline
  request. The PNG is 215 bytes with SHA-256
  `70495b016ec32b448d65e79ddff62cb003ae22434e8d11a9151a8138feb5da7c`, alpha bounds
  `[2,2,29,29]`, 108 outline pixels and six total RGBA values. Receipt SHA-256 is
  `c8d9890d66f4628eb51809c8f6d9e9b138964c476d64245ccbf8939b858d08ac`.
  Independent disk inspection confirmed the file hash and zero owned temporary files;
  the host reported Cube/Light/Camera unchanged.
- Extended the same `blender-render-static-pixel-png` Skill to request v3. v1 remains
  readable legacy no-outline input and v2 remains readable legacy no-shading input. New
  requests explicitly choose `shading_mode: NONE` with null `value_steps`, or
  `VALUE_STEPS` with an integer from 2 through 32. No step count is inferred from a game.
- Value banding quantizes rendered HSV value, preserves alpha and RGB ratios, runs before
  palette reduction, and leaves the outer outline last. This is a narrow Pixel postprocess,
  not a CEL/Flat-Toon material or lighting implementation.
- Offline scripts pass 126 tests. Blender 5.0.1 passes 22 candidate checks and 15 full
  stage/job/render checks, including four-step value bounds, AUTO palette, outline,
  receipt binding, collision refusal and exact teardown.
- Next: package and atomically update the Workspace installation, re-run installed-helper
  regression, then use a refreshed client task to verify v3 discovery and one natural-
  language value-step render under `D:/Blender/MCP_Test`.
- Packaging and installation are complete. The 9-file Skill ZIP SHA-256 is
  `8e8cfba54f382329a13120324da35207a868c44ff7004313e703a69222cc12ff`.
  The previous installed version is retained at `D:/AI/GameAssetAI-Workspace/.agents/
  skill-backups/blender-render-static-pixel-png-20260929-pre-value-steps`.
- Portable-ZIP and installed staging suites each pass nine checks. Installed candidate
  inspection passes 22 checks and its full background renderer passes 15 checks. Source
  and installed hashes are aligned. The only remaining value-step gate is refreshed-client
  discovery and one natural-language host render; this requires the user to open/use that
  refreshed task because current-session Skill catalogs do not hot-reload.
- The final 126-test run passed outside the Windows sandbox. Two sandboxed retries failed
  only because newly created temporary directories denied child-file access, not because
  assertions failed. All 192 directories created by those two failed retries were removed
  after verifying their exact parent roots and creation-time window; no owned test/render
  temporary directory remains.

## Value-step host completion and low-usage handoff - 2026-09-30

- The refreshed host completed the v3 natural-language render with four requested value
  steps, AUTO maximum four and a black one-pixel outer outline. The output at
  `D:/Blender/MCP_Test/gameassetai-pixel-value4-auto4-outline-check-20260929.png` is
  133 bytes with SHA-256
  `cf630ae015ea073d13325da24fd6a0d6b0727fda13d35e3d7f924d7ee21ffc66`.
- Reported output facts: 32x32 RGBA8, alpha bounds `[2,2,29,29]`, observed shading values
  `[170]`, three AUTO palette colors, 108 outline pixels, five total RGBA values and
  receipt SHA-256 `c3ad5bd70953cbc709709392fe755cfa0c0c5fb7f94b3df1c5759d8319f6c5c7`.
  The host reported Cube/Light/Camera unchanged. Independent disk checks confirmed the
  file hash and zero `.gameassetai-2d-*` remnants.
- The v3 discovery/execution gate is complete. Because the default Cube yielded only one
  actual value level, the next atomic task is a repository-owned tilted or multi-face
  Blender fixture that proves multiple value bands in the live renderer. Do this before
  starting Action PNG sequences; it strengthens the just-added feature without widening
  scope.
- The user reported only 15% remaining on the five-hour allowance. No new implementation
  unit was started. Resume with the multi-band fixture, run source/portable/installed
  regressions, update evidence, and only then select the Action PNG-sequence contract.

## Multi-band live shading fixture complete - 2026-09-30

- Replaced the uniform plane in `tests/rendering/run_2d_source_stage_load.py` with a
  six-vertex, two-face ridge whose visible facets have different horizontal normals under
  the existing owned off-axis light. This changes test data only; reusable Skill source,
  request schema and installed files were not changed.
- The 15-check full path passes with repository, portable-ZIP and Workspace-installed
  helpers. All three runs observed two legal four-step values `[85,170]`, three AUTO
  palette colors, 84 outline pixels, collision refusal, receipt binding and exact file
  teardown. Decoded artifact SHA-256 is consistently
  `3668d0fa21331e6f28b737c658bea0a9a2b5fea3340a6c57340ec15f27c57595`.
- The default-Cube single-level result remains valid host evidence, while the synthetic
  fixture supplies the missing representative multi-band evidence. The next independent
  pipeline unit is the explicit Action PNG-sequence request contract, reusing existing
  Action/slot/range inspection rules before any batch renderer or new Skill is created.

## Action PNG-sequence offline contract checkpoint - 2026-09-30

- Added development-only `scripts/validate_2d_action_sequence_request.py`; no new Skill or
  renderer was created. It embeds the current static v3 Scene/Object/Profile/view/lighting/
  style settings and expands one explicit Action range into collision-checked PNG targets.
- The contract requires exact Armature/Action names, an optional explicit slot identifier,
  integer inclusive range/positive step that lands on the end, finite playback FPS, at
  most 2048 frames, `ACTION_RANGE` bounds, `OBJECT_ORIGIN` anchor and no-overwrite indexed
  filenames. It never creates an output directory or file.
- Seven offline tests pass for deterministic/no-write expansion, range bounds, names/slot/
  FPS, framing refusal, filename/collision rules, static-v3 reuse and exact fields.
- Next atomic task: implement a read-only Blender candidate that verifies the Mesh,
  Armature modifier/binding, Action and slot, evaluates the requested frames to compute
  stable union bounds, and restores frame/action state exactly. Do not build the staged
  multi-file renderer or install a new Skill before this candidate passes synthetic tests.

## Action PNG-sequence candidate/stage/job checkpoint - 2026-09-30

- Implemented a read-only Blender candidate, stable union-bounds framing planner, authorized
  isolated Mesh/Armature/Action stage and hash-bound sequence job builder. No new installable
  Skill exists yet and none of these helpers publishes PNGs.
- `--suite 2d-action-sequence-candidate` passes 28 checks in Blender 5.0.1: exact Action/slot/
  modifier rules, sampled deformation and bounds, stronger source/Action/evaluation hashes,
  stale-state refusal, staging/job authorization and collision refusal, and exact teardown.
- `tests/rendering/run_2d_action_sequence_stage_load.py` passes 14 checks in a separate
  factory-startup process. The reopened blend contains exactly one Mesh, one Armature and one
  Action; binding and modifier targets are correct, 12.5 FPS survives Blender's fps/fps_base
  representation, all three evaluated bounds match the reviewed candidate, and no PNG is made.
- New/changed core files in this unit: `scripts/inspect_2d_action_sequence_candidate.py`,
  `scripts/preview_2d_action_sequence_framing.py`, `scripts/stage_2d_action_sequence_source.py`,
  `scripts/build_2d_action_sequence_job.py`, the two Action-sequence Blender fixtures, payload
  registration/count tests, and related documentation.
- Next priority: implement an isolated background sequence renderer that revalidates the job
  and loaded stage, renders every planned frame to owned temporary PNGs, verifies all frames,
  and only then publishes the complete set with rollback on any failure. Do not create/install
  a reusable Skill until that renderer and its failure/teardown regressions pass.
- Final validation for this checkpoint: 133 Python script tests passed outside the Windows
  sandbox, repository structure validation passed, the integrated Blender suite passed 28
  checks, and the standalone stage-load suite passed 14 checks. The sandboxed full-suite
  attempt failed only because Windows denied its temporary-directory access; the identical
  unrestricted run passed. The related targeted 70-test run also passed.
- The current execution environment exposes the repository files but not `.git`, so Git status/
  diff could not be obtained in this session. No conclusion about commit state was inferred.

## Action PNG-sequence renderer and local Skill checkpoint - 2026-09-30

- Added `scripts/render_2d_action_sequence.py`. It validates the exact job/stage chain,
  renders every frame to owned temporary PNGs, verifies RGBA8 facts, applies the existing
  optional value-step/palette/outline pipeline, and publishes only after every frame succeeds.
  Any mid-publication error rolls back only targets linked by that invocation.
- Expanded `tests/rendering/run_2d_action_sequence_stage_load.py` to 20 checks. Repository,
  packaged-Skill and Workspace-installed helpers all pass in Blender 5.0.1. The test forces
  failure on the second publication link, verifies complete rollback, then verifies a normal
  three-frame publish, stable 32x32 dimensions/Object-origin anchor, ordered artifact hashes,
  receipt binding, collision refusal and exact teardown.
- Created the single narrow Skill `skills/blender-render-action-png-sequence` using the eight
  tested helpers. Packaged nine files to `.local/source-bundles/
  blender-render-action-png-sequence.zip`; SHA-256 is
  `bbae462641ad450f0b7672e6500695dc1344824535e36b59c92b43aa4302295b`.
- Installed it without overwrite at `D:/AI/GameAssetAI-Workspace/.agents/skills/
  blender-render-action-png-sequence`. Deployment validation reports `aligned` with no
  missing, extra or changed files. Installed-helper full-path regression passes 20 checks.
- `skill-creator`'s `quick_validate.py` could not start because the current Python environment
  lacks PyYAML. No dependency was installed. Repository validation and project tests remain
  the authoritative local format checks.
- Remaining host gate: open a refreshed client task from `D:/AI/GameAssetAI-Workspace`, verify
  `blender-render-action-png-sequence` is exposed, then perform one natural-language render
  against a user-approved Armature/Action and new output prefix. The current default Cube-only
  Scene cannot satisfy this without creating synthetic rig/Action data.
- Final repository verification: all **134** Python script tests pass outside the Windows
  sandbox, `scripts/validate_repo.py` reports `Repository structure OK`, and `.local/validation`
  contains zero owned `.gameassetai-2d-sequence-*` artifacts. A sandboxed targeted run again
  failed only because Windows denied access to its `tempfile` directories; the unrestricted
  complete run passed.
- On the refreshed host, first ask only whether `blender-render-action-png-sequence` is exposed
  and request its supported input boundary. If exposed, use a disposable synthetic rig/Action
  or an explicitly approved existing asset and a new prefix under `D:/Blender/MCP_Test`.
  Do not modify the user's default Cube Scene merely to satisfy this gate without approval.

## Action PNG-sequence refreshed-client discovery - 2026-09-30

- The user confirmed that `blender-render-action-png-sequence` is exposed in a refreshed
  Workspace task. The client accurately reported request schema v1, single reviewed skinned
  Mesh/Armature/Action scope, stable Action-range framing, 2048-frame limit, optional palette/
  value-step/one-pixel outline, isolated rendering, no-overwrite and atomic rollback.
- The same report correctly refused rig/Action creation or editing, retargeting, root/range
  guessing, subframes, per-frame framing, sprite sheets, Unity import, partial resume, batch
  Actions/directions and visual-loop guarantees. Blender was not called or modified.
- Discovery is complete. The sole remaining host gate before sprite-sheet work is an actual
  natural-language render using a disposable synthetic Scene because the user's current
  Scene has only Cube/Light/Camera. The user must submit the explicit temporary-data approval
  in that refreshed task; this session cannot hot-invoke the newly installed Skill catalog.

## Action PNG-sequence host completion - 2026-09-30

- The refreshed host created a disposable separate Scene/Mesh/Armature/Action and successfully
  invoked `blender-render-action-png-sequence` for source frames 1, 2 and 3 at 32x32 RGBA8,
  12 FPS, no palette/value steps/outline and a fixed `[16,16]` Object-origin anchor.
- Output alpha bounds were `[3,9,15,22]`, `[9,9,22,22]`, and `[16,9,28,22]`. The receipt
  SHA-256 was `c9f58eced5c33df1a74f9c5615bf3c9ea53ef964eea392eb0ac6e3592c17bf07`.
- Independent disk inspection confirmed all three dimensions and hashes: `0000` is 988 bytes,
  `2288fa4434226ed2603aed2fc83f398599f10b2f890db52e94dc0bb6867e512c`; `0001` is
  1004 bytes, `59bf53315e79a50a433722277ddf3a66fc0d6ded50b3b97868b7fe442b36a5ec`;
  `0002` is 992 bytes, `549fed5a270d67387af2107db1d889072503ca68c8330d9b173938ede68765c8`.
- The host removed the exact stage/job and disposable Blender Scene/Object/Mesh/Armature/Action,
  retained only the requested PNGs, and reported identical start/end state SHA-256
  `d3b45f1eeeb883c63877d47f6e0a5f974ceca736d77560c1ebd6a953cd685456`.
  The Action-sequence host gate is complete; next is explicit sprite-sheet assembly.

## Explicit sprite-sheet assembly checkpoint - 2026-09-30

- Added the pure-Python v1 contract and assembler in
  `scripts/validate_2d_sprite_sheet_request.py` and `scripts/assemble_2d_sprite_sheet.py`.
  Inputs explicitly bind ordered source frames, SHA-256 values, bottom-left anchors, cell
  size, rows/columns, padding and `ROW_MAJOR_TOP_LEFT`; no grid or game setting is inferred.
- Assembly revalidates exact decode bytes, creates a transparent equal-cell sheet and JSON
  metadata, stages both outputs, and rolls back the PNG if JSON publication fails. It refuses
  overwrite/`.meta`, linked or malformed inputs, stale previews, mismatched hashes/dimensions,
  duplicate paths/indices, insufficient layout and sheets above the bounded pixel budget.
- Six offline tests pass, including exact pixel placement, anchor conversion and deliberate
  second-artifact publication failure. Related development/packaging tests bring the targeted
  run to 71 passing tests.
- Created and installed `assemble-png-sprite-sheet` at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/assemble-png-sprite-sheet`; deployment is byte-
  aligned. Its four-file ZIP SHA-256 is
  `eed46f3fe19031eaa2f75083f2b56ef2683838aa2d6154c717474475844a076d`.
- The installed helpers assembled the three retained host Action frames into
  `D:/Blender/MCP_Test/gameassetai-action-sequence-host-20260930-sheet.png` and sibling JSON.
  The 2x2 grid uses 32x32 cells and one-pixel padding, yielding 65x65 with three cells.
  PNG: 834 bytes, SHA-256 `08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`.
  JSON: 1553 bytes, SHA-256 `e36b415768547da31676a7fff85a240c10f93e29860324377a8b15a49ff13f4f`.
  Metadata image hash matches, and zero `.gameassetai-spritesheet-*` temporaries remain.
- Next host gate: open a refreshed Workspace task, confirm `assemble-png-sprite-sheet` is
  exposed, and call it naturally on new output names (the current sheet names now correctly
  collide and must not be reused). After that, select Profile-backed presets/direction sets
  or Unity slicing validation according to the Unity-first roadmap.
- Final verification for this checkpoint: all **141** Python script tests pass outside the
  Windows tempfile sandbox and `scripts/validate_repo.py` reports `Repository structure OK`.

## Sprite-sheet refreshed-client host completion - 2026-09-30

- The refreshed Workspace task exposed `assemble-png-sprite-sheet` and naturally assembled
  the three Action PNGs into new `gameassetai-spritesheet-host-check.png/.json` targets.
- User-reported result: 65x65, three frames, 2x2 grid, one-pixel padding, row-major top-left;
  cell rectangles and sheet anchors exactly match the reviewed plan. PNG SHA-256 is
  `08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`,
  JSON SHA-256 is `22c9439c888eea742d026bffab5ccf694da815a6c3ca1af7d0c27c09721729f7`,
  and receipt SHA-256 is `bd8ff0178269e2a6f84762933bb0ba1388379946b704bdd00f61588640cdd114`.
- Independent disk inspection confirmed the same PNG/JSON hashes, 834/1540-byte sizes,
  metadata cell count 3 and zero `.gameassetai-spritesheet-*` temporaries. Visual inspection
  shows frames in the expected top-left, top-right and bottom-left cells.

## Optional Profile-backed 2D preset contract - 2026-09-30

- Preserved the existing single Markdown Profile model. Added an optional exact fenced JSON
  block contract rather than a sidecar file, new Workspace directory or fuzzy prose parser.
- `scripts/extract_2d_profile_preset.py` accepts only a provenance-bound active Profile context,
  returns `absent` for null/unconfigured Profiles, allows at most one complete v1 block and
  reuses the existing static-v3 validator for view/lighting/style. It additionally validates
  explicit playback FPS and sprite-sheet padding/order. It performs no file write.
- Updated the Profile template with an indented placeholder skeleton so the template itself is
  not accidentally parsed as a configured preset. Missing values must remain absent rather
  than being filled with project-wide defaults.
- Five offline tests pass. Automatic fresh-hash integration into the three 2D Skills remains
  a later unit; no installed Skill changed in this checkpoint.
- Final verification for the combined host-evidence/preset checkpoint: all **146** Python
  script tests pass outside the Windows tempfile sandbox and repository validation reports
  `Repository structure OK`. Stop here rather than beginning cross-Skill preset integration
  with the user-reported five-hour allowance at 26%.

## Profile-backed 2D Skill integration checkpoint - 2026-09-30

- Added `scripts/resolve_2d_profile_preset.py`. It resolves a complete preset for exactly one
  purpose (`STATIC_RENDER`, `ACTION_SEQUENCE`, or `SPRITE_SHEET`) and binds active Profile name,
  active-profile reference SHA-256, Profile SHA-256 and canonical preset SHA-256. Callers must
  reread and pass the exact binding before output. Explicit settings and Profile settings cannot
  be partially merged; absent Profile/preset never reuses earlier values.
- Integrated the extractor/resolver into `blender-render-static-pixel-png`,
  `blender-render-action-png-sequence`, and `assemble-png-sprite-sheet`. Sprite-sheet requests
  now use `gameassetai.2d-sprite-sheet-request.v2`, store the four-field Profile provenance in
  metadata v2, and retain v1 as legacy read compatibility.
- Added six resolver tests, raised sprite-sheet tests from six to eight, and added
  `tests/rendering/run_2d_profile_preset_load.py`. All six source/Workspace-installed helper
  roots pass the latter's eight no-write freshness checks. Resolved static and Action settings
  also pass their existing request validators.
- Repackaged source archives:
  `blender-render-static-pixel-png-profile-v1.zip` SHA-256
  `70faaddfda3956649497a35ee17d813730d56d1f2625fa66a7c86576f99b57c1`;
  `blender-render-action-png-sequence-profile-v1.zip`
  `b86144db59bd7f9f9a489cc3181961b4317b49a6b24812c5761f217cb7a8a6fb`;
  `assemble-png-sprite-sheet-profile-v1.zip`
  `e45ae304691a5990b0a599c7f49c78d68a076d3e73372279e9ba43c431a460a8`.
- Updated all three local installations under
  `D:/AI/GameAssetAI-Workspace/.agents/skills` with hash-bound recovery backups in `.local`.
  Deployment validation reports `aligned` for every Skill. Client discovery remains unverified
  until a refreshed Workspace task loads the new Skill text.
- Blender 5.0.1 regression passes: static source and installed helpers each pass 15 checks;
  Action-sequence source and installed helpers each pass 20 checks, including rollback and exact
  teardown. `.local/validation` has no owned render/stage/job residue.
- Final verification: **154** script tests and **47** Workspace tests pass (four Workspace
  symlink tests skipped because Windows lacks symlink privilege); repository validation reports
  `Repository structure OK`. `.git` is unavailable in this execution environment, so no commit
  status was inferred.
- Next gate: in a refreshed task rooted at `D:/AI/GameAssetAI-Workspace`, confirm the three
  updated Skills describe the mutually exclusive explicit/Profile settings modes and sprite-sheet
  v2 provenance. Then perform one Profile-backed no-write preview/fresh-binding check before any
  new host render. Do not alter the user's real Profile merely to satisfy this gate.

## Profile integration refreshed-client confirmation - 2026-09-30

- The user confirmed all three updated Skills are exposed. The refreshed client accurately
  described mutually exclusive complete explicit/Profile-preset modes, purpose-specific
  resolution, four-hash `expected_binding` freshness before output and sprite-sheet request v2
  with legacy v1 read compatibility.
- The active Workspace Profile is null, so the client correctly refused to select or invent a
  Profile preset and did not run Blender or modify files. This completes the Profile-integration
  discovery gate without changing the user's Workspace configuration.

## Explicit multi-direction / multi-Action batch checkpoint - 2026-09-30

- Added `gameassetai.2d-render-batch-request.v1` in
  `scripts/validate_2d_render_batch_request.py`. It groups 1-64 explicit existing static-v3 or
  Action-sequence-v1 child requests, caps the batch at 2,048 PNGs, requires one output directory,
  rejects case-insensitive id/path collisions and fixes list-order/all-or-nothing/rollback policy.
  Each item records either four-null explicit provenance or a complete active Profile-preset
  binding matching the nested request.
- Added `build_2d_render_batch_job.py` and `run_2d_render_batch.py`. The authorized job binds the
  batch, every child stage/job and every helper hash. The coordinator launches the existing child
  renderers in separate background Blender processes and, on later failure, removes only prior
  outputs whose current SHA-256 still matches its receipt. Concurrently changed output is kept and
  reported as incomplete rollback.
- Added 17 focused offline regressions across batch request/job/runner behavior, including Profile
  binding, cross-child collision, shared-directory/total-output limits, authorization/drift,
  complete success, later-child rollback and changed-output preservation.
- Added `blender-render-2d-batch` with 19 deterministic helpers. Repository, packaged-Skill and
  Workspace-installed helper roots each pass the same Blender 5.0.1 seven-check mixed fixture:
  one static direction plus one three-frame Action direction, deliberate second-child process
  failure with rollback, four-PNG success, ordered receipts, artifact hashes and exact teardown.
- Portable ZIP: `.local/source-bundles/blender-render-2d-batch.zip`, 20 files, SHA-256
  `c0ff54217befb93753addca02f517030ec6cf5f968d329b582994027da1a27c5`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-2d-batch`; deployment validation is
  `aligned`. Client discovery remains unverified until a refreshed Workspace task.
- Documentation is in `docs/2d-render-batch-contract.md`; the Profile integration and guarded
  batch roadmap items are complete. Unity, sprite-sheet assembly, direction/Action inference,
  parallelism and partial resume remain outside this Skill.
- Final verification: **172** script tests and **47** Workspace tests pass (four Windows symlink
  tests skipped for unavailable privilege), repository validation reports `Repository structure
  OK`, and `.local/validation` contains no owned batch/stage/job/render residue. `.git` remains
  unavailable in this environment, so commit status was not inferred.
- Next gate: open a refreshed task rooted at `D:/AI/GameAssetAI-Workspace`, confirm
  `blender-render-2d-batch` exposure and ask only for its supported boundary/schema. Do not render
  or create a synthetic Scene in that discovery step. After discovery, one natural-language
  synthetic mixed batch is the remaining host gate.

## 2D batch refreshed-client host completion - 2026-09-30

- The refreshed Workspace task exposed and actually invoked `blender-render-2d-batch` in
  explicit mode without reading or applying the null active Profile. It completed one static
  child plus one three-frame Action child under the fixed `LIST_ORDER / ALL_OR_NOTHING /
  ROLL_BACK_BATCH_OUTPUTS` policy and published four 96x96 PNGs.
- User-reported batch receipt SHA-256 is
  `f8ad14eab7dc55d4f85ac6d9002f5f9cd51e53d1e6d37595fb253c03c58a03c4`.
  Independent disk revalidation found: static 5004 bytes,
  `fea35408bd6ae23189f5d67f239b8b785aaa27e7a0b63b09f00a264159a75e4c`;
  Action 01 4483 bytes,
  `3bbcfb14059037efaf8db7800d1d42001b8646f2c1dbbf606d3eb8462dc72ec3`;
  Action 02 4521 bytes,
  `7e6f9162f11924beab03c15407aba833202cc105d0a3837136beb34a710b0df5`;
  Action 03 4631 bytes,
  `07c73eb2814fb719c694b717bce57035e4078ec29aba7d0666232c58f73717fd`.
- The host removed its temporary Scene/Object/Mesh/Armature/Action and stage/job data. It
  reported exact restoration of Scene, frame, selection and active-object state; independent
  inspection found zero owned batch/stage/job temporary files in `D:/Blender/MCP_Test`.
  The 2D batch host gate is complete.

## Offline Unity Sprite import/slicing check contract - 2026-09-30

- Added `scripts/prepare_unity_sprite_import_check.py` with strict schema
  `gameassetai.unity-sprite-import-check.v1`. It binds one existing non-linked Unity
  `Assets/.../*.png` and SHA-256 to explicit TextureImporter and per-Sprite expectations.
- The generated no-overwrite C# check revalidates project/path/hash, optionally refreshes
  only that asset, compares image dimensions, Sprite mode, PPU, Point/uncompressed/mipmap/
  alpha/sRGB settings, and exact sorted Sprite names/rectangles/pivots/PPU. Native C# arrays
  avoid a Newtonsoft dependency. Active Scene and selection state must remain unchanged.
- Six offline tests pass, including stale hash/scope, rectangle/image bounds, pivot/rect
  bounds, unique names, Single cardinality, duplicate JSON, finite values and no overwrite.
  Documentation is `docs/unity-sprite-import-validation.md`.
- No Unity project or external PNG was modified. Live validation is pending an explicitly
  approved Unity project plus exact `Assets` destination; files in `D:/Blender/MCP_Test`
  cannot be imported by Unity in place.
- Final verification: **178** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped for unavailable privilege), and `scripts/validate_repo.py` reports
  `Repository structure OK`.

## Unity MCP connection and live Sprite slicing validation - 2026-09-30

- The user selected project
  `C:/Users/jiwoo/UnityProject/GameAssetAI_UnityWorkbench` and restricted asset work to
  `Assets/Blender`. Unity is 6000.3.9f1 and the existing manifest already pins
  `com.unity.pipeline` 0.8.0-exp.1, so no package installation or manifest edit was needed.
- Updated only the existing Codex Unity MCP entry to launch
  `unity mcp --project-path C:/Users/jiwoo/UnityProject/GameAssetAI_UnityWorkbench`.
  Although the sandboxed global status listing was empty, an exact-project `unity command`
  reached the live Editor at `127.0.0.1:7800` and exposed `eval`/`eval_file`.
- Copied the 65x65 host sprite sheet to a unique test name under the approved folder. Copy
  size/hash were 834 bytes and
  `08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`.
  Through `eval_file`, set Multiple Sprite, PPU 32, Point, Uncompressed, no mipmaps, alpha
  transparency and sRGB, plus the three explicit 32x32 cells and centered pivots.
- The generated v1 validator (request SHA-256
  `86d51e11389d3b4a44339245d40628d50247f0c811e18a85376260cc115b80e0`, code SHA-256
  `3a751bb27be3a71f5f4906dac1847d9291df97130775d264710e51004ba9a0f9`) passed all 23
  importer, image, Sprite metadata and Scene-preservation checks with zero compiler
  diagnostics. An intentional four-Sprite expectation failed closed at `sprite_count`
  with Unity CLI exit code 6.
- Cleanup used `AssetDatabase.DeleteAsset` on only the owned PNG; its `.meta` was removed,
  `Assets/Blender` returned to its original empty file inventory, and the active Scene and
  selection were preserved. The source in `D:/Blender/MCP_Test` was unchanged. Live Unity
  Sprite import/slicing validation is complete for this narrow equal-cell fixture.

## Optional Blender panel/operator evaluation - 2026-09-30

- Evaluated the now-stable static/Action/sprite-sheet/Profile/batch contracts against the
  proposed persistent Blender UI layer. No current host or test workflow requires a panel:
  reviewed hash-bound jobs, background Blender isolation, receipts, rollback and external
  Workspace Profiles already provide the required behavior.
- A panel would currently duplicate Profile/output state and add registration, hot-reload,
  Blender-version and uninstall lifecycle risk without replacing the background renderer.
  Therefore no add-on tree or Blender state was created.
- Re-evaluate only after evidence of a concrete interactive need such as repeated live
  framing preview, progress/cancel UI, a fresh-fingerprint Profile picker, or a demonstrably
  safer operator boundary. Decision details: `docs/2d-blender-addon-evaluation.md`.

## Alpha-derived silhouette-mask checkpoint - 2026-09-30

- Selected the first advanced output narrowly as an RGBA8 alpha-derived silhouette mask.
  Normal/depth coordinate contracts and material/object-ID semantics remain separate; no
  Blender node, Scene or source render was modified.
- Added strict request/preview helper `validate_2d_silhouette_mask_request.py` and authorized
  atomic publisher `derive_2d_silhouette_mask.py`. Policies are explicit
  `BINARY_NONZERO` or `PRESERVE_ALPHA`; source/hash/color/target/overwrite are exact.
- Six focused tests pass: read-only hash-bound candidacy, exact binary pixels, byte-exact
  alpha preservation, authorization/staleness/collision/policy refusal, injected post-link
  rollback, and retention of a concurrently changed published output. Packaged helper bytes
  align with repository sources and Skill Creator validation passes.
- Real file proof used the retained 96x96 batch-front PNG (5,004 bytes, SHA-256
  `fea35408bd6ae23189f5d67f239b8b785aaa27e7a0b63b09f00a264159a75e4c`). The new white
  binary mask is 257 bytes, SHA-256
  `b9f5fbf94138a3850c040751cdd1f9f7f5dfe28b66eddd8d19a9876f4a102b0e`, with 4,958
  visible pixels, alpha bounds `[9,9,86,86]`, two RGBA values and receipt SHA-256
  `16835934ba001635b187da658f959f693d6dc2bfd6ac89fe4f8e1b42f27e3c96`.
- Added source Skill `derive-png-silhouette-mask`. Four-file portable archive SHA-256 is
  `a70739ebdad94d59f951d381ad4865c5c964ea12cc946643649db7aece3542d2`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/derive-png-silhouette-mask`; deployment is
  byte-aligned. Refreshed-client discovery and one natural-language call remain the host gate.
- Final verification: **185** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped for unavailable privilege), Skill Creator validation passes, and
  repository validation reports `Repository structure OK`. No owned mask stage remains.

## Silhouette-mask refreshed-client discovery - 2026-09-30

- The user confirmed `derive-png-silhouette-mask` is exposed in a refreshed Workspace task.
  The client reported the exact RGBA8, explicit color, two alpha-policy, source-preserving,
  hash/fingerprint, new-file and receipt boundaries and correctly excluded Blender rendering,
  inference, material/object IDs, normals/depth/SDF, outlines, slicing and Unity settings.
- No file was created. Discovery is complete. The final host gate is one natural-language
  call on retained source
  `D:/Blender/MCP_Test/gai_batch_881faa3c7353_diag_action_01.png`, SHA-256
  `3bbcfb14059037efaf8db7800d1d42001b8646f2c1dbbf606d3eb8462dc72ec3`, to the currently
  absent target `gai_batch_881faa3c7353_diag_action_01-mask-host.png`, using opaque white
  and `BINARY_NONZERO`. The source is 4,483 bytes; target/`.meta` and owned stages are absent.

## Silhouette-mask host completion - 2026-09-30

- The refreshed Workspace task completed the exact opaque-white `BINARY_NONZERO` request
  against `gai_batch_881faa3c7353_diag_action_01.png` and published the reviewed new target
  `gai_batch_881faa3c7353_diag_action_01-mask-host.png`.
- User-reported result: 96x96 RGBA8, 2,342 visible pixels, zero partial-alpha pixels, two
  RGBA values, alpha bounds `[18,11,77,86]`, output SHA-256
  `c9813a17c6176ec58a22f69f95a2990a0caeeeb6f524a845b9d411df4d425ff2` and receipt
  SHA-256 `040bf53f0fd986a73efb50dc8d5a5150d9fa7433845b1ce758536a075657870f`.
  Status was `created` with `published: true`. Independent disk inspection confirmed the
  262-byte output hash and found zero owned material-mask stages in the host directory. The
  silhouette-mask host gate is complete.

## Static material-slot mask checkpoint - 2026-09-30

- Split the roadmap's advanced-pass bundle rather than combining unrelated semantics. Added
  `gameassetai.2d-material-mask-request.v1` and the separate
  `blender-render-material-mask-png` Skill. It requires an exact static base Mesh material
  slot index, opaque color, orthographic view, resolution and new RGBA8 target; it never
  infers a material from its name, appearance, selection or Profile.
- Candidate inspection fingerprints base topology, polygon slot assignments, material-slot
  identities, Object transform and Scene/setup/output state. It refuses missing/unassigned
  slots, invalid face indices, hidden/empty or Edit Mode Meshes, parents, constraints,
  modifiers, animation, Shape Keys and linked data.
- The authorized path writes an independent one-Object blend stage and hash-bound job. Only
  the isolated background Blender replaces staged slots with red/green emission ID shaders.
  Non-target faces remain opaque during the ID render, preserving visible-surface occlusion;
  final pixels are converted to the requested color or transparent black before no-overwrite
  publication. Original Scene, Mesh and materials are untouched.
- Repository source, packaged Skill and Workspace-installed helpers each pass the Blender
  5.0.1 12-check overlapping-face fixture: 200 target pixels, 200 occluder pixels, binary
  two-RGBA output, stale-request and collision refusal, receipt binding and exact teardown.
  The stable fixture artifact SHA-256 is
  `566139db2aef3050fcc42ab843bccba0e1d6ef9696f1c6f0081ad01ee4d03b1f`.
- Skill Creator validation passes. The nine-file portable ZIP is
  `.local/source-bundles/blender-render-material-mask-png.zip`, SHA-256
  `cce206a26980285ff31782e4137b6a9710086ddc8ac8a4a462b61aab0b785baa`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-material-mask-png`; deployment
  is byte-aligned and installed helpers pass the same Blender regression.
- Final verification: **190** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped for unavailable privilege), official Skill validation passes and
  repository validation reports `Repository structure OK`. No owned stage/job/PNG remains.
  Refreshed-client discovery and one natural-language host call are the remaining gates.
  Object-ID, normal, depth, impostor, evaluated/deformed and multi-slot batch outputs remain
  separate future work.

## Material-mask refreshed-client host completion - 2026-09-30

- The refreshed Workspace task exposed and invoked `blender-render-material-mask-png` on
  `Scene / Cube`, exact material slot 0 (`Material`). All six Cube faces were assigned to
  that slot, so zero non-target occluder pixels is the expected result for this host fixture.
- User-reported output: 32x32 RGBA8, 676 visible pixels, alpha bounds `[3,3,28,28]`, status
  `created`, `png_published: true`, and SHA-256
  `298b840e446ad09a7bee0872af5ae8641593ba541b2678882b9028fd7d81dff8`.
  Independent disk inspection confirmed the 100-byte file hash, no `.meta`, and zero owned
  `.gameassetai-material-mask-*` temporaries. The host reported that the original Scene and
  materials were not modified or saved. The material-mask discovery and execution gates are
  complete.

## Static target-Object visibility-mask checkpoint - 2026-09-30

- Added `gameassetai.2d-object-mask-request.v1` and the separate
  `blender-render-object-mask-png` Skill. The caller must provide one exact static target
  Mesh and an explicit unique list of zero to 63 static Mesh occluders. Unlisted Scene
  Objects are neither framed nor staged; the Skill never infers participants from the
  Scene, collection, selection or visibility state.
- Read-only inspection fingerprints every requested base Mesh's vertices, edges, polygons,
  Object transform/name, Scene frame/unit state and complete view/color/sampling/output
  setup. Union bounds of exactly those Objects provide stable orthographic framing. The
  same static dependency blockers used by material masks apply.
- Authorized staging copies only the target and named occluders and records exact roles.
  The background render assigns red emission to the target and green emission to occluders;
  depth evaluation therefore preserves front-surface occlusion before green pixels become
  transparent and red pixels become the requested opaque color. An entirely occluded target
  fails instead of publishing an empty file.
- Repository source, packaged Skill and Workspace-installed helpers each pass the Blender
  5.0.1 12-check fixture. A closer explicit occluder hides 200 of the target pixels, 200
  target pixels remain, and a third unlisted Object is absent from candidate, union framing
  and stage. Source drift/collision refusal, receipt binding and exact teardown pass. Stable
  artifact SHA-256 is
  `ecb3ff36af1954adbea230d5a61dd486f660db324acad827585588eba85bec19`.
- Official Skill validation passes. The nine-file portable archive is
  `.local/source-bundles/blender-render-object-mask-png.zip`, SHA-256
  `b8a2c7147ec77587901fb9a6b6b4b2d389f6e19f71f39d2fa10ac22ab140600b`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-object-mask-png`; deployment is
  byte-aligned and installed helpers pass the same native regression.
- Final verification: **195** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped), repository validation is clean and no owned Object-mask temporary
  remains. Refreshed-client exposure and one natural-language Cube call with an explicit
  empty occluder list remain the host gates. Multi-color ID atlas, normal, depth, impostor,
  evaluated/deformed and batch outputs remain independent future work.

## Object-mask host completion and normal-pass contract - 2026-09-30

- The refreshed Workspace task exposed and invoked `blender-render-object-mask-png` on
  `Scene / Cube` with an explicit empty occluder list. Candidate review had no blockers and
  its fingerprints remained fresh through output.
- User-reported result: 32x32 RGBA8, 676 target pixels, alpha bounds `[3,3,28,28]`, artifact
  SHA-256 `298b840e446ad09a7bee0872af5ae8641593ba541b2678882b9028fd7d81dff8`, receipt
  SHA-256 `65d785de5cf8a2a60d7bfd87e958f90f5da9747b3286babc029efc4bb397b53e`.
  Independent disk inspection confirmed the 100-byte output hash, no `.meta`, and zero
  owned Object-mask temporaries. Original Scene/Object/Mesh/Material state was not saved or
  changed. The Object-mask discovery and host gates are complete.
- Added offline-only `gameassetai.2d-normal-pass-request.v1` before implementing another
  renderer. It fixes `CAMERA_BASIS`: X camera-right, Y camera-up, Z camera-back toward the
  camera, so a front-facing normal has positive Z. `SHADING_NORMAL` and
  `SIGNED_XYZ_TO_UNORM_RGB` are the only v1 source/encoding; background is transparent black,
  sampling is nearest with anti-aliasing disabled, and output is a new RGBA8 PNG.
- Four focused tests pass for deterministic hashing/axis reporting, alternative space/source
  refusal, encoding/background/sampling policy and output collision handling. No Blender
  renderer, output, Skill or installation was created for normals.
- Added the read-only candidate gate and a Blender 5.0.1 tilted flat-face probe. A world
  normal `(1,1,1)/sqrt(3)` under camera right `+X`, up `+Z`, back `-Y` produced components
  `[+0.577,+0.577,-0.577]` and exact reference RGB `[201,201,54]`. Six checks pass for valid
  candidacy, axis signs, encoding, no PNG and preserved Scene count. The next safe gate is
  an isolated flat/smooth shading-normal render probe; no normal Skill is installed yet.
- Final checkpoint verification: **199** script tests and **47** Workspace tests pass (four
  Windows symlink tests skipped), repository validation reports `Repository structure OK`,
  and the native normal candidate probe passes six checks without creating an artifact.

## Isolated normal shader/render capability result - 2026-10-01

- Added an isolated Blender 5.0.1 capability probe that creates a flat tilted triangle and
  smooth sphere, builds a camera-basis normal emission shader, saves/reopens an owned blend
  stage, renders RGBA8 with `Raw` color management, decodes exact PNG bytes and removes both
  stage and PNG. It does not touch the interactive Blender Scene.
- The eight-check probe passes and exposes a required semantic correction: Blender
  `SHADING_NORMAL` is face-forward. The deliberately back-facing triangle's geometric
  `[201,201,54]` reference becomes a shading-normal result near `[54,54,201]`.
- Direct shader-to-PNG output is not byte-exact vector encoding. The flat region contains
  four values spanning R/G `53..55` and B `201..202` despite zero filter and `Raw`; the
  smooth sphere has 282 RGBA values from interpolation. Treating those PNG bytes as the
  contract would make output GPU/render-path dependent.
- Decision: the future normal Skill must use float normal readback and deterministic CPU
  face-forward/camera-basis/signed-to-UNORM encoding before atomic RGBA8 publication. Do not
  implement it as direct emission-to-PNG. No normal Skill or retained artifact exists yet;
  zero `.gameassetai-normal-*` files remain. Offline suites remain **199** script tests and
  **47** Workspace tests because this checkpoint adds a native Blender capability harness,
  not another unittest.
- Follow-up capability probing showed that Blender 5.0.1 background rendering does not
  provide a usable in-memory float Render Result in this harness. `write_still=True` leaves
  none available, and `write_still=False` through both the default call and `EXEC_DEFAULT`
  leaves a `Render Result` datablock sized `0x0`. The experimental readback assertions were
  removed so the committed capability probe remains green. The next implementation gate is
  an owned float OpenEXR intermediate, then deterministic CPU RGBA8 encoding and teardown.
- Post-recovery verification is clean: the native probe again passes all eight checks,
  **199** script tests and **47** Workspace tests pass (four Windows symlink tests skipped),
  repository validation reports `Repository structure OK`, and no owned normal temporary
  file remains.
- The owned float-file fallback then succeeded. The probe now renders an additional 32-bit
  RGBA OpenEXR, reloads its float pixels, performs deterministic CPU round-to-nearest RGBA8
  encoding and verifies exact teardown. All **13** checks pass: the flat back-facing region
  is exactly `[54,54,201,255]` after CPU encoding and the smooth region retains 282 distinct
  RGBA values. The roadmap's float-stage gate is complete. The next bounded task is the
  guarded static normal-pass Skill itself, followed by refreshed-client host validation.

## Static camera-basis normal-pass Skill checkpoint - 2026-10-01

- Added `blender-render-normal-pass-png` for one exact static base-Mesh Object. The v1 Skill
  retains the reviewed request/candidate contract and adds read-only framing, an independent
  one-Mesh blend stage, a hash-bound job and an isolated background renderer.
- Publication uses the proven deterministic path: camera-basis face-forward shading normals
  are rendered to an owned 32-bit RGBA OpenEXR, reloaded as floats, vertically normalized to
  PNG row order, rounded on CPU to RGBA8 and atomically linked to a new target. Transparent
  pixels are canonical black. Direct shader-to-PNG bytes are never published.
- Repository helpers and packaged Skill helpers independently pass the Blender 5.0.1
  eleven-check end-to-end fixture. It verifies request/candidate/framing, stale-request
  refusal, staging, job binding, exact flat normal `[54,54,201,255]`, receipt binding,
  collision refusal and exact teardown. Stable fixture PNG SHA-256 is
  `4a400fe607c8c9377aa6acdfeeb0d264a05854e1d793723920fcf524c1d14b54`.
- The nine-file portable archive is
  `.local/source-bundles/blender-render-normal-pass-png.zip`, SHA-256
  `c3fe01596ad74c5fe85cad34805f8ebb1ecc15e83778a9425388edadf1887254`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-normal-pass-png`; installed
  helpers pass the same eleven-check native regression.
- Skill Creator's bundled `quick_validate.py` could not run because the available system
  Python lacks PyYAML; repository validation and deployment-manifest validation are used in
  addition to the native regression. Refreshed-client discovery and one natural-language
  host render remain. The interactive Blender Scene was not used or modified.
- Final verification: **199** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped), repository validation reports `Repository structure OK`, source
  and installed Skill manifests have no missing/extra/changed files, and no owned normal-pass
  temporary remains. The prepared host target
  `D:/Blender/MCP_Test/gameassetai-normal-pass-host-check-20261001.png` and its `.meta` are
  absent. In a refreshed client, use explicit `Scene / Cube`, view direction `[0,-1,0]`, up
  `[0,0,1]`, margin `0.1`, resolution `32x32`, and that new target; active Profile is null
  and must not be inferred or applied.

## Static normal-pass refreshed-client host completion - 2026-10-01

- The refreshed client exposed `blender-render-normal-pass-png`. It produced a blocker-free
  `candidate_for_review` for `Scene / Cube` without using the null active Profile, then
  completed the exact confirmed 32x32 request in the isolated background workflow.
- User-reported output: RGBA8, alpha bounds `[3,3,28,28]`, 676 foreground pixels, one visible
  normal value `[128,128,255,255]`, PNG SHA-256
  `5dd6fdf2fec82409258755ebabef9a7645f990d507e11f7e44c49b461ec561bf` and receipt SHA-256
  `a26f3a853a7d330f825c23946a8b4eca41fe41681e946d5b38090f8f25440911`.
- Independent disk inspection confirmed the 104-byte PNG and hash, no `.meta`, and zero
  `.gameassetai-normal-pass-*` temporary files. The host reported that `Scene / Cube`, its
  Mesh and `Material` were not modified or saved. All normal-pass implementation, discovery
  and host gates are complete.

## Static camera-linear depth-pass Skill checkpoint - 2026-10-01

- Split depth from the remaining optional ID-atlas/impostor work. Added the exact
  `gameassetai.2d-depth-pass-request.v1` contract: one static base Mesh, orthographic
  `CAMERA_LINEAR` depth along the back-toward-camera direction, normalization over exact
  world-space base-Mesh vertex projections, near-black/far-white UNORM RGB, transparent
  background, disabled anti-aliasing and new RGBA8 output only. A span `<= 1e-6` is refused.
- Four offline tests pass. A seven-check read-only Blender 5.0.1 candidate fixture proves
  near/middle/far projections `+1/0/-1`, exact encoded references `0/128/255`, zero-span
  refusal, no output and preserved Scene count.
- A separate nine-check staged render probe proves actual fragment interpolation through an
  owned 32-bit float OpenEXR and deterministic CPU encoding: 512 visible pixels contain 120
  grayscale levels from 5 through 248, followed by exact stage/EXR/PNG teardown.
- Added `blender-render-depth-pass-png` with reviewed framing, independent one-Mesh staging,
  hash-bound job and atomic no-overwrite publication. Repository, packaged and installed
  helpers each pass the eleven-check end-to-end fixture. The 32x24 tilted triangle publishes
  200 foreground pixels and 72 visible depth values; stable PNG SHA-256 is
  `84808425c59adbd3b339e69e66cb6b2c304447dd3bad3da86d5407a0ddca716a`.
- The nine-file archive is `.local/source-bundles/blender-render-depth-pass-png.zip`,
  SHA-256 `4e678f145f736a73fbb30bd3eab7d1e325501ba020344e6209413ffd8fa97838`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-depth-pass-png`; refreshed-client
  discovery and one natural-language host render remain. All tests used factory-startup
  background Blender and did not access or modify the user's interactive Scene.
- Final verification: **203** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped), repository validation is clean, source and installed Skill
  manifests are aligned, and no owned depth temporary remains. The next host target
  `D:/Blender/MCP_Test/gameassetai-depth-pass-host-check-20261001.png` and `.meta` are absent.
  For a visually meaningful Cube gradient, use direction
  `[0.7071067811865476,-0.7071067811865476,0]`, up `[0,0,1]`, margin `0.1`, resolution
  `32x32`, explicit settings and no Profile. A refreshed client is required for discovery.

## Static depth-pass refreshed-client host completion - 2026-10-01

- The refreshed client exposed `blender-render-depth-pass-png` and produced a blocker-free
  `candidate_for_review` for `Scene / Cube` using only the explicit diagonal view. Its exact
  vertex projection range was `-1.41421354..+1.41421354` with span `2.82842708`; Profile was
  neither read nor applied. The Blender MCP protocol 7/server 13 warning did not affect the
  supported preview or render calls.
- User-reported output: 32x32 RGBA8, 163 bytes, 468 foreground pixels, alpha bounds
  `[3,7,28,24]`, 13 depth values, PNG SHA-256
  `597302cdab74a3c8b0d019596b40c9dd64d58233ee52440f75c6e09659612304` and receipt SHA-256
  `746147a7b668c7125dfdbdca87e9cb8b22c2dccb6878be508eb9de074f208082`.
- Independent disk inspection confirmed the file size/hash, no `.meta`, and zero owned
  `.gameassetai-depth-pass-*` temporaries. The host reported the original Scene unchanged.
  All depth-pass implementation, discovery and host gates are complete.

## Static multi-Object color-ID Skill checkpoint - 2026-10-01

- Split the Object-ID pass from unrelated impostor work. Added
  `gameassetai.2d-object-id-request.v1`: an explicit ordered list of 2 to 63 unique static
  base-Mesh Objects with unique post-quantization opaque RGBA8 IDs. Only listed Objects are
  framed/staged/rendered and mutually depth-occlude; unlisted Scene Objects are excluded.
- Four offline tests pass for exact hashing, count/name/color uniqueness, inference refusal,
  fixed sampling and collision-safe RGBA8 output. A seven-check read-only Blender candidate
  fixture confirms ordered colors, excludes a distant unlisted Object, blocks modifiers and
  creates no output or Scene.
- Added `blender-render-object-id-png`. Independent staged copies receive internal numeric
  float IDs in an owned 32-bit EXR; CPU remapping publishes the exact requested colors. The
  original materials are never used for identity and remain untouched.
- Repository, packaged and installed helpers each pass the twelve-check Blender 5.0.1
  pipeline. Two overlapping requested quads publish exact red/green IDs with 200 visible
  pixels each; an unlisted Object is absent, source drift and collision are refused, receipt
  binding and exact teardown pass. Stable PNG SHA-256 is
  `f9ce956b267be18c4141624f9a65637f3446316c16aa424b85c2f1cd99f627f9`.
- The nine-file archive is `.local/source-bundles/blender-render-object-id-png.zip`, SHA-256
  `e828116814bfd7154e7a66198e8f1ad6f294652f707468528d3b21bb0b1ba480`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-object-id-png`. Refreshed-client
  discovery and one host render remain. Because the interactive Scene currently has only
  `Cube`, the host gate needs a separate temporary Scene containing at least two Mesh
  Objects; it must be removed afterward without changing the original Scene.
- Final verification: **207** script tests and **47** Workspace tests pass (four Windows
  symlink tests skipped), repository validation is clean, source/installed manifests are
  aligned and no owned Object-ID temporary remains. The prepared host target
  `D:/Blender/MCP_Test/gameassetai-object-id-host-check-20261001.png` and `.meta` are absent.
  A refreshed client should create a separate temporary two-quad Scene with the second quad
  overlapping and closer, request opaque red/green IDs at 32x24 using front direction
  `[0,-1,0]`, up `[0,0,1]`, margin `0.1`, then remove only the temporary Blender data after
  preserving the reviewed PNG. The existing `Scene / Cube` must remain unchanged.

## Object-ID refreshed-client host completion and impostor decision - 2026-10-01

- The refreshed Workspace client exposed `blender-render-object-id-png`, produced a
  blocker-free reviewed plan and completed the authorized render in an isolated copy.
  The explicit host fixture used two overlapping Mesh Objects with opaque red/green IDs,
  a 32x24 target, direction `[0,-1,0]`, up `[0,0,1]` and margin `0.1`; no active Profile
  was read or applied.
- User-reported publication succeeded with 162 red pixels, 180 green pixels, alpha bounds
  `[3,5,25,19]`, PNG SHA-256
  `ddc807257baf1b34cd3e7649d5fceb2e252350d1de28b6c08845f804d86fd366` and receipt SHA-256
  `17b22f20d27246b5103f0eeaa4d9df492e4ea66a060555ccc7af44a1e0e3dfb0`.
  The host removed its temporary Scene/Object/Mesh/stage/job data and reported the original
  `Scene / Cube` unchanged.
- Independent disk verification confirmed 105 bytes, 32x24 RGBA8, the exact PNG hash and
  pixel counts, 342 visible pixels, alpha bounds `[3,5,25,19]`, no `.meta` and zero owned
  `.gameassetai-object-id-*` temporaries. Object-ID implementation, discovery and host gates
  are complete.
- Evaluated the remaining optional impostor item against the existing static color, normal,
  depth, Object-ID, batch and sprite-sheet workflows. A separate renderer would duplicate
  stable behavior, so `docs/2d-impostor-bundle-decision.md` defines impostor support as a
  future shared-framing orchestration layer. It must bind one canonical camera/framing plan
  across passes, publish atomically and emit a cross-pass manifest.
- Next implementation gate: define and offline-test
  `gameassetai.2d-impostor-bundle-request.v1`, its shared-framing plan and result manifest.
  Do not begin Blender execution or a new installable Skill until mismatch, collision and
  rollback behavior is proved offline.
- Final verification after the documentation/roadmap change: **207** script tests and
  **47** Workspace tests pass (four Windows symlink tests skipped), and repository validation
  reports `Repository structure OK`. Git metadata is unavailable from this working copy, so
  commit/diff status was not inferred.

## Static impostor bundle request gate - 2026-10-01

- Added the pure offline `gameassetai.2d-impostor-bundle-request.v1` validator in
  `scripts/validate_2d_impostor_bundle_request.py`. It composes existing current-schema
  COLOR, NORMAL and DEPTH requests without duplicating their pass semantics or reading
  Blender.
- V1 accepts 1-32 explicit views and 2-96 children. Every view must contain the same ordered
  set of at least two distinct passes. All children must use one exact Scene/Object and each
  view's children must have identical projection, direction, up vector, margin and resolution.
  COLOR is explicit-only with null Profile provenance, transparent background, disabled AA
  and nearest-neighbor sampling. Object-ID and animation remain outside v1.
- The validator requires unique safe item/view IDs, unique same-directory PNG paths, a new
  same-directory JSON manifest target and fixed `LIST_ORDER / ALL_OR_NOTHING /
  ROLL_BACK_BUNDLE_OUTPUTS / REJECT` policy. It returns a stable request hash and ordered
  child plan but performs no Blender inspection, shared-framing calculation or write.
- Five new offline tests cover deterministic read-only success, Scene/Object/view/resolution
  mismatch, incomplete or differently ordered per-view passes, output/manifest collisions,
  invalid policy/Profile/current schema and Object-ID refusal. Full verification is now
  **212** script tests and **47** Workspace tests passing (four Windows symlink tests skipped);
  repository validation reports `Repository structure OK`.
- During targeted sandbox-only retries, Windows denied access to several newly created empty
  throwaway test directories under ignored `.local`; the approved full regression command
  passed normally. Those directories are not request outputs, source files or runtime state.
- Next exact gate: implement a read-only Blender shared-framing preview that calculates one
  canonical center/orthographic scale/clip plan per view and proves every pass child binds it.
  Then define the no-write result-manifest validator before any coordinator, Skill packaging
  or host render.

## Static impostor bundle implementation and Skill checkpoint - 2026-10-02

- Added `preview_2d_impostor_shared_framing.py`. It reruns the existing COLOR/NORMAL/DEPTH
  validators and Blender candidates, calculates one canonical base-Mesh orthographic camera
  plan per explicit view, and binds the same plan hash to every pass without creating a
  Camera or writing a file. Its Blender 5.0.1 fixture passes 12 read-only/staleness/blocker/
  teardown checks.
- Added `validate_2d_impostor_result_manifest.py`. It verifies the exact ordered views and
  artifacts, regular non-hardlinked RGBA8 PNG signatures, sizes and SHA-256 values, child
  receipt hashes, shared-plan bindings and a still-new manifest target without publishing it.
  Five offline tests cover success and all material drift/collision cases.
- Added `build_2d_impostor_bundle_job.py` and `run_2d_impostor_bundle.py`. The job binds fresh
  request/shared-preview hashes, every stage/job and exact helper bytes. The runner executes
  children sequentially in isolated Blender processes, validates artifacts and receipts,
  rolls back only unchanged outputs created by the attempt after failure, preserves changed
  outputs, validates the result manifest and atomically publishes the manifest last. Six
  offline tests cover authorization, drift, success, later-child rollback, collision and
  changed-output preservation.
- A factory-startup Blender 5.0.1 end-to-end fixture passes 19 checks using real COLOR,
  NORMAL and DEPTH staging/renderers: request, shared framing, all child plan matches,
  all stage/jobs, bundle job/render, manifest order, nonempty outputs, no stray token files,
  artifact-root restoration, context preservation and exact Blender data teardown.
- Created `blender-render-impostor-bundle` with the existing pass implementations plus the
  new coordinator; no duplicate renderer was introduced. Both the source Skill and the
  installed Skill independently pass the 19-check native fixture. Only factory-startup
  background Blender was used; the user's open interactive Blender Scene was not accessed,
  changed or saved.
- Portable archive: `.local/source-bundles/blender-render-impostor-bundle.zip`, 26 files,
  67,716 bytes, SHA-256
  `944ef44cd3eef804cf263ba10e9fd660f27ed17ea45be90725305705b5993f6e`.
  Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-impostor-bundle`; source and
  installation manifests are aligned with no missing, extra or changed files.
- Skill Creator's bundled `quick_validate.py` remains unavailable because system Python has
  no PyYAML. The repository's stricter source/helper/deployment checks and native Blender
  executions pass. Final full verification is **224** script tests and **47** Workspace tests
  passing (four Windows symlink tests skipped), plus `Repository structure OK`.
- Exact next gate requires a refreshed Workspace-rooted client because Skill discovery is
  session-start scoped. Confirm that `blender-render-impostor-bundle` is exposed, then first
  ask it to report the supported boundary and request schema without rendering. After that,
  host-test one explicit `Scene / Cube` view with COLOR/NORMAL/DEPTH and four new paths
  (three PNGs plus one JSON manifest) under `D:/Blender/MCP_Test`. Unity is not required.

## Static impostor bundle refreshed-client discovery - 2026-10-03

- The refreshed Workspace client exposes `blender-render-impostor-bundle` and correctly
  reports the `gameassetai.2d-impostor-bundle-request.v1` boundary: explicit static
  COLOR/NORMAL/DEPTH children, identical ordered pass sets per view, common Scene/Object and
  view settings, shared orthographic framing, same-directory new targets, manifest-last
  all-or-nothing publication and rollback.
- The client also correctly refused to infer directions, use Actions/evaluated geometry,
  include Object-ID, merge a Profile, assemble sheets, configure Unity, create LODs or claim
  visual certification. It did not inspect or modify Blender and did not create files.
- One clarification for the host request: the underlying COLOR v3 validator accepts both
  `SOURCE_COPY` and `OWNED_NEUTRAL`; use explicit `OWNED_NEUTRAL` for the deterministic Cube
  host fixture. Null Profile provenance is still mandatory for this bundle.
- Verified four new collision-free host targets with no adjacent `.meta` files:
  `gameassetai-impostor-front-color-host-20261003.png`,
  `gameassetai-impostor-front-normal-host-20261003.png`,
  `gameassetai-impostor-front-depth-host-20261003.png`, and
  `gameassetai-impostor-front-host-20261003.json`, all under `D:/Blender/MCP_Test`.
- Next exact gate: in the refreshed client, preview one `Scene / Cube` front view using
  direction `[0,-1,0]`, up `[0,0,1]`, margin `0.1`, resolution `32x32`, ordered passes
  COLOR/NORMAL/DEPTH, explicit null Profile provenance and `OWNED_NEUTRAL` transparent COLOR.
  Do not render until the client reports `candidate_for_review`, no blockers, one common plan
  and the four exact targets. After approval, run the atomic bundle and retain PNGs/manifest.

## Static impostor bundle host preview - 2026-10-03

- The refreshed client completed the exact read-only `Scene / Cube` preview for ordered
  COLOR/NORMAL/DEPTH children. All three candidates are `candidate_for_review`; blockers and
  errors are empty. Cube facts are 8 vertices, 12 edges, 6 polygons, identity transform.
- Request fingerprints are COLOR
  `f159f06314fd33511fa86a5cb4a5d10844507315c219bb9cd80b24d3f03b9b61`, NORMAL
  `4749c5ca30cf6b0951cf5e2d097391489597ef56f31b38e44ec508ea2a065e07`, and DEPTH
  `b1172e102daa94a50fb2ba1936358f8330bbebad456c0c83dd2a4eef765e4eb1`.
- The one shared front plan uses direction `[0,-1,0]`, up `[0,0,1]`, right `[1,0,0]`,
  32x32 resolution, margin `0.1`, center `[0,0,0]`, camera `[0,-4,0]`, orthographic scale
  `2.4`, clip `1.5..6.5` and projected half-extents `[1,1,1]`.
- Bundle request fingerprint:
  `44bc1b535190641b1a2a388e4b0d192da74d407ddd68aaeb17c1c1c003365cbd`;
  source fingerprint:
  `42fd6b6d9468dfb4d1fffcf9eced662f37940adb13dceca07a1c94b93be0d3b3`;
  shared-plan fingerprint:
  `c373976c4d20f9e4936cdda83a529516e4e75c4a437a46ba72042f2ad3c94673`;
  complete preview fingerprint:
  `df0a112e620709a6c8cb7e2797da51271cd6c283c06834d115053a1f7b2aaf21`.
  All three children bind the same shared-plan fingerprint.
- COLOR is explicit PIXEL/OWNED_NEUTRAL with transparent background and null Profile,
  palette, outline and VALUE_STEPS settings. The host created no Camera, output or Scene
  change. Disk recheck confirms all three PNG targets, the JSON manifest target and their
  adjacent `.meta` paths remain absent; no owned impostor temporary is present.
- Next exact gate: authorize this unchanged request/preview fingerprint chain in the refreshed
  client and run the atomic bundle. The runner must recheck fingerprints, publish all three
  PNGs before the manifest, clean only its stage/jobs, and report artifact/receipt/manifest
  hashes plus unchanged interactive Blender state.

## Static impostor bundle host completion - 2026-10-03

- The refreshed client rechecked and matched the approved request, source, shared-plan and
  preview fingerprints, then completed the atomic one-view COLOR/NORMAL/DEPTH bundle. All
  three PNGs were validated before the JSON manifest was published last.
- Independent disk inspection confirmed three 32x32 PNGs and the exact reported hashes:
  COLOR 1,162 bytes,
  `fa8d51d2cf6f74197e4741689d5726d88ddf0f945e31a4a44630b6848f383e77`;
  NORMAL 104 bytes,
  `5dd6fdf2fec82409258755ebabef9a7645f990d507e11f7e44c49b461ec561bf`;
  DEPTH 102 bytes,
  `aabf80cbfc8bcba72459511842fdd0556a6642a39f308edacea193f09d0b9ff7`.
- The 2,141-byte `gameassetai-impostor-front-host-20261003.json` has SHA-256
  `14bc33aeb8851bb7dc7cc92f76570190b7eadb2fc4e57688d49efd2ab918dcc1`.
  Its `gameassetai.2d-impostor-bundle-result.v1` content binds the exact three ordered
  artifacts, request/source/preview hashes and common plan fingerprint. Child receipt hashes
  are COLOR `58adcf8ae0d654184734ca3f6f47e05998c5bf07575e02cde40999ccac105dce`,
  NORMAL `8caa918aa393fc9b010a176ce53fcc68c5599bbf31fde1c197975543c64ef247`,
  and DEPTH `c990d223b787a44fc155ea308f645b8a0e51dc640f70399119e5bb9ae251965a`.
  Bundle receipt SHA-256 is
  `d98862c5cc6cc2a554b1ba818bebc733c41161e25114a91235045c43fd55fed6`;
  bundle job SHA-256 is
  `535cd4e57c9dd266516e3d7f175fd63e2e3e1a6167d6bb92998c37b17c1b8567`.
- The host removed all six child stage/jobs and the bundle job, retained only the three PNGs
  and manifest, and reported the exact interactive `Scene / Cube` state unchanged. Disk
  inspection found no owned impostor temporary and no adjacent `.meta` file. The complete
  impostor implementation, package/install, discovery, preview and host-render gates pass.
- The planned 3D-to-2D pixel/stylized pipeline is now complete at its documented v1 boundary.
  Continue existing 3D work rather than expanding this optional pipeline by default. With
  only Blender currently open, the next suitable unresolved static-asset topic is a narrow
  read-only collider/LOD candidate contract; do not infer engine-specific collider or LOD
  settings and do not modify `Scene / Cube` while developing it.

## Existing static-collider inspection Skill checkpoint - 2026-10-03

- Split collider inspection, collider generation, LOD inspection and LOD generation into
  separate concerns in `docs/static-collider-lod-decision.md`. The first slice is read-only
  inspection of explicitly named existing collider base Meshes; it neither discovers nor
  generates geometry and makes no Unity/physics suitability claim.
- Added `gameassetai.static-collider-candidate-request.v1` and
  `validate_static_collider_request.py`. It requires one exact Scene/render Mesh, 1-32 distinct
  explicit collider Mesh names, `STATIC_TRIANGLE_MESH` or `CONVEX_MESH_CANDIDATE` intent,
  fixed BASE_MESH/WORLD/read-only policy and a finite `0..0.01` relative convexity tolerance
  only for convex candidates. Five offline hashing/refusal tests pass.
- Added `inspect_static_collider_candidate.py`. It reports base topology, world transforms and
  bounds, render/collider AABB relationships, dependencies and closed-half-space convexity
  evidence. It blocks stale request hashes, unsupported dependencies and open/nonconvex
  convex candidates; it does not evaluate the dependency graph or mutate Blender.
- The Blender 5.0.1 representative fixture passes nine checks: request ready, blocker-free
  closed convex candidate, 12 triangle evidence, an open triangle Mesh reported without a
  convex claim, stale-request refusal, open-convex blocker, modifier blocker, read-only source
  preservation and exact Scene/Object/Mesh teardown. Repository, source-Skill and installed-
  Skill helpers independently pass.
- Created and installed `blender-inspect-static-colliders`. Its three-file portable archive is
  `.local/source-bundles/blender-inspect-static-colliders.zip`, 6,747 bytes, SHA-256
  `ee825fbd22dea45aa046a65d0dd6aab502bd7a030c1086813c5df19e35ff9c41`.
  It was deployed without overwrite to
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-static-colliders`; source and
  installed manifests are aligned with no missing, extra or changed files.
- Skill Creator's quick validator again cannot import PyYAML, so repository validation,
  exact helper-source comparison, deployment comparison and three native Blender executions
  provide the evidence. Final full verification is **230** script tests and **47** Workspace
  tests passing (four Windows symlink tests skipped), plus `Repository structure OK`.
- The user's current interactive Scene is known to contain only `Cube`, `Camera` and `Light`,
  so it has no distinct existing collider Mesh to inspect. Next exact gate: refresh the
  Workspace client, confirm `blender-inspect-static-colliders` exposure and request its
  supported schema plus current-scene eligibility without creating test data. Expected safe
  outcome is exposure plus refusal to run until an explicit distinct collider Mesh exists.

## Existing static-collider refreshed-client discovery - 2026-10-03

- The refreshed Workspace client exposes `blender-inspect-static-colliders` and accurately
  reports `gameassetai.static-collider-candidate-request.v1`, the two supported collider kinds,
  exact distinct-name rules, BASE_MESH/WORLD/read-only policy and the convex-only finite
  `0..0.01` relative tolerance.
- A read-only current-Scene check found exactly `Cube`, `Camera` and `Light`, with only one Mesh.
  The client correctly refused to construct a request because no distinct collider Mesh exists;
  it did not infer from names, selection, Collection or proximity and did not reuse `Cube` as
  both render and collider Object.
- The client correctly stated that the Skill does not discover/generate colliders, evaluate
  modifiers, modify geometry, inspect/generate LOD, configure Unity, or certify physics cost or
  gameplay coverage. It created no test data and made no Blender change.
- Next exact gate: use a separate temporary Scene to host-test both supported paths without
  modifying `Scene / Cube`. Create identity-transform independent base Meshes for a render Cube,
  a slightly larger closed convex Cube, and an open ground quad. Run one explicit request with
  the closed Cube as `CONVEX_MESH_CANDIDATE` at tolerance `0.0001` and the quad as
  `STATIC_TRIANGLE_MESH` with null tolerance. Preserve the report, then remove only those
  temporary Scene/Object/Mesh IDs and restore the original active Scene/context without saving.

## Existing static-collider host completion - 2026-10-03

- The refreshed client created a separate temporary Scene with independent identity-transform
  render Cube, 2.2-unit closed convex Cube and open ground quad, then ran the installed Skill.
  Status was `candidate_for_review`, with empty blockers/errors. Request SHA-256 is
  `0bd0ef62dd534c3b36de870eed50fdaba3d53f0552af1ec3f0cfc7b01b9bffe1` and source
  fingerprint is `3557838ce07bc74e19b2ffef613664208f7b597f12b888eec44ba63de5ce9156`.
- The render Mesh reported 8 vertices, 12 edges, 6 polygons, 12 triangles, closed manifold
  topology, no degenerates and world AABB `[-1,-1,-1]..[1,1,1]`.
- The convex collider reported the same topology, AABB approximately
  `[-1.1,-1.1,-1.1]..[1.1,1.1,1.1]`, full render-AABB containment, six valid face planes,
  maximum outside ratio `3.41283540948222e-09` against tolerance `0.0001`, and
  `within_tolerance: true`.
- The static triangle ground reported 4 vertices, 1 quad/2 triangles and 4 boundary edges.
  Its open topology was correctly reported without a convexity claim or blocker.
- The host removed every temporary Scene/Object/Mesh, restored active `Scene`, active `Camera`,
  empty selection, frame 76, subframe 0 and OBJECT mode exactly, retained the original
  Camera/Cube/Light counts and did not save. Existing-collider inspection implementation,
  package/install, discovery, no-candidate refusal and synthetic host gates are complete.

## Existing static LOD-chain inspection Skill checkpoint - 2026-10-03

- Added `gameassetai.static-lod-chain-request.v1` and
  `validate_static_lod_chain_request.py`. V1 takes 2-8 explicitly ordered unique base-Mesh
  Objects with contiguous indices from zero and fixed BASE_MESH/WORLD/read-only,
  `EXACT_WORLD_MATRIX` and `STRICTLY_DECREASING` policies. It does not infer names, accept
  evaluated modifiers, define screen thresholds or authorize generation. Four offline tests
  cover deterministic ordering/hashing, bounds, exact policy and malformed/unknown inputs.
- Added `inspect_static_lod_chain_candidate.py`. It binds exact base vertices, polygons,
  material indices, slots and world matrices into a source fingerprint and reports per-level
  triangle counts/ratios, world bounds, center/extent relations, material-slot equality and
  dependencies. Stale hashes, unsupported dependencies, matrix differences, empty geometry
  and nondecreasing triangle counts are errors/blockers; no Mesh is modified.
- A Blender 5.0.1 fixture passes ten checks on a 12/8/4 triangle Cube/Octahedron/Tetrahedron
  chain: request/candidate, strict reduction, exact matrices, stale refusal, matrix mismatch,
  modifier dependency, nondecreasing order, read-only behavior and exact teardown. Repository,
  source-Skill and installed-Skill helpers independently pass.
- Created and installed `blender-inspect-static-lod-chain`. Its three-file archive is
  `.local/source-bundles/blender-inspect-static-lod-chain.zip`, 5,968 bytes, SHA-256
  `7c6289873f057fff5886ddd85d268eb0565d6ae76a402cfa21e0017879cd94d2`.
  It was deployed without overwrite to
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-static-lod-chain`; source and
  installed manifests are aligned with no missing, extra or changed files.
- Skill Creator's quick validator remains unavailable because PyYAML is absent; repository,
  exact helper-source/deployment and native Blender validation pass. Full verification is now
  **235** script tests and **47** Workspace tests passing (four Windows symlink tests skipped),
  plus `Repository structure OK`.
- The current Scene has only one Mesh (`Cube`), so no valid 2-level chain exists. Next exact
  gate: in a refreshed Workspace client, confirm Skill exposure and request its schema/current
  Scene eligibility without creating data. Expected outcome is safe no-chain refusal. A later
  temporary-Scene host fixture can exercise an explicit 12/8/4 chain and exact cleanup.

## Existing static LOD-chain refreshed-client discovery - 2026-10-03

- The refreshed Workspace client exposes `blender-inspect-static-lod-chain` and accurately
  reports the `gameassetai.static-lod-chain-request.v1` schema, explicit 2-8 level boundary,
  contiguous indices, BASE_MESH/WORLD/read-only scope, exact world-matrix alignment and strict
  base-triangle reduction.
- A read-only current-Scene check found only one Mesh Object, `Cube`, alongside `Camera` and
  `Light`. The client correctly refused to infer a chain from names, Collections, visibility,
  selection or triangle counts and therefore did not construct an invalid request.
- It correctly reported bounds/material/dependency inspection limits and refused generation,
  duplication, decimation, approximate transforms, modifier evaluation, threshold selection,
  export, Unity configuration, collider inspection and visual/runtime certification. It made
  no Blender change and created no test data.
- Next exact gate: create a separate temporary Scene containing independent identity-transform
  base Meshes with a 12-triangle Cube as LOD0, 8-triangle Octahedron as LOD1 and 4-triangle
  Tetrahedron as LOD2. Run one explicit 0/1/2 request, preserve the read-only report, remove
  only those temporary Scene/Object/Mesh IDs, and exactly restore the original active Scene,
  selection, active Object, frame, subframe and mode without saving.
- The first synthetic-host follow-up returned the prior no-chain discovery report again and
  created nothing. This is safe but does not satisfy the synthetic host gate. Keep the Skill
  itself read-only: explicitly authorize ordinary Blender MCP/Python fixture setup before the
  Skill call and ordinary Blender MCP/Python teardown afterward. Do not weaken or update the
  Skill to create its own test data.

## Existing static LOD-chain host completion - 2026-10-03

- After explicitly separating ordinary Blender fixture setup/teardown from the read-only Skill,
  the refreshed client completed the synthetic 12/8/4 chain inspection. Status was
  `candidate_for_review` with empty blockers, errors and review items. Request SHA-256 is
  `90bdc42a36d8db2bb849bfb935dddb2cc53f6c98ebbe2be4a35c7a4001b984c3`; source
  fingerprint is `9e6fdc7c75b82d3a1c86f32f811159c57b99c1893e941f26ec2497458805dd14`.
- LOD0 Cube reported 8/12/6/12 V/E/P/T; LOD1 Octahedron 6/12/8/8 with ratios
  `0.6667/0.6667`; LOD2 Tetrahedron 4/6/4/4 with ratios `0.3333/0.5`.
  All levels had identical identity matrices, determinant 1, AABB `[-1,-1,-1]..[1,1,1]`,
  zero center offset, unit half-extent ratios, identical empty material slots and no dependency.
- The host removed all temporary Scene/Object/Mesh IDs and exactly restored active `Scene`,
  active `Camera`, empty selection, frame 76, subframe 0, OBJECT mode and all original data
  counts without saving. Existing-LOD-chain implementation, package/install, discovery,
  no-chain refusal and synthetic host gates are complete.
- The next LOD gate is a development-only independent-copy Decimate experiment on a synthetic
  Mesh. It must prove source byte/fact preservation, real base-triangle reduction, retained
  finite UV/material structure and exact teardown before any generation request or Skill is
  designed. It must not touch the user's interactive Blender Scene.

## Independent-copy LOD Decimate capability - 2026-10-03

- Added a factory-startup Blender 5.0.1 experiment using an independent Object/Mesh copy of a
  synthetic UV-mapped Icosphere with one material. Native `DECIMATE`/`COLLAPSE` RNA and apply
  behavior were verified; the user's interactive Blender was not accessed.
- Nine checks pass: representative source, independent copy, actual RNA, copy-only modifier
  apply, base-triangle reduction, exact source preservation, retained finite UV/material
  structure, finite result and exact teardown.
- Explicit ratio `0.5` reduced 320 triangles/162 vertices to 160 triangles/82 vertices. Source
  hash was stable. Result radius increased by up to `0.0152056767`, so the experiment explicitly
  does not certify silhouette quality despite meeting the numeric triangle ratio.
- Next exact gate: define an offline request requiring an explicit ratio and unused output
  Object/Mesh names, exact source transform copying, independent Mesh data, source preservation,
  dependency refusal and separate preview/apply authorization. Do not infer a chain length,
  ratio, naming convention or Unity thresholds.

## Independent-copy LOD request gate - 2026-10-03

- Added pure offline `gameassetai.static-lod-copy-request.v1` validation in
  `validate_static_lod_copy_request.py`. It accepts one exact Scene/source and unused intended
  output Object/Mesh names, only `DECIMATE_COLLAPSE`, an explicit finite `0.01..0.99` ratio and
  `triangulate: false`.
- Fixed v1 preservation policy is BASE_MESH_ONLY, dependency REFUSE, source PRESERVE,
  NEW_OBJECT_AND_MESH, COPY_EXACT transform, shared read-only material datablocks, copied UV
  layers and PREVIEW_THEN_EXPLICIT_APPLY. Broader source edits, evaluated geometry, shared
  output Meshes, dropped UVs or immediate authorization are refused.
- Five offline tests pass for deterministic request hashing/no mutation, ratio/method bounds,
  name separation, exact preservation policy and malformed/missing/unknown inputs. The helper
  does not access Blender or authorize a copy.
- Exact next gate: implement a Blender candidate that rechecks unused output names and strict
  static base-Mesh dependencies, creates an owned temporary independent copy, applies the exact
  ratio, reports actual triangle/UV/material/bounds changes, removes all preview IDs and binds a
  source/setup/output fingerprint. Only then design guarded persistent copy apply/rollback.
- Full verification after the experiment and request gate is **240** script tests and **47**
  Workspace tests passing (four Windows symlink tests skipped), with
  `Repository structure OK`. The current checkpoint contains no persistent Blender output and
  no generation Skill has been created or installed.

## Independent-copy LOD transient preview gate - 2026-10-03

- Added `preview_static_lod_copy.py`. It revalidates the exact
  `gameassetai.static-lod-copy-request.v1` hash, resolves only the explicit Scene/source,
  refuses occupied intended output Object/Mesh names and strict static-base dependencies,
  and binds source/setup/preview fingerprints. It never treats a Profile budget as permission.
- A blocker-free preview creates only UUID-owned temporary Scene/Object/Mesh IDs, makes an
  independent Mesh copy, applies Blender's native `DECIMATE`/`COLLAPSE` at the explicit ratio,
  and reports actual triangle counts, retained UV-layer names/material slots/world matrix and
  world-bounds deltas. All temporary IDs are removed in `finally`; the intended persistent
  output names are never created and `mutation_authorized` remains false.
- The Blender 5.0.1 factory-startup fixture passes **11 checks**: request readiness,
  blocker-free candidate, real 320-to-160 triangle reduction at ratio `0.5`, retained structure,
  exact source preservation, preview-ID removal, stale-hash refusal, output-name collision
  refusal, modifier-dependency refusal, context restoration and exact global teardown.
- The first native run exposed Blender's built-in `sharp_face` Mesh attribute. The dependency
  filter now explicitly recognizes Blender built-ins while continuing to refuse unsupported
  user attributes; the rerun passes completely.
- Final verification is **240** script tests and **47** Workspace tests passing (four Windows
  symlink tests skipped), plus `Repository structure OK` and Python compile success. The first
  sandboxed full-test attempts were invalid because Windows denied their temporary directories;
  the same suite passed outside that sandbox, and the dedicated `.local/test-temp` directory
  created by the failed retry was removed completely.
- Exact next gate: design a separately authorized persistent independent-copy apply receipt
  that rechecks request/source/setup/preview fingerprints immediately before mutation, creates
  only the requested new Object/Mesh, validates the result, and rolls back only its owned IDs
  on any failure. Do not package/install a generation Skill until that fixture passes. Unity
  LODGroup thresholds and visual/silhouette quality remain separate later work.

## Independent-copy LOD guarded apply gate - 2026-10-03

- Added `apply_static_lod_copy.py`. It requires explicit `authorized=true` plus exact reviewed
  request/source/setup/preview fingerprints, reruns the disposable preview immediately before
  mutation, then creates exactly the requested independent Object and Mesh in the explicit
  Scene. No existing name is overwritten or autosuffixed and the source is never modified.
- The persistent result must match the reviewed preview's topology counts, world bounds,
  transform, material slots and UV-layer structure. A receipt fingerprint binds the complete
  four-hash review chain and validated output facts. Profile settings, ratios, names, chain
  length and Unity thresholds are not inferred.
- Failure handling tags only newly created Object/Mesh IDs with a per-run owner token and removes
  only those IDs when validation fails. If ownership or users change unexpectedly, cleanup stops
  and reports `unverified` instead of deleting uncertain data.
- The first fixture run exposed that temporary UUID Object/Mesh names were included in the
  preview fingerprint. Those names are now normalized to the intended output names and excluded
  from the preview geometry binding, making repeated fresh previews deterministic.
- Blender 5.0.1 passes the original **11** preview checks and **11** apply/rollback checks. Apply
  coverage includes authorization refusal, stale-preview refusal, real persistent 320-to-160
  creation, independent Mesh/exact transform, source preservation, success-context restore,
  forced post-create validation failure, owned-ID rollback, failure-context restore and exact
  teardown. The successful fixture output is also deleted during fixture cleanup.
- Final verification remains **240** script tests and **47** Workspace tests passing (four
  Windows symlink tests skipped), plus `Repository structure OK` and Python compile success.
- Exact next gate: design the narrow reusable Skill around the proven request/preview/apply
  helpers, document explicit confirmation and limitations, package it, compare packaged helper
  bytes to development sources, install without overwrite, and run source plus installed-helper
  native regressions before client discovery. Do not combine Unity LODGroup configuration into
  this Blender generation Skill.

## Independent-copy LOD Skill package/install checkpoint - 2026-10-03

- Used the `skill-creator` guidance to add `blender-create-static-lod-copy` with only the three
  proven request/preview/apply helpers. The Skill requires one explicit source, exact unused
  Object/Mesh names and an explicit ratio, then separates nonpersistent preview from a later
  explicit apply confirmation. It does not infer a chain, ratio, naming, Profile policy or Unity
  LODGroup settings.
- The portable four-file archive is
  `.local/source-bundles/blender-create-static-lod-copy.zip`, 9,517 bytes, SHA-256
  `c758c207825e3580c8a206644839247369ee77a70ac048f688a5c6d453cce3a4`.
- Installed without overwrite at
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-create-static-lod-copy`. Source and
  installed manifests are aligned with no missing, extra or changed files. Both source-Skill and
  installed-Skill helpers independently pass the 11-check Blender 5.0.1 persistent-create and
  forced-rollback fixture; every synthetic output is removed by the fixture.
- Skill Creator's `quick_validate.py` cannot run because its environment lacks PyYAML. Repository
  validation, Python compilation, exact packaged-helper comparison, deployment comparison and
  native source/installed Blender executions provide the evidence instead.
- Final verification is **241** script tests and **47** Workspace tests passing (four Windows
  symlink tests skipped), plus `Repository structure OK`.
- Exact next gate: refresh the Workspace client, confirm `blender-create-static-lod-copy` is
  exposed, and request its supported schema/current-Scene eligibility without creating data.
  The current known Scene has only the default `Cube`; it is technically a static source, but do
  not choose a ratio or output names automatically. After discovery, use an explicitly authorized
  temporary synthetic curved Mesh for one natural-language preview, separately approve apply,
  verify the receipt, then delete only the created test output and fixture data and restore the
  original context without saving.

## Independent-copy LOD live host preview - 2026-10-25

- To avoid another broad regression cycle, performed one focused live-Blender host preview using
  the installed `blender-create-static-lod-copy` helpers. Blender is 5.0.1; the MCP add-on works
  through fallback protocol 13 but reports that protocol 15 is current. This warning did not
  affect the preview.
- Preserved the user's active `Scene` containing only `Cube`, `Camera` and `Light`. Created one
  explicitly named temporary Scene, `GAA_LOD_HostCheck_20261025`, containing a synthetic
  UV-mapped 320-triangle Icosphere source. No existing Object or data-block was modified or saved.
- The exact ratio-0.5 request is `ready`; preview status is `candidate_for_review` with empty
  errors, blockers and dependencies. It predicts 320 to 160 triangles, 162 to 82 vertices,
  retains the material slot, UV-layer name and exact world matrix, and reports half-extent deltas
  `[0.0, 0.00024443864822387695, -0.0010366439819335938]` for visual review.
- Fingerprints: request
  `3d924545a83623bb689309ba02c420117b486bda17b7bd335f0c828822e51902`, source
  `89eacc7d56e399f372e089ff82cc6186b2506f260d26898ecf4d8a291b16d684`, setup
  `0ae149e86669e28688c63439ed04b9243d8eee54cff0e1430fc6ecd797f5c8a1`, preview
  `35287e2d35a453628e6c9b30bd20b11313c799486a08114933705d6ff25c210a`.
- Restored active `Scene`, active `Camera`, empty selection and frame 76. The temporary fixture
  Scene/source is intentionally retained unsaved for the required separate apply approval.
  `GAA_LOD_HostResult_20261025` and its Mesh do not exist yet.
- Next exact action requires user approval of this preview. On approval, apply using all four
  fingerprints, verify the receipt and source preservation, then remove the created test output,
  temporary source/Scene/Mesh/Material and restore the original context without saving. Formal
  automatic Skill exposure remains unverified because this session used the installed helpers
  directly.

## Independent-copy LOD live host apply completion - 2026-10-25

- The user continued after the exact live preview, authorizing the reviewed test apply. The
  installed helper rechecked all four fingerprints unchanged and created the exact independent
  `GAA_LOD_HostResult_20261025` Object/Mesh at 160 triangles and 82 vertices.
- Apply status was `created`, `published: true`, `source_preserved: true` and
  `output_independent: true`. Receipt fingerprint is
  `525e5e83406a95b5d8ad86539c801bcf7f4a31d92680a6aeea796f4977405d7f`.
- Removed the created output and every explicitly owned host fixture Scene/Object/Mesh/Material.
  Exact global Scene/Object/Mesh/Material restoration is true. Active `Scene`, active `Camera`,
  empty selection and frame 76 were restored; the Blender file was not saved.
- Synthetic live preview/apply behavior is complete. Formal automatic Skill exposure and its
  no-candidate natural-language refusal remain a smaller separate client-discovery gate.

## Unity LODGroup capability checkpoint - 2026-10-25

- Used the `unity-cli` workflow to connect to the already open
  `C:/Users/jiwoo/UnityProject/GameAssetAI_UnityWorkbench` Editor, Unity `6000.3.9f1`, state
  `ready`. Active `SampleScene` was clean and contained only Main Camera, Directional Light and
  Global Volume; the project currently has no Mesh assets.
- Added `tests/unity/run_lodgroup_capability.cs` and executed it in-memory through the connected
  Editor. It creates only a Unity Preview Scene with synthetic 12/8/4-triangle Meshes, binds one
  Renderer per level to a three-level `LODGroup`, and reads back transition heights
  `0.6/0.3/0.1` plus positive recalculated bounds.
- The first inline eval attempt failed at compilation because command-line quoting stripped C#
  string syntax; no code executed. The maintained `eval_file` fixture compiled and passed.
- The fixture destroys its root and transient Meshes and closes the Preview Scene in `finally`.
  A follow-up hierarchy read confirms `SampleScene` is still active, clean and unchanged. No
  Unity asset, Scene file or import setting was written.
- Exact next gate: define a strict offline Unity LODGroup request for explicitly ordered imported
  Mesh/prefab references and explicit transition heights, then add a read-only candidate before
  any persistent component configuration. Do not infer thresholds or import Blender fixtures
  until that contract exists.

## Unity LODGroup request gate - 2026-10-25

- Added pure offline `gameassetai.unity-lodgroup-request.v1` validation in
  `validate_unity_lodgroup_request.py`. V1 targets one exact normalized `Assets/...prefab`, with
  1-8 explicitly indexed levels, 1-32 exact relative Renderer paths per level and finite strictly
  decreasing user-supplied transition heights in `(0,1)`.
- V1 fixes fading to `NONE`, disables animated cross-fading, requires `EXPLICIT_ONLY`, separates
  preview from apply and refuses any existing LODGroup rather than silently replacing it. It does
  not inspect Unity, choose thresholds, discover names or authorize mutation.
- Five focused offline tests pass for deterministic read-only hashing, level/path/height rules,
  project/prefab path scope, fixed fade/policy and malformed/nonfinite refusal. Per the user's
  request, the broad 241+47 regression suites were not repeated; repository structure validation
  passes.
- Exact next gate: implement a connected-Unity read-only candidate that loads only the exact
  prefab, resolves every relative Renderer path, reports Mesh triangle counts/bounds/materials,
  refuses an existing LODGroup or unsupported prefab/dependency state, and binds a source
  fingerprint. Do not persist a component until that candidate has a representative rollback
  fixture.
