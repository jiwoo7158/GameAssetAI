# Static 2D render candidate and framing validation

## Scope

The candidate stage joins a successful
`gameassetai.2d-static-render-request.v1` preflight to the current Blender source without
creating setup data or authorizing a render.

`scripts/inspect_2d_static_render_candidate.py` produces separate SHA-256 fingerprints
for the request, base Mesh/material source, Profile/view/lighting/style setup, and output
contract. `scripts/preview_2d_orthographic_framing.py` requires all four to remain fresh
before deriving a camera plan from world-space bounds.

## Live result — 2026-09-29

Blender 5.0.1 passed 17 synthetic checks through MCP:

- successful offline request binding and blocker-free candidate creation
- distinct source/setup/output fingerprints
- exact Mesh counts and world bounds
- square, portrait and landscape orthographic framing calculations
- source mutation detection and exact restoration
- stale candidate and stale request refusal
- unsupported modifier and future CEL-mode blocking
- no output file, Camera or render authorization
- original context preservation and exact synthetic ID teardown

The framing convention uses explicit unit vectors: `direction` points from the target
toward the camera, `up` is camera-local +Y, and `right = up × direction`. Blender's
`ortho_scale` follows the larger render dimension: horizontal span for landscape output
and vertical span for portrait output. The scale is fitted to both projected axes.
`framing_margin` is a fraction added on each side, so scale is multiplied by
`1 + 2 × margin`.

## Current supported candidate

The first implementation deliberately accepts only the narrow combination needed for the
next experiment: orthographic `PIXEL`, either no palette or an explicit opaque fixed
palette, disabled anti-aliasing, nearest-neighbor intent and owned neutral lighting.
The broader request vocabulary for CEL, FLAT_TOON, automatic palettes and copied source
lighting is retained but blocked until each path has an implementation and Blender
regression. Translucent fixed-palette colors also fail closed in the first implementation.

Parents, constraints, modifiers, animation, Shape Keys, linked library data and image/group
material nodes are blockers for this first static path. This is not a statement that those
inputs are invalid assets; it prevents an unevaluated base-Mesh fingerprint from being
misrepresented as complete render evidence.

The plan uses base Object `bound_box`, not evaluated deformation, and creates no Camera in
the interactive process. The reviewed plan has now been applied successfully in a separate
factory-startup Blender render probe; see `docs/2d-static-render-validation.md`. The next
gate is a narrow Pixel render configuration and structural pixel/alpha validation.
