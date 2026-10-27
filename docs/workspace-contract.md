# Workspace Contract

This is the minimal filesystem/configuration contract, not a new asset-storage layout.
GameAssetAI is the development source; GameAssetAI-Workspace is personal runtime context.
Existing Unity, Unreal, Blender, mesh, rig, and animation files stay where they are.

## Creation and preservation

Run `python scripts/create_workspace.py "D:/AI/GameAssetAI-Workspace"` from the repository.
Python 3.10+ and its standard library are sufficient for the helper scripts.
The tested runtime is recorded in `docs/SESSION_STATE.md`; other versions are not yet tested.

- Use a new or empty directory outside the development repository.
- Repository roots, descendants, and ancestors are rejected, including resolved overlaps.
- Template/target symlinks and junctions, linked copy destinations, and file/directory
  collisions are rejected before target writes. The source template is validated first.
- Normal creation copies the template; it does not install skills or Blender MCP, open
  Blender, create engine projects, or access mapped projects.
- `--force` is an explicit merge/overwrite operation, **not** a safe workspace update.
  It replaces all same-named template files, including personal `AGENTS.md`,
  `config/projects.json`, and `config/active-profile.json`. Extra files remain.
  Back up the workspace yourself before intentionally using this option.
- Each copied file is staged beside its destination and replaced, not truncated.
  This preserves other hard-link targets and avoids truncation on copy failure.
- The entire operation is not transactional. An I/O failure can leave a partially
  created/merged workspace; completed replacements are not rolled back. No success is
  reported on failure. Avoid concurrent template or target modification.

The creation workflow is for first-time setup. Do not recreate a personal workspace
every session or use `--force` to switch games.

## Minimal runtime files

- `AGENTS.md`: stable instructions, not game-specific rules.
- `profiles/`: Markdown profiles.
- `config/active-profile.json`: active profile reference.
- `config/projects.json`: optional project mappings; `{"projects": {}}` is valid.

The full source template also includes READMEs, `_PROFILE_TEMPLATE.md`, and `notes/`.
These convenience files are checked when validating the source template, but are not
required by runtime workspace validation. Notes remain optional.
The source template must stay game-neutral: its active profile is `null` and its project
mappings are empty. Personal settings belong only in the generated workspace.

## Active profile

```json
{ "profile": "ExampleGame" }
```

This selects `profiles/ExampleGame.md` with exactly matching case. Use a non-reserved
filename stem, not an extension or path. Unicode names are supported. Empty names,
path separators, control characters, leading dots, trailing dots/whitespace,
Windows-invalid characters/device names, `README`, and `_PROFILE_TEMPLATE` are rejected.
The referenced profile must be a real, nonempty UTF-8 file, not a link.

`{ "profile": null }` is valid first-time state. Do not infer engine, art style,
budget, rig policy, or export destination when unspecified. Ask only when the task
depends on that missing information. There is no implicit profile inheritance.

Create a profile by copying `profiles/_PROFILE_TEMPLATE.md` to a new filename, recording
only known durable game rules, then editing `profile` in the JSON. Switch games by
changing that reference; preserve all other profiles and JSON metadata.
Profiles remain human-readable Markdown. Validation checks their reference and encoding,
not the completeness or correctness of art/topology/rig/export decisions.

## External project mappings

```json
{
  "projects": {
    "ExampleGame": {
      "unity": "D:/Games/ExistingUnity",
      "unreal": "E:/Games/ExistingUnreal",
      "blender": "D:/Art/ExistingBlenderFolder"
    }
  }
}
```

Project identifiers and path labels are nonempty strings; labels are not engine-enumerated.
Each value is a nonempty absolute Windows or POSIX path without control characters.
Windows backslashes must be escaped in JSON. Paths are stored without rewriting them.
Mappings do not have to match profile names and are not inferred from the active profile.
There is no default export destination inherited from a mapping.

Validation checks structure only: it does not access, move, create, or verify the existence
of mapped projects. The actual task must verify a chosen path before using it. A path
mapping alone does not authorize editing/exporting into that project.
`_comment` and other metadata are allowed; duplicate JSON keys and non-standard constants
are rejected. UTF-8 with or without a BOM is accepted.

## Verification boundaries

```bash
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
python -B scripts/validate_workspace.py "D:/AI/GameAssetAI-Workspace"
python -B scripts/validate_workspace.py "D:/AI/GameAssetAI-Workspace" --require-profile
```

The last command deliberately fails for an unselected profile. The validator is a
repository development helper, not an installed runtime skill dependency.
Offline tests verify creation, reference switching, and deterministic file reading.
They do **not** prove Codex automatically follows the active profile across real sessions.
That client behavior and Blender integration still need the manual foundation checks.
