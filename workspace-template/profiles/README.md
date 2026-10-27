# Profiles

Each profile contains durable game-specific asset rules.

Profiles should contain only information that is useful across repeated asset tasks for that game.

Typical fields:

- target engine
- art direction
- platform
- modeling constraints
- texture constraints
- rig / Mixamo policy
- animation policy
- existing-asset preservation rules
- export preferences

Do not add values simply to fill the file.

Unknown values can remain unspecified.

An optional complete machine-readable 2D render preset may be embedded in the same Markdown
using one unindented `gameassetai-2d-preset` fenced JSON block. See `_PROFILE_TEMPLATE.md` and
the repository's `docs/2d-profile-preset-contract.md`. Leave the block absent rather than
inventing unknown view, style, timing or sprite-sheet choices.
