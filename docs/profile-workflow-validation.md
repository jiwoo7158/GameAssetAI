# Profile workflow validation — 2026-09-16

## Subsequent Workspace client check — user-reported, 2026-09-18

The user reported rereading active configuration and referenced Markdown after every
transition. Cube has 12 triangles: limit 10 exceeded, limit 20 within budget; null Profile
checked structure only and left game limits unjudged without reusing prior limits.
Blender was not modified and before/after state matched. Original settings were restored
byte-for-byte, existing Profile hashes matched, and only two synthetic Profiles removed.
This completes the independent Workspace A/B/null outcome gate. Raw calls and client
build were not supplied; do not invent them or repeat this check as a blocker.
The historical explicit development test below remains separately attributed.

## Actual current-session check

Canonical Workspace `D:/AI/GameAssetAI-Workspace` validates; old manual Workspace no
longer exists, independently checked after the user removed it. Old Codex trust table
was already removed in the previous stage. No further deletion was performed.

The current session read Workspace AGENTS.md and used the installed mesh-diagnostics
helper. Two temporary UUID-named Markdown Profiles were created in the actual Workspace
with persisted recovery state before any configuration write. The fixture refused any
already-active real game; original config bytes and metadata were preserved.

- Re-read A reference and Markdown: explicit Cube limit 10 triangles. Live Blender Cube
  has 12 base triangles; diagnostics returned triangle_budget_exceeded, detail 12 > 10.
- Switched to B, re-read reference and different Markdown/hash: explicit limit 20.
  Same Cube returned no_findings; A's limit was not reused. Engine/style/UV/material/rig
  rules remained unspecified and were not supplied as diagnostic defaults.
- Restored original active-profile.json byte-for-byte, removed only exact synthetic
  Profiles and fixture state. Re-read context returns null and unknown rules again.
  Original active reference SHA-256:
  `d14461f6f09ae2b001a84e16178f9262e0d9fbbf57f8415abd6aa5a328440206`.
- Blender Scene remained Camera, Cube, Light. No mesh/rig/Action/file modification.

This verifies explicit Profile reading/switching → supplied constraints → live diagnostics
in the current session. It does NOT verify automatic Skill discovery, implicit invocation,
or behavior across an independently restarted client. Those remain a packaging/runtime
gate, not a blocker for continued explicit-source development.

## Reproduction and safety

`scripts/read_profile_context.py` is a read-only development helper returning exact
Markdown, active filename and hashes. It does not invent a Markdown parser/schema or
derive numeric rules from style. Installed Skills remain self-contained and need not
depend on the repository helper; Codex interprets clearly applicable explicit rules.

`tests/workspace/profile_check_fixture.py` actions start/a/b/restore operate with an
explicit Workspace and private --state path. Use only an unselected Profile Workspace
and approved writes. Restore refuses personal config/Profile changes rather than
overwriting them. Interruption between config/state writes recognizes either exact
generated config for restoration. No concurrent edits supported; state is a recovery
fixture artifact, not an authoritative runtime Profile cache.

Example (pass actual newly re-read Markdown rules to live Blender between switches):

```bash
python -B tests/workspace/profile_check_fixture.py start "D:/AI/GameAssetAI-Workspace" --state .local/profile-check-state.json
python -B tests/workspace/profile_check_fixture.py a "D:/AI/GameAssetAI-Workspace" --state .local/profile-check-state.json
python -B scripts/read_profile_context.py "D:/AI/GameAssetAI-Workspace"
python -B tests/workspace/profile_check_fixture.py b "D:/AI/GameAssetAI-Workspace" --state .local/profile-check-state.json
python -B scripts/read_profile_context.py "D:/AI/GameAssetAI-Workspace"
python -B tests/workspace/profile_check_fixture.py restore "D:/AI/GameAssetAI-Workspace" --state .local/profile-check-state.json
```

Do not use --force workspace creation or overwrite durable user rules for these tests.
