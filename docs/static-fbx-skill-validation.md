# Static FBX export Skill validation — 2026-09-21

`blender-export-static-fbx` packages the proven texture-free, single-Mesh FBX path.
It is intentionally not a textured, rigged, animated or batch exporter. Game-specific
axes, units, conversion options, modifier policy and destination remain explicit request
or Workspace Profile decisions.

The Skill contains seven files: `SKILL.md`, the offline request validator, four Blender
inspection/publication dependencies and the staged exporter. Repository-to-Skill helper
byte equality is covered by the scripts test suite. The repository package validator
created a repeatable ZIP with SHA-256
`0434A3C73264895C21812651EE10A9ED87633DCE7120FB072FCBF33BAF83104F`.
The optional Skill Creator quick validator was unavailable because the host Python lacks
PyYAML; no dependency was installed. Repository structure/package validation and native
tests provide the applicable evidence instead.

Blender 5.0.1 source-Skill, ZIP-helper and installed-helper runs each passed the same
**10 checks**: authorization and freshness refusal, one verified binary FBX publication,
source preservation, existing target and late `.meta` collision preservation, no stage
leak, exact fixture/artifact cleanup and original Scene preservation. The production
candidate fingerprint is self-contained in the Skill and tracks geometry/material state;
it no longer relies on a test-harness function.

The no-overwrite deployment added only
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-export-static-fbx`. Deployment
validation reports `aligned`, with no missing, extra or changed files. At installation
time, the already-open client had not refreshed its catalog; the later refreshed-session
result below closes that discovery gate. A disposable new path and explicit settings are
still required for apply.

The user subsequently confirmed refreshed-session exposure and a read-only Cube preflight.
The host reported no dependencies or warnings and correctly kept export authorization
false. With no active Profile, absolute target or axis/scale settings it did not invent a
request or claim `candidate_for_review`. This closes automatic exposure and safe
information-missing refusal.

The same refreshed client then completed the formal `candidate_for_review` and
fingerprint recheck and published a new test artifact without overwrite. The result was
15,020 bytes with SHA-256
`c88378061c4b1de95bb0cc9d38e5344ce59ebcd1a2fdaff279ebaea291294136`;
the temporary stage was removed and Blender Scene/Cube state matched before and after.
Unity's independent hash-bound validator passed the imported topology, UV, material,
animation, root-transform, Preview Scene bounds and active-Scene checks. Unity then
removed only this FBX and its generated `.meta`, restoring the authorized folder to its
two original files. This closes the narrow host-driven export/import/cleanup gate.

See `unity-export-contract.md` for the request schema and Unity unit/axis evidence, and
`static-export-preflight.md` for staging, collision and sidecar limitations.
