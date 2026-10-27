---
name: blender-create-static-asset
description: Create or copy-revise a recognizable static Blender prop, weapon, or simple environment asset as an explicit semantic multi-part native Mesh assembly, or safely import an explicitly verified Kiln GLB with complete part-role mapping.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-STATIC, REQ-STYLE, REQ-COST, REQ-SAFE
  evidence: representative
  external-dependencies: none
---

# Blender Create Static Asset

Turn a design brief into a deliberate Blender-native static asset, or revise an assembly created
with semantic roles by making an independent copy. This workflow is limited to hard-surface or
low-poly assets assembled from supported primitives.

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
2. Choose creation v1 for legacy compatibility, creation v2 for reusable semantic parts,
   `gameassetai.static-asset-revision-request.v1` for a copy-only revision of a v2 assembly, or
   `gameassetai.kiln-glb-import-request.v1` for a verified existing Kiln GLB.
3. Use meaningful, unique part names and stable `semantic_role` values in v2. A recognizable result
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
- Revision accepts only an owned v2 source whose semantic roles are complete and unique.
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

Creation v2 adds one unique `semantic_role` to every part. Revision names a source collection,
creates a differently named target assembly, and may replace any selected role's dimensions,
location and/or Euler rotation. It does not edit arbitrary imported meshes or materials.

Kiln import records producer/version/program provenance, source hash, all newly created data and
per-part Mesh/material facts. It accepts static Mesh Objects plus hierarchy Empties and keeps them
in one new Collection. Imported roles are descriptive provenance only: compatibility with native
v2.1 semantic revision is `NOT_VALIDATED` and must not be routed automatically.

## Validation and completion

Before accepting a result, verify requested part roles, dimensions and materials, exact source
preservation, absence of unowned changes, and representative front/side/three-quarter appearance.
An induced helper failure must leave no target Collection/Object/Mesh residue. Structural tests are
`tested`; a recognizable reviewed asset is `representative`; only recorded visible/semantic review
may be called `accepted`.

## Boundary

This Skill does not solve arbitrary prompt-to-3D generation, sculpting, topology design, UV
authoring, rigging or animation. It does not run Kiln, generate GLBs or translate prompts into Kiln
programs. Unsupported requests must be reported rather than approximated silently with primitives.
