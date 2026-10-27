# Release checklist

Historical checklist only: on 2026-09-21 the user removed external/public
distribution from the active scope. Do not pursue these release gates unless the
user explicitly restores that goal. Local Skill exposure/regression checks remain
relevant to personal Workspace use.

No stable release has been published. Source bundles and local deployment are development
evidence, not proof of client recognition or game-engine compatibility.

Before a supported-client release:

- [x] narrow self-contained SKILL.md/resources; current sources pass skill-creator validation
- [x] expected inputs/outputs/failure boundaries defined for six source-tested workflows
- [x] fifth positive-scale Skill host use/instruction-led synthetic apply/restore (user-reported)
- [x] sixth explicit-pivot Skill source/ZIP/installed helper regressions on Blender 5.0.1
- [x] sixth Skill actual target-client exposure/instruction-led synthetic apply/restore (user-reported)
- [x] repository/workspace/payload/bundle/deployment offline regressions pass
- [x] native Blender representative, refusal, preservation and rollback checks pass
- [x] actual ZIP helper code passes sequential live regression
- [x] current deployed files match source; no MCP or global config packaged
- [x] actual installed helpers executed directly through MCP; stale/name-collision refusals preserve data
- [x] current-session Profile switching → explicit limits → live diagnostics passes
- [x] target-client session exposes all three installed Skills and explicit calls work (user-reported)
- [x] fourth coplanar Skill exposure and instruction-led synthetic preview/apply/restore (user-reported)
- [x] three natural-language read-only requests give expected outcomes (user-reported)
- [ ] selected-Skill and raw MCP routing traces recorded
- [x] tested analysis-only requests report no modification/copy (user-reported)
- [ ] ambiguous removal establishes scope before apply
- [x] ambiguous Cube cleanup stays inspection-only with declared appropriate Skills (user-reported)
- [x] invoked synthetic preview → independent-copy apply → validation → restore (user-reported)
- [ ] client passes stale-preview/no-overwrite refusals (native helper checks passed)
- [x] fresh-client Profile changes/null state do not invent/stale-reuse game constraints (user-reported)
- [ ] exact client version, supported Blender version and MCP provenance recorded
- [ ] licensing, source review, supported installation/update/recovery policy verified
- [ ] Git source/version/tag and release integrity record defined before publication

Record actual results rather than checking items because a script/guide exists. No
paid account, generated character, imported proprietary asset, Mixamo or engine export
is required for this first limited source-workflow release. Unsupported production
rig/export cases remain limitations; do not imply those capabilities are released.

The user has completed session exposure and explicit-call checks in the Workspace;
do not ask for installation/source-folder verification again. The remaining client
gate is routing trace evidence and ambiguous removal/refusals,
not native helper capability (the copy-apply and rollback paths have direct live evidence).
The user subsequently passed synthetic instruction-led apply/restore; do not repeat it.
The three read-only natural-language outcome checks are also complete; do not repeat them.
Fresh Workspace Profile A/B/null checks are complete by user report, including exact
settings restoration and existing Profile hashes; do not repeat that gate either.
See `skill-session-validation.md` for independent prompts and provenance. This development
session's catalog still cannot substitute for the Workspace client's implicit selection.
Keep valuable original data untouched; cleanup checks use only synthetic fixtures.

Earlier direct installed-source MCP validation passed 331 checks for the first four, then
90 for the fifth and 63 for the sixth; these are distinct native suites, not a client
discovery guarantee. The old request to rerun
synthetic stale/name-collision helper checks in another conversation is unnecessary.
The unchecked client refusal item means automatic instruction-following/selection evidence,
not inaccessible installed files or a failing helper. This does not block repository work.
