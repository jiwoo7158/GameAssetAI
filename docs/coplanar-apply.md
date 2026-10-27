# Independent-copy structural simplification — 2026-09-18

## Latest client/tolerance update

User separately confirmed Skill exposure and actual synthetic preview/apply using
angle_limit=0.001/tolerance=0.000001, matching fingerprint, independent Object/Mesh,
4→4 vertices, 5→4 edges, 2→1 faces, 2→2 triangles, retained affine UV/material/boundary,
synthetic source unchanged, exact test Scene/Object/Mesh/material teardown and no original
starting-state differences. This gate is complete; do not repeat the prompt below.
Raw calls/client build were not supplied; do not invent them or claim general routing.

Current API accepts explicit geometry_tolerance (local xyz units) and uv_tolerance
(UV-coordinate units) separately. Legacy tolerance explicitly sets both, retained for
compatibility; mixing styles or omitting either separate bound refuses. Effective parameters
are normalized into the source hash, so equivalent legacy/separate inputs have identical
current hashes. Old helper-version fingerprints need a new preview (no automatic migration).
Changing either effective bound makes old apply stale. Area absolute check uses geometry
tolerance squared, not UV tolerance. No automatic game/scale-aware defaults introduced.

Latest packaged-helper native suite **158 + 4 = 162 checks pass**; offline tools 41 pass.
Tests isolate geometry-vs-UV effects, equivalent legacy/separate hashes, changed UV-bound
stale apply, and native strict UV checks despite loose geometry tolerance. Earlier counts
and shared-tolerance limitations below describe historical checkpoints.

Subsequent representative tests: local coordinate size ×1000 with explicit geometry/UV
bounds, two affine UV layers through independent-copy apply, retained layer names, second
layer-only nonaffinity blocks, and restored synthetic source. This is evidence for those
fixtures, not automatic scale policy or permission to relax whole-mesh restrictions.

Disconnected-component regression: two separated coplanar squares with one global affine
UV map predict 8/10/4/4 -> 8/8/2/4 (vertices/edges/faces/triangles). Marking one internal
edge as a seam predicts 8/9/3/4, and independent-copy apply retains that seam. Offsetting
only the second UV island makes the whole-mesh affine guard fail: preview/apply refuse
without new IDs, even though each island is individually affine. Restoring that offset
restores the synthetic source state. Exact fixture teardown restores original fingerprint
and ID lists. These seven added checks use actual current ZIP helpers, not changed Skill
sources. The API still accepts a whole named supported mesh, not selected faces/islands;
there is no candidate-region fallback or automatic merging across protected boundaries.

Updated source/installed Skill aligned after exact old-hash checks and backups under
`.local/deployment-backups/separate-tolerances/`. Installed changes used approved native
patch application, not a new automatic overwrite policy. Existing three Skills/Profiles/
projects/MCP unchanged. New archive directory `.local/source-bundles/separate-tolerances-20260918/`
contains the updated fourth archive and inspector dependency for this test harness:
fourth ZIP SHA `8e70b8894e79c56f88aa1befc06790ccd28dfaae5c506aa972ca6a8b76a5a3bd`.
This is not a complete four-archive directory for `all`; use coplanar-20260918 for old-three
regression and separate-tolerances-20260918 with coplanar-skill for current fourth tests.
The fourth Skill itself remains self-contained and does not require inspector at runtime.

## Implemented and verified

Development `scripts/apply_coplanar.py` consumes a fresh re-computed coplanar preview.
Explicit authorization boolean conveys a previously authorized operation, not permission
by itself. Require exact source fingerprint/parameters and unused output name ≤63 UTF-8
bytes. Refuse stale/missing hash, invalid authorization, collisions, unsupported source
and file-wide animation/drivers/constraints before creating copied IDs. Even no-change
requires valid preview binding; supported protected-boundary input returns no_change.

Copy Object and Mesh independently, intentionally share material references, native BMesh
dissolve only the copy. Preview now emits predicted_geometry_sha256: canonical oriented
face corner cycles/UV/material/smooth data, all vertex coordinates, edge seam/smooth flags
and UV layer names. Output signature/counts must match before linking. Preserve transforms,
material/UV references and source state/hash. Canonical cycles retain winding; this is a
bounded signature, not a certificate for all attributes or adversarial concurrent callbacks.

Write/validation/link failure removes only exact newly owned Object/Mesh IDs if users and
links remain safe. Unsafe ownership/users produce failure_cleanup=unverified; stop and
inspect, not automatically retry/delete. Link-failure test raises after an actual link,
so rollback covers that intermediate state. No original data is saved/cleaned/exported.

## Tested evidence

Blender 5.0.1, addon [1,7], protocol 7. Representative plane: edges 5→4, faces 2→1,
vertices 4 and triangles 2 unchanged. UV/material data retained; independent copied Mesh
edits do not affect source. No triangle-budget reduction or engine-ready claim.

Native suite expanded to **141 normal checks + 4 fixture-failure checks passed**. This
includes capability experiments, preview and apply, not 145 apply-only checks. Covers
no authorization/invalid boolean, absent/stale hash, real transform changes, changed
tolerance, name collision, group/Shape Key/animation-binding refusal, unrelated file
constraint guard/no new IDs, protected-boundary no-op, unsupported UV/nonplanarity,
write failure, corrupted output rejection and post-link failure rollback. Original
fingerprint/ID lists restored after exact synthetic teardown:
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.

## One source Skill and self-contained bundle

Added `skills/blender-simplify-coplanar/` only after the above tests passed. Skill Creator
guided discriminating scope, authorization immediately before mutation, self-contained
resources and no production claim. Four bundled helpers: state inspection, affine guard,
preview, apply; no dependency on another installed Skill or repository path at runtime.
Prototype mirrors remain under scripts for development; offline equality test prevents
divergence of these helpers/state extraction. Edit sources consistently and repackage;
do not automatically overwrite a user's deployed copy.

Skill Creator quick validation passed in Python UTF-8 mode. First validator attempt hit
Windows cp949 decoding of ≤; corrected validator invocation, not source encoding/design.

Actual packaged helpers passed the same live suite:

```powershell
python -B scripts/prepare_blender_check.py --suite coplanar-skill --bundle-dir .local/source-bundles/coplanar-20260918
```

The default all suite retains the earlier three installed workflow regressions; it does
not quietly include the prototype. Run coplanar-skill separately for the fourth Skill.
New versioned directory includes all four ZIPs; earlier three source archives are unchanged.
New ZIP SHA-256 `6f4e0ce3417f755ae712f177d7f17857393b686b707ad91c4306805b968d9674`.

Approved no-overwrite deployment copied the new Skill only to
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-simplify-coplanar`; existing Skills,
Profiles/settings and external projects retained. Installation/hash alignment does not
prove fresh-client discovery/automatic selection or instruction-following.

## Remaining client gate and limits

The new Skill needs exposure/behavior verification in the already working Workspace
client; the development catalog cannot refresh it. Existing three-Skill client tests
remain complete and must not be repeated as blockers. Suggested single synthetic request:

> 새 blender-simplify-coplanar Skill이 노출되는지 확인해줘. 원본 Scene을 수정하지 말고 별도 합성 Scene에 연속 affine UV와 재질을 가진 두 평면 삼각형을 만든 뒤, angle_limit=0.001 라디안과 tolerance=0.000001로 미리보기해줘. 이 합성 데이터의 중복 내부 엣지 제거를 허가하므로 미리보기 fingerprint를 사용해 독립 복사본에만 적용하고 검증해줘. 삼각형 감소로 오해하지 말고, 테스트 데이터만 제거한 뒤 시작 상태를 복원해줘.

Whole-mesh planar/affine restriction and shared xyz/UV absolute tolerance are deliberate
prototype boundaries. Material contents shared, generic attributes mostly refused; no
production imported assets, multi-island optimizer, ratio decimator, pivot/rig/engine export
certification. Next dev priority: separate geometry/UV tolerance policy and candidate/island
scope tests before generalizing, not a broad new feature collection.
