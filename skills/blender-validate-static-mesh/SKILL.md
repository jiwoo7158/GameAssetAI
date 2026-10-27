---
name: blender-validate-static-mesh
description: Run read-only diagnostics on explicitly targeted existing Blender meshes before game-asset cleanup or export. Distinguish topology facts, review items, and supplied profile-limit violations; do not repair meshes, apply transforms/modifiers, certify rigs, or export.
---

# Validate an existing static mesh

When loading helper source with `exec`, use one dictionary for both globals and locals:
`namespace = {}; exec(compile(helper_source, "<mesh-helper>", "exec"), namespace, namespace)`.
Call `namespace["diagnose_mesh"](...)` in that same MCP request. Separate globals/locals
can leave imports unavailable to helper functions. Compile each source separately;
do not concatenate future-import-bearing files or rely on earlier MCP call namespaces.

## Inputs and preconditions

Use an explicit mesh object name in the current or explicitly named Scene. If the user
requests selection, inspect current selection and call the helper once per selected mesh;
an empty selection is an error, not permission to choose the active object or all meshes.
Inspect current scene and addon/version through actual live MCP tools before code execution.
This skill never installs MCP or requires moving source files/projects.

## Profile constraints

Before judging game-specific limits, re-read workspace `config/active-profile.json` and
the referenced exact-case Markdown profile. Translate only clearly applicable rules into
the optional `constraints` dictionary: `max_triangles`, `max_materials`, `require_uv`,
`closed_surface`. Integer maxima must be nonnegative; boolean rules must be explicit.
Do not guess a numeric budget from art style, confuse polygons with triangles, inherit a
mapping as an export destination, or silently interpret an ambiguous/LOD-specific rule.
Missing constraints remain untested, not passed. Generic factual diagnostics can run
without an active profile using `constraints=None`. Report the profile/field used separately
from helper facts; helper input alone does not prove the profile was read.

## Procedure

Read [scripts/validate_mesh.py](scripts/validate_mesh.py), send its exact source to live
Blender Python execution, and append a call such as:

```python
print(json.dumps(diagnose_mesh(object_name="user-specified name", constraints=None),
                 ensure_ascii=False, allow_nan=False))
```

Do not assume Blender can access installed skill paths; transmit code, not a guessed path.
Keep the helper's namespace separate from other loaded helpers. Pass the actual user request
to tools where required, and check error text even when the MCP envelope says `isError: false`.

Default basis is the **base mesh**. If final viewport geometry is requested, set
`evaluate=True` only for an object in the current Scene. The helper obtains and releases
a temporary evaluated mesh without applying modifiers. It does not silently fall back
to base data. Viewport evaluation is not render/FBX/engine evaluation or instance export.
Graph refresh can change unsynchronized animated properties. Evaluation is therefore
conservatively refused if file datablocks contain active animation/Driver/NLA/object or
pose constraints, including dependencies outside the target Scene. Use base diagnostics
instead; do not remove animation or constraints to bypass this guard.
Base diagnostics do not force graph refresh; stored world matrices may reflect the last
evaluation rather than unsynchronized animation/property changes. Report that basis.

Check execution `status` independently of diagnostic `verdict`. Report the named target,
basis, metrics, findings, and unrequested game constraints. `no_findings` is not certification
that the mesh is engine-ready. Compare base Cube statistics with native/scene inventory
when testing; repeat on representative existing data before modifying it.

## Diagnostic interpretation

- Empty faces, nonfinite coordinates/transforms, zero-area faces, noninvertible world
  transforms, and explicit constraint violations are issues; the helper never repairs them.
- Open boundaries, wire/loose geometry, inconsistent edge winding, coincident coordinates,
  n-gons, absent materials, shared data, and unapplied/mirrored transforms are review items,
  not universal game errors. Intended planes/seams/collision meshes may be legitimate.
- Shape Keys, Armature relationships/modifiers, and object/data animation or drivers are
  preservation-sensitive: this skill can report them but cannot certify the asset as static.
- A `closed_surface` rule checks edge incidence only, not every nonmanifold vertex case.
  UV presence/finite values are checked, not overlap, density, packing, or correctness.

## Outputs, safety, and fallback

Schema `gameassetai.mesh-diagnostics.v1` contains execution status, target/basis, metrics,
supplied constraints, findings (`code`, `severity`, `detail`), and diagnostic verdict
(`issues`, `needs_review`, `no_findings`). Unsupported/missing target, invalid constraints,
edit-mode data, or failed evaluation produce explicit error/uncertainty, not a green result.
No source selection/mode/mesh/material/rig/Action/file changes are permitted. Any temporary
evaluation must be cleared in `finally`. If native execution is unavailable, report the
verified subset only and explicitly mark full diagnostics unavailable.

Tested on Blender 5.0.1 with synthetic valid/invalid/open/shared/animated/modifier fixtures,
plus the existing Cube. No self-intersection, outward-normal, skinning, LOD, collider,
retargeting, engine-import, or production performance guarantee is implied. Installation
discovery and actual cross-session profile awareness still need client validation.
