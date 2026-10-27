# Action Range Extraction Validation

`blender-extract-action-range` copies one explicit frame interval from an existing Action
into a new fake-user-protected, unbound Action. It preserves the source Action and all
current/NLA references and keeps original frame numbers.

## Evidence

- Blender: 5.0.1
- MCP implementation: `ahujasid/blender-mcp`, `localhost:9876`
- Add-on: 1.7, protocol 7; server expected protocol 11 and used compatible fallbacks
- Archive: `.local/source-bundles/action-range-rebase-20260928/blender-extract-action-range.zip`
- Archive SHA-256: `ce5e41a44daaaa7f7a1c62b781baeee105d106f86f6befd655c86abe4fb54560`
- Installed at:
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-extract-action-range`

Repository source, portable ZIP and actual installed helpers each passed the same 17-check
Blender regression. Coverage includes candidate review, authorization, missing-boundary,
nonlinear, modifier, stale and collision refusal; exact retained frame/marker range;
unknown-policy refusal; exact `KEEP_FRAMES`, `REBASE_TO_ZERO` and `REBASE_TO_ONE`
key/handle/marker timing; source content/reference preservation; unbound output; and exact
teardown.

The first native attempt exposed an undeclared `_curves` dependency and stopped before
creating fixture data. The helper set now explicitly includes `inspect_animation.py`. The
second attempt exposed Blender invalidating cached Keyframe references after collection
removal; removal now reacquires each current point by reverse index. The corrected source,
ZIP and installed runs all pass. The original Cube/Light/Camera Scene was preserved.

## Boundaries

Supported policies are `KEEP_FRAMES`, `REBASE_TO_ZERO` and `REBASE_TO_ONE`. Rebasing
applies one reviewed offset to copied key, handle and in-range pose-marker times. Every
F-Curve must have unique key times, exact keys at both integer boundaries, LINEAR
interpolation only, and no samples or modifiers. The
workflow does not synthesize boundary values, preserve arbitrary Bezier segment shape,
rename/delete the source, bind the result, edit a Rig, save, export, or
certify loops, deformation or Unity behavior. Refreshed-client discovery remains open.

The previous installed version remains byte-exact at
`D:/AI/GameAssetAI-Workspace/.agents/skill-backups/blender-extract-action-range-20260928-pre-rebase`.
The hash-bound update plan is retained under `.local/` for recovery evidence.
