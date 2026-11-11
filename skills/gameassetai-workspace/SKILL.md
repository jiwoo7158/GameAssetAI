---
name: gameassetai-workspace
description: Create, connect, validate, diagnose, and safely update a GameAssetAI Workspace; manage persistent game Profiles and inspect catalogs without overwriting personal data.
---

# GameAssetAI Workspace

Use this Skill for onboarding, Workspace connection or diagnosis, Profile management, catalog
inspection, and project-path guidance. Route asset creation to `gameassetai-create-asset`, existing
asset revision to `gameassetai-modify-asset`, and publication/export to
`gameassetai-output-asset`.

## Runtime boundary

An installed Skill contains `scripts/gameassetai.py`, `runtime/`, catalog data, and a Workspace
template. Run commands from that installed Skill directory; do not import a development checkout.
The normal project-scoped product is a verified `dist/workspace` clone whose four Skills are
already under `.agents/skills/`. Initialize its personal state once from the clone root:

```text
python .agents/skills/gameassetai-workspace/scripts/gameassetai.py workspace init-clone .
```

This command refuses arbitrary nonempty directories and Git repositories. It requires valid
distribution metadata and Skill hashes, adds only missing personal `config/` and `profiles/`
state, and is safe to rerun. It never replaces an existing Profile or setting.

For a fresh project-scoped install, do not install into an unrecognized folder first. From the
development/distribution environment run the integrated sequence:

```text
python scripts/gameassetai.py package install-project <bundle> <workspace> --template workspace-template
python scripts/gameassetai.py package validate-install <workspace>/.agents/skills
```

This creates or connects and validates the Workspace before installing and validating all four
Skills. Create and select the Profile only after those steps. User-scoped installation into the
user's `$HOME/.agents/skills` may happen before a Workspace exists. Leave legacy `.codex/skills`
installations in place unless the user explicitly chooses a reviewed migration, and warn when the
same Skill name is installed at both project and user scope.

Typical installed commands:

```text
python scripts/gameassetai.py workspace create <path>
python scripts/gameassetai.py workspace connect <path>
python scripts/gameassetai.py workspace validate <path> --require-profile
python scripts/gameassetai.py profile create <workspace> <id> --name <name> --description <text>
python scripts/gameassetai.py profile select <workspace> <id>
python scripts/gameassetai.py profile show <workspace> [--profile <id>]
python scripts/gameassetai.py profile get <workspace> <setting> [--profile <id>]
python scripts/gameassetai.py profile set <workspace> <setting> --value-json <json> [--profile <id>]
python scripts/gameassetai.py workspace output-root <workspace> [--set <absolute-directory> | --clear]
python scripts/gameassetai.py catalog list styles
```

## Procedure

1. Resolve the exact user-selected Workspace path and validate or connect it before any edit.
2. Read `config/active-profile.json` and the selected JSON Profile. Do not use chat memory as the
   durable game configuration.
3. Distinguish a one-asset instruction from a durable game-wide rule. Update a Profile only when
   the user explicitly requests or approves persistence. Ask before resolving a conflict or an
   ambiguous game-wide change.
4. Use `profile get` before `profile set`. Set one dot-separated mutable field at a time with a
   JSON value; untouched fields are preserved and the complete Profile is validated before atomic
   replacement.
5. Validate the Workspace again and report the exact Profile and setting changed.

Valid durable areas include `styles.three_d`, `styles.two_d`, `art_direction.palette`,
`art_direction.rules`, nested `asset_defaults`, `rig_animation`, and `output_defaults`. Do not
invent missing rules. Official `styles.three_d` accepts only a registered 3D id or null, and
`styles.two_d` accepts only registered 2D ids. Put user-specific descriptive style rules under art
direction instead of inventing catalog ids. A request such as changing one sword's handle is not a
game-wide rule.

Workspace results are allocated by the output Skill and shared Runtime under
`<selected-root>/<active-profile>/<catalog-category>/<asset-id>/<number>-<purpose>/`; the internal
root is `<workspace>/outputs`. An explicit task root overrides Profile `output_defaults.root`,
which overrides `settings.preferences.output_root`, which overrides the internal root. An external
root must be an existing real absolute directory explicitly chosen by the user; a project bookmark
does not authorize it. Do not recreate a moved/deleted external root. Moving or deleting results
is normal user management and must not change Workspace validity or Profile state.

`config/projects.json` contains optional absolute-path bookmarks. The current CLI validates this
file but does not provide a project-mapping write command; explain the schema and validate after a
careful manual edit. A bookmark never authorizes modifying the target. `unity-workbench` remains
optional and explicit-request only.

Existing valid v2 Workspaces connect without changes. Recognized legacy/Markdown-Profile
Workspaces are reported as migration-required and are not converted automatically. Preserve them,
make a separate backup, and follow the documented manual migration review.

Do not install Blender, Blender MCP, external AI models, or Unity as a side effect. On failure,
report the exact validation or safety error; never use a force-overwrite fallback.
