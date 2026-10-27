# Isolated static PNG render validation

## Result — 2026-09-29

Blender 5.0.1 passed an eight-check write-capable probe using a separate process:

```text
blender.exe --background --factory-startup \
  --python tests/rendering/run_2d_background_render.py -- \
  --artifact-root D:/GitHub/GameAssetAI/.local/validation \
  --repo-root D:/GitHub/GameAssetAI
```

The latest probe created only factory-startup data in that process, validated one complete
v1 request, reviewed its Blender candidate, calculated a hash-bound orthographic framing
plan, created owned Camera/light data from that plan, and rendered one 32×24 PNG with
8-bit RGBA. It published through a no-overwrite hard link, confirmed that a second
publication was refused, and deleted both the unique stage and published files.

The latest **18 checks** passed: factory/background isolation, request preflight,
candidate review, framing/fingerprint binding, zero-width reconstruction filter,
initially absent targets, stage creation, PNG dimensions/RGBA8 decoding, visible alpha
subject and margins, fixed-palette mapping with alpha preservation, byte-identical
publication, receipt binding, collision refusal, repeated-render pixel identity and exact
file teardown. The final quantized PNG had SHA-256
`f05cc66c70f79d21d2aaffc437f4c3368058b2912c15c5cef44855029daad942` for this run.

The decoded result contained 400 foreground pixels with alpha bounds `[6, 2, 25, 21]`,
zero partially transparent pixels and 39 source RGBA values. Fixed-palette processing
reduced the published output to three RGBA values without changing alpha. Two consecutive renders in
the same process decoded to identical RGBA pixels. Their PNG container bytes were not
identical, so artifact-byte determinism must not be claimed from Blender's PNG writer;
validation uses decoded pixel content and records each artifact hash separately.

`scripts/quantize_rgba.py` performs deterministic nearest-RGB mapping to an explicit
opaque fixed palette, preserves every alpha byte, canonicalizes fully transparent RGB and
encodes a minimal deterministic RGBA8 PNG. Five offline tests cover tie-breaking, alpha,
duplicates, refusals and PNG structure. AUTO palette generation is not implemented.

`scripts/build_2d_render_receipt.py` then reopens the published regular PNG and binds its
path, size, SHA-256 and structural pixel facts to the request, source, setup, output and
framing hashes. Four offline failure/success tests pass. The live receipt SHA-256 for this
run was `f2ac3cf6af452184c7cdc42590672053416103dbc3696b68daee76d2b0b475cb`.

The already-open interactive Blender was not used for rendering, so its global
`Render Result` was not overwritten. MCP inspection after the child process exited still
reported the original `Cube`, `Light`, `Camera` Scene with one material. No matching test
artifact remained under `.local/validation`.

## Boundary

This proves that the installed Blender executable can bind the v1 request to a synthetic
source Mesh, apply the reviewed framing plan and stage a structurally valid PNG in an
isolated process. It does not yet serialize an existing user Mesh into that child process,
implement palette/outline/shading operations or certify visual determinism across
machines. Production output must still recheck the destination immediately before
publication and bind the final artifact hash to a receipt.
