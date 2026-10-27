# Optional Profile-backed 2D preset contract

## Purpose

Game-specific 2D choices remain in the existing Workspace Profile Markdown. A Profile may
contain exactly one fenced `gameassetai-2d-preset` JSON block with schema
`gameassetai.2d-profile-preset.v1`. No sidecar file or new Workspace directory is introduced.

No active Profile or no exact block returns `absent`, not an inferred default. Ordinary prose,
headings and near-matching code blocks are never parsed as machine settings.

## Complete preset

The optional block is deliberately complete rather than a partial merge. It contains exact
static-v3 `view`, `lighting` and `style` objects plus:

- `sequence.playback_fps`: explicit finite value in `(0, 240]`;
- `sprite_sheet.padding`: explicit integer from 0 through 256;
- `sprite_sheet.order`: `ROW_MAJOR_TOP_LEFT`.

Static settings are passed through the existing v3 validator. Output directories, filenames,
Scene/Object/Armature/Action names, frame ranges and sprite-sheet columns/rows remain request-
specific and cannot be stored or guessed by this first preset.

## Provenance and freshness

`extract_2d_profile_preset.py` accepts only a `gameassetai.profile-context.v1` result with
active Profile name, absolute path and reference/Profile SHA-256 values. It does not reread or
write the Workspace. `resolve_2d_profile_preset.py` selects one complete purpose-specific
setting set and binds the Profile reference, Profile content and canonical preset hashes.
Before output, a caller must reread the Profile context and resolve with the exact prior binding.
Any changed/absent Profile is refused by the calling Skill; prior settings are never reused.

The static PNG, Action PNG-sequence and sprite-sheet Skills now support this resolver. Each
request chooses either complete explicit settings or the complete active preset; partial merging
is forbidden. Sprite-sheet v2 records all four provenance fields in its request and metadata;
legacy v1 remains readable without claiming Profile provenance.

Eleven offline tests cover null/unconfigured absence, valid extraction, purpose-specific
resolution, static/Action request construction, stable binding, changed/absent context refusal,
duplicate/malformed/unknown fields, strict values and missing provenance. A no-write loader also
passes against every source and Workspace-installed Skill helper tree.
