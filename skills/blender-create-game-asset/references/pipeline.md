# Game-asset workflow routing

## Choose the source route

| User intent | First Skill | Continue only when applicable |
| --- | --- | --- |
| New prop, weapon or simple environment piece | `blender-create-static-asset` | inspection, copy-only cleanup, transform/pivot, static export or 2D rendering |
| New low-poly humanoid | `blender-create-character-base` v3 `BOOLEAN_CONNECTED` blockout | topology/revision and deformation-readiness gate, then rigging and reviewed Action authoring |
| Existing static Mesh | `blender-inspect-asset` and `blender-validate-static-mesh` | guarded cleanup/transform/pivot/LOD or static export |
| Existing character or Armature | `blender-inspect-asset` and `blender-inspect-humanoid` | animation inventory, Mixamo preflight or explicit retarget path |
| Existing/imported animation needing a game clip | `blender-prepare-game-action` after inventory | strict range extraction when eligible; otherwise evaluated-pose range/FPS bake with loop/root inspection |
| Explicit Mixamo-style FBX to apply to a compatible empty Humanoid rig | `blender-import-humanoid-animation` | inspect the new Action, then optional cleanup/rendering |
| Reviewed rig needing a new simple Action | `blender-author-pose-action` | evaluated loop review and Action rendering |
| Reviewed single-Mesh/single-Armature game Action for Unity | `blender-export-animated-fbx` | staged FBX, fresh Blender round-trip, then explicit Unity Generic import validation |

## Optional downstream routes

- Static 2D sprite/icon: `blender-render-static-pixel-png`.
- Animated frames: `blender-render-action-png-sequence`.
- Equal-cell sheet: `assemble-png-sprite-sheet`.
- Mixed explicit render batch: `blender-render-2d-batch`.
- Normal/depth/mask/object-ID/impostor outputs: use only when explicitly required.
- Static texture-free FBX: `blender-export-static-fbx`.
- Single skinned Mesh/Armature/Action Unity Generic FBX: `blender-export-animated-fbx`.

## Known gaps that must not be hidden

- Static creation is explicit primitive assembly, not arbitrary prompt-to-mesh modeling.
- Character creation has a guarded v3 exact-Boolean connected candidate. The global
  `VOXEL_CONNECTED` experiment remains suspended after visible limb/foot fusion. V3 must pass
  component/manifold/clearance gates and recorded multi-view acceptance. Its current Boolean
  topology is not a product rig target until edge-flow, UV and pose-deformation gates exist.
- Character rigging supports only the owned base character and first-pass region weights.
- Pose authoring requires explicit key poses; it is not full procedural motion generation.
- Mixamo-style FBX import and explicit pose-space sampled retargeting are implemented for the
  bounded 17-role mapping, but Adobe login/upload/download remains manual and no real Mixamo
  service round trip is proven.
- Game Action preparation supports explicit pose-bone Actions, sampled range/FPS rebasing and
  exact redundant-key cleanup. Seamless-loop repair, root-motion conversion, NLA editing and
  approximate key reduction remain outside its contract.
- Animated FBX v1 is engine-proven only for one local Mesh, one Armature, one Object-slot Action,
  Unity Generic, `IN_PLACE`, non-looping clips and Blender materials without texture baking.
  Humanoid Avatar certification, root-motion conversion, loop editing, Animator Controllers,
  multi-Mesh/multi-Action export, GLB and Unreal remain unsupported.

If a request crosses one of these gaps, complete the supported portion, preserve its output, and
state the missing capability rather than routing to an unrelated inspection or rendering Skill.
