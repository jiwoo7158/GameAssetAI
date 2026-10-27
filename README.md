# GameAssetAI

GameAssetAI is a development repository for building reusable AI skills that let Codex work with Blender as a game-asset technical artist / modeling assistant.

Current capability status, active gaps and deferred-but-retained Blender Add-on work are tracked in
`docs/IMPLEMENTATION_MEMORY.md`.

Current character warning: the whole-body `VOXEL_CONNECTED` experiment is suspended after live
review found unintended leg/foot fusion despite passing structural tests. The generated rig and
weight-copy results on that topology are diagnostic evidence only. The Blender Add-on source is
retained but is not persistently installed, so panel availability after restart is not yet proven.

The repository itself is **not** a game project and does not require existing Unity or Unreal projects to be moved or reorganized.

## Core idea

There are two separate environments:

1. **GameAssetAI repository**
   - Used when developing and testing skills.
   - May be versioned in Git, but public distribution is not in the current scope.

2. **GameAssetAI-Workspace**
   - Used during normal Blender asset work.
   - Holds personal game profiles and project paths.
   - The user's existing Unity / Unreal / Blender folder structure stays unchanged.

Normal asset work is intended to look like:

```text
Codex Desktop
  + installed GameAssetAI skills
  + GameAssetAI-Workspace
  + Blender MCP
        ↓
      Blender
```

## What this initial repository contains

This package deliberately starts small.

It contains:

- architecture and requirements documentation
- a routing-only natural-language asset entry that selects the tested static, character, rig,
  Action, inspection and downstream output Skills without duplicating their implementations
- rules for Codex to develop GameAssetAI itself
- a reusable workspace template
- a skill authoring template
- repository validation tooling
- executable offline repository/workspace regression tests
- test planning scaffolding
- one direct Blender-native static asset creation Skill for explicit low-poly multi-part props,
  with a viewport-reviewed five-part sword fixture
- a Blender 5 Add-on foundation with owned Scene and Compositor preset builders and a sidebar
  panel
- two narrow Blender-tested read-only source skills for asset inventory and static mesh diagnostics
- one narrowly Blender-tested copy-only loose-geometry cleanup skill with preview guards
- one narrowly Blender-tested planar structural-simplification Skill with affine UV,
  preview fingerprint and independent-copy apply/rollback (not triangle decimation)
- one positive-scale preparation Skill and one explicit-pivot relocation Skill,
  each operating on guarded independent copies
- one request-bound, texture-free static FBX export Skill with staged no-overwrite
  publication; synthetic Unity import evidence, not a general production exporter
- read-only humanoid, exact-signature Mixamo-preflight and animation-inventory Skills
- one guarded Action-copy Skill that creates an explicitly named unbound persistent copy
  while preserving the source and all existing references
- one strict exact-key linear Action-range extraction Skill that preserves the source,
  references and optionally keeps frames or rebases the copy to frame 0 or 1 without
  synthesizing boundary keys
- one read-only stored F-Curve endpoint loop-candidate Skill with explicit range and
  tolerance; not evaluated-pose or visual loop certification
- one read-only explicit Object/Bone root-translation evidence Skill; no root guessing,
  in-place decision, evaluated motion or engine policy
- one isolated evaluated-root-motion Skill reporting local-basis, Armature and world-space
  sampled paths; no motion transfer, in-place decision or Unity policy
- one isolated evaluated-pose loop Skill comparing explicit endpoint poses and bounded
  finite-difference seam velocities; no deformation, visual-loop or engine certification
- one guarded root-translation-only bake Skill with explicit TRANSFER/IN_PLACE policy,
  Armature-space XYZ mask and scalar; no inferred proportions or Action composition
- one guarded composition Skill combining strict rotation-only and root-location-only
  bake outputs into a new unbound Action; no automatic binding or arbitrary merging
- one guarded empty-target Action-binding Skill with an exact rollback receipt; no
  existing Action replacement, Action deletion or NLA editing
- one guarded exact-current Action replacement Skill with a rollback receipt; both
  Actions are preserved and NLA/drivers are refused
- one read-only explicit source/target humanoid retarget-readiness Skill; it inventories
  mappings, source Action coverage and rest-bone differences but does not retarget
- one guarded name-only Action remap-copy Skill for already aligned humanoid rigs; the
  result remains unbound and differing rest poses/axes still require a future workflow
- one guarded rotation-only local-basis bake Skill for differing-rest mapped rigs; it
  creates an unbound quaternion Action and excludes translation, scale and root motion
- one isolated static Pixel PNG Skill for a single simple Mesh, with hash-bound blend/job
  staging, explicit value-step shading, RGBA8 palette processing, optional explicit one-pixel outer silhouette,
  receipt evidence and no-overwrite publication

The downstream 3D-to-2D Pixel/Cel/Toon pipeline is incremental and does not replace or
duplicate these 3D Skills. Its first narrow static Pixel/RGBA8 output is implemented;
AUTO palette, value-step shading and one-pixel outer silhouette are implemented. A narrow
single-Action PNG-sequence Skill is implemented and host-tested. Explicit equal-cell sprite
sheet assembly and Profile-backed settings are host-tested. An explicit multi-direction/
multi-Action batch coordinator now passes synthetic Blender rollback tests and a refreshed-
client natural-language mixed batch. A file-level Unity Sprite import/slicing check contract
is offline-tested and passed one live Unity 6000.3.9f1 equal-cell fixture. CEL/Toon and
irregular packing remain planned. An explicit alpha-derived PNG silhouette-mask Skill is
host-tested. Separate static base-Mesh material-slot and explicit target-Object visibility
masks and an explicit multi-Object color-ID pass are implemented and Blender-tested;
all three pass types are now host-tested. Impostors remain a separate shared-framing
orchestration concern and will reuse the existing renderers rather than duplicate them.
Its explicit COLOR/NORMAL/DEPTH bundle request now has an offline validation gate; shared
Blender framing and the result manifest have read-only validation gates. Atomic child
staging/render rollback and manifest-last publication are implemented in the packaged
`blender-render-impostor-bundle` Skill. Its refreshed-client discovery and atomic
COLOR/NORMAL/DEPTH host render both pass.
Narrow camera-basis normal and object-relative camera-linear
depth Skills are implemented through deterministic float-EXR/CPU encoding. Normal and
depth are host-tested. The Object-ID refreshed-client discovery/render gate also passes.
See `docs/2d-pixel-pipeline-plan.md`, `docs/2d-static-pixel-skill-validation.md` and
`docs/2d-action-sequence-skill-validation.md`, `docs/2d-render-batch-contract.md` and
`docs/2d-impostor-bundle-decision.md`.

It does **not** pretend that general modeling, character generation, production rigging,
animation authoring or Mixamo have already been solved. The first static creation slice is
deliberately limited to explicit primitive assemblies.
Inspection/diagnostics have source-workflow test evidence under `docs/`. The user confirmed
session exposure, explicit calls, three natural-language read-only outcomes and synthetic
copy-apply/restore for all three installed Skills. Raw selected-Skill/call traces were not
supplied; fresh Workspace Profile A/B/null behavior passed by user report;
raw routing traces and production game-asset import workflows remain unverified.
Ambiguous Cube cleanup inspection-only triage also passed by user report, with declared
inspection/diagnostic Skill selection. A development-only read-only transform snapshot
has native evidence in `docs/transform-preflight.md`. That workflow now also has one
narrow positive-scale independent-copy Skill with preview/freshness/output validation and
rollback, not general Apply Transforms. Source/ZIP/installed helper checks pass; the user
also confirmed fifth-Skill actual preview/verify/copy-apply and exact synthetic restoration.
Raw client routing/build and engine certification remain separate evidence gaps.

Existing static-collider work now has a separate read-only Skill that inspects only explicitly
named base-Mesh candidates and reports topology, world bounds, dependencies and bounded
convexity evidence. It does not generate colliders, create LODs or configure Unity. Source and
installed Blender regressions pass; the refreshed client exposes the Skill and safely refuses
the current one-Mesh Scene. A separate temporary-scene host inspection also passes with exact
cleanup and context restoration.
Existing LOD-chain inspection is also separate and read-only: it accepts only an explicit
ordered set of base Meshes, checks exact world-transform alignment and decreasing base
triangulation, and reports bounds/material relationships. It does not generate or decimate.
The refreshed client exposes this Skill and safely refuses the current single-Mesh Scene;
its separate temporary-scene 12/8/4-chain host inspection and exact teardown also pass.
Development-only FBX exporter/Blender-importer synthetic roundtrip evidence is in
`docs/static-export-preflight.md`. One synthetic FBX import and non-saved prefab
instantiation passed in Unity 6000.3.9f1 (`docs/unity-import-validation.md`);
the new texture-free staged path and one synthetic game-asset import are verified,
while textured/rigged/animated production export and real production assets remain
unverified. See `docs/static-fbx-skill-validation.md`.
Explicit local-point pivot preview and independent-copy apply now have source/ZIP/installed
native evidence as a sixth narrow Skill; the user also confirmed actual synthetic client
preview/verify/independent-copy apply and exact restore. Raw routing/build remains unknown.
No automatic pivot policy. See `docs/pivot-copy-validation.md`.
See `docs/skill-session-validation.md` for the evidence boundary and next client checks.
The user also confirmed fourth-Skill exposure, synthetic preview/copy-apply and exact
restoration. Separate geometry/UV tolerances now have source/bundle regression evidence;
legacy calls remain supported. See `docs/coplanar-apply.md` for provenance and limits.
Explicit current-session Profile switching to Blender diagnostics passed; see
`docs/profile-workflow-validation.md`. See `skills/README.md`
and `docs/skill-packaging.md` for current capabilities and reproducible regression/bundles.

Those skills should be added after they are researched and tested against real Blender + MCP workflows.

## Recommended first steps

1. Put this repository under Git.
2. Open the repository root in Codex when developing GameAssetAI.
3. Read `docs/requirements.md` and follow `docs/development-workflow.md`.
4. Run the offline foundation checks:

```bash
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests/workspace -p "test_*.py" -v
```

5. Create the personal workspace in a new/empty folder outside this repository using:

```bash
python scripts/create_workspace.py "D:/AI/GameAssetAI-Workspace"
```

6. Validate it with `python -B scripts/validate_workspace.py "D:/AI/GameAssetAI-Workspace"`.
   See `docs/workspace-contract.md` to create/switch profiles. Do not use `--force` as
   an update command: it overwrites personal instructions and configuration.
7. Configure the chosen Blender MCP externally and verify it using
   `docs/blender-verification.md`. GameAssetAI skills do not install MCP.
8. During normal asset work, open the generated `GameAssetAI-Workspace` in Codex instead of this repository.

## Repository map

```text
GameAssetAI/
├─ AGENTS.md
├─ README.md
├─ LICENSE
├─ .gitignore
├─ docs/
├─ skills/
├─ scripts/
├─ tests/
├─ templates/
└─ workspace-template/
```

See `docs/architecture.md` for the intended responsibilities of each area.

## Scope

Primary target:

- Blender game asset creation and modification
- Unity-focused workflows; Unreal-specific support is out of current scope
- static meshes
- characters
- armatures / bones
- imported rigs
- Mixamo-compatible humanoid workflows
- imported animation cleanup and editing
- game-engine export preparation

Not a primary target:

- AI video generation
- cinematic video pipelines
- forcing every asset to be generated from scratch
- forcing a specific game directory layout
- replacing all human review
- Unreal-specific export or import workflows
- external/public Skill distribution

Local installation and validation of Skills in the personal Workspace remain part of
normal development; they are not a public release workflow.

## Design principle

GameAssetAI skills should answer **how to perform reusable work**.

Game-specific decisions belong in the user's workspace profile.

Example:

```text
Skill:
"Inspect the active profile for poly budget before optimizing a mesh."

Profile:
"Environment props should normally stay below 5k triangles."
```

This keeps the same installed skills useful across many games and art styles.
