# Current-Action Replacement Validation

`blender-replace-current-action` swaps one explicitly identified Armature current Action
for one explicitly identified protected/unbound Action. It preserves both Actions and
returns a hashed receipt that can restore only the exact unchanged previous binding.

## Evidence

- Blender: 5.0.1
- MCP implementation: `ahujasid/blender-mcp`, `localhost:9876`
- Add-on: 1.7, protocol 7; server expected protocol 11 and used compatible fallbacks
- Archive: `.local/source-bundles/action-replacement-20260927/blender-replace-current-action.zip`
- Archive SHA-256: `13032bbc4fb267a770e2055ae2fc5a38c37935e42de4f16fa7eaf98efe058a82`
- Installed at:
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-replace-current-action`

Repository source, the portable ZIP and the actual installed helpers each passed the same
16-check synthetic Blender regression. Coverage includes exact preview, missing
authorization, NLA/driver rejection, stale replacement content, wrong-current rejection,
exact reference swapping, unchanged Action content, missing rollback authorization,
tampered receipt and changed-previous rejection, exact restoration and owned-data teardown.
The original Cube/Light/Camera Scene matched its starting state after every run.

## Boundaries

The only supported policy is `CURRENT_ONLY`. The previous Action must be the named
Armature's sole current reference, and the replacement must be unbound. Both must already
be fake-user protected single-Object-slot Actions. The workflow never deletes either
Action, edits curves, handles NLA stacks or drivers, changes a Rig, saves, exports, or
configures Unity. Production Action compatibility, deformation and Unity animation import
remain separate validation. Refreshed-client discovery is not yet verified.
