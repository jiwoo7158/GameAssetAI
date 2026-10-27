# Explicit 2D render batch contract

## Purpose

`gameassetai.2d-render-batch-request.v1` groups already complete static-v3 and
Action-sequence-v1 requests. It makes multiple directions and Actions possible without
inventing view names, frame ranges, output names or style defaults. Validation is read-only.

The first boundary permits 1-64 ordered items, at most 2,048 PNGs, and one shared existing
output directory. Item ids and output paths are case-insensitively unique. Every nested request
must independently pass its existing validator.

## Setting provenance

Each item declares exactly one source:

- `EXPLICIT`: all four Profile binding fields are null and the child Profile fields are null;
- `ACTIVE_PROFILE_PRESET`: name, active-profile reference SHA-256, Profile SHA-256 and
  canonical preset SHA-256 are complete, while the nested child carries the matching first
  three fields.

Callers resolve the preset before review and repeat resolution with the exact binding before
creating the batch job. Missing or changed Profile state is a refusal, never a fallback.

## Staging and execution

Every child uses its existing candidate, framing, independent stage and child-job workflow.
`build_2d_render_batch_job.py` then revalidates the batch, all child stage/job bytes, their
embedded requests and the exact helper hashes. It writes one new hidden JSON job only after
explicit authorization.

`run_2d_render_batch.py` rechecks that complete chain, launches each staged child in a separate
background Blender in list order, and verifies each child receipt and artifact. Publication is
all-or-nothing at batch scope: if a later child fails, earlier artifacts are deleted only while
their bytes still match their recorded SHA-256. A concurrently changed artifact is preserved and
reported as incomplete rollback.

## Evidence and limitations

Offline regressions cover request exactness, explicit directions/Actions, Profile binding,
case-insensitive collisions, total-output and shared-directory bounds, job authorization/drift,
successful coordination, later-child rollback and changed-output preservation.

Blender 5.0.1 passes a seven-check mixed synthetic run: one static direction plus one three-frame
Action direction, deliberate second-child process failure with complete rollback, successful
four-PNG publication, ordered child receipts, artifact hashes and exact teardown. Repository and
packaged-Skill helpers both pass.

The contract does not infer compass directions, generate Actions, run children in parallel,
resume partial work, assemble sheets or configure Unity. PNG success is not visual-quality or
engine-import certification.
