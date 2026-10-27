# Retarget readiness inspection validation

Validated on 2026-09-23 with Blender 5.0.1 through
`ahujasid/blender-mcp` at `localhost:9876`.

## Scope

`blender-inspect-retarget-readiness` is a read-only preflight for one explicitly named
source Armature, one distinct target Armature, and one source Action. Both rigs require
explicit humanoid role-to-bone mappings. The inspector reports:

- mapping and hierarchy completeness for both rigs
- source Action ownership and slot selection
- mapped animated roles, unmapped animated bones, and non-bone channels
- per-role armature-space rest-bone length ratios and direction dot products
- non-identity Armature Object transforms and existing target animation

A positive `retarget_candidate` is deliberately narrow. It is not a deformation,
rest-pose, bone-roll, axis, constraint, skin-weight, root-motion, Mixamo, Unity, or visual
quality certificate, and it never authorizes a mutation.

## Blender evidence

The owned synthetic fixture creates separate mapped source and target Armatures, a bound
source Action, and one animated bone outside the humanoid mapping. The source, packaged
ZIP, and installed Workspace helper runs each passed 11 checks:

- complete candidate and two humanoid reports
- expected 1.5 rest-length ratios within Blender float tolerance
- mapped Action coverage and explicit unmapped-bone reporting
- preservation-sensitive transform review
- same-rig refusal
- incomplete mapping reporting
- unbound Action refusal as a candidate
- invalid slot refusal
- read-only animation inventory
- exact fixture teardown and original-state restoration

The first fixture run exposed two test-only issues: an EditBone reference was read after
leaving Edit Mode, and the length-ratio assertion was tighter than Blender's float
storage. The fixture now stores the name while valid and uses a `1e-5` test tolerance.
The production inspector's reported measurements were unchanged.

## Packaging and installation

Portable archive:

`.local/source-bundles/retarget-readiness-20260923/blender-inspect-retarget-readiness.zip`

SHA-256:
`76b8c48517d44aaf83b3c64b65fe44ec560ef8926f204eb707334115fb7d13a0`

The Skill is installed without overwrite at:

`D:/AI/GameAssetAI-Workspace/.agents/skills/blender-inspect-retarget-readiness`

Repository, ZIP, and installed helper execution are verified. Refreshed-client automatic
discovery and no-target behavior remain a separate host gate. No real retarget, constraint,
rest-pose change, bone rename, Action bake, Unity operation, or user asset modification was
performed.

