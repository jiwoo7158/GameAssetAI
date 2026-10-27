# Copy optimization experiment plan — 2026-09-18

Status: synthetic experiment, guarded preview and independent-copy apply/rollback passed
on Blender 5.0.1, 2026-09-18; see `docs/coplanar-apply.md`. A narrow source Skill exists;
general optimization and production certification remain unimplemented.

## First bounded experiment

Investigate removal of redundant coplanar internal edges on independent synthetic
Object/Mesh copies. Do not start with general ratio-driven decimation of user assets.
First query native operation documentation/RNA through the connected Blender instance;
verify actual available parameters and delimiter behavior rather than copying old API
examples. Native BMesh dissolve and delimiters now have narrow synthetic evidence;
Decimate modifier/production behavior remain unverified.

Coplanar edge removal may reduce edges/faces but leave the triangulated triangle count
unchanged. Such a result is structural simplification, not triangle-budget optimization.
Record both metrics, never pass an unmet triangle target based on polygon count. Do not
add automatic collapse as a fallback if dissolve does not meet a target.

## Synthetic representative cases, sequentially

1. Coplanar adjacent faces, continuous UV mapping and one material: duplicated data,
   explicit candidate edges; retain area, boundary positions and UV mapping.
2. Same geometry with discontinuous UV across internal edge: require no dissolve or
   verified delimiter refusal. Layer names alone are not UV-preservation evidence.
3. Internal edge across differing material assignments: retain material boundary.
4. Marked seam/sharp edge or differing face normals: retain explicitly protected boundary.
5. Noncoplanar variant: do not flatten or change silhouette to satisfy a count.
6. Continuous but nonaffine UV: native delimiter still dissolves. Require a separate
   affine-map guard before future reuse; corner equality alone is not sufficient.

Fixtures use exact UUID-owned IDs in a separate Scene, no current selection as target.
Begin/end with native source fingerprint, context and tracked ID names. Exact teardown
must preserve existing file objects, rigs, Actions, materials and user mode. Do not save
the original file; fixture creation can dirty it and clean-flag preservation is not claimed.

## Gates before reusable implementation

Current scope regression covers separated coplanar components sharing one global affine
UV map, a retained internal seam on one component, and refusal when only one UV island
is offset (locally affine islands but incompatible global mapping). Preview/apply remain
whole named mesh operations: there is no selected-face/island API, per-region tolerance,
or fallback to processing only a valid subset. Any future candidate-region design must
define exact face/edge identity, region boundaries and freshness before implementation.

- Read source and current Profile; budgets do not authorize edits. Explicit target and
  preservation goals are data, not game defaults. A source report is not freshness proof.
- Preview reports exact proposed change on supported inputs; source fingerprint includes
  relevant UV/material/seam/sharp/transform data. Do not reuse the loose-cleanup hash
  without inspecting whether it covers the new operation's inputs.
- Apply only to independent copies, explicit globally unused output name, fresh preview,
  authorized operation. Linked users/source remain unchanged. Shared materials are not
  permission to edit their contents.
- Compare native boundary/area/UV/material data and base triangulation, plus viewport
  before/after. Numerical/synthetic checks do not certify general silhouette quality.
- Validate output before retaining/linking it. Inject write/validation failures; rollback
  only exact new owned IDs, stop on unexpected users/links. No automatic retry after
  uncertain MCP outcome.
- Initially refuse dependent rigs, groups, Shape Keys, animation, constraints, modifiers,
  custom normals and unsupported attributes; inspect file-wide evaluation risks.

Do not create a new installable Skill until at least one representative native experiment
and protected-boundary/failure cases pass. Broad optimization, pivot/transform application,
LOD and engine export remain separate roadmap capabilities.
