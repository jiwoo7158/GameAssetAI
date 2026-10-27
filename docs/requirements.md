# Requirements

## Requirement identifiers

The identifiers below are stable traceability anchors. Skill instructions and implementation work
packages should cite the applicable IDs; they do not imply that the requirement is implemented.

| ID | Area |
| --- | --- |
| `REQ-WORKFLOW` | low-friction Codex, Workspace, Blender and profile workflow |
| `REQ-STATIC` | static asset creation and revision |
| `REQ-CHAR` | new and existing character, armature and humanoid preparation |
| `REQ-ANIM` | imported/existing animation, cleanup, editing and retargeting |
| `REQ-ENGINE` | Unity-first preparation and verified handoff |
| `REQ-2D` | optional downstream Pixel/Cel/Toon output |
| `REQ-STYLE` | game-specific style through explicit requests or profiles |
| `REQ-COST` | useful local core without a paid generation dependency |
| `REQ-SAFE` | inspection, preservation, rollback and semantic acceptance |

## User workflow requirements (`REQ-WORKFLOW`)

The default daily workflow should require as little context switching as possible.

Target:

```text
1. Open Codex with GameAssetAI-Workspace
2. Open Blender
3. Ensure Blender MCP is available
4. Select / switch game profile when necessary
5. Work through natural-language requests
```

The user should not have to repeatedly:

- browse into the installed skill directory
- maintain `input/` folders
- maintain `references/` folders
- move Unity / Unreal projects
- duplicate existing Blender files into the workspace
- re-enter stable game rules every session

## Asset requirements

GameAssetAI should eventually handle:

### Static assets (`REQ-STATIC`)
- props
- weapons
- environment pieces
- modular assets
- low-poly / stylized / PSX-oriented assets
- existing static mesh cleanup

### Character assets (`REQ-CHAR`)
- new character meshes where feasible
- existing character meshes
- existing armatures
- Mixamo auto-rig workflows
- game-ready deform skeleton concerns

### Animation (`REQ-ANIM`)
- imported Mixamo animation
- imported FBX/BVH animation
- existing Blender Actions
- cleanup and organization
- retargeting where technically supported
- animation editing
- custom attack / dodge / skill refinement

### Engine preparation (`REQ-ENGINE`)
- Unity

### Downstream 2D output (`REQ-2D`)
- Pixel Art, Cel Shading and Flat Toon rendering from existing or newly prepared 3D assets
- explicit camera/view, lighting, resolution, palette, outline and shading controls
- single PNG, animation PNG sequence and later sprite-sheet output
- source Mesh/Rig/Action preservation and no-overwrite staged publication
- optional later normal/impostor passes and Unity sprite import validation

Unreal-specific preparation is out of current scope. Existing Unreal projects remain
where they are; general asset inspection need not reject them merely for existing.

## Art-style requirements (`REQ-STYLE`)

No global art style is assumed.

Game profiles may specify:

- low-poly
- stylized
- anime
- PSX-inspired
- semi-realistic
- realistic
- custom project-specific direction

Reusable skills must remain style-agnostic unless the skill is intentionally style-specific.

Reusable 2D conversion mechanics must not hard-code a game's palette, camera, resolution,
naming or export path. Those values belong in the active Workspace Profile or an explicit
request.

## Cost requirements (`REQ-COST`)

Core workflow should not depend on a paid external 3D generation service.

Optional paid or free external generators may be integrated later as replaceable tools.

Codex + Blender + Blender MCP should remain useful without them.

## Safety / preservation requirements (`REQ-SAFE`)

Existing user data is valuable.

Skills should:

- inspect before destructive edits
- preserve existing rigs when possible
- preserve animations when possible
- avoid deleting or rewriting assets without need
- distinguish "analyze" from "modify"
- create backups / duplicates when appropriate
- validate after change
- stop downstream rigging, animation, rendering and export when the source fails visible/semantic
  review, even if topology counts, manifold checks, weights or numerical metrics pass

For generated humanoids, validation must cover intended body-part connectivity, left/right limb
and foot clearance, unintended bridges/self-intersection and representative front, side and
three-quarter silhouettes. `one component` and `watertight` are not sufficient acceptance rules.

The Blender Add-on is part of the normal workflow. Do not call it available from source tests or
session-only registration; persistent Preferences installation and restart survival are required.

## Unknowns to validate

Before production skills are considered stable, verify:

- exact Blender MCP capabilities in the target environment
- screenshot / scene inspection behavior
- bone / armature inspection reliability
- animation Action manipulation
- FBX / GLB import-export behavior
- Unity-facing axis / scale conventions
- Mixamo import and retarget workflows
- Blender version compatibility
- local Desktop Skill installation / update workflow (not public distribution)
