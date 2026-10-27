---
name: assemble-png-sprite-sheet
description: Assemble explicitly ordered, equal-size RGBA8 PNG animation frames into one new sprite-sheet PNG plus JSON cell metadata without Blender or Unity. Use when frame paths, hashes, anchors, grid dimensions, padding, and row-major order are known. Never infers layout, overwrites files, edits sources, renders frames, or configures engine imports.
---

# Assemble PNG Sprite Sheet

Combine verified PNG frames into a deterministic sheet while preserving every source file.
This is an offline post-process and does not require Blender MCP or Unity.

## Required inputs

Collect the exact ordered frame list. For every frame require its absolute path, lowercase
SHA-256, source frame, nonnegative sequence index and two-number bottom-left pixel anchor.
Also require:

- exact cell width and height matching every frame
- positive columns and rows with enough cells
- explicit padding from 0 through 256 pixels
- order `ROW_MAJOR_TOP_LEFT`
- one settings source for padding/order: either explicit values or a complete active Profile
  `gameassetai-2d-preset`; never merge them
- distinct new sibling absolute `.png` and `.json` targets
- `overwrite: false`

Do not infer a grid, reorder frames, invent anchors, choose padding from a game style, or use
filename sorting as authority. The first version accepts only non-interlaced RGBA8 PNGs and
at most 2048 frames, 32768 pixels per sheet dimension and 16,777,216 total pixels.

## Workflow

1. Load `validate_2d_static_render_request.py`, `extract_2d_profile_preset.py`,
   `resolve_2d_profile_preset.py`, `validate_2d_sprite_sheet_request.py`, `quantize_rgba.py`,
   and `assemble_2d_sprite_sheet.py` from this Skill's `scripts` directory.
2. If the active Profile supplies padding/order, freshly resolve `SPRITE_SHEET` and retain
   the complete four-hash binding. An absent or invalid preset is not a default. Explicit
   mode uses four `null` Profile fields and must not consult or partially merge a preset.
   Build the exact `gameassetai.2d-sprite-sheet-request.v2` dictionary and call
   `validate_2d_sprite_sheet_request`. Report errors and stop unless status is `ready`.
   Validation must create or modify no file. Version 1 remains readable only for legacy
   requests and has no Profile provenance.
3. Show the explicit sheet dimensions, grid, padding, order, frame-to-cell mapping and target
   paths. Confirm that the user's request authorizes those exact new outputs.
4. Before assembly, reread and resolve any selected Profile preset with the retained
   `expected_binding`; refuse any change. Call
   `assemble_2d_sprite_sheet(request, preview, authorize=True)` using the fresh preview.
   Accept success only when status is `created`, both artifacts are published, and their
   SHA-256 and receipt hash are present.
5. Report PNG/JSON paths, sheet dimensions, frame count, hashes, cell rectangles, anchors and
   receipt SHA-256. Never remove the source frames or successful requested outputs.

## Fail closed

Refuse a missing/linked/non-RGBA8 input, hash or dimension mismatch, duplicate path/index,
unsupported order, insufficient/oversized layout, existing target or `.meta`, changed fresh
preview, owned-stage collision, or publication error. Both outputs are staged before either
is published. If publication fails partway, remove only artifacts created by that invocation.

## Boundaries

This Skill does not render Blender Actions, crop frames, pack irregular rectangles, extrude
edges, rotate cells, trim transparency, infer timing, create multiple sheets, configure a
Unity Sprite Editor, or validate an engine import. Treat those as separate later stages.
