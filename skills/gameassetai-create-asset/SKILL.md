---
name: gameassetai-create-asset
description: Plan and execute a catalog-aware new game-asset task from text, style presets, and optional references while reporting unsupported generation capabilities honestly.
---

# GameAssetAI Create Asset

Use this Skill for new 3D asset work. Read the active Workspace Profile, validate an Asset
Specification, inspect Blender through the configured MCP connection, choose only an implemented
generation provider, and stop for visible/semantic review before rigging, 2D conversion, or export.

The catalog includes characters, creatures, props, equipment, environments, structures, and
VFX meshes. Registration does not mean generation is implemented. Never force humanoid topology,
limbs, Rig, or animation rules onto another character type.

The bundled runtime retains bounded Blender-native static assembly and template-based humanoid
building blocks. Their evidence does not establish general prompt-to-mesh generation or the four
target 3D styles. If no suitable implemented provider exists, produce a validated specification
and report the capability gap instead of substituting a primitive-only final asset.

Do not mutate an existing source asset under this Skill; route that request to the modification
Skill. Preserve any open Scene data not owned by the current operation.
