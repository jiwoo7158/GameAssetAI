# Alpha-derived silhouette mask validation - 2026-09-30

## Scope

`derive-png-silhouette-mask` creates one new solid-color RGBA8 PNG from the alpha channel
of one exact existing RGBA8 PNG. It is a deterministic downstream postprocess, not a
Blender geometry render, material/object mask, outline, normal or depth pass.

The v1 request binds source path and lowercase SHA-256, a new target path, one explicit
opaque normalized RGBA color, `overwrite: false`, and one of two alpha policies:

- `BINARY_NONZERO`: every source alpha above zero becomes 255;
- `PRESERVE_ALPHA`: visible RGB changes while every source alpha byte is retained.

The read-only validator refuses unknown/missing/duplicate fields, non-standard JSON,
linked or malformed paths, non-RGBA8/interlaced/unbounded PNGs, stale hashes, empty alpha,
source/target identity, existing target/`.meta`, invalid colors and inferred policies. It
reports exact dimensions, visible/partial-alpha counts, request hash and candidate fingerprint.

Authorized publication rereads the source and request, requires the exact fresh candidate,
encodes a canonical non-interlaced RGBA8 PNG, verifies a same-directory stage byte/pixel
readback, and hard-links it to a new target. Failure removes only the invocation-owned
unchanged artifact. A simulated concurrent modification is retained and reported rather
than deleted.

## Evidence

Six offline tests cover read-only candidacy, exact binary output, alpha preservation,
authorization/stale/collision/policy refusal, post-link rollback and concurrent-change
preservation. Packaged helper bytes match repository sources and Skill Creator validation
passes.

A real retained batch render was processed without Blender invocation:

- source: `D:/Blender/MCP_Test/gai_batch_881faa3c7353_front_static.png`
- source: 96x96, 5,004 bytes, SHA-256
  `fea35408bd6ae23189f5d67f239b8b785aaa27e7a0b63b09f00a264159a75e4c`
- source visible pixels: 4,958; partial-alpha pixels: 0
- output: `gai_batch_881faa3c7353_front_static-mask.png`
- output: 257 bytes, SHA-256
  `b9f5fbf94138a3850c040751cdd1f9f7f5dfe28b66eddd8d19a9876f4a102b0e`
- output alpha bounds: `[9,9,86,86]`; unique RGBA: 2; partial alpha: 0
- receipt SHA-256:
  `16835934ba001635b187da658f959f693d6dc2bfd6ac89fe4f8e1b42f27e3c96`

Visual inspection shows the expected white silhouette on transparency. The source hash is
unchanged and no owned stage remains. This validates an alpha silhouette only; material IDs,
occluded geometry, normals, linear depth, signed distance and Unity import remain separate.

The four-file portable archive is
`.local/source-bundles/derive-png-silhouette-mask.zip`, SHA-256
`a70739ebdad94d59f951d381ad4865c5c964ea12cc946643649db7aece3542d2`.
The Skill is installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/derive-png-silhouette-mask`; deployment
validation reports `aligned`. Refreshed-client discovery and one natural-language call
remain separate host evidence.

The user subsequently confirmed refreshed-client exposure. The client accurately described
RGBA8 input, explicit color, `BINARY_NONZERO`/`PRESERVE_ALPHA`, source preservation,
hash/fingerprint review, no-overwrite publication and receipt facts, while refusing Blender,
automatic color/threshold inference, material/object masks, normals/depth/SDF, outlines,
slicing, Unity import and linked/non-RGBA8 inputs. It created no file. One natural-language
authorized publication to a new target remains the final host gate.
