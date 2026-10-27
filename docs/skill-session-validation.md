# Installed session validation — 2026-09-16

### Seventh Skill installed-helper outcome — 2026-09-21

`blender-export-static-fbx` was installed without overwrite into the personal Workspace.
Source/deployment byte comparison is aligned with no missing, changed or extra files.
Repository source, packaged ZIP and exact installed helpers each passed the same 10-check
Blender 5.0.1 staged-export regression with exact cleanup and original Scene preservation.
The current already-open client has not refreshed its Skill catalog, so automatic
discovery and natural-language routing are not yet evidence. See
`static-fbx-skill-validation.md`; a refreshed Workspace session is the remaining host gate.

The refreshed client later exposed `blender-export-static-fbx` automatically and selected
it for a read-only Cube preflight. It reported export authorization false and, because no
Profile/target/settings existed, did not construct a formal candidate or write anything.
This user-reported outcome closes discovery and safe refusal.

The user later completed formal candidate review, matching-fingerprint apply and staged
cleanup through the same Skill. Independent Unity validation passed against the exact
15,020-byte/SHA-bound artifact, after which only that FBX and generated `.meta` were
removed. Blender and Unity Scene states and the two original Unity folder file hashes
matched their baselines. The seventh Skill host-driven apply/import/cleanup gate is now
complete; raw client call envelopes remain a provenance detail, not a functional blocker.

## Evidence and boundaries

### Fifth Skill host outcome — user-reported, 2026-09-18

User identified `blender-prepare-positive-scale` on Blender 5.0.1 and reported actual
preview_scale_copy (preview, tolerance 0.00001), verify_scale_preview (hash match) and
apply_scale_copy (created on independent copy). Synthetic source scale (2,3,0.5) preserved,
copied scale unit, independent Mesh, world/pivot error zero, topology/UV/material refs
retained. Exact synthetic teardown and starting/restored state matched; original Scene
not modified. Fifth gate is complete by user report; do not ask for repetition. Full
raw call envelopes/client build were not supplied and remain separate release evidence.

### Ambiguous cleanup triage — user-reported, 2026-09-18

User supplied outcome and screenshot declaring `blender-inspect-asset` and
`blender-validate-static-mesh` for natural-language cleanup with no modification allowed.
Cube returned 8/12/6/12 vertices/edges/faces/triangles, no relevant loose/duplicate/
degenerate/incidence findings; UV/material present, unit scale, no reported modifier/
rig/Shape Key/animation. Whole-planar coplanar simplification correctly excluded volumetric
Cube. Null Profile budgets not invented; no original edit/copy and before/after matched.
This specific selection/read-only outcome gate is complete. Screenshot is client-declared
Skill selection, not raw selection/MCP trace. It does not prove clarification/apply behavior
for ambiguous removable geometry. Do not repeat Cube triage/setup as a development blocker.

### Direct installed-source check — 2026-09-18

The development session can read the actual Workspace and installed Skills and call the
same Blender MCP. Lack of an independent conversation controller is NOT a blocker for
installed helper validation. Workspace AGENTS, cleanup SKILL and null active Profile were
read first; no invented game rules. Helpers were explicitly selected/read, not implicitly
discovered. `prepare_blender_check.py --installed-skills-dir` now transmits those exact
installed helper sources with no source/ZIP fallback and compiles each in a shared namespace.

Actual installed helper runs: inspection 36, diagnostics 73, cleanup 60, coplanar 158 +
failure teardown 4 = 331 checks pass on Blender 5.0.1/addon [1,7]/protocol 7. Cleanup
returns `Result name already exists; overwrite/autosuffix refused` and `Preview fingerprint
missing/stale; re-preview before apply`. Existing copied result remains unchanged, stale
attempt preserves the intentionally changed synthetic source and ID lists, and exact
coordinate restoration matches source state. Exact owned fixtures were removed and
original fingerprint/ID lists restored. No original save/export or personal-file writes.
Raw MCP responses and transmitted-source hashes are retained privately at
`.local/validation/installed-safety-20260918.json`; this is direct explicit execution
evidence, NOT a selected-Skill/implicit-routing trace. Offline tooling 47 pass.

Do not ask the user to repeat installed stale-preview/name-collision helper tests.
Automatic selection for ambiguous language remains a separate host-level test because
the current session's supplied Skill catalog does not list these four GameAssetAI Skills.

Subsequent Profile gate passed by user report: each transition reread settings and
referenced Profile; Cube 12 triangles exceeded limit 10, passed limit 20, and null Profile
left game budgets unjudged without stale reuse. Blender state matched, original settings
restored byte-for-byte, existing Profile hashes matched, only two synthetic Profiles
removed. See `profile-workflow-validation.md`; no repeat needed. Raw routing/build
evidence remains absent, rather than inferred from these outcomes.

Fourth Skill subsequent result: user confirmed blender-simplify-coplanar exposure,
explicit synthetic preview/fingerprint-bound independent-copy apply, 4/5/2/2 → 4/4/1/2,
affine UV/material/boundary/source preservation, owned Scene/Object/Mesh/material teardown
and original starting-state differences none. See `coplanar-apply.md`; no repeat needed.

The user reported automatic session exposure and actual calls for three Skills in
the Workspace: inspect returned three Scene objects, static diagnostics returned Cube
12 triangles/no findings, cleanup preview returned zero removal targets. Selection,
mode and datablock lists remained unchanged. Active Profile was absent; no game-specific
limits were judged. The first execution-namespace error was corrected and retested.
No traceback, exact client build or installed implementation commit was supplied;
do not invent those details or claim the exact cause of that first failure is known.

### Subsequent synthetic copy-apply result (user-reported)

The user completed the synthetic-only natural-language apply/restore request: one
isolated vertex and one wire edge, independent copy after preview, vertices 7→4,
edges 5→4, one face retained, including removal of the two wire endpoints. Synthetic
source preservation, independent Mesh, retained face/UV, zero remaining loose geometry,
exact test Scene/Object/Mesh removal and no differences from the recorded original
starting state were reported. Treat this workflow as passed; do not ask to repeat it.
The summary does not identify the selected Skill, raw MCP calls, fingerprint argument,
client version or collision/refusal behavior. Do not infer all routing/safety gates passed.

Added a matching native quad fixture to make this result repeatable: both flags remove
three vertices, while wire-only removes the edge but keeps all seven vertices. This
distinguishes category authorization from geometry counts alone. Latest direct combined
ZIP-helper run: **36 + 73 + 57 = 166 checks passed**, exact fixture cleanup and original
fingerprint restored. Helpers/bundle contents unchanged; test harness hash
`ef609156fc182d50b1b154ca2cdfd1942eec84e5807ebf3983936e6d956a48ad`.

Direct development regression separately verified Blender 5.0.1: inspection 36,
diagnostics 73, copy-cleanup 48 checks, all passed. Cleanup now applies with a fingerprint
retained from an explicit prior preview, and a deliberately corrupted copied surface
is rejected with complete owned-ID rollback. Original fingerprint, mode/selection and
tracked datablock names restored; fixture teardown complete. This is native helper
evidence, not a test of the client's instruction selection or approval behavior.

The three SKILL instructions now show same-dictionary globals/locals `exec` and a
function lookup/call in the same MCP request. Separate globals/locals can hide imports
from defined functions. The payload generator explicitly shares both dictionaries;
an executable offline regression proves imported function lookup and separate future
imports. Do not assume an execution namespace survives another MCP call.

Repository and installed instructions are byte-aligned. Previous installed instructions
were checksum-verified and backed up under ignored
`.local/deployment-backups/namespace-fix-20260916/` before the narrow update.
Helpers, personal Profiles, original project paths and MCP configuration were unchanged.
New versioned source bundles live in `.local/source-bundles/namespace-fix-20260916/`;
old bundles are historical artifacts, not current source equivalents.

Current bundle SHA-256:

- inspect: `2c473eb8bd83f79329e49e39c6a21af19b739919cd15d2cf295b485ce384cf8c`
- static diagnostics: `9651718e8a0e5e99384ce2239e15cd8dd7e46e282e5883019cd0f02ac8d4163b`
- copy cleanup: `147f0c8395008af45ca9402b2bd36c219e492d7a54cd121f1cdc33d4d9f3170d`

Final repository/actual Workspace validators and all three Skill Creator quick validations
passed. Offline regressions: 25 tool tests passed; 47 Workspace tests, 43 passed and
4 explicit Windows symlink-privilege skips. Final MCP inventory and viewport show only
the original Cube, Light and Camera. No original file was saved, cleaned or exported.

## Remaining client checks

### Historical independent-client safety request — no longer needed for helper validation

Installed-source helper refusals subsequently passed directly, as recorded above. Do not
repeat the prompt below as a user gate; it remains a historical reproduction recipe.
What remains for independent host testing is automatic selection/ambiguous language,
not direct helper execution. Historically, the installed Workspace
client following the instructions, not another source script or catalog/hash check.
This development session cannot start that independent conversation. Use the existing
Workspace without reinstalling or changing original Cube, settings or Profiles:

`원본 Scene은 수정하지 마. 별도 합성 Scene에서 정리 가능한 메시를 만들고 미리보기해줘.
그 다음 합성 원본의 좌표 하나를 바꿔 이전 fingerprint로 복사본 정리를 시도했을 때
거부되고 새 데이터가 생기지 않는지 확인해줘. 좌표를 복원하고 새 미리보기 후에는
이미 존재하는 테스트 Object 이름을 결과 이름으로 사용해서 덮어쓰기가 거부되는지도
확인해줘. 실제 정상 적용은 필요 없어. 테스트 데이터만 제거하고 시작 상태를 복원해줘.
선택된 Skill과 실제 MCP 호출, 각 거부 결과와 복원 비교를 기록해줘.`

This authorizes only synthetic fixture changes and refusal attempts, not edits to existing
user assets. Unexpected success or uncertain ownership must stop further mutation and
inspect exact created IDs, rather than recursively deleting or retrying. After this check,
ambiguous natural-language cleanup routing still needs a separately scoped conversation;
an instruction-led synthetic test does not prove that behavior.

### Read-only outcomes completed (user-reported)

The user supplied separate responses to prompts 1–3 below: Scene inventory returned
Cube/Light/Camera; base Cube diagnostics returned 8 vertices, 12 edges, 6 faces,
12 triangles with no findings/review items, one UV layer/material slot, unit scale,
no reported rig/Shape Key/animation sensitivity. Null Profile game budgets stayed unknown,
and self-intersection, outward normals, UV quality and engine import were not certified.
Cleanup preview returned zero isolated vertices/wire edges, without modification or copy.
These outcome checks passed; do not request them again. The pasted responses are not raw
MCP traces or proof of the precise selected Skill. Remaining behavioral gaps are ambiguous
removal, refusal handling and raw routing provenance. Profile freshness subsequently
passed by user report, as recorded above.

In the already working Workspace, submit each prompt independently, without naming a
Skill or past expected result. Record which Skill was selected, actual MCP calls,
output and preservation evidence. A catalog/file check alone cannot pass this gate.

1. `현재 Scene의 오브젝트 목록만 알려줘. Scene은 수정하지 마.`
   **Completed by the user.**
   Expected: inspection, no modification.
2. `Cube가 게임용 정적 메시로 쓰기 전에 구조상 문제가 있는지 검사만 해줘.`
   **Completed by the user.**
   Expected: diagnostics, no repair; absent Profile means game-specific limits unknown.
3. `Cube의 고립 정점과 면에 속하지 않는 와이어 엣지를 정리할 대상이 있는지만 미리보기해줘. 수정하지 마.`
   **Completed by the user.**
   Expected: explicit category preview, no apply/new output IDs, even if zero targets.
4. `원본 Scene은 건드리지 말고 별도 합성 Scene에서 고립 정점과 와이어 엣지를 만든 뒤, 미리보기 후 독립 복사본에만 정리를 적용하고 검증해줘. 끝나면 테스트 데이터만 제거하고 시작 상태를 복원해줘.`
   **Completed by the user. Do not repeat as a blocker.**
   Expected: synthetic-only authorization, preview fingerprint to apply, no overwrite,
   independent output, retained surface/UV/material validation, exact fixture teardown.

Do not run removal on valuable Cube merely to exercise apply. An ambiguous removal
request must establish target/categories before mutation. Fresh-client Profile switching
and stale-rule prevention passed by user report, separately from explicit development tests.

External MCP provenance remains user-identified: implementation `ahujasid/blender-mcp`,
source https://github.com/ahujasid/blender-mcp, socket `localhost:9876`.
