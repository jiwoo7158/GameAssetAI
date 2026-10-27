# Independent-Copy LOD Generation Experiment

## Scope

Before designing an LOD-generation request or Skill, verify Blender 5.0.1's native Decimate
modifier on a disposable independent Mesh copy. This is a capability experiment, not a
production operation and not evidence of visual quality or Unity compatibility.

The experiment must:

- run in factory-startup background Blender in a separate owned Scene
- create a triangulated synthetic curved Mesh with one material and finite UV data
- make an independent Object and Mesh copy; never apply a modifier to the source
- use the actual Blender 5.0.1 `DECIMATE` collapse modifier and query relevant RNA
- prove the copied base triangle count decreases after apply
- prove source geometry/UV/material facts remain byte-for-byte stable
- verify the result retains finite geometry, UV layer and material-slot structure
- report bounds/radius change rather than claim silhouette preservation
- remove every owned Scene/Object/Mesh/Material and restore context exactly

## Boundaries after success

A successful synthetic reduction only permits design of a later explicit request/preview. It
does not justify a universal ratio, automatic chain length, source overwrite, modifier-stack
evaluation, rigged/animated inputs, UV quality claims, normals/tangent guarantees, or Unity
LODGroup thresholds. Those require separate policies and representative tests.

## Blender 5.0.1 result

The factory-startup experiment passes nine checks. A synthetic UV-mapped Icosphere with one
material was copied into independent Object/Mesh IDs. Native `DECIMATE`/`COLLAPSE` at explicit
ratio `0.5` reduced base triangles from 320 to 160 and vertices from 162 to 82. The source
geometry/UV/material hash remained identical. The result retained one finite UV layer and the
same material-slot structure. Its observed radius range changed from approximately
`0.999999893..1.000000103` to `0.999999940..1.015205780`; this demonstrates why triangle
reduction is not silhouette certification. Exact Scene/Object/Mesh/Material teardown passed.

The pure `gameassetai.static-lod-copy-request.v1` contract now passes five offline tests. It
requires an explicit `0.01..0.99` ratio, unused output Object/Mesh names, exact transform copy,
independent Mesh data, source preservation, dependency refusal, UV copying and separate
preview/apply authorization.

The Blender candidate preview now evaluates this contract on disposable independent IDs. Its
representative Icosphere fixture reproduces the explicit 320-to-160 triangle reduction, retains
the UV layer name, material slots and exact world transform, reports bounds deltas, and proves
the source hash is unchanged. It also refuses stale request hashes, occupied intended output
names and source modifiers, removes all preview IDs and restores context exactly. This still
does not authorize or create persistent output.

The guarded apply now requires explicit authorization and the exact reviewed request, source,
setup and preview fingerprints. It repeats the disposable preview immediately before mutation,
creates one exact named independent Object/Mesh pair, validates the applied result against the
reviewed preview and rolls back only ownership-tagged output IDs on any failure. A forced
post-create validation failure proves rollback and source preservation. This development helper
still does not constitute an installed generation Skill or define Unity LOD thresholds.

The proven helpers are now packaged as the narrow `blender-create-static-lod-copy` Skill. Its
entrypoint requires the complete explicit request, reports a nonpersistent reviewed preview,
and pauses for explicit approval before passing the four fingerprints to apply. The four-file
source archive and installed local Workspace copy are byte-aligned, and both source-packaged and
installed helpers pass the 11-check Blender apply/rollback fixture. Client discovery and a
natural-language host run remain separate gates; Unity LODGroup work is still out of scope.

The installed helpers subsequently completed one live Blender host preview and separately
authorized apply at ratio `0.5`. The output matched the reviewed 320-to-160 triangle plan,
produced receipt fingerprint
`525e5e83406a95b5d8ad86539c801bcf7f4a31d92680a6aeea796f4977405d7f`, preserved the
source, and was then removed with the entire owned fixture. The original Scene/data/context
matched exactly afterward.

A first Unity 6000.3.9f1 capability probe now also succeeds in an isolated Preview Scene. It
constructs a three-level `LODGroup` over synthetic 12/8/4-triangle Meshes, reads back transition
heights `0.6/0.3/0.1`, one Renderer per level and positive calculated bounds, then destroys all
objects/Meshes and closes the Preview Scene. The active `SampleScene` stays clean and unchanged.
This proves the native API path only; a request contract, imported-asset binding and persistent
configuration/rollback workflow remain to be designed.
