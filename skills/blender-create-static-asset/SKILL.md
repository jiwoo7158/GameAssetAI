---
name: blender-create-static-asset
description: Create or copy-revise a recognizable static Blender prop, weapon, furniture-like or simple environment asset as an explicit semantic multi-part native Mesh assembly. Supports legacy primitives, profile silhouettes, profile-beveled solids, bounded image-textured v5 style production, owned-part geometry revision, safe Kiln GLB import, and bounded revision of an explicitly mapped external static GLB.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-STATIC, REQ-STYLE, REQ-COST, REQ-SAFE
  evidence: accepted
  external-dependencies: none
---

# Blender Create Static Asset

Turn a design brief into a deliberate Blender-native static asset, or revise an owned assembly by
making an independent copy. V3 can create a user-authored two-dimensional silhouette as a real
extruded Mesh. V4 adds a bounded profile-beveled solid whose center silhouette differs from its
front/back core, creating actual sloped faces rather than a shading-only bevel. Both can replace
one semantic part on an independent copy without scaling the whole Object.
Creation v5 keeps these geometry kinds and adds explicit art-direction provenance, deterministic
local box UVs, bounded generated PNG base-color patterns, packed Blender Images and image-textured
materials. Revision v4 makes an independent copy of an owned v5 assembly, regenerates the selected
replacement part UVs and shares existing Materials and packed Images read-only. It is a narrow
production path, not a general UV unwrap or texture-painting system.
External-revision v1 imports a hash-pinned static GLB, assigns explicit roles to every Mesh Object
and offsets a declared local-axis end region on independent Mesh copies. It does not infer
semantics or claim general imported-Mesh editing.
It remains a bounded low-poly hard-surface workflow rather than arbitrary prompt-to-mesh.

## Requirements and responsibility

This user-facing production Skill owns bounded static creation and revision for `REQ-STATIC`.
Explicit materials and geometry choices advance `REQ-STYLE`; local Blender-native implementation
and guarded copy/rollback satisfy `REQ-COST` and `REQ-SAFE`. It does not own character, animation,
rendering or engine export responsibilities.

## Implementation basis and dependencies

Use Blender's Python API and the packaged GameAssetAI validator/assembly helper only. There is no
external runtime dependency. The optional Kiln boundary consumes an existing GLB but neither
installs nor invokes Kiln.

## Workflow

1. Inspect the target Scene and existing names before proposing creation.
2. Choose creation v1 for legacy compatibility, creation v2 for primitive semantic parts,
   creation v3 for explicit style plus `PRIMITIVE`/`PROFILE_EXTRUSION` geometry, creation v4 for
   those kinds plus `PROFILE_BEVELED_EXTRUSION`, creation v5 when the same geometry also needs
   explicit art-direction provenance, UVs and optional generated image textures,
   `gameassetai.static-asset-revision-request.v1` for legacy transform revision, revision v2 for
   copy-only replacement of owned v3 part geometry, revision v3 for owned v4 part geometry,
   revision v4 for owned v5 geometry with UV regeneration and read-only appearance sharing,
   the Kiln request for a verified GLB, or external-revision v1 for a verified static GLB with an
   explicit Object/role map and bounded end-region edit.
3. Use meaningful, unique part names and stable `semantic_role` values in v2-v5. A recognizable result
   should normally have multiple parts and at least two purpose-specific materials.
4. Show the planned parts, dimensions, placement and colors. Persistent creation requires a
   separate explicit confirmation.
5. Validate with `scripts/validate_static_asset_assembly_request.py`.
6. After confirmation, run `scripts/create_static_asset_assembly.py` inside Blender with
   `authorized=true`, calling `create_asset`, `revise_asset_copy`, `import_kiln_glb` or
   `revise_external_glb` as appropriate.
7. Inspect the resulting collection and report the receipt. Do not claim visual quality without
   looking at the result.

## Preservation

- Create a new Collection, Object, Mesh and Material data only.
- Revision duplicates Collection/Object/Mesh data and shares source materials read-only.
- Revision accepts only an owned semantic source whose roles are complete and unique.
- Geometry revision v2 accepts only an owned v3 source with complete geometry metadata. It creates
  a new Mesh for the selected role and shares source materials read-only; other parts are copied.
- Geometry revision v3 applies the same copy-only policy to an owned v4 source.
- Geometry revision v4 applies it to an owned v5 source. Every result Mesh is independent;
  replacement Meshes receive a newly generated UV layer using the source part's recorded mapping,
  while unchanged Materials and packed Images remain shared read-only.
- Refuse occupied requested names; never accept Blender auto-suffixed replacements.
- Do not modify, hide, rename or delete existing Scene data.
- Tag all created data with one run owner token.
- On failure, roll back only data carrying that token.
- Cleanup from a receipt must stop if ownership cannot be verified.
- Kiln import requires an absolute regular `.glb`, its exact lowercase SHA-256, a complete unique
  mapping for every imported Mesh Object and unused target names. It owns and rolls back the
  synchronous import delta without applying native-assembly ownership.
- External revision separates the imported read-only source Collection from the owned result
  Collection. Every result Mesh datablock is independent; materials remain shared read-only. A
  failure removes the complete operation delta without changing the external file or existing data.
- Creation v5 creates independent Material and Image data and refuses occupied Blender names or
  existing texture files. Each PNG is first saved to a unique same-directory staging name,
  signature-checked, then published through an atomic no-overwrite hard link. Published files are
  rollback-owned only while their path identity and SHA-256 still match. A save, pack, second-image,
  geometry or publication-collision failure removes owned staging/final files and data without
  deleting a collision winner or any pre-existing user file.

## Request boundary

The request explicitly names the Scene, asset, output Collection, materials and parts. Each part
uses `BOX`, `CYLINDER`, `ICOSPHERE` or `WEDGE`, exact dimensions, location, Euler rotation in degrees,
material name and required/null segment count. The fixed policy is:

```json
{
  "existing_names": "REFUSE",
  "source_scene": "PRESERVE",
  "creation": "NEW_COLLECTION_OBJECTS_MESHES_MATERIALS",
  "failure": "ROLL_BACK_OWNED_DATA"
}
```

Creation v2 adds one unique `semantic_role` to every part. Creation v3 replaces the primitive-only
part fields with a `geometry` object:

- `PRIMITIVE`: the legacy primitive, dimensions and segment count;
- `PROFILE_EXTRUSION`: 3-32 counter-clockwise `[x,z]` points plus positive Y depth. Repeated or
  near-duplicate vertices, zero-length/backtracking edges, crossings, non-adjacent endpoint
  contact and collinear overlap are refused; valid concave profiles remain supported. This
  authors the visible silhouette rather than selecting another stock primitive.

Creation v4 keeps those kinds and adds:

- `PROFILE_BEVELED_EXTRUSION`: matching 3-32 point counter-clockwise outer and core XZ profiles,
  plus positive Y depth. The outer ring lies at the center plane and the core profile is used on
  both depth caps. Core points must be strictly inside the outer profile, correspondence counts
  and nearest cyclic index alignment must match, core edges must remain inside the outer polygon,
  and connectors may not cross or touch. Numerically unstable near-zero bevel widths are refused.
  This creates two real sloped bands and a closed positive-
  volume solid. It is useful for bounded cutting bevels, chamfered perimeters and raised/recessed
  panel transitions; it is not Blender's general Bevel operator.

Creation v5 retains the v4 geometry set and adds two exact objects:

- `art_direction`: explicit provenance (`USER_REQUEST` or `WORKSPACE_PROFILE`), surface style,
  silhouette, proportion, geometry-detail and palette decisions, plus unsupported requested facts;
- `appearance`: `LOCAL_BOX_PROJECT`, optional generated-PNG policy, an absolute explicit texture
  directory, resolution/byte budgets and mandatory image packing.

Each v5 material declares a role and an optional `WOOD_GRAIN` or `PAINTED_METAL` texture with an
explicit PNG name, 32-512 resolution, palette, scale and seed. The validator enforces unique
image/file names and budgets. The Blender helper creates one deterministic `UVMap` by dominant-
face local box projection, writes a real PNG, connects a `ShaderNodeTexImage` to Principled Base
Color and packs the image. Painted-look style requires at least one image texture; Angular Low-
Poly may deliberately remain color-material only. This UV policy is supported only for the
current non-degenerate static geometry kinds and does not minimize seams or distortion.
Each part may additionally declare a bounded local-box UV quarter-turn (`0`, `90`, `180` or `270`)
and U/V mirror flags. This is a deterministic orientation control, not general seam placement.

Resolve style input before constructing v5. Explicit user decisions win. For missing decisions,
read the active Workspace Profile verbatim with Repository `scripts/read_profile_context.py` and
record its path plus SHA-256 as `WORKSPACE_PROFILE` provenance. If a required art-direction fact is
absent from both sources, ask for it instead of inventing or silently blending defaults. The
Blender helper consumes the resulting complete specification; it does not parse Markdown itself.

V3 also requires explicit style facts. `STYLIZED_LOW_POLY` or `CUSTOM` records the requested shape
language, while `EXPLICIT_PART_GEOMETRY`, `FLAT`, `DECLARED_LIMITED`, `max_materials` and a triangle
budget are mechanically enforced. The profile points and declared materials—not the family label
alone—carry the art direction. Use a complete style object from the user's request or active
Workspace Profile; never silently merge partial values or treat this representative style as a
global default.

Revision v1 may replace selected role transforms. Revision v2 may replace a selected v3 role's
complete geometry and/or transform, producing a new Mesh while leaving Object scale unchanged.
Revision v3 does the same for a selected v4 role and may replace beveled-profile parameters.
Revision v4 does the same for a selected v5 role, preserving art-direction provenance and
appearance metadata while regenerating UVs for replaced geometry. It does not edit texture pixels,
Materials or Images.
Neither owned revision edits arbitrary imported meshes or materials.

Kiln import records producer/version/program provenance, source hash, all newly created data and
per-part Mesh/material facts. It accepts static Mesh Objects plus hierarchy Empties and keeps them
in one new Collection. Imported roles are descriptive provenance only: compatibility with native
v2.1 semantic revision is `NOT_VALIDATED` and must not be routed automatically.

External revision v1 uses `gameassetai.external-static-revision-request.v1` and supports one
explicit operation, `LOCAL_AXIS_END_OFFSET`. The request names an absolute `.glb`, exact SHA-256,
unused source/result Collections, provenance, every imported Mesh Object and its unique semantic
role, then selects mapped roles with local axis (`X`/`Y`/`Z`), end side (`MIN`/`MAX`), threshold and
non-zero delta. The selected region must contain some but not all vertices. Runtime safety refuses
an offset larger than the source axis span, crossing of the selected end through the unselected
region, collapsed edges/faces, face-normal inversion and closed-volume orientation/collapse. It preserves topology,
UV layers, material slots, Object transforms and an imported Empty-only parent hierarchy. It
refuses unmapped Meshes, modifiers, vertex groups, Shape Keys, linked data, non-static data and
unsupported parenting. `.blend`, arbitrary region selection, topology edits, automatic role
discovery and material/UV editing are not supported by this first B3 contract.

## Validation and completion

Before accepting a result, verify requested part roles, dimensions/profile bounds and materials,
exact source preservation, absence of unowned changes, outward cap/side normals, closed manifold
edges, positive signed volume, no zero-area faces or duplicate 3D vertices, actual triangle/spec
consistency, and representative front/side/three-quarter appearance. Compare original and revised
assets with the same camera transform and orthographic scale when judging dimensional changes.
An induced helper failure must leave no target Collection/Object/Mesh residue. Structural tests are
`tested`; a recognizable reviewed asset is `representative`; only recorded visible/semantic review
may be called `accepted`.

The accepted B5 breadth boundary uses this one contract for a painted fantasy shield, an angular
fantasy lantern and a modular stone doorway, plus an independent revision of each. Those examples
prove reuse across three bounded static domains; they do not imply arbitrary weapons, furniture or
architecture can be generated from a noun alone.

## Boundary

This Skill does not solve arbitrary prompt-to-3D generation, arbitrary imported-Mesh semantic
editing, sculpting, general UV unwrap/texture painting, rigging or animation. Its external path is a bounded,
explicitly mapped GLB end-region edit only. V4 provides explicit matched-profile
beveled solids, not a general extrude/inset/Bevel/Boolean/sweep framework. It does not run Kiln, generate GLBs or
translate prompts into Kiln programs. Unsupported requests must be reported rather than
approximated silently with primitives.
