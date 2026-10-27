# Action PNG-sequence Skill validation

## Scope

`blender-render-action-png-sequence` renders one explicitly named Action on one reviewed
skinned Mesh. It uses a stable range-wide orthographic camera and a separate background
Blender process. It does not modify or save the interactive Scene, edit/retarget the Action,
guess a root bone, overwrite output, assemble a sprite sheet or import into Unity.

## Blender 5.0.1 evidence

- The candidate/framing/stage/job suite passes 28 checks from repository sources and from
  the packaged Skill helpers.
- The factory-startup full path passes 20 checks from repository, packaged-Skill and
  Workspace-installed helpers.
- A three-frame synthetic weighted Mesh reopens with exactly one Mesh, Armature and Action;
  copied Action binding, Armature modifier target, 12.5 FPS and evaluated deformation match
  the reviewed candidate.
- All three 32x32 RGBA8 frames are rendered to owned temporary files first. Their ordered
  paths, source frames, indices, dimensions, SHA-256 values, alpha bounds, visible/color
  counts and common Object-origin anchor are bound into a sequence receipt hash.
- A synthetic failure on the second publication link removes the first link and leaves no
  target. A successful rerun publishes all three; a subsequent collision attempt changes
  none of them. Stage, job, render temporaries and published fixture files are removed exactly.

## Packaging and local deployment

The portable ZIP contains nine files and has SHA-256
`bbae462641ad450f0b7672e6500695dc1344824535e36b59c92b43aa4302295b`.
The source and installation at `D:/AI/GameAssetAI-Workspace/.agents/skills/
blender-render-action-png-sequence` are byte-aligned. A refreshed client session exposed the
Skill and accurately reported its v1 schema, supported processing, asset requirements,
all-or-nothing publication behavior and exclusions without touching Blender (user-reported).

## Remaining gates

The refreshed host completed a natural-language three-frame render at 32x32 RGBA8 and 12 FPS.
The frames use source 1/2/3, a fixed `[16,16]` anchor and distinct alpha bounds that move across
the fixed canvas. It reported atomic publication, exact test-data/stage/job teardown and an
unchanged starting-state hash. The three PNG hashes were independently rechecked from disk.

Sprite sheets, direction sets, batch Actions and Unity import validation remain later work.
