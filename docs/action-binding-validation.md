# Empty-Target Action Binding Validation

`blender-bind-action-empty` connects one explicit, fake-user-protected and currently
unbound Action to one explicit Armature only when the target has no current Action, NLA
tracks or drivers. It does not replace animation. Successful apply returns a hashed receipt
that can remove only the exact unchanged binding and preserves the Action.

## Evidence

- Blender: 5.0.1
- MCP implementation: `ahujasid/blender-mcp`, `localhost:9876`
- Add-on: 1.7, protocol 7; server expected protocol 11 and used compatible fallbacks
- Archive: `.local/source-bundles/action-binding-20260927/blender-bind-action-empty.zip`
- Archive SHA-256: `6e4259f71baa1afb34851a332273eb724aa3818bd79a44af7cf2e95ff07e5c3a`
- Installed at:
  `D:/AI/GameAssetAI-Workspace/.agents/skills/blender-bind-action-empty`

Repository source, the portable ZIP and the actual installed helper each passed the same
14-check synthetic Blender regression. It covered a valid candidate, missing authorization,
stale Action content, occupied-target refusal, exact Action/slot binding, content/reference
preservation, missing rollback authorization, receipt tampering, successful rollback,
protected unbound Action retention, and restoration of both absent and pre-existing empty
animation-data states. All owned Scene/Object/Armature/Action data was removed and the
original Cube/Light/Camera Scene matched its starting state.

## Boundaries

The request and preview are exact-name and content-hash bound. Apply supports only
`EMPTY_ONLY`; rollback requires the unchanged receipt, binding and Action fingerprint.
The workflow never deletes an Action, replaces an occupied current Action, edits NLA,
changes curves or the Rig, saves, exports, or configures Unity. Replacement and production
animation/Unity validation remain separate work. Refreshed-client discovery is not yet
verified.
