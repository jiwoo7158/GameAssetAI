# 2D Impostor Bundle Architecture Decision

## Decision

Do not add another Blender renderer merely to produce an impostor. The existing static
color, normal, camera-linear depth and Object-ID renderers already own the individual pass
semantics. `blender-render-2d-batch` already owns guarded sequential execution and rollback,
and `assemble-png-sprite-sheet` already owns deterministic equal-cell packing.

Future impostor support is therefore a narrow orchestration layer. It must coordinate the
existing pass implementations instead of duplicating 3D generation, materials, cameras,
rendering, post-processing or sheet assembly.

## Required v1 boundary

The first bundle contract should remain static and explicit:

- one exact Blender Scene and one exact static base-Mesh Object
- one or more explicit orthographic `direction` / `up` pairs; no compass-set inference
- one explicit resolution and framing margin shared by every requested pass
- an explicit pass list drawn from color, normal and camera-linear depth, with Object-ID
  included only after its multi-Object source scope is explicitly compatible
- new absolute output paths, no overwrite, and one declared settings source
- deterministic list order and all-or-nothing publication for the bundle
- a machine-readable manifest binding every view, pass, artifact hash and receipt

Color, normal and depth outputs for a direction must use one canonical camera basis and one
canonical framing plan. The coordinator must pass that reviewed plan into every child and
reject any child that independently resolves a different center, orthographic scale, clip
range, resolution or source fingerprint.

## Existing components to reuse

- `blender-render-static-pixel-png`: color pass
- `blender-render-normal-pass-png`: camera-basis normal pass
- `blender-render-depth-pass-png`: object-relative camera-linear depth pass
- `blender-render-object-id-png`: optional explicit multi-Object identity pass
- `blender-render-2d-batch`: execution-order, collision and rollback patterns
- `assemble-png-sprite-sheet`: optional per-pass equal-cell sheets

Each pass should produce its own sheet and metadata when sheets are requested. Different
semantic passes must not be packed into one ordinary animation sheet.

## Implemented boundary

The generic batch schema accepts only static color and Action-sequence children, so filename
combination alone is not a verified impostor pipeline. `validate_2d_impostor_bundle_request.py`
provides the dedicated offline gate for
`gameassetai.2d-impostor-bundle-request.v1`. It accepts explicit COLOR/NORMAL/DEPTH child
requests, requires at least two identical ordered passes per view, and proves common
Scene/Object/view/resolution, unique same-directory PNGs, a new JSON manifest target and
fixed all-or-nothing policy without writing files. Object-ID remains outside v1 because its
multi-Object scope differs from the other three children.

`preview_2d_impostor_shared_framing.py` now provides the Blender read-only gate. It reruns
every child candidate inspection, fingerprints the shared base-Mesh source, calculates one
canonical camera plan per view and binds the same plan fingerprint to every pass in that
view. A Blender 5.0.1 fixture passes front/diagonal scale checks, stale-request and source
change checks, dependency blocking, no-write behavior and exact teardown.

`validate_2d_impostor_result_manifest.py` provides the result gate. Given the reviewed
request preflight, shared preview and proposed result, it requires exact ordered view/artifact
coverage, rechecks every regular PNG byte count and SHA-256, binds child receipt hashes and
refuses a changed or occupied JSON target.

`build_2d_impostor_bundle_job.py` binds the complete request/source/shared-plan chain, exact
staged child jobs and helper bytes. `run_2d_impostor_bundle.py` rechecks that chain, renders
children sequentially in isolated Blender processes, verifies every child receipt, rolls back
only unchanged outputs created by the attempt after failure, and publishes the validated JSON
manifest last. Offline failure tests and a 19-check Blender 5.0.1 COLOR/NORMAL/DEPTH fixture
pass. The implementation is packaged as `blender-render-impostor-bundle`; the remaining gate
is refreshed-client discovery and one natural-language host render.

## Non-goals

The coordinator will not generate or modify 3D assets, infer directions, create LODs,
choose game-specific art style, pack irregular atlases, configure Unity shaders/materials,
or certify the visual quality of an impostor. Those remain separate workflows.
