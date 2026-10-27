---
name: blender-export-static-fbx
description: Safely export one simple texture-free Blender static Mesh to a new FBX path using an explicit request, live preview fingerprint and staged no-overwrite publication. Use for Unity-oriented static FBX export, not textures, rigs, animation, batch export or replacing existing files.
---

# Export one texture-free static Mesh to FBX

Use only for one named, simple static Mesh and a new explicit `.fbx` target. Read the
active Workspace Profile when it defines export policy. Missing axes, scale, Blender
unit/space conversion, modifier policy, path mode or destination remain unknown; never
turn the synthetic Unity test values into universal defaults.

First run [request validation](scripts/validate_static_fbx_request.py) outside Blender on
the exact request. It must use schema `gameassetai.static-fbx-request.v1` and pass
without errors. This is read-only and does not authorize a write.

Before Blender work, query the current addon/Scene. Load these Blender scripts into one
shared namespace in order: [transform inspection](scripts/inspect_static_transform.py),
[export context](scripts/inspect_static_export_context.py),
[candidate inspection](scripts/inspect_static_fbx_candidate.py),
[atomic publication](scripts/promote_export_artifact.py), and
[staged export](scripts/export_static_fbx_staged.py). Send exact contents through the
current Blender Python MCP tool; do not assume Blender can read installed file paths.
Compile sources independently into shared globals/locals. Pass the user's exact prompt
to MCP and inspect returned text, not only transport status.

Run `inspect_static_fbx_candidate(request, preflight)` under a temporary context override
for the exact Scene/Object. It must report `candidate_for_review`, no blockers, the same
request hash and a source fingerprint. This preview never authorizes export. Report the
explicit settings and limitations before mutation.

Only when the user has authorized that exact source, target and settings, load the scripts
again, re-create the same temporary override, re-inspect, require the preview fingerprint
to match, then call `export_static_fbx_staged(..., authorize=True)`. The helper rechecks
source and destination, writes a unique hidden stage in the target directory, verifies one
binary FBX/Object record and atomically hard-links it to an absent target. It refuses an
existing target or `.meta`, a late `.meta` race, stale state and unsupported hard links.
It never overwrites and never removes a published target.

Supported scope is intentionally narrow: Object mode, one local polygon Mesh, no parent/
children, modifiers, constraints, vertex groups, Shape Keys, animation, shared/linked data,
Image Texture or node-group material, `COPY` path mode, sidecars, rig or animation export.
Do not remove dependencies to force eligibility. `bake_space_transform` is explicit and
Blender labels it experimental; static Unity fixture evidence does not authorize using it
for armatures or animation.

After success, verify the exact target path, size and SHA-256 from the report. If Unity is
available and the user authorized its project path, validate import separately in a Preview
Scene and delete only explicitly test-owned artifacts. Otherwise report Unity import as
unverified. On an uncertain MCP result, re-inventory Blender and the exact target/stage
names before retrying. Never retry against a path that now exists, delete a published file,
save the Blender file, or modify an existing Unity asset without separate authorization.

