# Static Object visibility-mask PNG validation

## Contract

`blender-render-object-mask-png` masks one exact static target Mesh against zero to 63
explicitly named static Mesh occluders. The request never treats every Scene Object as an
implicit participant. Union bounds of exactly these Objects define one stable orthographic
frame; unrelated Objects neither change framing nor appear in the render.

All Objects must be nonempty, render-visible, local base Meshes without parents,
constraints, modifiers, animation, Shape Keys or Edit Mode. Candidate fingerprints bind
each Mesh's vertices/edges/polygons, transform and name, along with Scene frame/unit state,
view, color, sampling and output.

## Isolated render

The authorized stage contains independent copies of only the reviewed Objects and records
their target/occluder roles. A hash-bound background job replaces all staged target surfaces
with a red emission ID shader and all occluder surfaces with green. The final conversion
keeps only red-dominant visible pixels in the requested opaque color. Green surfaces remain
opaque during depth evaluation, so they hide target pixels correctly, then become transparent
in the published RGBA8 PNG.

## Evidence and limits

Blender 5.0.1 passes 12 checks with a full target quad, a closer explicit half-width
occluder, and a distant unrelated Object that is proven absent from candidate/stage/framing.
The result contains 200 target pixels and 200 occluder pixels, alpha bounds `[3,2,12,21]`,
two RGBA values and stable artifact SHA-256
`ecb3ff36af1954adbea230d5a61dd486f660db324acad827585588eba85bec19`.
The fixture also proves source-drift and collision refusal, receipt binding and exact file
teardown.

This is not a multi-color ID atlas, implicit full-Scene render, evaluated/deformed workflow,
material mask, normal/depth/SDF pass, Unity import or visual-quality certification.
