---
name: gameassetai-output-asset
description: Allocate collision-safe Workspace output runs and produce bounded Blend, FBX, PNG, animation-sequence, or sprite-sheet deliverables from an accepted source.
---

# GameAssetAI Output Asset

Use this Skill only after the source passes explicit visible/semantic review. Begin a unique run
under `outputs/<game>/<asset-category>/<run-id>/`; create only the artifact folders needed by the
request. The run manifest is descriptive output metadata, not hidden runtime state.

The bundled runtime retains bounded static and Generic animated FBX preparation, deterministic
static/action PNG rendering, batch coordination, quantization, and sprite-sheet assembly. Current
evidence does not prove Unity Humanoid Avatar setup, every material/texture round trip, autonomous
pixel-art direction, or a complete eight-direction product workflow.

Never infer an export destination from a project mapping alone. Use UnityWorkbench only when the
user explicitly requests it. Never overwrite an existing deliverable, and never make a later run
depend implicitly on an earlier output directory.
