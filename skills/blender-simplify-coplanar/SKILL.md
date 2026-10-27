---
name: blender-simplify-coplanar
description: Preview and optionally dissolve redundant coplanar internal edges on an independent copy of a simple planar Blender mesh, preserving affine UV mapping and protected boundaries. Not general decimation, triangle-budget optimization, rig cleanup, curved-mesh simplification, transform application, or export.
---

# Simplify a supported planar mesh on an independent copy

Inspect the live addon status and Scene first. Require an explicit target object/Scene;
never replace empty selection with an arbitrary object. Existing topology may be intentional.
A generic optimize/inspect request or triangle budget alone does not authorize dissolve.
Establish that the redundant internal edges are unwanted before any copy apply.

Read the bundled helpers: [state_helpers.py](scripts/state_helpers.py),
[check_affine_uv.py](scripts/check_affine_uv.py),
[preview_coplanar.py](scripts/preview_coplanar.py),
[apply_coplanar.py](scripts/apply_coplanar.py). Transmit their exact contents through live
Blender Python execution; do not assume Blender can read installed local paths. Compile
each separately, in that order, with one dictionary for globals and locals:
`exec(compile(source, filename, "exec"), namespace, namespace)`.
Call functions from that same dictionary in the same MCP request. Do not rely on previous
request namespaces; carry the preview fingerprint as JSON data. Check actual error text
even if the MCP envelope says isError=false. Pass the actual user request where required.

## Preview before apply

Read the current Workspace Profile before game-specific conclusions. Explicit numerical
`angle_limit`, `geometry_tolerance` and `uv_tolerance` must be established for this operation,
not guessed from a game budget/art style. Prototype supports angle_limit at most 0.001
radians. Geometry tolerance is an absolute local-xyz bound; UV tolerance is a separate
absolute UV-coordinate bound. Both must be positive and finite. If the
request/Profile does not establish suitable values, explain this limitation or ask for
scope; synthetic development values are not user-game defaults.

Call `namespace["preview_coplanar"](object_name, scene_name=..., angle_limit=...,
geometry_tolerance=..., uv_tolerance=...)`.
It uses ephemeral BMesh only and creates no Object/Mesh IDs. Every UV layer must have
one affine mapping across the whole planar mesh; UV splits/nonlinear maps/nonplanarity
block. This narrow restriction is deliberate, not proof all imported assets are supported.
Material/seam/sharp/normal delimiters protect internal boundaries. Candidate indices are
not a promised-removal list. Valid no-change previews are normal; do not bypass guards.

Report vertices/edges/faces AND triangles. Reducing edges/faces can leave triangle count
unchanged; do not claim a budget has been met, engine readiness or improved visual quality.

## Authorized copy apply

Only after explicit authorization for this operation, call
`namespace["apply_coplanar"](object_name, scene_name=..., result_name=...,
expected_source_sha256=preview["source_sha256"], angle_limit=...,
geometry_tolerance=..., uv_tolerance=..., authorized=True)`.
Use the exact preview parameters and a globally unused result name (≤63 UTF-8 bytes).
The boolean conveys an already established authorization, not permission in itself.
Missing/stale hash, changed parameters or name collisions refuse before copied IDs.
No predicted change means no new output. Never overwrite, autosuffix, hide/delete originals,
apply modifiers/transforms, select outputs or save/export as part of this operation.

Legacy `tolerance=...` explicitly sets both bounds for existing calls. Do not mix it
with separate parameters. Effective parameters are normalized into the fingerprint;
changing either bound requires a new preview. Re-preview old-version fingerprints after
helper updates; do not migrate hashes or automatically retry apply. Separate bounds prevent
a loose geometry tolerance silently relaxing UV checks, not a general quality guarantee.

Copy Object and Mesh independently; material contents remain shared references. Output
is linked only after its canonical geometry/UV/material/smooth/seam/sharp signature and
counts match the simulated result and source state/transforms remain unchanged. After
success inspect source and output, verify Mesh independence and obtain viewport/Scene
inventory. Overlapping copies are expected; do not move the original to improve visibility.

## Refusal and recovery

Require Object mode, valid assigned surface materials/UVs and no loose/nonmanifold/
degenerate surface. Refuse linked/overrides, dependent parent/children/modifiers/constraints,
groups, Shape Keys, animation, custom normals and unsupported attributes. Apply also
conservatively refuses file-wide animation/drivers/constraints; never delete them to bypass.

Failed write/validation/linking rolls back only exact new owned IDs if ownership/users/
links remain safe. If failure_cleanup is unverified, stop and inspect exact names/tokens;
never wildcard-delete or automatically retry an uncertain MCP result. Bounded source hash
does not cover every property/material content or concurrent add-on behavior.

Source helper and synthetic refusal/rollback tests passed on Blender 5.0.1. Installed-client
selection and instruction behavior require separate verification; this is not a production
optimizer, UV-quality certificate or engine-import guarantee.
