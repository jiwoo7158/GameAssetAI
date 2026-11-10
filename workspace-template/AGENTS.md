# GameAssetAI Workspace Instructions

This is a persistent user Workspace, not the GameAssetAI development repository. Durable game
rules live in JSON Profiles, not in chat memory.

## Before every game-specific task

1. Validate this Workspace and read `config/active-profile.json`.
2. Load the exact selected file from `profiles/`. If no Profile is active, do not invent a game
   concept, style, budget, Rig policy, render setup, or export destination.
3. Read the current text request and identify each user-supplied reference image as concept, front,
   side, back, three-quarter, or another explicit role. A user-generated AI concept image is an
   input to 3D work; a Blender render is a review preview; a game PNG/pixel sprite/sprite sheet is
   a later output. Never treat one stage as another or assume a missing image exists.
4. Compare the request and references with the active Profile. Explain a style conflict instead of
   silently ignoring either source.
5. Distinguish an asset-local request from a durable game-wide rule before changing the Profile.
6. Inspect the current Blender Scene and exact targets before modifying existing data.

## Durable Profile information

A Profile may store only information the user supplied or approved, including:

- game name, concept, and durable art direction;
- independent 3D and 2D styles;
- palette, design, silhouette, and game-specific proportion rules;
- material and texture rules;
- camera and rendering rules;
- Rig and animation policy;
- output formats and engine-related settings;
- cross-asset production rules and persistent style characteristics learned from references.

Fields are optional where the schema permits. Do not fill gaps by guessing. Character, weapon,
environment, and other asset families in the same game share this Profile unless an explicit
asset-local override applies.

## Profile changes

"Make this sword handle red" is local to that asset. "Keep every weapon in this game red and in
this style" may be a durable rule. Update a Profile only when persistence is explicit or the user
approves it. If a requested rule conflicts with existing settings or has multiple reasonable
interpretations, ask before changing it. Never copy a rule into another game's Profile.

Use the installed Workspace Skill to read the exact setting before changing one field, then
validate after the atomic update:

```text
python scripts/gameassetai.py profile get <workspace> art_direction.palette
python scripts/gameassetai.py profile set <workspace> art_direction.palette --value-json <json>
python scripts/gameassetai.py workspace validate <workspace> --require-profile
```

The CLI preserves fields not named by the update. It does not automatically infer rules from an
image, merge arbitrary Profile documents, or migrate a legacy Markdown Profile.

## Data and output safety

Paths in `config/projects.json` are bookmarks, not write authorization. Existing Blender files,
meshes, Armatures, Actions, materials, images, source references, and game projects may live
anywhere; preserve them and prefer a copy or checkpoint. `unity-workbench` is optional and may be
used only when the user explicitly requests it.

Store generated deliverables under `outputs/<game>/<asset-category>/<run-id>/` unless the user
chooses another destination. `outputs/` is disposable product state: deleting it removes those
deliverable copies but must not affect Profiles, settings, installed Skills, catalogs, or future
work. A previous run is input only when the user explicitly selects it.

Catalog registration is not proof that a generator exists. Stop downstream Rig, animation, 2D,
and export work when a source fails visible or semantic review, and report unsupported work
honestly.
