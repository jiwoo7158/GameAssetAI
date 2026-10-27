# Explicit root-motion inspection — 2026-09-23

`blender-inspect-root-motion` inventories stored translation evidence for either one
explicit Object or one exact Armature bone in a named Action and frame range. It never
guesses a root from bone names. Multi-slot Actions require an explicit slot; a sole slot
may be used unambiguously.

For each matching XYZ location F-Curve it reports endpoint values, net delta, stored key
minimum/maximum and span inside the range. `translation_evidence=true` means an endpoint
delta or stored key-value span exceeded the explicit tolerance supplied by the user or
active Profile. Non-root bone channels are excluded. Root rotation channels are listed
but deliberately not interpreted.

An owned Blender 5.0.1 Armature fixture passed ten checks: explicit Root translation,
axis evidence, non-root exclusion, rotation review, Object/Bone distinction, missing bone,
invalid range and bad slot refusal, animation/frame preservation and exact teardown.
Repository source, portable ZIP and installed Workspace helpers pass the same suite.
The ZIP SHA-256 is
`8d7ab1e164b4a00c0305bedc293d8a65658cf83780d92dc58a1e00c580092e11`.

The Skill was installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-root-motion`.
Refreshed-client discovery remains unverified.

This result does not decide in-place versus moving-root policy and does not include
interpolation extrema, world-space displacement, root rotation, constraints, drivers,
NLA blending, evaluated poses, retargeting, Unity root-motion settings or edits.
