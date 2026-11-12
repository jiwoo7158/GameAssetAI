# Legacy isolation inventory

This directory is a historical holding area, not active GameAssetAI product code. The inventory
records the 90 tracked candidates isolated on 2026-11-13 before the first representative asset
experiment:

| Kind | Original root | Isolated root | Files |
|---|---|---|---:|
| Blender Runtime | `src/gameassetai/blender/` | `archive/legacy/src/gameassetai/blender/` | 70 |
| Blender Add-on | `blender_addon/gameassetai/` | `archive/legacy/blender_addon/gameassetai/` | 14 |
| Retained contract tests | `tests/retained_blender/` | `archive/legacy/tests/retained_blender/` | 6 |

## Common disposition

- **Current decision:** unverified and held (`미검증·보류`). No file in this inventory is a
  currently adopted product capability, production helper, provider, Add-on, or formal product
  test.
- **Current product reference:** none. Active Runtime, Skills, package/distribution builds, CI,
  and formal tests must neither import nor discover this tree. Deleting the complete `archive/`
  tree from a separate checkout must not change product behavior.
- **Old evidence:** file-local guards, historical contract tests, and earlier roadmap/test records
  exist, but none is current representative visual acceptance, Blender 5.2 adoption evidence, or
  engine proof. Historical test labels are not promoted into the current capability matrix.
- **Future handling:** inspect a specific candidate only when a bounded work package needs it.
  Adoption requires dependency, Blender-version, safety, representative-asset, license (where
  applicable), and rollback review; then move only the adopted code into active source with
  focused current tests. Git history is the recovery mechanism for anything later deleted.
- **External dependency abbreviations:** `bpy`, `bmesh`, and `mathutils` are Blender Python APIs;
  `stdlib` is Python's standard library. Bare sibling module names below are internal legacy
  dependencies, not active product imports.

## Blender Runtime candidates (70)

Every row maps from `src/gameassetai/blender/<file>` to
`archive/legacy/src/gameassetai/blender/<file>` and inherits the common disposition above.

| File | Actual function | Internal dependencies | External dependencies / note |
|---|---|---|---|
| `__init__.py` | Historical package marker and evidence claim | none | none; claim is not current evidence |
| `action_copy.py` | Preview/apply guarded unbound Action copies | none | `bpy`, stdlib |
| `aligned_retarget_action.py` | Remap Action paths for explicitly aligned rigs | none | `bpy`, stdlib |
| `apply_coplanar.py` | Apply a coplanar mesh operation to an owned copy | preview helpers by runtime loading | `bpy`, `bmesh` |
| `apply_pivot_copy.py` | Apply pivot changes to an owned copy | scale/pivot preview helpers by runtime loading | `bpy`, `mathutils` |
| `apply_scale_copy.py` | Apply scale to an owned copy | transform/scale preview helpers by runtime loading | `bpy`, `mathutils` |
| `assemble_2d_sprite_sheet.py` | Assemble verified PNG frames and metadata | `quantize_rgba`, `validate_2d_sprite_sheet_request` | stdlib |
| `author_pose_action.py` | Author a pose Action from a request | `validate_pose_action_request` | `bpy`, stdlib |
| `bake_root_translation.py` | Bake root translation through temporary rig copies | none | `bpy`, `mathutils`, stdlib |
| `bake_rotation_retarget.py` | Bake rotation retarget data through working copies | none | `bpy`, stdlib |
| `bind_action_empty.py` | Bind a protected Action to an empty Armature with rollback | none | `bpy`, stdlib |
| `build_2d_action_sequence_job.py` | Build a hash-bound Action sequence render job | none | stdlib |
| `build_2d_render_batch_job.py` | Build an authorized staged-render batch job | `validate_2d_render_batch_request` | stdlib |
| `build_2d_render_receipt.py` | Build a hash-bound receipt for a static PNG | none | stdlib |
| `build_2d_staged_render_job.py` | Build a hash-bound isolated render job | none | stdlib |
| `check_affine_uv.py` | Check affine UV mapping for coplanar corners | none | stdlib |
| `cleanup_loose.py` | Preview/clean loose geometry on an owned copy | none | `bpy`, `bmesh`, stdlib |
| `compose_retarget_actions.py` | Compose rotation and root-location Actions | none | `bpy`, stdlib |
| `create_character_base.py` | Build a parameterized primitive-based character base | `validate_character_base_request` | `bpy`, `bmesh`, `mathutils` |
| `create_static_asset_assembly.py` | Build parameterized static-part assemblies | `validate_static_asset_assembly_request` | `bpy`, `bmesh`, `mathutils` |
| `export_animated_fbx.py` | Stage/publish one skinned animated FBX | none | `bpy`, `mathutils`, stdlib |
| `export_mixamo_handoff.py` | Export a Mixamo handoff file | none | `bpy`, stdlib |
| `export_static_fbx_staged.py` | Stage, verify, and publish a static FBX | none | `bpy`, stdlib |
| `extract_2d_profile_preset.py` | Extract an exact 2D block from Profile context | `validate_2d_static_render_request` | stdlib |
| `extract_action_range.py` | Extract a keyed Action frame range into a copy | none | `bpy`, stdlib |
| `import_humanoid_animation.py` | Import humanoid animation with snapshots/rollback | humanoid, Mixamo, and request validators | `bpy`, `mathutils`, stdlib |
| `inspect_2d_action_sequence_candidate.py` | Inspect an Action sequence candidate in a temporary Scene | none | `bpy`, stdlib |
| `inspect_2d_static_render_candidate.py` | Inspect a static 3D-to-2D candidate | none | `bpy`, stdlib |
| `inspect_action_loop.py` | Compare stored F-Curve endpoints | none | `bpy`, stdlib |
| `inspect_animation.py` | Inventory Actions, bindings, NLA, and root channels | none | `bpy`, stdlib |
| `inspect_asset.py` | Inventory Blender Scene objects, meshes, materials, animation | none | `bpy`, stdlib |
| `inspect_evaluated_pose_loop.py` | Compare evaluated pose endpoints on a rig copy | none | `bpy`, stdlib |
| `inspect_evaluated_root_motion.py` | Evaluate explicit root-bone motion on a rig copy | none | `bpy`, stdlib |
| `inspect_humanoid.py` | Inspect an explicitly mapped humanoid Armature | none | `bpy` |
| `inspect_mixamo_preflight.py` | Inspect Mixamo-style Armature readiness | none | `bpy`, stdlib |
| `inspect_retarget_readiness.py` | Inventory source/target retarget readiness | none | `bpy`, stdlib |
| `inspect_root_motion.py` | Inspect Object or bone translation in an Action | none | `bpy`, stdlib |
| `inspect_static_export_context.py` | Combine static asset/transform export context inspection | asset/transform inspectors by runtime loading | `bpy` |
| `inspect_static_fbx_candidate.py` | Inspect a static FBX request candidate | none | `bpy`, stdlib |
| `inspect_static_transform.py` | Capture a read-only transform snapshot | none | `bpy`, stdlib |
| `prepare_game_action.py` | Prepare an evaluated Armature Action as a game clip | none | `bpy`, `mathutils`, stdlib |
| `preview_2d_action_sequence_framing.py` | Plan stable orthographic framing over an Action range | none | `mathutils`, stdlib |
| `preview_2d_orthographic_framing.py` | Plan orthographic framing for a static candidate | none | `mathutils`, stdlib |
| `preview_coplanar.py` | Preview coplanar processing and geometry hashes | cleanup/UV helpers by runtime loading | `bpy`, `bmesh`, stdlib |
| `preview_pivot_copy.py` | Predict/verify a pivot change | transform/scale helpers by runtime loading | `bpy`, `mathutils`, stdlib |
| `preview_scale_copy.py` | Predict/verify a scale change | transform inspector by runtime loading | `bpy`, `mathutils`, stdlib |
| `promote_export_artifact.py` | Atomically publish a staged export | none | stdlib |
| `quantize_rgba.py` | Quantize RGBA8 pixels and encode minimal PNG | none | stdlib |
| `record_visual_review.py` | Write a hash-bound review decision | none | stdlib; historical record helper only |
| `render_2d_action_sequence.py` | Render an Action sequence in background Blender | job/request contract by input | `bpy`, stdlib |
| `render_2d_staged_source.py` | Render a staged static source in background Blender | job/request contract by input | `bpy`, stdlib |
| `replace_action_current.py` | Replace/rollback an exact current Action | none | `bpy` |
| `resolve_2d_profile_preset.py` | Resolve a complete 2D preset with provenance checks | `extract_2d_profile_preset` | stdlib |
| `rig_character_base.py` | Construct a landmark-driven character rig | `validate_character_rig_request` | `bpy`, `mathutils`, stdlib |
| `run_2d_render_batch.py` | Run staged child renders with rollback | `validate_2d_render_batch_request` | stdlib/subprocess |
| `stage_2d_action_sequence_source.py` | Stage Mesh, Armature, and Action copies | none | Blender host context, stdlib |
| `stage_2d_static_source.py` | Stage a static Mesh copy to a temporary blend | none | Blender host context, stdlib |
| `state_helpers.py` | Inspect source state and file-wide dependencies | none | `bpy` |
| `validate_2d_action_sequence_request.py` | Validate Action-to-PNG-sequence requests | `validate_2d_static_render_request` | stdlib |
| `validate_2d_render_batch_request.py` | Validate mixed static/Action render batches | both 2D request validators | stdlib |
| `validate_2d_sprite_sheet_request.py` | Validate PNG-frame sprite-sheet requests | none | stdlib |
| `validate_2d_static_render_request.py` | Validate static 3D-to-2D render requests | none | stdlib |
| `validate_animated_fbx_request.py` | Validate animated-FBX export requests | none | stdlib |
| `validate_character_base_request.py` | Validate character-base/revision request data | none | stdlib |
| `validate_character_rig_request.py` | Validate character-rig request data | none | stdlib |
| `validate_humanoid_animation_import_request.py` | Validate humanoid animation import requests | none | stdlib |
| `validate_mesh.py` | Calculate Blender mesh diagnostics | none | `bpy`, stdlib |
| `validate_pose_action_request.py` | Validate pose Action request data | none | stdlib |
| `validate_static_asset_assembly_request.py` | Validate static assembly request geometry/data | none | stdlib |
| `validate_static_fbx_request.py` | Validate static FBX export requests | none | stdlib |

## Blender Add-on candidates (14)

Every row maps from `blender_addon/gameassetai/<file>` to
`archive/legacy/blender_addon/gameassetai/<file>` and inherits the common disposition above. The
Add-on is not installed or enabled by this repository change.

| File | Actual function | Internal dependencies | External dependencies / note |
|---|---|---|---|
| `__init__.py` | Register/unregister the historical Add-on | Add-on operators, panels, properties | `bpy` through children |
| `constants.py` | Store owned-object/node/material tag constants | none | none |
| `operators/__init__.py` | Register/unregister Add-on operators | operator modules | `bpy` through children |
| `operators/action_preview.py` | Preview an Action through a Blender operator | none | `bpy` |
| `operators/build_nodes.py` | Build/remove an owned pixel compositor | `constants` | `bpy` |
| `operators/export_preview.py` | Export a preview PNG | none | `bpy`, stdlib |
| `operators/material_presets.py` | Create/apply flat, emission, or cel materials | `constants` | `bpy`, stdlib |
| `operators/presets.py` | Save/load Add-on setting presets | none | `bpy`, stdlib |
| `operators/sequence_bridge.py` | Bridge UI requests to sequence render helpers | runtime helpers loaded by path/subprocess | `bpy`, stdlib |
| `operators/setup_scene.py` | Create/remove an owned preview Scene setup | `constants` | `bpy`, `mathutils` |
| `operators/sprite_sheet_bridge.py` | Bridge the latest sequence to sheet assembly | runtime helpers loaded by path | `bpy`, stdlib |
| `panels/__init__.py` | Register/unregister panels | panel modules | `bpy` through children |
| `panels/pixel_pipeline.py` | Draw a pixel-pipeline UI panel | none | `bpy` |
| `properties.py` | Define Add-on Scene properties/settings | none | `bpy` |

## Retained contract-test candidates (6)

Every row maps from `tests/retained_blender/<file>` to
`archive/legacy/tests/retained_blender/<file>` and inherits the common disposition above. These
tests are historical evidence only and are intentionally outside current `unittest` discovery.

| File | Actual function | Internal dependencies | External dependencies / note |
|---|---|---|---|
| `__init__.py` | Mark the historical retained-test package | none | none |
| `test_action_sequence_contract.py` | Offline Action-sequence request regressions | two legacy 2D validators | stdlib `unittest` |
| `test_character_base_contract.py` | Offline character-base request regressions | legacy character-base validator | stdlib `unittest` |
| `test_sprite_sheet_contract.py` | Offline sprite-sheet validation/assembly regressions | legacy sheet validator, assembler, quantizer | stdlib `unittest` |
| `test_static_asset_contract.py` | Offline static-assembly request regressions | legacy static-assembly validator | stdlib `unittest` |
| `test_static_fbx_contract.py` | Offline static-FBX preflight regressions | legacy static-FBX validator | stdlib `unittest` |

## Adoption gate

An archived file may return to active source only through a bounded roadmap package that records:

1. the current task and representative asset requiring it;
2. why Blender native capability or current active Runtime is insufficient;
3. exact internal/external dependencies, supported Blender version, and license/maintenance facts;
4. source-preservation, no-overwrite, rollback, and failure behavior;
5. focused current tests plus representative visible/semantic review where the capability affects
   asset quality; and
6. removal or continued isolation of superseded alternatives.

Until that gate is satisfied, archived code must not be imported, vendored into a Skill, copied
into `dist/workspace`, executed by CI, or described as a supported capability.
