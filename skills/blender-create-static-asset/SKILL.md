---
name: blender-create-static-asset
description: Create or copy-revise a recognizable static Blender prop, weapon, furniture-like or simple environment asset as an explicit semantic multi-part native Mesh assembly. Supports legacy primitives, profile silhouettes, v4 profile-beveled solids with real variable cross-sections, owned-part geometry revision, and safe import of an explicitly verified Kiln GLB.
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
   those kinds plus `PROFILE_BEVELED_EXTRUSION`,
   `gameassetai.static-asset-revision-request.v1` for legacy transform revision, revision v2 for
   copy-only replacement of owned v3 part geometry, revision v3 for owned v4 part geometry, or
   the Kiln request for a verified GLB.
3. Use meaningful, unique part names and stable `semantic_role` values in v2-v4. A recognizable result
   should normally have multiple parts and at least two purpose-specific materials.
4. Show the planned parts, dimensions, placement and colors. Persistent creation requires a
   separate explicit confirmation.
5. Validate with `scripts/validate_static_asset_assembly_request.py`.
6. After confirmation, run `scripts/create_static_asset_assembly.py` inside Blender with
   `authorized=true`, calling `create_asset`, `revise_asset_copy` or `import_kiln_glb` as appropriate.
7. Inspect the resulting collection and report the receipt. Do not claim visual quality without
   looking at the result.

## Preservation

- Create a new Collection, Object, Mesh and Material data only.
- Revision duplicates Collection/Object/Mesh data and shares source materials read-only.
- Revision accepts only an owned semantic source whose roles are complete and unique.
- Geometry revision v2 accepts only an owned v3 source with complete geometry metadata. It creates
  a new Mesh for the selected role and shares source materials read-only; other parts are copied.
- Geometry revision v3 applies the same copy-only policy to an owned v4 source.
- Refuse occupied requested names; never accept Blender auto-suffixed replacements.
- Do not modify, hide, rename or delete existing Scene data.
- Tag all created data with one run owner token.
- On failure, roll back only data carrying that token.
- Cleanup from a receipt must stop if ownership cannot be verified.
- Kiln import requires an absolute regular `.glb`, its exact lowercase SHA-256, a complete unique
  mapping for every imported Mesh Object and unused target names. It owns and rolls back the
  synchronous import delta without applying native-assembly ownership.

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
  both depth caps. Core points must remain inside/on the outer profile, correspondence counts must
  match and the profiles must differ. This creates two real sloped bands and a closed positive-
  volume solid. It is useful for bounded cutting bevels, chamfered perimeters and raised/recessed
  panel transitions; it is not Blender's general Bevel operator.

V3 also requires explicit style facts. `STYLIZED_LOW_POLY` or `CUSTOM` records the requested shape
language, while `EXPLICIT_PART_GEOMETRY`, `FLAT`, `DECLARED_LIMITED`, `max_materials` and a triangle
budget are mechanically enforced. The profile points and declared materials—not the family label
alone—carry the art direction. Use a complete style object from the user's request or active
Workspace Profile; never silently merge partial values or treat this representative style as a
global default.

Revision v1 may replace selected role transforms. Revision v2 may replace a selected v3 role's
complete geometry and/or transform, producing a new Mesh while leaving Object scale unchanged.
Revision v3 does the same for a selected v4 role and may replace beveled-profile parameters.
Neither revision edits arbitrary imported meshes or materials.

Kiln import records producer/version/program provenance, source hash, all newly created data and
per-part Mesh/material facts. It accepts static Mesh Objects plus hierarchy Empties and keeps them
in one new Collection. Imported roles are descriptive provenance only: compatibility with native
v2.1 semantic revision is `NOT_VALIDATED` and must not be routed automatically.

## Validation and completion

Before accepting a result, verify requested part roles, dimensions/profile bounds and materials,
exact source preservation, absence of unowned changes, outward cap/side normals, closed manifold
edges, positive signed volume, no zero-area faces or duplicate 3D vertices, actual triangle/spec
consistency, and representative front/side/three-quarter appearance. Compare original and revised
assets with the same camera transform and orthographic scale when judging dimensional changes.
An induced helper failure must leave no target Collection/Object/Mesh residue. Structural tests are
`tested`; a recognizable reviewed asset is `representative`; only recorded visible/semantic review
may be called `accepted`.

## Boundary

This Skill does not solve arbitrary prompt-to-3D generation, arbitrary imported-Mesh semantic
editing, sculpting, UV/texture authoring, rigging or animation. V4 provides explicit matched-profile
beveled solids, not a general extrude/inset/Bevel/Boolean/sweep framework. It does not run Kiln, generate GLBs or
translate prompts into Kiln programs. Unsupported requests must be reported rather than
approximated silently with primitives.
