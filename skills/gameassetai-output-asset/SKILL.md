---
name: gameassetai-output-asset
description: Allocate a link-safe collision-resistant Workspace run and produce bounded Blend, FBX, PNG, animation-sequence, or sprite-sheet deliverables from an accepted source.
---

# GameAssetAI Output Asset

Use this Skill after a source asset has passed explicit visible and semantic review. Route
Workspace/Profile administration to `gameassetai-workspace`; route source creation or revision to
the matching Skill before publication.

1. Validate the Workspace and active Profile.
2. Confirm the accepted source, requested formats, asset category, game id, and destination.
3. Allocate a unique run with the bundled CLI:

   ```text
   python scripts/gameassetai.py outputs begin <workspace> --game <game> --category <category> --asset <asset>
   ```

4. Use only the needed `models/`, `previews/`, `exports/`, or `sprites/` folders inside that run.
5. Execute the bounded exporter/renderer, validate files and manifest data, and report the exact
   run path. Never overwrite an existing run or artifact.

The allocator rejects link/reparse-point path components and collisions. The manifest describes
the run but is not hidden product state. Users may delete the entire `outputs/` tree; this removes
their deliverable copies but must not damage Profiles, settings, catalogs, installed Skills, or
future work.

Current helpers cover bounded static and Generic animated FBX preparation, deterministic
static/action PNG rendering, batch coordination, quantization, and sprite-sheet assembly. They do
not prove Unity Humanoid Avatar setup, every material round trip, autonomous pixel-art direction,
or an accepted end-to-end eight-direction workflow.

An AI concept/reference image supplied before modeling, a Blender preview rendered for review,
and a final game PNG/pixel sprite/sprite sheet are distinct artifacts. Do not infer an export
destination from a project bookmark. Use UnityWorkbench only when explicitly requested, and never
make a later run depend implicitly on an earlier output directory.
