# Static Pixel PNG Skill validation

## Implemented boundary

`blender-render-static-pixel-png` renders one reviewed simple static Mesh to one new
orthographic PNG. It preserves the interactive Blender file by copying the Mesh/Object
into an owned hidden `.stage.blend`, binding that file to a hidden JSON job, then loading
the stage in a background Blender process. Publication is no-overwrite and the returned
receipt binds the PNG to the request, source, setup, output and framing hashes.

The first version accepts only Pixel mode, owned neutral lighting, disabled filtering,
nearest-neighbor intent, transparent RGBA8, and palette mode `NONE` or an explicit opaque
`FIXED` palette. It now also supports deterministic weighted median-cut `AUTO` reduction
with an explicit maximum of 2 through 256 colors, alpha preservation and transparent-RGB
exclusion. It supports an explicit one-pixel outer outline and explicit 2-32 step HSV-value
banding. Perceptual optimality is not claimed. CEL/Flat-Toon materials/lighting, textures/node groups, modifiers,
parents, constraints, Shape Keys, animation, rigs and batch/sequence output fail closed.

## Blender 5.0.1 evidence

- Repository, portable ZIP and installed-Workspace helpers each passed the 9-check live
  staging regression: explicit authorization, reviewed hash chain, collision preservation,
  stale-source refusal, no PNG publication, context preservation and exact ID teardown.
- The complete installed-helper path passed 12 checks in a factory-startup background
  Blender: stage and job creation, stage reload, independent Mesh/material preservation,
  stage hash verification, PNG publication, receipt binding, target-collision refusal and
  exact temporary-file teardown.
- The earlier isolated render regression still passes 18 checks, including RGBA8 decoding,
  visible framing margins, zero partial alpha, deterministic fixed-palette processing and
  repeatable decoded pixels. Blender PNG container bytes remain outside the determinism
  claim.
- The interactive Scene remained `Cube`, `Light`, `Camera` with one material. No current
  `.blend` was saved and no test PNG, job or blend stage remained.

The current value-step-capable portable Skill ZIP contains 9 files and has SHA-256
`8e8cfba54f382329a13120324da35207a868c44ff7004313e703a69222cc12ff`.
The installed path is
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-render-static-pixel-png`.
The user confirmed refreshed-session discovery and a natural-language Cube render to a
32x32 transparent PNG. The output was 1,201 bytes with SHA-256
`17e8aa7ff0f0d7fb26d4c79752d421f35ceb3ba6af62c4dfbb49c6970048f00f`,
alpha bounds `[3, 3, 28, 28]` and receipt SHA-256
`3d0d736f70243bf5a0a347bfe807cfc8b4a04dd3f56941e000600a985e532d78`.

That host run exposed a real CLI-only defect: `render_2d_staged_source.py` referenced
`bpy` without importing it. The initial background attempt published no PNG; the host
recovered using the unchanged hash chain and completed safely. The source and installed
Skill now explicitly import `bpy`. The regression loads the renderer in an independent
namespace and invokes its actual `main()` argument parser, preventing a surrounding test
module from masking this class of failure. The prior installed version is retained at
`D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
blender-render-static-pixel-png-20260929-pre-bpy-import`.

The subsequent AUTO-palette update passes 4 dedicated algorithm tests, the 20-check live
candidate suite and a 13-check installed-helper background path. The synthetic result was
bounded to four derived opaque RGB colors, preserved alpha, produced a hash-bound receipt,
refused target collision and removed every owned temporary file. The pre-AUTO CLI-fixed
version is retained at `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
blender-render-static-pixel-png-20260929-pre-auto-palette`.

The v2 request adds an explicit `NONE` or opaque one-pixel `OUTER` silhouette while the
validator preserves v1 as legacy no-outline input. The installed helper passed 14 full
background checks with AUTO max 4 followed by a black outer ring: 84 outline pixels,
alpha bounds `[5,1,26,22]`, receipt binding, target-collision refusal and exact teardown.
The pre-outline AUTO version is retained at `D:/AI/GameAssetAI-Workspace/.agents/
skill-backups/blender-render-static-pixel-png-20260929-pre-outline`.

The first natural-language outline prompt was sent from a client session that still held
the pre-outline Skill snapshot. It correctly refused, saying its cached request schema had
no outline fields. Read-only disk checks immediately afterward confirmed both repository
and installed `SKILL.md` advertise the optional one-pixel outline and both installed
validators use `gameassetai.2d-static-render-request.v2`. Their hashes match the validated
deployment (`SKILL.md` `d3c7c9f6...`, validator `b5e75760...`). The requested target did
not exist, no `.gameassetai-2d-*` file remained, and Blender stayed Cube/Light/Camera.
This is a session-catalog freshness gate, not an implementation rollback or reason to
create a duplicate Skill name.

A subsequent completely new task from `D:/AI/GameAssetAI-Workspace` passed that
freshness gate. It reported the exact v2 request shape and both supported outline modes:
`NONE` requires a null color and zero width, while `OUTER` requires an opaque normalized
RGBA color and width exactly one. Blender was not invoked or modified for this read-only
discovery check. The only remaining host-level outline evidence is a natural-language
render through that refreshed task, followed by receipt, cleanup and Scene-state checks.

That host-level outline render subsequently passed. The 32x32 RGBA8 output at
`D:/Blender/MCP_Test/gameassetai-pixel-auto4-outline-check-20260929.png` is 215 bytes
with SHA-256 `70495b016ec32b448d65e79ddff62cb003ae22434e8d11a9151a8138feb5da7c`.
It has alpha bounds `[2,2,29,29]`, four AUTO palette colors, 108 opaque black outline
pixels and six total RGBA values including transparency and outline. The receipt SHA-256
is `c8d9890d66f4628eb51809c8f6d9e9b138964c476d64245ccbf8939b858d08ac`.
Independent file checks confirmed the artifact hash and no owned stage/job remains.

The next narrow capability uses request v3 to add `NONE` or explicit `VALUE_STEPS`
shading with 2 through 32 bands. Value banding runs before palette processing and the
outline remains last. Offline scripts pass 126 tests. Blender 5.0.1 passes 22 candidate
checks and 15 full stage/job/render checks; the latter verified a four-step value bound,
AUTO palette, one-pixel outline, collision refusal, receipt binding and exact teardown.
The portable ZIP and Workspace-installed staging helpers each pass nine checks. The
Workspace installation is byte-aligned with source, and the pre-value-step installation
is retained at `D:/AI/GameAssetAI-Workspace/.agents/skill-backups/
blender-render-static-pixel-png-20260929-pre-value-steps`. A refreshed-client
natural-language v3 render was the remaining host gate.

That v3 host gate passed on 2026-09-30. The 32x32 RGBA8 output at
`D:/Blender/MCP_Test/gameassetai-pixel-value4-auto4-outline-check-20260929.png` is
133 bytes with SHA-256
`cf630ae015ea073d13325da24fd6a0d6b0727fda13d35e3d7f924d7ee21ffc66`.
It reports alpha bounds `[2,2,29,29]`, observed shading values `[170]`, three derived AUTO
palette colors, 108 opaque black outline pixels and five total RGBA values. Receipt
SHA-256 is `c3ad5bd70953cbc709709392fe755cfa0c0c5fb7f94b3df1c5759d8319f6c5c7`.
Independent disk inspection confirmed the artifact hash and zero owned temporary files;
the host reported Cube/Light/Camera unchanged.

This proves refreshed-client discovery and execution of the v3 value-step path, but the
front-facing default Cube produced only one observed value level. Offline algorithm tests
cover multiple input values. A repository-owned two-facet ridge fixture now proves that
multiple expected bands survive the live renderer: source, portable-ZIP and installed
helpers each completed the 15-check stage/job/render path with observed values `[85,170]`,
three AUTO palette colors, 84 outline pixels, collision refusal and exact teardown. The
decoded artifact SHA-256 was consistently
`3668d0fa21331e6f28b737c658bea0a9a2b5fea3340a6c57340ec15f27c57595`.
The next pipeline unit may therefore move to the explicit Action PNG-sequence contract.

## Tooling notes

The scripts test suite passes 126 tests and repository validation passes. The Skill
Creator `quick_validate.py` could not run because its optional `yaml` module is absent;
no dependency was installed merely for that check. Frontmatter, compilation, packaging,
source parity and live behavior were validated by repository tooling.
