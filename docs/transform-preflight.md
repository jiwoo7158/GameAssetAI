# Read-only pivot/transform preflight — 2026-09-18

## Latest client / shading / numerical evidence

User confirmed `blender-prepare-positive-scale` use on Blender 5.0.1: preview with explicit
0.00001 tolerance, matching verify fingerprint, created independent copied Object/Mesh,
source scale (2,3,0.5) unchanged and copied scale (1,1,1); world/pivot error zero, topology/
UV/material references retained. Only synthetic Scene/Object/Mesh/material removed;
starting/restored state differences none. This completes the fifth-Skill host outcome gate
by user report, not raw independently captured client-build/routing trace. Do not repeat it.

At the initial shading/numerical checkpoint, unchanged installed helpers passed 87 checks.
Five added checks: tilted
triangle with rotated/nonuniform positive scale retains transformed native normal and
tangent directions within explicit fixture-only vector tolerance 1e-5, bitangent signs
equal; predicted coordinate overflow refuses, numerical probes create no IDs. Tangents
are calculated/freed only on synthetic Meshes, never original user data. These are fixture
results, not blanket smooth/custom-normal/tangent/render/engine appearance certification.

Isolated raw-channel scale 1e38 predicts nonfinite coordinates and is refused. Scale
(1e-30,1,1) returns preview; no apply was attempted and conditioning was NOT certified.
Absolute coordinate residual alone is not a conditioning or shading-readiness test.
The first probe used extreme matrix decomposition and could contaminate stored transform
channels; final probes restore raw channels independently and avoid that confound.
Raw final response/hashes: ignored `.local/validation/scale-boundaries-isolated-20260918.json`.
That checkpoint changed the harness and documentation only; subsequent fix follows.

## Final linked-output validation correction

Injected UV mutation after actual link returned `created` on the old apply helper. Final
validation now rechecks Object/Mesh independence, exact unit scale, topology/edge/UV/material
surface, non-scale raw channels and parent-inverse before returning success. Injected linked
UV, scale and source-Mesh reassignment each refuse and roll back owned copies completely.
This guards the demonstrated final-state gap, not arbitrary concurrent callbacks.

Expanded suite: **90 checks pass** using development sources, actual new ZIP and actual
Workspace installation. Existing installed suites separately pass 169 + 162 checks;
total distinct latest installed checks **421**, not repeated-origin cumulative counts.
During old-helper reproduction the failing harness left owned synthetic IDs; exact
ownership/reference checks removed only those IDs. Harness now tracks unexpected successful
copies before assertions so teardown can retain the original assertion. All final runs
restore original fingerprint and ID lists. Original Scene was never saved/exported.

Mirrored apply helpers changed; only that installed helper was patched after old SHA check
and byte-exact base64 backup in `.local/deployment-backups/scale-postlink-20260918/`.
Other installed Skills and personal settings/Profiles/projects remain unchanged.
Latest archive `.local/source-bundles/scale-postlink-20260918/blender-prepare-positive-scale.zip`
SHA-256 `4a0035da669209d6bc9f510dce913f50838c43e6f8139e2cca1db264e731c1a7`.
Raw ZIP/installed response/source hashes: `.local/validation/scale-postlink-20260918.json`.
Earlier archives and check counts below are historical, not current deployment identifiers.

## Latest copy-apply / source Skill checkpoint

`scripts/apply_scale_copy.py` now implements the narrowly guarded positive-scale operation.
Three self-contained mirrored helpers form `skills/blender-prepare-positive-scale/`;
source-equality regression prevents drift. Skill Creator guided scope/authorization and
UTF-8 quick validation passed. This is a tested development workflow, not general Apply
Transforms or production/engine certification. Earlier no-apply statements below are history.

Require explicit authorization, globally unused <=63 UTF-8 byte Object name and fresh
preview hash/effective tolerance/Scene. Empty/unrelated animation data, drivers or constraints
block apply conservatively via file-wide native ID inspection. No-change still requires
freshness/authorization/name checks and creates no IDs. No active Profile defaults are added.

Independent Object/Mesh copies only; shared material references. Native Mesh.transform
scales copied vertices. Output scale is exactly one; other raw channels, parent-inverse,
topology/edge flags/UV contents/layer activity/material slot links/references, original
reported-world coordinates and pivot are checked. Source hash, surface and reported-world
matrix remain unchanged before/after link. Reported source world/basis inconsistency refuses
rather than forcing dependency refresh. No original save/export.

Actual testing found cached copied matrix_world stale after scale-channel assignment;
the initial implementation refused/rolled back rather than retaining incorrect output.
Setting only the new unparented copy's matrix fixes that. Matrix decomposition introduced
sub-unit scale rounding for rotated input; restoring exact scale/location/Euler channels
then revalidating fixed this second failure. No scene-wide graph update was used.

Write failure, wrong copied coordinates, copied NaN and error after actual link remove
only exact newly owned safe Object/Mesh IDs. Changed ownership/users returns cleanup
unverified and requires inspection, not blind retries. Numerical comparisons reject NaN
instead of letting `NaN > tolerance` silently pass. Arbitrary concurrent callbacks, evaluated
geometry, numerical conditioning, normals/tangents and procedural material appearance are
NOT certified. Reflected/singular/dependent sources remain out of scope.

Source, actual ZIP and actual installed helpers each pass the same 82 native checks:
56 prior snapshot/preview/capability checks + 26 copy-apply/refusal checks. Rotated/translated
and nonuniform positive input, two UV layers/layer activity, source independence, missing/
stale hash/auth/name, unrelated Constraint/empty animation, unit no-change, failed write/
corrupt/NaN/post-link rollback and original exact fixture teardown passed. Current preview
hash also binds parent-inverse and active/render UV state; older hashes require re-preview.
Raw ZIP/installed response/hash artifact: ignored `.local/validation/scale-apply-20260918.json`.

```bash
python -B scripts/prepare_blender_check.py --suite scale-copy-skill --bundle-dir .local/source-bundles/scale-copy-20260918
python -B scripts/prepare_blender_check.py --suite scale-copy-skill --installed-skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"
```

Archive SHA `3bafd45ed790168308068760d67ac7e87c995195783e62679c1fac3b7d7a1671`.
The bundle directory also contains inspector for the harness, not a full five-archive set;
runtime Skill requires no other installed Skill. Approved no-overwrite first installation
added only the new Skill to the existing Workspace. Profile/project/MCP settings unchanged.

### Remaining host-only check

**Completed by user report above. Do not repeat this historical request as a blocker.**

This session explicitly tested installed code but its supplied catalog does not expose
the new Skill. Verify its instruction-led use in the existing Workspace conversation;
do not reinstall or repeat older Skill/Profile/Cube gates. One synthetic-only request:

`원본 Scene은 수정하지 마. 별도 합성 Scene에 UV·재질이 있는 단순 메시와 양수 스케일
(2, 3, 0.5)을 만들고, 좌표 허용 오차 0.00001로 미리보기한 뒤 fingerprint가 일치하는
독립 복사본에만 스케일을 적용해줘. 원본 보존, 복사 Mesh 독립성, 복사본 스케일 1,
좌표·피벗·UV·재질 유지 여부를 검증해줘. 끝나면 테스트 데이터만 제거하고 시작 상태를
복원해줘. 사용한 Skill과 실제 호출 결과를 알려줘.`

The explicit tolerance is test input, not a common game default. Unexpected/uncertain
cleanup stops mutation. This test does not require engine import or original Cube edits.

## Latest analytic scale-preview checkpoint

`scripts/preview_scale_copy.py` adds development-only preview and read-only freshness
verification, NOT an apply API. Load inspect_static_transform first in the same namespace.
`preview_scale_copy(object_name, *, geometry_tolerance, scene_name=None)` requires explicit
positive finite tolerance. First supported scope: positive scale, XYZ rotation, no delta
transforms, parent/children, modifiers/constraints, rigs/groups, Shape Keys/animation,
linked/override data, custom normals or unsupported generic attributes. Polygon surface
and finite UV data required (UV layers themselves are optional). Reflection/zero scale
remain refused despite the earlier synthetic native capability experiment.

Preview predicts scaled local vertices, unit scale and a location/rotation-preserving
matrix basis. Matrix-basis transformed positions must match within explicit tolerance.
No persistent IDs/copy/graph refresh/operator. Unit input returns no_change. Numerical
prediction is NOT evaluated-world geometry, normal/tangent or engine certification.

Fingerprint binds Scene/Object/Mesh names, raw transform channels/rotation mode/basis,
ordered vertices/edge flags/faces/UV data/material slot links/references and effective
tolerance. Material contents and general custom properties are not a deep backup.
`verify_scale_preview(..., expected_source_sha256=..., geometry_tolerance=...)` recomputes
the supported snapshot: missing/stale hash returns error even for no_change; match states
snapshot freshness only, never mutation authorization. Changing effective tolerance also
requires new preview. No identity or concurrent-edit guarantee across calls.

Current native suite 56 pass: prior 24 snapshot checks + 6 separate native copy experiment
checks + 26 analytic preview/freshness checks. New tests cover rotated/translated nonuniform
positive scale, exact prediction, no IDs/source changes, missing/stale geometry/transform/
UV/seam/Scene/parameter hash, restored state, invalid tolerance, nonfinite UV, reflection/
zero/delta/parent/Edit Mode refusal and no-change. Exact fixture teardown restores original
fingerprint/IDs. Raw response/hashes in ignored `.local/validation/scale-preview-20260918.json`.
The 30-check section below records the earlier checkpoint.

Development helper `scripts/inspect_static_transform.py` reports an explicitly named base
mesh's raw local transform channels, Blender-reported matrices, reported world determinant,
parent and local vertex bounds. No IDs, operators, dependency refresh, transform application,
origin movement or export. This is not an installed Skill or engine certificate.

## Contract and limits

`inspect_static_transform(object_name, *, scene_name=None)` requires an explicit mesh within
the named/current Scene, Object mode and finite raw channels/matrices/base coordinates.
Invalid/missing target or Scene, wrong type, Edit Mode and nonfinite values return error,
withhold numerical snapshot and never choose a fallback target or force mode.

Successful schema `gameassetai.transform-preflight.v1` reports advisory review items for
nonunit/nonuniform/zero local scale, reported world reflection/singularity, parent,
unevaluated constraints/modifiers, preservation bindings, linked/override data or empty mesh.
`export_ready` stays unknown, `mutation_authorized` false and freshness snapshot-only.
Bounds center is information, NOT a pivot target. Profile/user intent supplies engine,
units, axes and pivot goals; this helper invents none of these.

Reported matrices may be stale without dependency refresh. Exact zero does not certify
near-singular numerical conditioning. Base bounds exclude modifiers, rig deformation and
engine geometry. Nonfinite inactive stored rotation channels conservatively refuse;
rotation-mode conversion is not performed. UV/normals/final export validation is separate.

## Actual native evidence

Blender 5.0.1/addon [1,7]/protocol 7: 30 synthetic checks pass (24 snapshot/refusal/teardown,
6 separate copy-scale capability checks). Identity with intentionally
offset vertices reports center without changing origin; mirrored/nonuniform and singular
transforms, parent, Constraint, vertex groups, nonfinite vertex/raw Euler values, missing
target/Scene and explicit-name refusal tested. Edit Mode refuses while preserving mode.
Repeated supported inspections retain fixture fingerprint/IDs. Exact owned Scene/Object/
Mesh teardown restores original fingerprint and tracked names:
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
Fixture setup may dirty the file; no original save/export.

Capability experiment only: independently copied synthetic Object/Mesh, nonuniform
reflected scale transformed into copied Mesh coordinates, copied scale reset to one.
Local matrix-basis transformed positions match within explicitly test-only 1e-6; UV corner
values, material reference and polygon vertex order retained, source unchanged and copied
vertex edits independent. This does NOT certify evaluated world geometry, normals/tangents,
near-singular inputs, parent/rig behavior or engine export, and is not a reusable apply API.

First expanded run stopped exact cleanup because a copied Mesh still used the shared
test material. Read-only inspection confirmed remaining owned IDs/users; exact Mesh then
material then empty Scene recovery completed. Harness cleanup now groups all Meshes before
materials. Rerun passes 30 with complete teardown and restored original fingerprint.
Raw successful response/source hashes: ignored `.local/validation/transform-preflight-20260918.json`.

```bash
python -B scripts/prepare_blender_check.py --suite transform-preflight
```

Transmit JSON code through MCP after checking current addon/Scene and synthetic-test scope.
The suite stays separate from `all`. No fifth Skill, installation change or Apply Transform.
Before a future copy-based operation, define explicit operation/preservation goals, fresh
source/parameter binding, actual world geometry/UV/material validation and exact rollback.
Start with static independent copies, not parenting, rigs, Shape Keys or automatic pivots.
