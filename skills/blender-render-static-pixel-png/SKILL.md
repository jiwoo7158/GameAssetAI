---
name: blender-render-static-pixel-png
description: Render one simple static Blender Mesh as a new orthographic pixel-style PNG through an isolated background Blender process. Use for a single transparent game sprite or icon when the source has no rig, animation, modifiers, constraints, parent, Shape Keys, linked data, image textures, or node groups. Supports explicit RGBA8 output, deterministic palette reduction, optional value-band shading, and an optional one-pixel outer silhouette; does not support CEL/Toon, animation, overwriting, or engine import validation.
---

# Render Static Pixel PNG

Render one reviewed Mesh to one new PNG while keeping the interactive Blender Scene and
global Render Result untouched. Treat the source Mesh, materials and current file as
user data. Do not save the current `.blend`.

## Required inputs

Collect exact values before rendering:

- `scene_name` and one `object_name`
- absolute new `.png` target path in an existing non-linked directory
- orthographic unit `direction` and perpendicular unit `up`
- resolution and framing margin
- transparent-background choice
- palette mode `NONE`, `AUTO` with an explicit maximum from 2 through 256, or `FIXED`
  with explicit opaque RGBA colors
- shading mode `NONE`, or `VALUE_STEPS` with an explicit integer from 2 through 32
- outline mode `NONE`, or `OUTER` with one explicit opaque RGBA color and width `1`
- one settings source: either a complete explicit view/lighting/style set, or the complete
  active Profile `gameassetai-2d-preset` block; never merge the two
- active Profile name/reference/profile hashes when the preset is used; otherwise use all
  three Profile fields as `null` and do not invent or reuse game rules

The first version requires `PIXEL`, `OWNED_NEUTRAL`, disabled anti-aliasing,
nearest-neighbor intent, RGBA 8-bit output and `overwrite: false`. AUTO uses a
deterministic weighted median-cut RGB palette, preserves every alpha byte, ignores fully
transparent RGB during palette generation and records the derived RGBA8 palette.
The optional outer outline is applied after palette processing, preserves all existing
visible pixels and may add one color beyond the requested palette maximum.
`VALUE_STEPS` bands the rendered HSV value before palette processing, preserves alpha and
RGB channel ratios, and does not imply a game-specific shadow/highlight art direction.

## Workflow

1. Call Blender MCP status and Scene inspection first. Refuse a disconnected or
   incompatible target rather than assuming Scene state.
2. Load these helpers into one shared Blender execution namespace, in order:
   `validate_2d_static_render_request.py`,
   `extract_2d_profile_preset.py`, `resolve_2d_profile_preset.py`,
   `inspect_2d_static_render_candidate.py`,
   `preview_2d_orthographic_framing.py`,
   `stage_2d_static_source.py`, and `build_2d_staged_render_job.py`.
3. For Profile settings, freshly read the active Profile context and resolve
   `STATIC_RENDER`; retain its complete four-hash binding. An absent or invalid preset is
   not a default. For explicit settings, do not consult or partially merge a preset. Build
   the exact `gameassetai.2d-static-render-request.v3` dictionary. Run request
   validation, candidate inspection and framing preview. Report blockers. Do not write
   files when any status is not ready/reviewable/planned.
4. Confirm the user has explicitly requested this render and exact target/settings. If a
   Profile preset supplied settings, reread and resolve it with the retained
   `expected_binding` immediately before staging; refuse any change. Then create unique
   sibling paths matching
   `.gameassetai-2d-<token>.stage.blend` and
   `.gameassetai-2d-<token>.job.json`. Call `stage_2d_static_source(...,
   authorize=True)`, then `build_2d_staged_render_job(..., authorize=True)` in the same
   request and namespace. Never reuse an old preview, stage or job.
5. Start a separate background Blender with the staged blend loaded. Run
   `render_2d_staged_source.py` and pass `--job`, the returned `--job-sha256`, and
   `--helper-root` pointing to this Skill's `scripts` directory. Do not run the renderer
   in the interactive Blender process.
6. Accept success only when the child result is `created`, `png_published` is true, the
   receipt hashes are present, and the exact target is a new regular PNG. Report its
   path, dimensions, SHA-256, alpha bounds, color count and receipt SHA-256.
7. Remove only the exact owned job and source-stage paths created by this request after
   success or handled failure. Never delete or replace the target, its `.meta`, a user
   `.blend`, or an unknown pre-existing file. Reinspect the interactive Scene and report
   whether its object inventory changed.

## Fail closed

Do not proceed when the target or target `.meta` exists, any reviewed hash changes, a
temporary path collides, the source has unsupported dependencies, or the child process
cannot verify the exact job/stage hashes. Leave the source untouched and state the
specific blocker. A failed render must not be described as a usable artifact.

## Boundaries

This Skill does not promise silhouette cleanup, texture sampling, perceptual AUTO palette
quality, inner/variable-width outlines, CEL/Flat-Toon materials or lighting, animation frames, rig handling, byte-identical Blender
PNG containers, Unity import suitability, or general 3D asset creation. Add those as
separately tested later stages rather than silently widening this workflow.
