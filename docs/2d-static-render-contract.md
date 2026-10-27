# Static 3D-to-2D render request contract

## Purpose

`gameassetai.2d-static-render-request.v3` is the current fail-closed input boundary for
static 3D-to-2D output. It keeps reusable mechanics separate from game-specific choices
and binds every accepted request to one exact Scene, Object and output path. The validator
continues to read v1 as legacy no-outline input and v2 as legacy no-shading input.

`scripts/validate_2d_static_render_request.py` validates and hashes the request without
reading a Workspace, opening Blender, creating a directory or authorizing a render.
Passing this gate means only that the request is structurally complete and the target is
currently collision-free; Blender state and target freshness must be checked again before
preview and publication.

## Sections

- `profile`: either all-null for a fully explicit non-Profile request, or the exact active
  Profile name plus the lowercase SHA-256 values of both its reference JSON and Markdown.
- `view`: orthographic projection, explicit perpendicular unit direction/up vectors and a
  finite framing margin. Direction means the direction from target toward camera.
- `lighting`: explicit use of copied source lighting or future owned neutral lighting,
  plus an explicit transparent-background decision.
- `style`: explicit Pixel/Cel/Flat Toon intent, output resolution, anti-aliasing and
  nearest-neighbor policy, NONE/AUTO/FIXED palette policy, an explicit outline policy,
  and in v3 an explicit shading policy. The implemented outline is either `NONE` with
  null color/width 0, or `OUTER` with one opaque RGBA color and width 1. Shading is
  either `NONE` with null `value_steps`, or `VALUE_STEPS` with an integer from 2 through
  32. Value steps quantize HSV value before palette processing while preserving alpha
  and RGB channel ratios; they do not select a game-specific look.
- `output`: one absolute `.png` target, RGB/RGBA, 8/16-bit depth and mandatory
  `overwrite: false`.

No field is silently filled from a preset. The Profile hashes record provenance but do
not cause this validator to interpret Markdown. A caller must read applicable explicit
Profile rules, construct the request, then retain these hashes for freshness checks.

## Safety and current limits

- Unknown and missing fields are refused at every nesting level.
- Numeric values must be finite. Camera vectors must be unit length and perpendicular.
- Output parents must already exist and contain no link/reparse component.
- Existing PNGs and sibling Unity `.meta` files are collision blockers.
- Invalid or Windows-reserved output stems are refused on every platform.
- Validation is read-only and produces a canonical request SHA-256 only on success.
- The accepted style and lighting identifiers are contract vocabulary, not proof that
  their Blender implementations exist. A later candidate inspection must advertise and
  check supported combinations before rendering.

Nine offline regressions cover stable hashing/no writes, Profile provenance, camera
geometry, palette modes, v1/v2 compatibility, v3 outline/shading policies, output
collisions, exact nested fields and nonfinite refusal.
