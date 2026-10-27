# Animation loop endpoint inspection — 2026-09-23

`blender-inspect-animation-loop` performs a read-only scalar comparison of every stored
F-Curve in one explicitly named Action at explicit start and end frames. It reports the
evaluated values, absolute delta, supplied tolerance result, presence of keys at both
boundaries and stored Cycles modifiers without changing the current frame.

The user or active Workspace Profile must provide the range and value tolerance. The
Skill does not infer game-specific tolerances. `endpoint_candidate=true` requires every
stored component to match within that tolerance and every channel to contain keys at both
explicit boundaries.

An owned Blender 5.0.1 fixture passed nine checks: matching and mismatching components,
Cycles-modifier inventory, boundary-key coverage, explicit relaxed tolerance, missing
boundary review, invalid range/tolerance refusal, missing Scene/Action refusal, inventory
and frame preservation, and exact fixture teardown. Repository source, portable ZIP and
installed Workspace helpers pass the same suite. The ZIP SHA-256 is
`101d1df1cfacd66a3c97a23ddda2ec8510f5cb7c0614196a37e6318b8aad5ec1`.

The Skill was installed without overwrite at
`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-animation-loop`.
Refreshed-client discovery remains unverified.

This is intentionally not a visual or evaluated-pose loop certificate. It does not
normalize Euler wrapping or quaternion sign equivalence and does not inspect tangent or
velocity continuity, constraints, drivers, NLA blending, root-motion policy, retargeting,
Unity clip settings, or animation edits.
