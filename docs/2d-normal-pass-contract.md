# Static normal-pass request contract

This checkpoint defines normal meaning before any Blender renderer or Skill is created.
The narrow v1 contract is `gameassetai.2d-normal-pass-request.v1` for one exact static Mesh.

## Coordinate and encoding contract

- `space`: `CAMERA_BASIS` only.
- basis X is camera right, basis Y is camera up, and basis Z is camera back, pointing from
  the framed subject toward the camera. A front-facing normal therefore has positive Z.
- `source`: `SHADING_NORMAL` only. It is intended to respect the base Mesh's flat/smooth and
  split-normal shading state; geometric-face and tangent-space alternatives are not inferred.
- `encoding`: `SIGNED_XYZ_TO_UNORM_RGB`, independently mapping each normalized component
  from `[-1,1]` to `[0,255]` by the eventual renderer's documented rounding rule.
- visible alpha is 255; background is canonical transparent black `[0,0,0,0]`.

The request also fixes an explicit orthographic direction/up pair, whole-Object framing
margin, resolution, disabled anti-aliasing, nearest-neighbor sampling and a new no-overwrite
RGBA8 PNG target. World-space, object-space, tangent-space, geometric normal, octahedral
encoding, anti-aliased output, modifiers and animation are not part of v1.

## Current evidence and next gate

Four offline tests verify deterministic request hashing, the exact camera-axis report,
rejection of alternative/inferred spaces and sources, fixed encoding/background/sampling,
and collision-safe RGBA8 output policy. A read-only Blender 5.0.1 candidate probe uses a
flat tilted triangle with world normal `(1,1,1)/sqrt(3)`. Under right `+X`, up `+Z`, back
`-Y`, it reports camera components approximately `[+0.577,+0.577,-0.577]` and encoded RGB
`[201,201,54]`, with no file creation or Scene-count change.

The next implementation gate is an isolated staged shader/render probe that demonstrates
actual flat and smooth shading-normal pixels. That Blender 5.0.1 probe now passes eight
checks after reopening its owned stage. It found two implementation-critical behaviors:

- `SHADING_NORMAL` is face-forward. A back-facing flat triangle whose geometric reference
  is `[201,201,54]` renders approximately `[54,54,201]` after Blender flips the shading
  normal toward the viewer.
- even with `Raw`, zero filter size and no anti-aliasing, the directly rendered flat region
  contains four nearby RGBA8 values (`[53..55,53..55,201..202,255]`). The smooth sphere
  produces 282 values as expected from interpolated normals.

Therefore the production path must not treat direct shader-to-PNG bytes as exact vector
encoding. An in-memory float readback was also probed in Blender 5.0.1 background mode:
`write_still=True` left no usable Render Result, while `write_still=False` with both the
default invocation and `EXEC_DEFAULT` exposed only a `Render Result` image of size `0x0`.
The next gate is consequently an owned float OpenEXR stage, followed by deterministic CPU
face-forward and signed-to-UNORM RGBA8 encoding. That fallback now passes: Blender writes
and reloads an owned 32-bit RGBA OpenEXR, CPU round-to-nearest conversion collapses the flat
region to exactly `[54,54,201,255]`, the smooth region retains 282 encoded values, and the
EXR/PNG/stage files are all removed. The guarded `blender-render-normal-pass-png` Skill now
uses this path and passes an eleven-check Blender 5.0.1 end-to-end regression from both its
repository source helpers and installed Skill helpers. Refreshed-client discovery and one
natural-language host render remain; no user normal-pass output has been requested yet.
