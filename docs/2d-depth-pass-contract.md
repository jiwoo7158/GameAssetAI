# Static camera-linear depth-pass request contract

This checkpoint defines depth meaning before any Blender depth renderer or Skill is created.
The narrow v1 request is `gameassetai.2d-depth-pass-request.v1` for one exact static Mesh.

## Coordinate, range and encoding contract

- `space`: `CAMERA_LINEAR` only.
- `source`: `BASE_MESH_POSITION` only. Modifiers, Shape Keys and animation are outside v1.
- the depth axis is the request's unit `view.direction`, pointing from the subject toward
  the camera (`camera_back_toward_camera`).
- `normalization`: `OBJECT_VERTEX_BOUNDS`. For each base-Mesh vertex world position `v`,
  compute `p = dot(v, view.direction)`. `p_near = max(p)` and `p_far = min(p)`.
- a candidate requires finite `p_near`, `p_far` and `p_near - p_far > 1e-6`; a planar or
  edge-on Mesh with no depth span is refused instead of inventing a constant range.
- each visible fragment world position `x` is encoded as
  `d = clamp((p_near - dot(x, view.direction)) / (p_near - p_far), 0, 1)`.
- `encoding`: `NEAR_BLACK_FAR_WHITE_UNORM_RGB`. CPU round-to-nearest writes the same
  `round(d * 255)` value to R, G and B; visible alpha is 255.
- background is canonical transparent black `[0,0,0,0]`.

Thus the closest base-Mesh vertex plane is black and the farthest is white. Values are
object-relative and comparable across pixels of this output, not across different Objects,
frames or requests. Orthographic projection makes the interpolation camera-linear.

## Narrow v1 boundaries

The request fixes one exact Object, orthographic direction/up, whole-Object framing margin,
resolution, disabled anti-aliasing, nearest-neighbor sampling and a new no-overwrite RGBA8
PNG. It does not infer the active Camera or Profile. Perspective, camera clip/NDC depth,
metric-world-unit output, scene-wide normalization, named occluders, evaluated/deformed
geometry, animation, anti-aliasing, 16/32-bit publication and multi-pass packaging are not
part of v1.

## Current evidence and next gate

Four offline tests cover deterministic hashing and exact near/far semantics, refusal of
alternate spaces/sources/ranges, fixed encoding/background/sampling and collision-safe
RGBA8 output. A seven-check read-only Blender candidate probe proves exact `+1/0/-1`
projections, `0/128/255` references, zero-span refusal and no file/Scene-count change.

An isolated nine-check render probe then preserves 120 grayscale depth levels (`5..248`)
from a tilted triangle through the owned 32-bit float EXR and deterministic CPU RGBA8 path.
The complete `blender-render-depth-pass-png` pipeline passes eleven checks from repository,
packaged and installed helpers: reviewed chain, stale refusal, independent stage, hash-bound
job, 72-value published gradient, receipt binding, collision refusal and exact teardown.
Refreshed-client discovery and one natural-language host render remain.
