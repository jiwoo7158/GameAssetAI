# Explicit pivot copy experiment — 2026-09-18

## Intent and boundary

Roadmap transform preparation began with development-only `scripts/preview_pivot_copy.py`
and `scripts/apply_pivot_copy.py`; the subsequent self-contained source Skill is
`skills/blender-relocate-pivot-copy/`. No automatic center/bottom selection, source
modification, export or engine convention. Profile/user intent supplies a base-mesh local
three-coordinate point;
explicit finite positive geometry tolerance is required. Missing policy remains unknown.

Uses existing transform snapshot/scale-preview eligibility: independent simple static
positive-scale XYZ source; linked/rig/animation/parent/children/delta/modifier/custom-normal/
unsupported attribute cases refuse. Apply additionally refuses file-wide animation or
constraints, requires explicit boolean authorization, globally unused <=63 UTF-8 byte
Object name and fresh preview fingerprint. No graph refresh/save/export.

## Mathematical contract

For chosen local point p and reported source basis B, predict copied vertices v-p and
copied basis B*T(p). Visible asset world positions remain unchanged; world origin becomes
B*p. This is an origin relocation, not mesh centering, scene translation or scale application.
Stored source world/basis disagreement beyond explicit positional tolerance refuses.
Fingerprint binds existing scale-preview snapshot, effective tolerance, reported world and
chosen point. Freshness is only a bounded snapshot check, never permission or deep backup.

Apply copies Object/Mesh independently, translates only copied coordinates, restores exact
source rotation/scale channels and assigns the predicted world origin to copied location.
Before and after actual link it checks Mesh independence/vertex count, topology/edge flags,
UV contents/activity/material references, non-location channels, parent-inverse, coordinates,
reported world positions/origin and unchanged supported source snapshot/surface/world.
Safe rollback deletes only tagged newly owned Object/Mesh; changed ownership/users means
cleanup unverified, inspect instead of blindly retrying. Materials intentionally share refs.

## Expanded native evidence — 2026-09-19

The same owned fixture now has **two triangular faces, two material slots with distinct
face assignments, and two UV layers with explicit active/render state**. The independent
copy retains all of these, as well as reported world positions and source preview hash.
Temporary source animation data, constraint, modifier and vertex group refuse; a temporary
file-wide Scene animation owner blocks apply. Only those synthetic blockers were removed;
the original user Scene was untouched. Current **61 checks pass** and all fixture ID lists
and original fingerprint restore. Raw response/source hashes:
`.local/validation/pivot-multisurface-20260919.json`. Afterward the source Skill, actual
ZIP and actual installed helper each passed the same **61 native checks**. The sixth Skill
was installed without overwriting any of the five prior Skills. Byte-alignment validation
passes; actual session catalog exposure, implicit routing and instruction-led host call
are **not yet verified**. This is not an engine-ready export workflow.

Skill Creator guided a narrow self-contained four-helper package. The apply helper now
contains only its own file-wide blocker/surface checks, rather than loading the scale-apply
implementation. Development and Skill helpers are compared by an offline regression.
Creator quick validation passes. ZIP SHA-256:
`96ddaab497944146fd468b87950ac5eee0a4ace87c231df31b0a1f3281456e7d` at
`.local/source-bundles/pivot-skill-20260919/blender-relocate-pivot-copy.zip`.
Source/ZIP/installed response and decoded helper hashes:
`.local/validation/pivot-skill-20260919.json`. No publication or client-build certification.

Subsequent regression added a second owned Object sharing the source Mesh. The created
copy has an independent Mesh while both original users retain their coordinates and
shared reference. Updated source/ZIP/installed runs each pass **63 checks**, with exact
fixture teardown and original fingerprint restored. Skill resources, ZIP and installed
bytes did not change; only the repository harness grew. Latest raw responses:
`.local/validation/pivot-shared-source-20260919.json`.

## Historical initial native evidence

Blender 5.0.1, addon [1,7], protocol 7; **49 checks pass**. Translated/rotated/nonuniform
positive-scale offset triangle with UV: prediction, copy independence, retained world
positions/origin/channel values/UV/topology/source, stale/missing fingerprint, candidate/
tolerance/scene binding, malformed/nonfinite/overflow points, invalid tolerances, delta/
reflection refusal, collision and unit-point no-change. Injected write/link failure and
post-link UV/scale/Mesh reassignment/extra isolated vertex all refuse and fully roll back.
Only synthetic test IDs are created/removed; exact ID lists and original fingerprint restore:
`f17ed65d5c9d05decdb8e3a53caf274b1d00b94f4c9eb8bc500e0cd331fa887d`.
Raw response/source hashes: ignored `.local/validation/pivot-copy-20260918.json`.

Repeatable development payload: `python -B scripts/prepare_blender_check.py --suite pivot-preview`.
`--suite pivot-skill` tests source/ZIP/installed pivot helpers. Both suites contain current
apply tests; seven sources compile independently in one shared globals/locals dictionary.
The inspector test harness remains repository-sourced under bundle/installed origins.

## Remaining work

The representative multisurface/dependency fixture is complete. The user subsequently
confirmed actual Workspace-client use of `blender-relocate-pivot-copy` on a separate UV
triangle: `preview_pivot_copy` succeeded for local (0.25, 0.25, 0), expected world origin
(1.25, 2.25, 3); `verify_pivot_preview` fingerprint matched; `apply_pivot_copy` returned
`created` for an independent copy. Source Mesh, UV and topology remained; reported world
coordinates and pivot error were both zero within explicit 0.00001 tolerance. Only
test-owned Scene/Object/Mesh were removed; starting/ending state had no difference.
This completes the sixth Skill's instruction-led host outcome **by user report**. Raw
selected-Skill/MCP envelopes and client build were not provided; do not infer them or
request this already-passed synthetic gate again.

The completed host request had this documented form (historical, do not repeat):

> 기존 Scene과 에셋은 건드리지 마. Blender의 별도 임시 Scene에 정점 세 개로 된 UV가 있는
> 테스트 Mesh를 만들고, 그 Mesh의 로컬 좌표 (0.25, 0.25, 0)로 피벗을 옮기는 작업을
> 미리보기해줘. 위치 오차 허용값은 0.00001이야. 미리보기 fingerprint가 현재 상태와
> 일치하면 이 작업을 명시적으로 승인하니, 겹치는 독립 복사본에만 적용하고 원본 Mesh와
> 월드 좌표·UV가 유지됐는지 검증해줘. 사용한 Skill, 결과, 실패·복원 여부를 보고하고
> 이번 테스트에서 소유한 Scene/Object/Mesh만 제거해. 시작 상태와 끝 상태를 비교해줘.

This checks client exposure/instruction following, not native helper correctness (already
tested). If Skill does not appear or the client cannot prove the bounded input state, stop
without editing the original. Record the client's actual chosen Skill and Blender result;
do not infer a raw routing trace from a summary.
Parented/reflected/rigged inputs, custom normals, evaluated geometry, procedural material
appearance, numerical conditioning, arbitrary concurrent callbacks and engine import/export
are not certified. Temporary fixture setup may dirty an unsaved file; no clean-flag claim.
