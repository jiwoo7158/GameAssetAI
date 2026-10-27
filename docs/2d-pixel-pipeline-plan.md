# 3D-to-2D pixel / stylized pipeline plan

## Status and interpretation

This is a future-development plan, not a current implementation claim. It adapts
`blender_pixel_pipeline_plan.md` to the existing GameAssetAI repository instead of copying
the reference document's proposed project tree.

In that reference, `SKILL_3D_ASSET.md` means the existing Blender 3D asset Skills under
`skills/`. Do not create a replacement monolithic 3D Skill, rename existing Skills, or
duplicate their modeling, rigging, animation, inspection, retargeting or export behavior.

The former Add-on deferral in this document is superseded by `docs/PROJECT_AUDIT.md`. The Add-on
is a retained core UI/execution layer. Persistent installation, source alignment, transactional
update/restore and restart survival are complete; current priorities are recorded in the audit,
implementation memory and active roadmap.

The 2D pipeline is a downstream consumer of existing Blender assets:

```text
existing or newly prepared 3D asset / Action
→ inspect and preserve source
→ explicit 2D view/style setup
→ preview and validate
→ render staged outputs
→ optional sprite-sheet / Unity validation
```

## Architecture fit

- Keep GameAssetAI as the development source for reusable Skills, helpers, tests,
  documentation and any future Blender-side implementation.
- Keep GameAssetAI-Workspace as the personal Codex workspace containing active game
  profiles and mappings. It is not a render-output directory by default.
- Keep Blender, Unity and asset projects in their current locations.
- Continue using externally configured Blender MCP. The repository Add-on encapsulates tested
  operators/UI but must not install or own Blender MCP.
- Maintain the existing Add-on tree and add persistent installation/update/version verification;
  do not duplicate Skill/helper logic inside UI operators.

## Responsibility boundary

Reusable repository behavior may define schemas, validation and neutral mechanisms for:

- Pixel Art, Cel Shading and Flat Toon modes
- explicit side, top-down, quarter, isometric and portrait camera views
- orthographic camera and framing setup
- explicit lighting configurations
- low-resolution render, nearest-neighbor preview and anti-aliasing policy
- outline, shadow-band and highlight-band controls
- automatic palette reduction or an explicitly supplied fixed palette
- single-image and Action-frame PNG sequence rendering
- anchor/pivot metadata and later sprite-sheet assembly
- later optional normal, mask, depth and impostor passes

Game-specific choices belong in the active Workspace Profile, including art direction,
fixed palette, preferred view, target resolution, outline/shading parameters, naming,
output destination and Unity import expectations. Reusable code must not silently choose
JRPG, dark-pixel, palette, resolution or project paths as universal defaults.

## Safety and output contract

- Inspect the target Object, materials, rig and Action before setup or rendering.
- Separate analysis/preview from mutation and export authorization.
- Prefer an owned temporary Scene or explicitly named independent setup over rewriting the
  user's active Scene, camera, lights, materials, compositor or workspace layout.
- Do not replace source materials or Actions merely to render a style variant.
- Require explicit absolute output roots or validated Profile values.
- Stage render outputs, validate expected files and dimensions, and publish without
  overwriting existing PNG, sprite-sheet, metadata or Unity `.meta` files.
- Record camera, lighting, palette, resolution, frame range, Blender version and source
  fingerprint so repeated output can be compared.

## Incremental roadmap

### Phase 0 — capability and contracts

1. Inventory Blender 5.x render, compositor, color-management and image-save APIs exposed
   through the current MCP execution path. Completed read-only on Blender 5.0.1; see
   `docs/2d-render-capability-validation.md` for version-specific API findings.
2. Define explicit, game-neutral request schemas for view, lighting, pixel/style and
   output. The first static contract is complete; see
   `docs/2d-static-render-contract.md`.
3. Define source/setup/output fingerprints and deterministic teardown requirements.
4. Build isolated synthetic fixtures; do not use production assets as the first test.

### Phase 1 — minimal static output

1. Read-only candidate inspection for one explicit Mesh and view.
2. Temporary orthographic camera/framing preview.
3. Temporary neutral lighting and transparent-background preview.
4. One explicit Pixel/Cel/Toon render configuration.
5. Staged single PNG output with resolution, alpha, palette/count and no-overwrite checks.

This phase should prove one view and one static asset before adding a broad preset library,
custom UI or batch behavior.

The first Pixel/RGBA8 slice is now implemented as
`blender-render-static-pixel-png`; see `docs/2d-static-pixel-skill-validation.md`.
Deterministic explicit-count AUTO palette reduction is also implemented in the same Skill.
An explicit one-pixel outer outline and game-neutral HSV-value step banding are implemented
in that same Skill. This does not claim perceptual palette optimality or complete
CEL/Flat-Toon materials, lighting, animation or batch items in later phases.

### Phase 2 — animation output

1. Explicit Action/slot/frame-range inspection using existing animation Skills.
2. PNG sequence rendering with stable camera, lighting, framing and anchor.
3. Continuity checks for dimensions, alpha bounds, anchor and frame naming.
4. Sprite-sheet assembly with explicit row/column/order metadata.

### Phase 3 — production convenience

- validated Profile-backed preset save/load
- direction sets and multiple Actions
- batch processing with collision and partial-failure recovery
- Blender panel/operator layer backed by stable command behavior
- preview workspace only if it can be created reversibly without disturbing user layouts

### Phase 4 — optional engine/advanced outputs

- normal, mask, depth and impostor passes
- Unity sprite import/slicing validation and import presets
- optional Unity MCP integration after file-level validation is stable

Unity MCP is not required for the Blender-side MVP. Unreal-specific work and public Skill
distribution remain outside current scope.

The historical panel deferral is no longer authoritative. Persistent installation,
source/installed verification, transactional update/restore and fresh-process survival are now
complete. See
`docs/2d-blender-addon-evaluation.md` for the superseding decision.

## Validation gates

Each phase must pass repository-source, portable-bundle and installed-helper Blender tests
where applicable. A rendering feature is not stable until it has at least:

- one representative successful fixture
- missing/ambiguous input refusal
- existing asset/Scene preservation evidence
- deterministic output and collision checks
- exact temporary-data teardown
- documented Blender/version and color-management limitations

Visual review may supplement these checks but must not replace structural and pixel-level
validation. Do not claim pixel-art quality, animation continuity or engine compatibility
from file creation alone.
