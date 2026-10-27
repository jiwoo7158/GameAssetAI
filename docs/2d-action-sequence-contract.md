# Action PNG-sequence request contract

## Purpose

`gameassetai.2d-action-sequence-request.v1` is the offline, read-only input boundary for
rendering one explicit Blender Action as an ordered PNG sequence. It does not open Blender,
bind an Action, render, create directories or publish files.

The request embeds the current `gameassetai.2d-static-render-request.v3` fields except for
its single-file output. This reuses the already tested Profile, camera, lighting, Pixel,
palette, value-step and outline policies instead of creating a second style contract.

## Required sections

- `static_template`: exact v3 Scene/Object/Profile/view/lighting/style data.
- `animation`: exact Armature and Action names, optional explicit slot identifier, integer
  start/end/step and playback FPS. The positive step must land exactly on the inclusive
  end frame. The first contract permits at most 2048 output frames.
- `framing`: `ACTION_RANGE` bounds with an `OBJECT_ORIGIN` anchor. Per-frame framing and
  guessed root bones are intentionally refused because they can cause sprite jitter.
- `output`: an existing absolute directory, safe filename prefix, nonnegative starting
  index, 1-8 digit padding and mandatory `overwrite: false`.

The validator produces an ordered mapping from each source frame to a sequence index,
absolute PNG path and ordinary static-request hash. Every planned PNG and sibling `.meta`
must be absent. It returns hashes for both the complete sequence request and the expanded
frame plan, while leaving the directory unchanged.

## Implemented development boundary

The read-only Blender candidate now requires one exact Armature modifier, a deform vertex
group, an exact Action/slot and pose-transform F-Curves that reference existing bones. It
evaluates an isolated Mesh/Armature copy at every planned frame, computes stable union bounds
and binds the source, Action, evaluation and frame plan to hashes while restoring the open
Scene exactly.

The framing planner derives one orthographic camera from that sampled union and records the
Mesh Object origin anchor. An authorized staging helper copies only the reviewed Mesh,
Armature and Action into a hidden blend, retargets the copied modifier/binding, preserves
fractional playback FPS, and refuses target collisions. A separate authorized job builder
binds that stage and the exact ordered frame plan to a new hidden JSON file. Neither helper
renders or publishes a PNG. The isolated renderer now renders and verifies all owned temporary
frames before publishing any target; a partial publication error removes only files created by
that invocation.

Root-bone anchoring, fractional frame sampling, per-frame framing, spritesheets, partial
resume, Unity import and batch Actions remain separate later capabilities.

Seven offline regressions cover deterministic frame mapping/no writes, exact bounded frame
ranges, names/slot/FPS, narrow framing, naming/collision behavior, reuse of the current
static v3 contract, and missing/unknown field refusal.

Blender 5.0.1 passes 28 integrated candidate/framing/stage/job checks. A separate factory-
startup full-path regression passes 20 checks, including Action binding, modifier retarget,
fractional FPS, per-frame evaluated deformation, ordered artifact/receipt hashes, deliberate
mid-publication rollback, collision refusal and exact file teardown.
