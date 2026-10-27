# Explicit PNG sprite-sheet contract

## Purpose

`gameassetai.2d-sprite-sheet-request.v1` combines an explicitly ordered list of existing
RGBA8 PNG frames into one new PNG sheet and one new JSON metadata file. It is a pure file
operation: Blender, Unity and the source PNGs are not modified.

## Required input

- Each frame supplies its exact source frame, sequence index, absolute path, SHA-256 and
  bottom-left pixel anchor. Paths and indices must be unique and indices increase in the
  request's authoritative order.
- Layout explicitly supplies cell width/height, columns, rows, inter-cell padding and
  `ROW_MAJOR_TOP_LEFT`. All inputs must be non-interlaced RGBA8 PNGs whose dimensions equal
  the cell size. Empty cells remain transparent.
- Output supplies distinct sibling absolute `.png` and `.json` paths in an existing real
  directory with `overwrite: false`. Targets and sibling `.meta` files must not exist.

The sheet is limited to 2048 input frames, 32768 pixels on either dimension and 16,777,216
total pixels. The contract provides no inferred grid, padding, order, animation timing or
game-specific default.

## Metadata coordinates

Cell rectangles use `[x, y, width, height]` from the sheet's top-left, matching PNG row
order. Each cell preserves the source bottom-left anchor and records its derived sheet-space
bottom-left anchor. The metadata binds source paths/hashes, layout, cell mapping and the
published sheet SHA-256.

## Publication safety

Validation is read-only. Authorized assembly reruns validation, rechecks every input hash at
the exact decode used for composition, writes owned hidden PNG/JSON stages, verifies them,
then publishes both using new hard links. If the second publication fails, the first is
removed. Existing targets are never replaced and owned stages are always removed.

Six offline regressions cover deterministic cell mapping, pixel placement, transparent
padding, metadata/anchor binding, authorization and stale preview refusal, hash/dimension/
layout/collision errors, exact fields and deliberate partial-publication rollback.

The installed helper was also exercised against the three retained natural-language Action
sequence frames. A 2x2 grid with 32x32 cells and one-pixel padding produced a 65x65 sheet,
three metadata cells and no owned temporary file. The PNG SHA-256 is
`08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`; metadata SHA-256 is
`e36b415768547da31676a7fff85a240c10f93e29860324377a8b15a49ff13f4f`.

A refreshed client then exposed `assemble-png-sprite-sheet` and completed the same explicit
layout through a natural-language call to new target names. The PNG is byte-identical with
SHA-256 `08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`;
the path-bound JSON SHA-256 is
`22c9439c888eea742d026bffab5ccf694da815a6c3ca1af7d0c27c09721729f7`, and the receipt is
`bd8ff0178269e2a6f84762933bb0ba1388379946b704bdd00f61588640cdd114`.
Independent disk inspection confirmed 65x65 output, three cells and zero owned temporary files.
