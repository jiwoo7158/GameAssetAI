# Blender MCP Foundation Verification

Status: **Blender steps 1–6 and explicit current-session Profile step 7 exercised**.
Installed session exposure and explicit calls were separately confirmed by the user;
three natural-language read-only outcomes were also confirmed by the user. Raw routing
traces and fresh-client Profile behavior remain unverified. See
`docs/skill-session-validation.md` and `docs/profile-workflow-validation.md`. Source helpers were loaded explicitly from the
actual Workspace; this does not establish implicit skill invocation.
See `docs/blender-mcp-environment.md`, `docs/inspection-validation.md`, and
`docs/static-mesh-validation.md`. Screenshot confirmed the original object inventory;
visibility variations and each fixture transform were not independently screenshot-tested.
Source-workflow synthetic regressions passed; they do not certify all imported assets.
MCP is an externally configured work tool; GameAssetAI skills do not install it.
Do not treat this plan as a production skill or verified Blender procedure.

## User preparation required

1. Open Blender with a dedicated empty/scratch scene, not valuable production data.
2. Configure/start the chosen Blender MCP externally and expose its tools to the current
   Codex session. Follow that implementation's current setup instructions.
3. Supply the implementation/version (or source URL) and Blender version when known.

Do not require accounts, paid 3D generation, Rigify, or Mixamo for this first verification.
No engine or Blender project needs to be moved into this repository or workspace.

## Verification sequence

1. Inventory tools actually exposed in the current session. Record their names and
   descriptions; do not assume an old README's tools exist.
2. Perform read-only scene inspection. Report objects, selection/active object, mode,
   transforms, mesh statistics, materials, armatures/bones, and Actions/animation where
   available. Mark unsupported fields explicitly. Compare with Blender's visible state.
3. Check screenshot/viewport capture if exposed. Record whether it captures the current
   scene and whether visibility/selection affects the result.
4. If Python execution is exposed, run a read-only native-data query and compare it with
   the tool inspection. Record Blender version, execution restrictions, and result shape.
5. In the scratch scene only, inspect the target and record its original transform.
   Use a cube for a small translation, inspect the new transform, and verify in Blender.
   Restore the original transform and re-inspect. Do not delete arbitrary scene data.
6. Test a harmless missing-object query. Record its error/fallback behavior without
   modifying data. Stop if reported state and Blender's real state disagree.
7. In a generated personal workspace, manually create two synthetic profiles and switch
   the active reference. Ask Codex to report the active filename and its distinct rules
   before each task. Confirm it does not reuse stale rules or invent missing constraints.

Imported rigs, Mixamo animations, retargeting, and Unity/Unreal exports are later,
separate verification stages. Do not alter existing armatures or Actions during this test.

## Evidence record

Write an actual development note under `docs/` after running the checks, containing:

- date, OS, Blender version, Codex client/version, MCP implementation/version/source
- scratch-scene description and any fixture licensing
- available tool names, request/result examples, and unsupported capabilities
- each check: pass/fail/not run, observed state, and independent Blender confirmation
- before/after/restored transforms and whether user data remained unchanged
- profile-switch results; errors and fallback behavior
- limitations, next narrow workflow, and regression checks required before stability

Leave untested capabilities marked **not run**; do not check roadmap items merely
because this plan exists. If read-only inspection cannot be trusted, no asset-modifying
skill should proceed.
