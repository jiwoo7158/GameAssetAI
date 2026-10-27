# Tests

GameAssetAI should be developed against real Blender behavior.

This directory stores:

- test plans
- test-scene descriptions
- regression checklists
- later, small redistributable fixture files when licensing permits

Do not commit third-party game assets merely for convenience.

## Suggested test groups

```text
tests/
├─ workspace/
├─ blender-scene/
├─ static-mesh/
├─ rigging/
├─ animation/
└─ export/
```

Add groups only when real tests exist.

## Executable offline tests

```bash
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
python -B -m unittest discover -s tests/scripts -p "test_*.py" -v
```

`tests/workspace/test_foundation.py` uses standard-library unittest and isolated temporary
repositories/workspaces. It tests creation, overwrite/preservation, unsafe targets,
links/hard links, collisions, simulated I/O failures, JSON/Profile validation, mapping
structure, repository failure cases, and CLI behavior from another working directory.
Temporary fixtures are automatically cleaned; no user's game project is read or changed.
If real symlink creation is unavailable, those checks are explicitly skipped, not passed.
Use a disposable writable temp directory outside the source tree when sandbox restrictions
prevent access to the OS temp folder; alternatively run the isolated suite with approval.

`tests/scripts/` tests payload preparation, byte-preserving repeatable source bundles,
and no-overwrite local deployment, including simulated failure cleanup.
Profile context/temporary switch recovery tests are included in the Workspace suite;
read-only deployment drift tests are included in the scripts suite. Live evidence for
actual Workspace switching is `docs/profile-workflow-validation.md`.

## Executable Blender tests

`--suite humanoid-inspection` builds only an owned synthetic Armature fixture and tests
explicit role mapping, hierarchy, missing/duplicate bones, deform/animation reviews,
Edit Mode refusal and exact teardown. It does not rig, retarget or certify Mixamo/Unity.
See `docs/humanoid-inspection-validation.md`.

`--suite mixamo-preflight` adds an owned Mixamo-style Armature and bound Mesh, testing
exact signature mapping, missing vertex-group and transform reviews, wrong-prefix/Edit
Mode refusal and teardown. See `docs/mixamo-preflight-validation.md`.

`--suite animation-inventory` creates an owned animated Armature and verifies 11 bounded
behaviors: Action/F-Curve/key inventory, current binding, NLA strip, driver, unused
Action, explicit root channel, no root guessing, invalid-root refusal, JSON/frame
preservation and exact teardown. The same suite accepts repository, ZIP or installed
Skill helpers. See `docs/animation-inventory-validation.md`.

`--suite action-copy-plan` verifies nine read-only request/reference/naming checks.
`--suite action-copy` verifies eight Blender apply checks for authorization, freshness,
collision refusal, independent content copy, unchanged source/current/NLA references,
unbound persistence, context preservation and teardown. See
`docs/action-copy-validation.md`.

`--suite action-range-extraction` verifies 17 Blender checks for strict exact-boundary
LINEAR interval extraction, authorization and boundary/interpolation/modifier/stale/
collision/unknown-policy refusal, exact key/marker retention, frame-0/frame-1 rebasing,
source/reference preservation and teardown.
See `docs/action-range-extraction-validation.md`.

`--suite action-loop` verifies nine read-only Blender checks covering matching and
mismatching stored components, explicit tolerance, boundary keys, Cycles inventory,
invalid/missing inputs, frame/inventory preservation and teardown. See
`docs/animation-loop-validation.md`.

`--suite root-motion` verifies ten read-only Blender checks for explicit bone translation,
axis evidence, non-root exclusion, rotation review, Object/Bone distinction, bad mapping,
range and slot refusal, frame/inventory preservation and teardown. See
`docs/root-motion-inspection-validation.md`.

`--suite evaluated-root-motion` verifies 11 Blender checks for integer-frame root-bone
evaluation in local-basis, Armature and world space, including a zero-net/nonzero-path
loop, static Object scale, constraint/step/slot/Object-motion refusal, source preservation
and exact teardown. See `docs/evaluated-root-motion-validation.md`.

`--suite evaluated-pose-loop` verifies 16 Blender checks for explicit evaluated pose-bone
endpoint and finite-difference seam-velocity comparison, per-bone/aggregate results,
bounded refusals, source preservation and exact teardown. See
`docs/evaluated-pose-loop-validation.md`.

`--suite subframe-pose-probe` verifies fractional-frame LINEAR pose evaluation at 1.25 and
1.75, Action preservation and exact owned teardown. See
`docs/subframe-pose-evaluation.md`.

`--suite 2d-render-capabilities` verifies 10 read-only checks for PNG/RGBA output APIs,
orthographic camera controls, Blender 5 compositor access and color-management controls.
It creates no render, image, node graph or file. See
`docs/2d-render-capability-validation.md`.

`tests/scripts/test_2d_static_render_request.py` provides nine offline regressions for
the exact Profile/view/lighting/style/output contract, stable request hashing and
no-overwrite PNG path checks. It does not run Blender or certify rendered pixels. See
`docs/2d-static-render-contract.md`.

`tests/rendering/run_2d_background_render.py` runs only in a separate Blender
`--background --factory-startup` process. Its 18 checks validate a v1 request/candidate,
apply its fingerprint-bound framing plan, render a 32×24 RGBA8 PNG, publish without
overwrite, decode alpha/framing pixels, apply a fixed palette, bind a receipt, compare a
repeated render, refuse collision and remove all unique files exactly. Pixel arrays match across the repeated render even though
PNG container bytes do not. It does not touch the open interactive Blender or consume a production asset. See
`docs/2d-static-render-validation.md`.

`tests/rendering/run_2d_source_stage_load.py` uses a two-facet ridge under the owned
off-axis light. Its full 15-check source/portable/installed path requires at least two of
the requested value bands, currently `[85,170]`, while retaining palette, outline,
receipt, collision and exact teardown checks.

`--suite 2d-render-candidate` verifies 22 live Blender checks for request/source/setup/
output fingerprint binding, dependency and stale-state refusal, world bounds,
orthographic square/portrait/landscape framing, fixed-palette eligibility and exact fixture teardown. It is a read-only plan,
not a render or Camera creation workflow. See `docs/2d-static-candidate-validation.md`.

`tests/scripts/test_quantize_rgba.py` has 13 palette/shading/outline/PNG tests;
`tests/scripts/test_2d_render_receipt.py` has four provenance/artifact receipt tests.

`tests/scripts/test_2d_action_sequence_request.py` has seven offline tests for exact
Action/slot/range input, stable frame-to-file expansion, current static-v3 reuse,
all-new output paths and narrow stable-framing policies. It does not inspect Blender or
claim that the Action can be evaluated.

`--suite 2d-action-sequence-candidate` verifies 28 Blender checks for exact binding and
slot rules, evaluated range bounds, stale-state refusal, stable framing, independent staging,
hash-bound job creation, collision refusal and exact context/ID/file teardown.
`tests/rendering/run_2d_action_sequence_stage_load.py` independently reopens the hidden
blend in factory-startup Blender and passes 20 checks for copied Action binding, Armature
modifier retarget, fractional FPS, matching per-frame deformation, stable dimensions/anchor,
ordered receipt hashes, collision refusal and exact teardown. It deliberately fails the
second publication link once and verifies the first published file is rolled back. The same
suite passes with repository, packaged-Skill and Workspace-installed helpers.

`tests/scripts/test_2d_sprite_sheet.py` has eight offline regressions for explicit frame order,
cell placement, transparent padding, bottom-left anchor conversion, source/output hashes,
authorization and stale-preview refusal, collision/layout/format failures and deliberate
PNG-before-JSON publication rollback. They also cover v2 Profile provenance and v1 compatibility.
It does not invoke Blender or Unity.

`tests/scripts/test_2d_profile_preset.py` has five offline tests for absent Profile/defaults,
one exact fenced JSON preset, static-v3 reuse, provenance requirements and malformed/duplicate/
unknown value refusal. `test_2d_profile_preset_resolution.py` adds six tests for complete
purpose-specific settings, fresh binding, change/absence refusal and valid static/Action request
construction. `tests/rendering/run_2d_profile_preset_load.py` verifies the same no-write path
against packaged and installed helper roots.

`test_2d_render_batch_request.py`, `test_2d_render_batch_job.py` and
`test_2d_render_batch_runner.py` cover explicit mixed child planning, Profile binding,
cross-child collisions, bounded outputs, hash-bound job creation and all-or-nothing rollback.
`tests/rendering/run_2d_render_batch.py` performs the mixed static/Action Blender 5.0.1 success,
deliberate later-child process failure and exact teardown regression.

`--suite root-translation-bake` verifies 12 Blender checks for explicit TRANSFER and
IN_PLACE root-location-only Actions, authorization/staleness, mask/scale/constraint
refusals, linear integer keys, preservation and teardown. See
`docs/root-translation-bake-validation.md`.

`--suite retarget-action-composition` verifies nine checks for strict rotation/location
input contracts, preview/authorization/staleness/nonlinear refusal, combined unbound
output, preservation and teardown. See `docs/retarget-action-composition-validation.md`.

`--suite action-binding` verifies 14 checks for EMPTY_ONLY binding, authorization and
stale/occupied refusal, exact Action/slot references, tamper-resistant receipt rollback,
both animation-data restoration branches and exact teardown. See
`docs/action-binding-validation.md`.

`--suite action-replacement` verifies 16 checks for exact current-Action replacement,
authorization/stale/wrong-current/NLA/driver refusal, reference and content preservation,
receipt tampering, changed-source rollback refusal, exact restoration and teardown. See
`docs/action-replacement-validation.md`.

`--suite retarget-readiness` verifies 11 read-only Blender checks over separate synthetic
source/target humanoid Armatures and a bound source Action: mapping completeness, rest
metrics, mapped/unmapped Action coverage, transform preservation review, same-rig,
incomplete-map, unbound-Action and invalid-slot behavior, unchanged animation inventory
and exact teardown. See `docs/retarget-readiness-validation.md`.

`--suite aligned-retarget` verifies 16 Blender checks for a strict name-only Action
remap copy: preview/authorization/freshness, transform/rotation/constraint/rest/collision
refusals, unbound fake-user output, path/slot/group remapping, stored-value preservation,
unchanged source/target data and exact teardown. It does not test pose-space conversion
or ordinary Mixamo retargeting. See `docs/aligned-retarget-validation.md`.

`--suite rotation-retarget-bake` verifies 12 checks using explicit humanoid rigs with
different rest directions: preview/auth/stale and transform/constraint/step refusals,
temporary-copy quaternion baking, target paths, integer linear keys, source/target
preservation and exact teardown. It excludes translation, scale, root motion and
world-space visual certification. See `docs/rotation-retarget-bake-validation.md`.

Current scale suite **90 checks** includes tilted synthetic normal/tangent/bitangent,
isolated overflow/no-ID probes and linked UV/scale/Mesh reassignment rollback. Mirrored
apply helper and installation were narrowly fixed. Tiny positive preview is not successful
apply or conditioning certification. Fifth host use/apply/restore passed by user report.
See `docs/transform-preflight.md` for latest archive and direct evidence.

`--suite pivot-preview` (development helpers) and `--suite pivot-skill` (sixth Skill
source/ZIP/installed helpers): **63 checks each** for explicit local-point origin
prediction/freshness, independent-copy apply/refusal/rollback, two faces/materials/UV
layers, shared source Mesh preservation and dependency guards. No automatic pivot policy
or client-routing certificate.
See `docs/pivot-copy-validation.md`.

`--suite export-context` is a separate read-only development preflight: 34 Blender
checks for current FBX/glTF operator RNA names, static base inventory, dependency
reviews and no assumed engine/Profile policy. It performs no export or save. See
`docs/static-export-preflight.md`.

`--suite fbx-probe` creates only owned temporary synthetic FBX files and reimports one
into another owned Blender Scene; 23 checks cover model scope, roundtrip base geometry,
UV/material reference, reported world positions, native overwrite hazard, atomic
no-overwrite publication/collision and exact cleanup. Explicit axes/scale are test
inputs, not engine defaults. A **separate** single-fixture Unity import is recorded in
`docs/unity-import-validation.md`; neither test certifies production export.

`tests/scripts/test_static_fbx_request.py` exercises the read-only explicit request
guard before any new static FBX workflow. It does not run Blender or Unity and does
not certify that requested axes/units match a game. See `docs/unity-export-contract.md`.
The `export-context` native suite also checks the request-hash-bound Blender candidate
review, dependency/texture refusals and unchanged original Scene; it still exports
nothing and never authorizes a file write.

`--suite fbx-staged` is the narrow texture-free write regression: 10 Blender checks
cover explicit authorization, request/fingerprint freshness, verified single-file
publication, target and late `.meta` collision refusal, no stage leak and exact cleanup.
It writes only under the supplied repository `.local/validation` root and is not an
installed Skill or textured export workflow.

`tests/scripts/test_unity_static_fbx_check.py` covers strict request/path/hash/expectation
validation, duplicate/non-standard JSON refusal, generated C# escaping and no-overwrite
output. Live Unity positive and intentional mismatch evidence is recorded in
`docs/unity-static-fbx-validation.md`.

`tests/scripts/test_unity_sprite_import_check.py` covers the strict PNG path/hash and
Sprite import/slicing expectation contract, native generated C# arrays, rectangle/pivot
guards, duplicate/non-standard JSON refusal and no-overwrite output. Live Unity execution
passed one explicit equal-cell fixture; see `docs/unity-sprite-import-validation.md`.

`tests/scripts/test_2d_silhouette_mask.py` covers hash-bound read-only preview, exact
binary and alpha-preserving output, collision/staleness refusal, post-link rollback and
concurrent-change retention. See `docs/2d-silhouette-mask-validation.md`.

`tests/scripts/test_2d_material_mask_request.py` covers the exact explicit request boundary.
`tests/rendering/run_2d_material_mask.py` verifies Blender 5.0.1 candidate/framing freshness,
independent staging, material-slot ID rendering with non-target occlusion, binary RGBA8
publication, collision refusal, receipt binding and exact file teardown. See
`docs/2d-material-mask-validation.md`.

`tests/scripts/test_2d_object_mask_request.py` covers explicit target/occluder identity,
bounded unique lists, sampling and output policy. `tests/rendering/run_2d_object_mask.py`
uses target, closer occluder and unlisted Object fixtures to prove union framing, source
freshness, requested-only staging, occlusion, binary output, collision refusal and teardown.
See `docs/2d-object-mask-validation.md`.

`tests/scripts/test_2d_normal_pass_request.py` covers the offline camera-basis normal-pass
contract, including axis meaning, source/space/encoding refusal, sampling and RGBA8 collision
policy. See `docs/2d-normal-pass-contract.md`.

`tests/rendering/run_2d_normal_candidate.py` is a read-only Blender 5.0.1 tilted-triangle
probe. It verifies camera components `[+,+,-]`, encoded RGB `[201,201,54]`, no PNG and
preserved Scene count.

`tests/rendering/run_2d_normal_stage_render_probe.py` reopens an owned blend stage and
renders a back-facing flat triangle plus smooth sphere. Thirteen checks document Blender's
face-forward shading-normal flip, four-value direct-PNG byte drift, and the successful owned
32-bit OpenEXR fallback. CPU conversion produces one exact flat color
`[54,54,201,255]`, preserves 282 smooth values and removes stage/EXR/PNG files exactly.

`tests/rendering/run_2d_normal_pass.py` exercises the complete reviewed candidate, framing,
independent Mesh stage, hash-bound job, 32-bit float OpenEXR render, deterministic CPU RGBA8
publication, collision refusal and exact teardown. Repository and installed Skill helpers
both pass eleven checks; the flat back-facing fixture encodes exactly `[54,54,201,255]`.

`tests/scripts/test_2d_depth_pass_request.py` covers the offline static camera-linear depth
contract: exact base-Mesh vertex-bound normalization, near-black/far-white RGBA8 encoding,
alternative-space/source/range refusal, fixed sampling and new-file collision policy.
`tests/rendering/run_2d_depth_candidate.py` adds exact range/reference and zero-span checks;
`run_2d_depth_stage_render_probe.py` proves float-EXR gradient fidelity; and
`run_2d_depth_pass.py` covers the complete staged publication and teardown pipeline. See
`docs/2d-depth-pass-contract.md`.

`tests/scripts/test_2d_object_id_request.py` covers the offline multi-Object color-ID pass:
2-to-63 explicit members, unique names and quantized RGBA8 colors, no Scene inference,
fixed sampling and new-file collision policy. `tests/rendering/run_2d_object_id_candidate.py`
proves ordered membership, unlisted exclusion and dependency blocking; and
`run_2d_object_id.py` covers independent staging, internal float IDs, exact CPU color
mapping, mutual depth occlusion, collision refusal and teardown. See
`docs/2d-object-id-pass-contract.md`.

Earlier transform suite was 82 checks, including 26 positive-scale apply/refusal/rollback
checks. `--suite scale-copy-skill` tests packaged fifth-Skill helpers against the same
synthetic harness. Source/actual ZIP/installed helper runs each pass; host automatic
discovery/instruction-following remain separate. Earlier 56-check description is historical.

`--suite transform-preflight` is a separate development-only transform snapshot suite:
56 native checks pass (24 snapshot/refusal/teardown, 6 copy-scale capability and 26 analytic
preview/freshness checks)
for explicit target, finite state, reflected/nonuniform/singular
matrices, parent/Constraint/bindings, Edit Mode preservation and exact owned teardown.
The older snapshot stage was not an apply Skill; the new positive-scale source Skill
remains separate from general Apply Transforms and engine export certification.

`tests/blender-scene/run_inspection.py` and `tests/static-mesh/run_diagnostics.py` run
inside Blender, not ordinary Python. Generate a self-contained payload using
`python -B scripts/prepare_blender_check.py --suite all` and pass its JSON `code` to
the exposed MCP execution tool after checking Scene/addon status and test authorization.
See `docs/skill-packaging.md` for ZIP-helper regression and preservation requirements.
`tests/static-mesh/run_loose_cleanup.py` is the third sequential suite; it tests preview,
stale-fingerprint refusal and cleanup only on independent invocation-owned copies.
The latest earlier-three ZIP-helper run passed 166 checks; it does not prove client routing.
`--suite coplanar-skill --bundle-dir .local/source-bundles/separate-tolerances-20260918` runs
the fourth self-contained Skill's separate synthetic capability/preview/apply suite:
162 checks pass, including disconnected-component scope and retained seam tests.
`coplanar-experiment` tests development helper mirrors instead.

`--installed-skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"` reads actual installed
helpers instead of repository/ZIP helpers, with missing/invalid/linked resources refused.
Latest direct installed runs: earlier three 169 checks, fourth 162, total 331 pass.
This is explicit source execution, not host automatic Skill selection evidence.

Deployment failure tests cover interrupted partial writes and corrupted readback,
exact removal of invocation-owned paths, unchanged source bytes and untouched sibling
personal Skills. Hash-bound update tests additionally cover read-only planning, retained
byte-exact backup, drift/collision refusal, injected promotion rollback, non-destructive
restore and CLI plan/apply/restore. They do not certify concurrent writers, hard process
interruption or client catalog refresh.

These tests do not claim installed-client integration is stable. Actual evidence is in
`docs/inspection-validation.md` and `docs/static-mesh-validation.md`; remaining runtime
checks and their evidence requirements are in `docs/blender-verification.md`.
