# Source packaging and regression

Current use is local installation/testing in GameAssetAI-Workspace, not external
distribution. The source ZIP experiments below are retained as historical
development evidence; no public release work is planned.

Fourth Skill update: `docs/coplanar-apply.md`. Latest versioned directory
`.local/source-bundles/coplanar-20260918/` contains four historical source ZIPs. Run `all` for the
earlier three there; current fourth uses `coplanar-skill` with
`.local/source-bundles/separate-tolerances-20260918/`. Source/bundle evidence is distinct from
installed-client behavior. No installed copy is automatically overwritten.

Packaging is separate from Blender work. No package tool installs MCP, changes the
client configuration, connects to sockets, uploads files, or creates game assets.

## Source bundles

```bash
python -B scripts/package_skill.py skills/blender-inspect-asset --output .local/source-bundles/blender-inspect-asset.zip
python -B scripts/package_skill.py skills/blender-validate-static-mesh --output .local/source-bundles/blender-validate-static-mesh.zip
```

Each ZIP contains a top-level skill directory with SKILL.md and its actual resources.
Files are byte-preserved; timestamps/permissions are fixed for repeatable ZIP output in
the same tool environment. Existing archives and outputs inside the source skill are
rejected, never overwritten. Links/reparse points and invalid Python resources are rejected;
Python bytecode/cache/VCS debris are omitted. Sources must not change concurrently.

The scanner checks the literal name/description header used by these source skills and
Python syntax; it is not a complete YAML semantic validator. Authoring verification uses
skill-creator's `quick_validate.py` with PyYAML in an isolated uv development environment.
Core repository/workspace/packaging/payload helpers remain standard-library-only.

These ZIPs are **portable development source bundles**, not proof that a particular
client accepts ZIP upload or that installation/discovery/release has passed. Do not
mark stable packaging/release roadmap items complete merely by producing them. Installed
copies are deployment artifacts; edit/retest the repository sources, then deploy again.

## Explicit local deployment and next runtime gate

Official OpenAI documentation currently lists `$CWD/.agents/skills` as a local Codex
discovery location. Sources remain under this repository's `skills/`; installed copies
are optional deployment artifacts, not a new required workspace contract or asset folder.
Source: [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills), checked 2026-09-16.
The user confirmed actual session exposure and explicit calls for all three Skills;
read-only natural-language outcomes were subsequently confirmed by the user. Raw routing
traces remain absent. Do not rename existing user skill directories.

```bash
python -B scripts/deploy_skill.py skills/blender-inspect-asset --skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"
python -B scripts/deploy_skill.py skills/blender-validate-static-mesh --skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"
```

This copies validated resources, hashes and byte-verifies them, rejects overlaps,
links/junctions in destination ancestors, and refuses every existing skill directory.
There is no overwrite/update switch. Failure cleanup uses only exact newly created
files/directories, not recursive deletion. Parent discovery folders may remain after
failure; interruption may leave a partial deployment, which a retry refuses. No
concurrent edits are supported. This does not install MCP or change global settings.

The personal Workspace above was newly created with approval and both skills copied
and byte-verified on 2026-09-16. It validates with an intentionally null active Profile
and empty project mappings. No existing game project was accessed.

The Workspace source-folder/session check and explicit synthetic Profile data-flow tests
are complete; do not request setup again. See `skill-session-validation.md` for the remaining
raw routing/authorization evidence. The three read-only outcomes passed; the user has
subsequently passed instruction-led synthetic copy-apply/restore; do not request a repeat.
The development session can read the Workspace and explicitly run installed helper sources
through Blender MCP. This passed directly; another conversation is not required to repeat
helper tests. Its supplied catalog cannot be refreshed by an available tool, so automatic
host selection remains a separate evidence boundary. A behavioral
failure is not grounds to reconfigure MCP or alter global installations blindly.

## Reproducible live regression payload

```bash
python -B scripts/prepare_blender_check.py --suite all
```

This prints JSON containing `code` and SHA-256 of the exact helper/test sources. Pass
`code` to the currently exposed Blender Python-execution tool with the user's actual
request. The payload does not assume Blender can read repository or installed-skill paths.
It compiles helpers in a separate execution namespace and executes the tests sequentially.
Available suites: `inspection`, `static-mesh`, `all`.
The sequentially tested third suite `loose-cleanup` is also included in `all`.
Its helper ZIP is `blender-cleanup-loose-geometry.zip` and deployment uses the same
explicit no-overwrite tool as the two earlier Skills.

To test the actual bundled helper bytes instead of repository helpers, add
`--bundle-dir .local/source-bundles`. Test harnesses still come from the repository.
Missing ZIPs/resources fail explicitly without falling back to repository helpers.
The earlier ZIP-helper run passed 36 inspection + 73 diagnostics checks. The latest
combined run additionally passed 57 copy-cleanup checks: **166 total**.
That 166-check count is historical. The current cleanup harness adds three preservation
checks; direct installed runs now pass 36 + 73 + 60 = 169. Current bundle locations are
listed at the top; older archives are historical and must not be silently substituted.
Same-dictionary exec globals/locals and separately compiled sources are regression-tested.

Inspect addon status and Scene first. Fixture tests require an Object-mode window and
authorized synthetic changes. They do not force the user's starting mode or save a file.
Generated fixtures have exact invocation-owned IDs; source fingerprints, context, and
tracked datablock names must match after cleanup. Stop if cleanup/preservation fails.
Only synthetic fixture operators change mode/selection/transforms. Inspection/diagnostic
helpers are read-only; cleanup apply edits only new independent invocation-owned copies.
A previously clean file may become dirty through fixture setup or retained copied output.

Offline tests:

```bash
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
python -B -m unittest discover -s tests/scripts -p "test_*.py" -v
python -B scripts/validate_repo.py
```

The offline suites test filesystem/source/payload/package invariants; they do not replace
the live Blender suites. Inspection/static diagnostic evidence is in the corresponding
validation documents. Explicit current-session Workspace switching passed; automatic
raw routing/authorization evidence remains a release gate; fresh Workspace A/B/null Profile
behavior passed by user report;
exposure, explicit calls and three read-only outcomes were confirmed by the user.

## Deployment drift check

```bash
python -B scripts/validate_skill_deployment.py skills/blender-cleanup-loose-geometry "D:/AI/GameAssetAI-Workspace/.agents/skills/blender-cleanup-loose-geometry"
```

Repeat for the other Skills. The validator reports aligned/drift/error and missing,
extra or changed resource hashes without writing either tree. Cache/bytecode exclusions
match source packaging; invalid Python/linked components fail. Exit 0 means byte-aligned
resources, not that Codex discovers or executes the Skill. All three actual deployed
Skills were aligned on 2026-09-16. Do not overwrite a drifted personal copy automatically.
See `docs/release-checklist.md` for the unverified release gates.

## Direct installed-helper regression

```bash
python -B scripts/prepare_blender_check.py --suite all --installed-skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"
python -B scripts/prepare_blender_check.py --suite coplanar-skill --installed-skills-dir "D:/AI/GameAssetAI-Workspace/.agents/skills"
```

Pass emitted code to live MCP only after inspecting current Scene/addon and confirming
synthetic-test scope. Helpers come from the explicit installation, harnesses from this
repository. Missing/invalid/linked installed sources fail; no repository/ZIP fallback.
Origin options cannot be combined. Sources must not change concurrently. Text SHA-256
is calculated after UTF-8/BOM/newline decoding; use the deployment validator for raw byte
alignment. These runs passed 169 + 162 = 331 native checks with exact fixture teardown.
This proves explicit installed helper behavior, not automatic Skill discovery or routing.

## Conservative local update and recovery

First installation still uses `deploy_skill.py` and refuses an existing directory.
`update_skill.py` now provides a separate hash-bound update transaction. Its read-only
`plan` records exact source and installed manifests plus a new explicit backup path.
`apply` refuses if either tree changed, stages and verifies the complete new Skill before
directory promotion, retains the exact previous installation at the backup path, and
restores it if promotion fails. It never silently merges drift or follows links.

```bash
python -B scripts/update_skill.py plan SOURCE INSTALLED --backup NEW_BACKUP_PATH
python -B scripts/update_skill.py apply UPDATE_PLAN.json
python -B scripts/update_skill.py restore UPDATE_PLAN.json --replaced NEW_REPLACED_PATH
```

The JSON printed by `plan` must be saved unchanged as `UPDATE_PLAN.json`; this separation
makes the manifest and paths reviewable before mutation. `restore` is also non-destructive:
it moves the currently installed new version to the unused `--replaced` path, verifies
both manifests, and moves the retained backup back into place. A changed current version,
changed backup, existing backup/replaced path, overlap, link, invalid Python resource or
unavailable parent refuses before mutation. Client discovery/refresh remains separately
`not_verified` after either operation.

Offline tests cover aligned no-op, exact backup retention, source/installation drift,
existing-backup refusal, injected promotion failure rollback, restore, changed-backup
refusal and the full CLI plan/apply/restore flow from another working directory. Hard
process interruption, concurrent filesystem writers and discovery refresh still cannot
be guaranteed. Do not delete an entire `.agents/skills` folder, use workspace creation
`--force` as repair, or update a drifted/personal copy without reviewing its exact plan.
After an update, use a fresh Blender preview and rerun deployment alignment and the
relevant installed-helper regression before discarding any retained recovery version.
