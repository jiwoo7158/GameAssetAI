# Static multi-Object color-ID pass contract

This checkpoint defines the ID-pass meaning before a Blender renderer or Skill is created.
The narrow v1 request is `gameassetai.2d-object-id-request.v1`.

## Identity and visibility contract

- `objects` contains 2 to 63 ordered entries. Every entry provides one exact
  `object_name` and one opaque normalized `id_rgba`.
- Object names must be unique. Colors must remain unique after round-to-nearest RGBA8
  conversion; two different float colors that quantize to the same bytes are refused.
- exactly the listed static base-Mesh Objects participate. Unlisted Scene Objects are not
  inferred, staged, framed, rendered or treated as occluders.
- requested Objects depth-occlude each other normally. Each visible pixel receives the
  requested color of the closest listed Object. Fully occluded requested Objects remain in
  metadata with zero visible pixels; the complete output may not be empty.
- background is canonical transparent black `[0,0,0,0]`.

## Render and output contract

The request fixes an orthographic direction/up pair, union framing over exactly the listed
Objects, framing margin, resolution, disabled anti-aliasing, nearest-neighbor sampling and a
new RGBA8 PNG with `overwrite: false`. The implementation must use isolated internal IDs
and deterministic CPU remapping to the requested RGBA values; source materials must not
control identity colors.

The active Scene selection, collections, visibility of unrelated Objects, material names,
Profile and hierarchy are never identity sources. Material-slot IDs, per-face IDs, named
unlisted occluders, evaluated/deformed Objects, animation, more than 63 IDs, anti-aliased
edges, existing-output replacement, sprite slicing and Unity import are outside v1.

## Current evidence and next gate

Four offline tests cover deterministic hashing, explicit/bounded Object membership, unique
names and quantized colors, inference refusal, fixed sampling and collision-safe RGBA8
output. A seven-check read-only Blender candidate proves exact ordered membership/color
reporting, exclusion of an unlisted distant Object, dependency blocking and no file or Scene
count change.

The complete `blender-render-object-id-png` pipeline passes twelve Blender 5.0.1 checks from
repository, packaged and installed helpers. Two overlapping requested quads publish exact
red/green IDs with 200 visible pixels each, preserve mutual depth occlusion, exclude a third
unlisted Object, refuse source drift and target collision, bind the receipt and tear down all
owned files. Refreshed-client discovery and one natural-language host render remain.
