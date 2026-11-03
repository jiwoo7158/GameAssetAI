# Game-asset workflow routing

## Choose the source route

| User intent | First Skill | Continue only when applicable |
| --- | --- | --- |
| New prop, weapon, furniture-like or simple environment piece | `blender-create-static-asset` v3/v4 for explicit profile geometry; v5 for bounded UV/image-textured style production | semantic geometry revision (v4 for owned v5 assemblies), inspection, static export or 2D rendering |
| New low-poly humanoid | `blender-create-character-base` v3 `BOOLEAN_CONNECTED` blockout | topology/revision and deformation-readiness gate, then rigging and reviewed Action authoring |
| Existing static GLB with explicit part mapping and a supported local-axis end edit | inspect the file, hash, Object names and structure, then `blender-create-static-asset` external-revision v1 | visual/structural review, then static export or 2D rendering |
| Other existing static Mesh | `blender-inspect-asset` and `blender-validate-static-mesh` | guarded cleanup/transform/pivot/LOD or static export; do not imply arbitrary geometry editing |
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

- Static creation v3/v4 adds explicit profile and matched-profile-beveled solids plus owned
  semantic geometry replacement. External-revision v1 additionally supports one complete,
  explicit static-GLB Object/role map and local-axis end-region offset on independent copies. It
  remains a bounded workflow rather than arbitrary prompt-to-mesh, sculpting, `.blend` ingestion,
  automatic semantics or arbitrary imported-region/topology editing. Creation v5 adds local-box
  UVs and deterministic generated base-color PNGs for current static geometry only. Owned v5
  revision regenerates UVs for selected replacement geometry and shares source Materials/Images
  read-only; it does not provide general unwrap, hand painting, PBR map sets or material revision.
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
