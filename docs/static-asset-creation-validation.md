# Native static asset creation and revision validation

## Scope

`blender-create-static-asset` is the first direct asset-creation Skill in this repository. It
creates a new named Collection containing explicit primitive-based Mesh parts and owned
materials. It targets recognizable low-poly props, weapons and simple environment pieces.

It is not a general text-to-3D, character, sculpting, UV texturing, rigging or animation system.

## Contract

- Schema: `gameassetai.static-asset-assembly-request.v1`.
- Primitives: `BOX`, `CYLINDER`, `ICOSPHERE`, `WEDGE`.
- 1–64 explicitly named parts and 1–16 explicitly defined materials.
- Exact dimensions, locations and rotations.
- Existing requested names are refused.
- Persistent creation requires `authorized=true`.
- New Collection, Object, Mesh and Material data are tagged with one run token.
- Failure and receipt cleanup remove only data with verified matching ownership.

## Representative Blender result

Blender 5.0.1 factory-startup validation creates a recognizable five-part training sword:

- steel blade;
- steel wedge tip;
- brass crossguard;
- leather cylindrical grip;
- brass low-poly pommel.

The focused test passed nine checks covering authorization refusal, five-part creation, three
material assignments, minimum topology, request/receipt hashes, receipt cleanup and exact global
Object/Mesh/Material/Collection restoration. No output remains after the fixture.

A live Blender host check then created the installed-Skill result in a separate temporary Scene.
The first viewport review showed that a box-only blade ended flat. The implementation added the
`WEDGE` primitive, updated the installed Skill through a hash-bound backup, and recreated the
asset with a six-vertex/five-face pointed blade tip. Front, three-quarter and side material views
were inspected. The revised result was recognizable as a low-poly sword and the temporary Scene,
five Objects, five Meshes and three Materials were removed. The original `Scene` returned to its
exact `Camera`, `Cube`, `Light` inventory.

## Evidence boundary

This proves deterministic native multi-part construction, a real viewport-led revision and exact
cleanup. It does not certify the visual design quality of arbitrary prompts or cover topology
editing beyond the four v1 primitives.

## Semantic copy revision — 2026-10-27

The existing Skill was extended without adding a second Skill or external dependency:

- creation schema v1 remains supported unchanged;
- creation v2 requires one case-insensitively unique `semantic_role` per part;
- revision v1 duplicates an owned v2 Collection, Objects and Meshes, shares source materials
  read-only, and replaces explicit dimensions/location/rotation only for named roles;
- unowned, non-semantic, ambiguous, missing-role and occupied-name sources are refused;
- source data is never edited, and an induced mid-copy failure removed every target-owned block.

Blender 5.0.1 focused regression passed legacy sword creation/cleanup, v2 creation, body/handle
revision, exact source geometry/transform preservation and deliberate rollback.

Representative run 03 is in
`.local/validation/static-asset-lantern-20261027-run-03/`. It contains one `.blend` file and
front/side/three-quarter PNGs for an eight-part compact lantern, a differently proportioned tall
lantern and a wide-body/wide-handle revision of the compact source. All three are visually
recognizable; handle/body changes are observable and the original compact assembly remains present.
The earlier runs are retained as rejected experiment evidence: run 01 had outward/disconnected
handles; run 02 fixed compact/wide handles but left the tall top bar disconnected.

The evidence level is `representative`, not arbitrary-prompt or production-quality acceptance.
UV creation, arbitrary imported-mesh editing, sculpting, free-form topology and material revision
remain unsupported.

## Kiln review — 2026-10-27

Kiln 1.5.0 was reviewed from its official repository and release record. It is MIT-licensed and
offers a Node 22/24 JavaScript/TypeScript engine, local MCP/CLI, named procedural parts, immutable
revisions, rendered review and GLB export. These capabilities overlap this Skill's responsibility,
but Kiln is not Blender-native and adds a second authoring/runtime model plus GLB handoff.

Kiln 1.5.0 was subsequently installed and exercised only in the approved isolated evaluation
folder. Its field-cannon GLB is now representative input for a bounded optional adapter; Kiln
itself is still not a Repository or Workspace dependency.

The `gameassetai.kiln-glb-import-request.v1` path verifies the source file and SHA-256, requires a
complete unique Mesh Object/semantic-role map, imports through Blender's native glTF operator and
places all new objects in one separately owned Collection. Provenance and created-data inventories
are returned in a hashed receipt. Imported ownership differs from native v2.1 assembly ownership,
so semantic revision compatibility remains `NOT_VALIDATED`.

Blender 5.0.1 validation used the 13-part field cannon. The successful result retained 10 Mesh
datablocks (three mirrored instances share meshes) and four materials. Invalid hash was refused
before import. Removing one role caused a post-import refusal and exact rollback of the generated
Object/Mesh/Material/Collection delta. Receipt cleanup also restored the exact factory baseline,
while deliberately removing one Mesh owner token caused cleanup to refuse before deletion. The
existing native v1/v2.1 regression remained passing. The reviewable `.blend` and receipt are under
`D:/AI/GameAssetAI-Kiln-Evaluation-20261027/adapter-output/`.
