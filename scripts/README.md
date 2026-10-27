# Scripts

Repository-level helper scripts.

These scripts support development and workspace setup.

They are not automatically part of an installed skill unless a skill explicitly packages or references them.

Current tools:

- `apply_scale_copy.py` — explicitly authorized fresh-preview positive-scale independent
  copy apply, coordinate/UV/material/pivot validation and exact owned rollback, no graph
  refresh/export. `--suite scale-copy-skill` loads the three self-contained Skill helpers;
  add `--bundle-dir .local/source-bundles/scale-copy-20260918` or --installed-skills-dir.

- `preview_scale_copy.py` — development analytic positive-scale preview/fingerprint and
  read-only freshness check; requires transform inspector, no apply/copy/graph refresh.

- `inspect_static_transform.py` — read-only raw/reported transforms and local bounds;
  no graph refresh, origin placement, Apply Transform or export certificate. Separate
  `--suite transform-preflight` native test; contract in `docs/transform-preflight.md`.

- `create_workspace.py` — create a personal GameAssetAI-Workspace from the template
- `validate_repo.py` — check required directories, nonempty UTF-8 files, and workspace-template configuration
- `validate_workspace.py` — read-only validation of a workspace and its active profile/project mappings
- `prepare_blender_check.py` — emit exact-source live Blender regression payloads without connecting to Blender
- `package_skill.py` — create non-overwriting portable development source bundles, not installation/releases
- `deploy_skill.py` — byte-verify a copy into an explicit local skill directory; refuse existing deployments
- `update_skill.py` — plan/apply/restore one hash-bound local Skill update; retain both the previous backup and, on restore, the replaced new version
- `inspect_blender_addon_installation.py` — read-only source/installed Add-on version,
  Blender compatibility and per-file hash comparison; generated Python caches are ignored
- `update_blender_addon.py` — hash-bound plan/apply/restore for an existing local Blender Add-on;
  atomically promotes tested source, preserves the previous installation and requires restart
- `inspect_humanoid.py` — read-only explicit humanoid role mapping, ancestry, deform/root and animation-sensitivity inspection; no name guessing or rig edits
- `inspect_mixamo_preflight.py` — read-only exact Mixamo signature and bound-Mesh/transform/animation preparation review; no upload, rig edit or retarget
- `inspect_animation.py` — development source kept byte-identical to the installed read-only Action/binding/NLA/F-Curve inventory helper; explicit root-bone channels only
- `plan_action_copy.py` — validate an explicit source/target Action copy request and bind it to inventory without authorizing a write
- `action_copy.py` — detailed Action content fingerprint plus guarded unbound persistent-copy preview/apply; preserves source references
- `extract_action_range.py` — guarded exact-boundary LINEAR interval copy with retained
  in-range pose markers and optional frame-0/frame-1 rebasing; no key synthesis or source edits
- `inspect_action_loop.py` — read-only explicit-range stored F-Curve endpoint comparison; not evaluated-pose or visual loop certification
- `inspect_root_motion.py` — read-only explicit Object/Bone translation evidence over a named Action range; no root guessing or policy/editing
- `inspect_evaluated_root_motion.py` — integer-frame local-basis/Armature/world root path
  metrics on an owned temporary rig copy; no transfer or engine policy
- `bake_root_translation.py` — guarded explicit-mask/scalar TRANSFER or IN_PLACE root
  location bake into an independent unbound Action
- `compose_retarget_actions.py` — guarded composition of strict rotation-only and
  root-location-only Actions into one independent unbound Action
- `bind_action_empty.py` — guarded EMPTY_ONLY Action binding plus content-bound receipt
  rollback; never replaces or deletes an Action
- `replace_action_current.py` — guarded exact current-Action swap and receipt rollback;
  preserves both Actions and refuses NLA/drivers
- `inspect_retarget_readiness.py` — read-only explicit source/target humanoid mapping,
  rest-bone and source Action coverage comparison; no constraints, pose evaluation,
  retarget or bake
- `aligned_retarget_action.py` — guarded name-only Action copy/path remap for strictly
  aligned explicit humanoid rigs; produces an unbound Action and refuses pose conversion
- `bake_rotation_retarget.py` — development/Skill helper that samples rotation-only
  local matrix bases on owned rig copies and retains one unbound quaternion Action
- `read_profile_context.py` — read exact active Markdown/filename/hashes without inferred rules or external project access
- `validate_skill_deployment.py` — read-only missing/extra/changed file detection between source and installed copies; not runtime discovery
- `validate_2d_action_sequence_request.py` — read-only Action/frame/output expansion that
  reuses the current static v3 style contract and refuses collisions before Blender
- `inspect_2d_action_sequence_candidate.py` — isolated evaluated-range inspection and
  Mesh/Armature/Action fingerprints without changing the source Scene
- `preview_2d_action_sequence_framing.py` — one stable orthographic plan from sampled union
  bounds with an explicit Object-origin anchor
- `stage_2d_action_sequence_source.py` — authorized hidden blend copy containing only the
  reviewed Mesh, Armature and Action; it renders and publishes nothing
- `build_2d_action_sequence_job.py` — authorized collision-safe JSON binding the reviewed
  stage and exact ordered frame plan; it renders and publishes nothing
- `render_2d_action_sequence.py` — isolated background renderer that validates every owned
  temporary frame before publication and rolls back partial publication on failure
- `validate_2d_sprite_sheet_request.py` — read-only exact frame/hash/grid/output contract for
  equal-size RGBA8 PNG inputs with no inferred layout
- `assemble_2d_sprite_sheet.py` — deterministic row-major sheet plus JSON cell/anchor metadata;
  stages both outputs and rolls back partial publication
- `extract_2d_profile_preset.py` — read-only extraction/validation of one optional exact fenced
  2D preset from an already provenance-bound Workspace Profile context; no prose guessing
- `plan_static_optimization.py` — advisory base-diagnostics/explicit-target decisions; no Blender edits, budget inference or optimization method
- `check_affine_uv.py` — pure development UV-map predicate with explicit tolerance; no editing or general UV-quality certificate
- `preview_coplanar.py` — native in-memory whole-planar-mesh preview; loads the state helper/affine guard, creates no Object/Mesh IDs, no apply
- `apply_coplanar.py` — development independent-copy dissolve with source/prediction hash,
  explicit authorization/name and guarded rollback; not general decimation

`--suite coplanar-skill` loads the fourth Skill's self-contained helpers; add
`--bundle-dir .local/source-bundles/separate-tolerances-20260918` to test current fourth packaged bytes.

Use `--installed-skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"` with `--suite all`
or `--suite coplanar-skill` to read actual installed helpers and transmit their source
through MCP. This option is mutually exclusive with `--bundle-dir`; missing/invalid/linked
installed sources refuse rather than falling back to repository helpers. It does not
install, update, connect to Blender or write personal files. Harnesses remain repository
sources; reported source hashes describe decoded source text. This tests installed helper
behavior, not automatic discovery, natural-language selection or an independent client.

`prepare_blender_check.py --suite coplanar-experiment` emits the separate synthetic
structural-simplification/failure-test payload. `all` retains the three installed workflow
regressions. See `docs/coplanar-experiment.md` for native capability evidence/limitations.

`prepare_blender_check.py --suite evaluated-pose-loop` loads the explicit evaluated
pose-loop Skill plus its 16-check synthetic Armature regression. Repository, portable
ZIP and installed-helper origins are supported; the test never retains fixture data.

`prepare_blender_check.py --suite subframe-pose-probe` runs a seven-check development
fixture proving fractional-frame dependency-graph pose evaluation and exact restoration.
It is capability evidence, not a visual-loop Skill or sampling policy.

`prepare_blender_check.py --suite 2d-render-capabilities` runs a read-only 10-check
inventory of render, PNG/RGBA, orthographic-camera, compositor and color-management APIs.
It records Blender 5 compositor/RNA differences but does not render or write a file. See
`docs/2d-render-capability-validation.md`.

`validate_2d_static_render_request.py` is the offline, read-only request gate for one
future static PNG. It requires exact Profile provenance or an explicitly unprofiled
request, orthographic view, lighting/style/palette policies and a collision-free absolute
PNG target. It hashes valid input but does not inspect Blender or authorize rendering.
See `docs/2d-static-render-contract.md`.

`prepare_blender_check.py --suite 2d-render-candidate` loads the request validator,
read-only Blender candidate and orthographic framing planner. Its 22 checks bind separate
source/setup/output fingerprints, detect stale state and unsupported dependencies, verify
square/portrait/landscape framing, fixed-palette eligibility and exact teardown. It creates no Camera or file. See
`docs/2d-static-candidate-validation.md`.

`quantize_rgba.py` provides deterministic opaque fixed-palette RGBA8 mapping and minimal
PNG encoding while preserving alpha. `build_2d_render_receipt.py` rechecks the published
regular PNG and binds its SHA/metrics to the request/source/setup/output/plan chain. These
helpers do not choose game defaults or write receipt files. `quantize_rgba.py` also
provides deterministic explicit-count AUTO reduction using weighted median-cut RGB;
it preserves alpha but does not claim perceptual palette optimality.
The same helper provides an explicit opaque one-pixel 8-neighbor outer ring that never
replaces a source-visible pixel. Palette processing runs first, so the outline can add one
color beyond the requested palette maximum.
It also provides explicit 2-32 step HSV-value banding that preserves alpha and RGB channel
ratios. Value banding runs before palette reduction; no game-specific step count is chosen.

`stage_2d_static_source.py`, `build_2d_staged_render_job.py` and
`render_2d_staged_source.py` implement the first production boundary: a reviewed Mesh is
copied to a hidden blend stage, bound to a collision-safe JSON job, and rendered only in
a background Blender to a new PNG. `--suite 2d-source-stage` tests repository staging;
`--suite 2d-static-pixel-skill` tests the packaged/installed Skill staging helpers.
`tests/rendering/run_2d_source_stage_load.py` validates the full stage/job/render/receipt
path and exact temporary-file teardown.

`stage_2d_action_sequence_source.py`, `build_2d_action_sequence_job.py` and
`render_2d_action_sequence.py` form the separate Action-sequence path. It uses one stable
range-wide camera, validates all frame PNGs before publication, publishes without overwrite,
and removes partial output if publication fails. See
`docs/2d-action-sequence-skill-validation.md`.

`validate_2d_render_batch_request.py`, `build_2d_render_batch_job.py` and
`run_2d_render_batch.py` coordinate explicit static and Action child requests. They bind every
stage/job/helper hash, require one output directory and fixed list-order/all-or-nothing policy,
and roll back verified earlier outputs when a later child fails. They never infer directions or
Actions. See `docs/2d-render-batch-contract.md`.

`validate_2d_impostor_bundle_request.py` is the offline first gate for static multi-pass
impostors. It composes current explicit COLOR/NORMAL/DEPTH requests, requires identical
Scene/Object/view/resolution and pass order per view, collision-free same-directory outputs,
a new manifest target and fixed all-or-nothing policy. It does not inspect Blender, calculate
shared framing, publish a manifest or support Object-ID/animation. See
`docs/2d-impostor-bundle-decision.md`.

`preview_2d_impostor_shared_framing.py` reruns every child candidate in Blender and binds one
base-Mesh orthographic plan per view to all of that view's passes without creating a Camera.
`validate_2d_impostor_result_manifest.py` then verifies a proposed ordered result, actual PNG
hashes/sizes, plan bindings and child receipt hashes without writing the JSON target. Neither
helper stages or renders children, coordinates rollback or publishes the manifest.

`build_2d_impostor_bundle_job.py` binds the fresh request, shared preview, staged child jobs
and exact helper bytes. `run_2d_impostor_bundle.py` executes those children sequentially in
isolated Blender processes, validates every receipt and PNG, rolls back only unchanged outputs
created by the attempt on failure, validates the result manifest and publishes that manifest
last. It never removes a changed output or mutates the interactive Scene.

`validate_2d_silhouette_mask_request.py` and `derive_2d_silhouette_mask.py` form the
separate alpha-derived mask path. They bind one RGBA8 source hash, explicit color/policy
and new target, then stage, verify and publish without overwrite. This is not a Blender
normal/depth/material mask. See `docs/2d-silhouette-mask-validation.md`.

`validate_2d_material_mask_request.py`, `inspect_2d_material_mask_candidate.py`,
`preview_2d_material_mask_framing.py`, `stage_2d_material_mask_source.py`,
`build_2d_material_mask_job.py` and `render_2d_material_mask.py` implement the separate
static base-Mesh material-slot mask path. An isolated ID-shader render retains non-target
occlusion before conversion to the requested two-color RGBA8 PNG. See
`docs/2d-material-mask-validation.md`.

`validate_static_collider_request.py` is the pure first gate for explicitly named existing
static collider Mesh candidates. It separates triangle-mesh and convex-candidate intent,
requires base geometry/world comparison/read-only policy, validates a scale-relative convexity
tolerance and hashes the exact request. It does not inspect Blender, generate a collider,
configure an engine or define an LOD. See `docs/static-collider-lod-decision.md`.

`inspect_static_collider_candidate.py` resolves only those exact Blender base Meshes. It
reports topology, world bounds and bounds relationships, and performs a scale-relative
closed-half-space convexity check only for explicit convex candidates. Dependencies and
invalid convex candidates are blockers; the helper never edits Blender or certifies engine
acceptance.

`validate_static_lod_chain_request.py` is the pure gate for an explicitly ordered existing
LOD chain. V1 requires 2-8 contiguous levels beginning at zero, unique exact Object names,
base-Mesh/world/read-only scope, identical world matrices and strictly decreasing base
triangulation. It does not inspect Blender, infer names, generate LODs or define engine screen
thresholds. See `docs/static-collider-lod-decision.md`.

`inspect_static_lod_chain_candidate.py` resolves only the named base Meshes and binds their
geometry/transforms to a source fingerprint. It reports base triangle counts and ratios,
world bounds/center/extent relations and material-slot equality. Unsupported dependencies,
nonidentical world matrices and nondecreasing triangle counts are blockers; no Mesh is edited.

`validate_static_lod_copy_request.py` is the offline first gate for a future independent-copy
LOD operation. It requires explicit unused output Object/Mesh names, a bounded collapse ratio,
base-Mesh-only dependency refusal, exact transform copying, source preservation, copied UV
layers and separate preview/apply authorization. It does not inspect Blender or authorize a
copy. See `docs/lod-generation-experiment.md`.

`preview_static_lod_copy.py` binds that request to exact source/setup fingerprints, refuses
existing output names and unsupported source dependencies, and evaluates the requested
Decimate ratio only on disposable independent Scene/Object/Mesh IDs. It reports actual
triangle, UV/material and world-bounds changes, proves the source stayed stable, removes all
preview IDs, and never creates the requested persistent output or authorizes apply.

`apply_static_lod_copy.py` requires explicit authorization plus the reviewed request, source,
setup and preview fingerprints. It re-runs the transient preview immediately before creating
one exact named independent Object/Mesh pair, validates the applied result against the preview,
and rolls back only its ownership-tagged IDs on failure. It does not choose ratios, overwrite
names, modify the source, define Unity thresholds or certify visual quality.

`validate_unity_lodgroup_request.py` is the offline first gate for configuring an existing
explicit prefab hierarchy as a Unity LODGroup. V1 requires normalized explicit Renderer paths,
strictly decreasing user-supplied transition heights, no fading, no existing LODGroup and a
separate preview/apply authorization. It does not inspect Unity, infer thresholds or mutate an
asset.

The parallel `validate_2d_object_mask_request.py` through `render_2d_object_mask.py`
workflow masks one exact target Mesh against only explicitly named occluder Meshes. It
fingerprints and stages those Objects, frames their union, preserves occlusion with staged
ID shaders and excludes every unlisted Scene Object. See `docs/2d-object-mask-validation.md`.

`validate_2d_normal_pass_request.py` is the offline-only first gate for a future normal
pass. It fixes camera-right/up/back axes, shading-normal source, signed-XYZ-to-UNORM RGB,
transparent-black background, pixel sampling and RGBA8 no-overwrite output. It does not
inspect or render Blender. See `docs/2d-normal-pass-contract.md`.

`inspect_2d_normal_pass_candidate.py` adds a read-only base-Mesh dependency/fingerprint
gate and flat-face camera-basis reference samples. These validate axis signs and encoding
before a future shader renderer; they do not claim interpolated output pixels.

Use Python 3.10+; no third-party dependencies are required. Keep these scripts together
because creation/repository validation share `validate_workspace.py`.

Development-only pivot experiment:
`preview_pivot_copy.py` predicts an explicitly supplied base-mesh local origin and binds
the supported snapshot/effective tolerance/reported world; `apply_pivot_copy.py` requires
freshness/authorization/name and changes independent copies only. Development preview
loads transform/scale-preview helpers; apply is now self-contained apart from pivot preview.
`prepare_blender_check.py --suite pivot-preview` tests development sources and
`--suite pivot-skill` tests the self-contained sixth Skill source/ZIP/installation.
See `docs/pivot-copy-validation.md`; no automatic pivot policy,
original save/export, dependency refresh or engine certificate is provided.

`inspect_static_export_context.py` is a development-only read-only exporter/context
inventory; `prepare_blender_check.py --suite export-context` tests its native behavior.
It does not invoke an exporter or choose a game-specific format, axes or units. See
`docs/static-export-preflight.md`.

`prepare_blender_check.py --suite fbx-probe` emits an **isolated development test** that
writes unique FBX artifacts under ignored `.local/validation/`, reimports one into a
separate Blender Scene, verifies bounded behavior and no-overwrite publication, then
removes only exact test-owned artifacts. `promote_export_artifact.py` hard-links a validated
same-directory staged file to a new target or fails closed; it never removes the stage.
It does not export to an existing Unity project or define production settings.

`validate_static_fbx_request.py` is a development-only read-only validator for a
fully explicit static FBX request. It refuses missing axes/scale/flags, a pre-existing
target or `.meta`, linked parents and unsupported copy-mode sidecars. It neither reads
game-specific rules from Markdown nor exports/authorizes a file. See
`docs/unity-export-contract.md` and `tests/scripts/test_static_fbx_request.py`.
`inspect_static_fbx_candidate.py` checks the same request hash against the current
Blender Scene/Object and exporter RNA/poll; it blocks preservation dependencies and
obvious texture-node sidecar risk, but does not recheck or write the destination.

`export_static_fbx_staged.py` is the next development-only texture-free boundary.
Given the exact request/preflight/candidate plus explicit authorization, it rechecks
the Blender source and target, writes a unique same-directory stage, verifies one binary
FBX and atomically publishes without overwrite. `prepare_blender_check.py --suite
fbx-staged` runs its synthetic 10-check regression. It is not an installed Skill and
does not support `COPY`, texture sidecars, rigs or animations.

`prepare_unity_static_fbx_check.py` validates an explicit existing Unity `Assets/...`
FBX path/hash and expected static import metrics, then creates a no-overwrite C# file for
Unity CLI `eval_file`. The generated check optionally refreshes only that asset, uses a
temporary Preview Scene, verifies topology/UV/material/clip/transform/bounds expectations
and active Scene preservation. See `docs/unity-static-fbx-validation.md`.

`prepare_unity_sprite_import_check.py` validates an explicit existing Unity `Assets/...`
PNG path/hash and exact Sprite importer/slicing expectations, then creates a no-overwrite
C# file for Unity CLI `eval_file`. It only observes settings and imported Sprite metadata;
it never edits importer settings. See `docs/unity-sprite-import-validation.md`.

Run from the repository root:

```bash
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
python -B -m unittest discover -s tests/scripts -p "test_*.py" -v
```

Script paths are resolved from the script, not the working directory. A relative workspace
target is resolved from the caller's working directory. Use an absolute target for clarity.
See `docs/workspace-contract.md` for creation, `--force` risks, and Profile examples.
These tools do not install MCP, manage Blender, or access mapped external projects.
See `docs/skill-packaging.md` for payload/bundle usage and their verification boundaries.
