# Skills

This directory contains the source of GameAssetAI's installable skills.

Current narrowly tested source skills:

- `blender-adjust-character-joint-weights-copy`: previews and creates an independent owned
  character Mesh copy with explicit bilateral or unilateral shoulder/hip weight-transition
  refinement. Its copy/preservation mechanics are tested, but product routing is suspended until
  a source passes semantic topology acceptance; the first live voxel source was rejected. See
  `docs/character-joint-weight-copy-validation.md`.

- `blender-create-game-asset`: routing-only entry for natural-language character, weapon, prop,
  enemy and environment requests. It selects existing creation/inspection/revision/output Skills
  and keeps unsupported gaps explicit; it does not duplicate their Blender code. See
  `docs/SKILL_REUSE_AUDIT.md`.

- `blender-author-pose-action`: creates one explicit Blender 5 layered Action from complete
  per-frame bone rotations and optional v2 local root/pelvis locations, refusing occupied/current
  animation and rig/request front-axis mismatches. See `docs/pose-action-authoring-validation.md`.

- `blender-rig-character-base`: adds an explicit 18-bone humanoid Armature, 17 deform groups and
  an Armature modifier to the owned generated character base. V1 retains rigid regions; v2 adds
  smooth two-bone transition bands at major joints. It preserves Mesh geometry and is the input
  to pose/deformation review, not production skinning or Mixamo. Do not use the rejected
  `VOXEL_CONNECTED` candidate as a target. See
  `docs/character-rig-validation.md`.

- `blender-create-character-base`: creates one visible low-poly humanoid base Mesh in an explicit
  A-pose or T-pose with four material roles and user-supplied proportions. Current product use is
  limited to blockout creation: v1/v2 `VOLUME_ISLANDS` keeps separate volumes and v3
  `BOOLEAN_CONNECTED` creates a guarded connected blockout. Neither is deformation-ready. The
  validator refuses schema v2's global `VOXEL_CONNECTED` option after unintended limb/foot fusion.
  See `docs/character-base-creation-validation.md`.

- `blender-create-static-asset`: the first direct native asset-creation Skill. It converts an
  explicit multi-part plan into a new owned Blender Collection using boxes, cylinders and
  low-poly icospheres with purpose-specific materials. A four-part, three-material training
  sword passes Blender 5.0.1 creation, authorization refusal and exact cleanup checks. It is
  intentionally limited to low-poly props, weapons and simple environment assemblies; it is not
  character, rig, animation, sculpting or arbitrary text-to-3D generation. See
  `docs/static-asset-creation-validation.md`.

- `blender-create-static-lod-copy`: preview and explicitly authorized creation of one exact-named
  independent lower-detail Object/Mesh using an explicit Decimate collapse ratio. It rechecks a
  four-fingerprint review chain, preserves the source and rolls back only owned output IDs on
  failure. It does not infer chains/ratios, overwrite, handle rigged/evaluated assets, certify
  visual quality or configure Unity LODGroups. See `docs/lod-generation-experiment.md`.

- `blender-inspect-static-lod-chain`: read-only inspection of an explicitly ordered existing
  base-Mesh LOD chain. It requires exact world-matrix alignment and strictly decreasing base
  triangulation, then reports bounds, ratios, material slots and dependencies without
  discovering/generating/decimating or configuring engine LODs. Source and installed Blender
  5.0.1 tests, refreshed-client no-chain refusal and synthetic host inspection pass. See
  `docs/static-collider-lod-decision.md`.

- `blender-inspect-static-colliders`: read-only inspection of explicitly named existing
  base-Mesh collider candidates relative to one render Mesh. It reports topology, world
  bounds, dependencies and bounded convexity evidence without discovering/generating
  colliders, creating LODs or configuring Unity. Source and installed Blender 5.0.1 tests
  and refreshed-client no-candidate/synthetic host inspections pass. See
  `docs/static-collider-lod-decision.md`.

- `blender-render-impostor-bundle`: coordinates explicit static COLOR/NORMAL/DEPTH children
  against one canonical orthographic framing plan per view. It binds every stage, job,
  helper, receipt and artifact hash, rolls back unchanged outputs on failure, and publishes
  the validated JSON manifest last. Repository, source-Skill and installed-Skill Blender
  5.0.1 tests pass; refreshed-client discovery remains. It does not infer views, use an
  active Profile, support Object-ID/Actions, assemble sheets or configure Unity. See
  `docs/2d-impostor-bundle-decision.md`.

- `blender-render-2d-batch`: coordinates explicit static-view and Action-sequence child
  requests in list order with one shared output directory, Profile-preset provenance, bounded
  output count and hash-verified all-or-nothing rollback. Repository and packaged-Skill Blender
  5.0.1 tests pass; refreshed-client discovery remains unverified. It does not infer directions,
  Actions, names, style or Unity settings. See `docs/2d-render-batch-contract.md`.

- `assemble-png-sprite-sheet`: combines explicit equal-size RGBA8 PNG frames into one new
  sheet and JSON metadata with exact order, anchors, Profile provenance and two-artifact atomic
  publication. Source/installed tests and refreshed-client host use pass.

- `blender-render-action-png-sequence`: renders one reviewed Mesh/Armature/Action to an atomic
  PNG sequence with stable range-wide framing. Source/installed Blender tests and refreshed-
  client host use pass.

- `blender-extract-action-range`: copies one exact-boundary LINEAR frame interval and its
  in-range pose markers into a protected unbound Action while preserving the source and
  all references. It may keep frames or rebase the copy to frame 0 or 1, but does not
  synthesize keys. Source/ZIP/installed tests pass on Blender 5.0.1; updated client
  instructions remain unverified. See
  `docs/action-range-extraction-validation.md`.

- `blender-replace-current-action`: replaces one exact current Armature Action with one
  protected unbound Action and returns a hash-bound receipt to restore the previous
  binding. NLA/drivers and extra references are refused; neither Action is deleted.
  Source/ZIP/installed tests pass on Blender 5.0.1; refreshed-client exposure and safe
  no-input refusal were confirmed by the user.
  See `docs/action-replacement-validation.md`.

- `blender-bind-action-empty`: binds one protected unbound Action only to an Armature
  with no current Action/NLA/drivers and returns a hash-bound receipt for exact unbind.
  It never replaces or deletes an Action. Source/ZIP/installed tests pass on Blender
  5.0.1; refreshed-client exposure and safe no-input refusal were confirmed by the user.
  See `docs/action-binding-validation.md`.

- `blender-compose-retarget-actions`: combines only the strict rotation-only and
  root-location-only bake outputs into one independent unbound Action. Source/ZIP/
  installed tests pass on Blender 5.0.1; refreshed-client exposure and safe no-input
  refusal were confirmed by the user. See
  `docs/retarget-action-composition-validation.md`.

- `blender-bake-root-translation-copy`: guarded TRANSFER or IN_PLACE root-location bake
  using an explicit Armature-space XYZ mask and scalar. The independent result contains
  location only; it is not combined with rotation or bound/exported. Source/ZIP/installed
  helper tests pass on Blender 5.0.1; refreshed-client exposure and no-input refusal were
  confirmed by the user. See `docs/root-translation-bake-validation.md`.

- `blender-inspect-evaluated-root-motion`: samples one explicit parentless root bone and
  Action on a temporary independent Armature, reporting local-basis, Armature and world
  translation metrics. It does not transfer motion or choose in-place/Unity policy.
  Source/ZIP/installed helper tests pass on Blender 5.0.1; refreshed-client exposure and
  safe no-input refusal were confirmed by the user. See
  `docs/evaluated-root-motion-validation.md`.

- `blender-inspect-evaluated-pose-loop`: compares evaluated local-basis transforms and
  finite-difference seam velocities for every explicitly listed animated pose bone on a
  temporary independent Armature. Source/ZIP/installed helper tests pass on Blender 5.0.1.
  It does not certify subframe extrema, deformation, visual or engine loop continuity. See
  `docs/evaluated-pose-loop-validation.md`.

- `blender-bake-rotation-retarget-copy`: frame-sampled local-basis quaternion bake to
  one unbound Action through temporary rig copies. Differing rest matrices are allowed,
  but translation, scale, root motion, constraints and world-space pose certification are
  excluded. Source/ZIP/installed helper tests pass on Blender 5.0.1; refreshed-client
  exposure and safe no-input refusal were confirmed by the user. See
  `docs/rotation-retarget-bake-validation.md`.

- `blender-retarget-aligned-action-copy`: guarded name-only F-Curve path remap into
  one unbound copied Action when two explicit humanoid mappings have matching rest
  matrices, transforms and rotation modes. It is not general Mixamo/custom-rig retarget
  or pose baking. Source/ZIP/installed helper tests pass on Blender 5.0.1; refreshed-client
  discovery remains unverified. See `docs/aligned-retarget-validation.md`.

- `blender-inspect-retarget-readiness`: read-only comparison of two explicit humanoid
  mappings and one source Action, including Action coverage and rest-bone metrics. It
  does not retarget, pose, bake or certify deformation/engine behavior. Source/ZIP/
  installed helper tests pass on Blender 5.0.1; refreshed-client discovery remains
  unverified. See `docs/retarget-readiness-validation.md`.

- `blender-inspect-root-motion`: read-only stored translation evidence for one explicit
  Object or Armature bone, Action, slot/range and tolerance. It never guesses a root or
  chooses in-place/engine policy. Source/ZIP/installed helper tests pass on Blender 5.0.1;
  refreshed-client discovery remains unverified. See
  `docs/root-motion-inspection-validation.md`.

- `blender-inspect-animation-loop`: read-only stored F-Curve scalar comparison at
  explicit Action start/end frames with explicit tolerances and boundary-key coverage.
  It does not certify evaluated pose, tangent, root-motion or visual loop continuity.
  Source/ZIP/installed helper tests pass on Blender 5.0.1; refreshed-client discovery
  remains unverified. See `docs/animation-loop-validation.md`.

- `blender-copy-action`: preview and explicitly authorized independent copy of one
  existing Action to an unused name. The original and all current/NLA references remain
  unchanged; the unbound copy receives a fake user. Source/ZIP/installed helper tests
  pass on Blender 5.0.1; refreshed-client discovery remains unverified. It does not split,
  bind, retarget, edit, import or export clips. See `docs/action-copy-validation.md`.

- `blender-inspect-animation`: read-only file-wide Action and scoped binding/NLA/driver/
  F-Curve inventory with explicit-only root-bone channels. Source, ZIP and installed
  helper regressions pass on Blender 5.0.1; refreshed-client discovery remains
  unverified. It does not import, extract, rename, evaluate, retarget or edit animation.
  See `docs/animation-inventory-validation.md`.

- `blender-inspect-mixamo-preflight`: read-only exact Mixamo naming signature,
  explicit humanoid mapping and bound-Mesh/transform/animation preparation review. It
  does not upload, rig, retarget or export. See `docs/mixamo-preflight-validation.md`.

- `blender-inspect-humanoid`: read-only explicit role-to-bone mapping, ancestry,
  deform/root and animation-sensitivity inspection. It does not guess mappings, edit a
  rig, retarget, or certify Mixamo/Unity compatibility. See
  `docs/humanoid-inspection-validation.md`.

- `blender-export-static-fbx`: explicit request-bound export of one simple texture-free
  static Mesh to a new FBX through verified staging and atomic no-overwrite publication.
  Source/ZIP/installed helper tests pass on Blender 5.0.1; Unity 6000.3.9f1 synthetic
  import passed, while refreshed-client discovery remains unverified. No textures,
  sidecars, rigs, animation, batch export or existing-file replacement. See
  `docs/static-fbx-skill-validation.md`.

- `blender-render-static-pixel-png`: one simple static Mesh to a new orthographic Pixel
  RGBA8 PNG through hash-bound blend/job staging and an isolated background Blender.
  Supports no palette reduction, deterministic explicit-count AUTO reduction, or an
  explicit opaque fixed palette, plus an optional explicit one-pixel outer silhouette;
  no inner/variable outline, CEL/Toon, animation, overwrite or Unity import claim. Repository, portable
  ZIP and installed-helper Blender 5.0.1 regressions pass; refreshed-session discovery and
  host rendering are verified. See `docs/2d-static-pixel-skill-validation.md`.

- `derive-png-silhouette-mask`: derive one new opaque-color RGBA8 silhouette from one
  exact existing RGBA8 PNG using either nonzero-alpha binarization or alpha preservation.
  It is hash-bound, no-overwrite and rollback-tested; it does not call Blender or produce
  material IDs, normals or depth. See `docs/2d-silhouette-mask-validation.md`.

- `blender-render-material-mask-png`: render one explicit material slot on one static base
  Mesh to a new RGBA8 mask while retaining non-target surface occlusion. It uses an isolated
  staged copy and internal ID shaders; no slot inference, source edit, modifiers, animation,
  object IDs, normals or depth. See `docs/2d-material-mask-validation.md`.

- `blender-render-object-mask-png`: render one exact static target Mesh against an explicit
  list of static Mesh occluders. Union framing and staged ID shaders preserve depth visibility
  while unrelated Scene Objects remain excluded. No implicit Scene scan, evaluated geometry,
  multi-color ID atlas, normals or depth. See `docs/2d-object-mask-validation.md`.

- `blender-relocate-pivot-copy`: explicit local-point origin relocation on an
  independent static copy; no automatic center/bottom or engine policy. Development,
  ZIP and installed helper tests pass on Blender 5.0.1; client discovery/host instruction
  use passed by user report; raw routing/build remains unverified. See
  `docs/pivot-copy-validation.md`.

- `blender-prepare-positive-scale`: positive XYZ static-scale preview and independent-copy
  apply with base/reported-world coordinates/pivot/UV/material checks and exact rollback;
  not general Apply Transforms, reflected scale correction or engine certification.
  Source/ZIP/installed helper tests pass; host use and synthetic apply/restore confirmed
  by user report. See
  `docs/transform-preflight.md`.

- `blender-inspect-asset`: read-only scene/named/selection inventory, with helper and
  representative/failure/preservation tests on Blender 5.0.1.
- `blender-validate-static-mesh`: read-only diagnostics, optional supplied game constraints,
  base/guarded viewport basis, and preservation/failure tests on Blender 5.0.1.
- `blender-cleanup-loose-geometry`: preview or explicitly authorized loose-geometry
  removal on an independent copy, stale-preview guards and limited simple-mesh inputs.
- `blender-simplify-coplanar`: whole-planar affine-UV structural preview and independent
  copy apply, predicted geometry hash and rollback; not triangle decimation. Source/ZIP
  tests passed; user confirmed session exposure and synthetic copy-apply/restore.

See `docs/inspection-validation.md`, `docs/static-mesh-validation.md`, and
`docs/loose-cleanup-validation.md` and `docs/coplanar-apply.md`. Source workflow validation is not proof of installed
client discovery, every Blender version, or imported production asset compatibility.
The repository does not ship a large set of pretend-complete production skills.

Develop skills one at a time, test them against Blender, and promote them to stable status only when their behavior is verified.

Use the template in:

```text
templates/skill/SKILL.template.md
```

Recommended future areas are tracked in `docs/roadmap.md`.
