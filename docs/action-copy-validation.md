# Non-destructive Action copy validation — 2026-09-23

`blender-copy-action` is the first bounded Action-organization mutation. It copies one
existing Action to an explicit unused name, leaves the source and all current/NLA
references untouched, does not bind the copy, and enables the copy's fake user so the
unbound datablock can persist when the user later saves the blend file.

The request is fail-closed and exact: Scene, source and target names plus
`preserve_source=true`, `bind_copy=false`, and `set_fake_user=true`. Blender 5.0.1 was
observed silently truncating Action names beyond 255 UTF-8 bytes, so preview refuses
those names. Preview is read-only and returns request, inventory and detailed Action
content hashes. Apply requires explicit authorization, immediately regenerates the
preview, and refuses stale source content/references or a target collision.

The owned Blender fixture passed nine planning checks and eight apply checks. Apply
coverage includes missing authorization, stale source, late collision, independent copy,
Cycles modifier/content equality, unchanged source/current/NLA references, unbound target,
context preservation and exact teardown. An initial fixture changed a keyframe coordinate
and restored only its value, but Blender also moved its handles; the resulting legitimate
stale refusal led the test to use a fully reversible F-Curve mute toggle instead.

Repository source, portable ZIP and installed Workspace helpers pass the same eight apply
checks on Blender 5.0.1. The ZIP SHA-256 is
`591f467ea20487baf28ba0289194798f98ccbcc22c7e772e41695bc3428f155d`.
The Skill was installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-copy-action`; refreshed-client
discovery remains unverified.

This is not frame-range extraction, take splitting, source renaming, binding, NLA
creation, pose evaluation, loop validation, root-motion policy, retargeting, editing,
import, export, or Unity clip configuration. Unsupported custom-property values and
non-finite stored values refuse rather than receiving a partial copy guarantee.
