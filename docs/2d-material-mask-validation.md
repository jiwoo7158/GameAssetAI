# Static material-mask PNG validation

## Scope

`blender-render-material-mask-png` produces one RGBA8 mask for one explicit material slot
on one static base Mesh. It is separate from the alpha-derived silhouette postprocess: the
material result requires Blender geometry, exact face assignments and depth occlusion.

The v1 request explicitly binds Scene/Object names, material-slot index, opaque output
color, orthographic view, framing margin, resolution and a new absolute PNG path. It does
not infer a slot from color, name, material nodes, an active selection or a game Profile.

## Isolation and semantic behavior

Candidate inspection fingerprints base vertices, edges, polygon material indices, material
slot identities, Object transform, Scene frame/unit state and setup/output values. Parents,
constraints, modifiers, animation, Shape Keys, linked data, hidden/empty Meshes, invalid or
unassigned slots and invalid face material indices are blockers.

The authorized workflow writes an independent one-Object blend stage and a hash-bound job.
Only the background process replaces staged material slots with internal red/green emission
ID shaders. Non-target faces remain opaque during the ID render and therefore preserve
front-surface occlusion; the final conversion makes only target pixels visible using the
requested color. Original materials and the interactive Scene are never changed.

## Evidence

Blender 5.0.1 passes a 12-check synthetic fixture with a target quad partly covered by a
closer non-target-material quad. It verifies request/candidate/framing, stale-request
refusal, independent staging, job creation, two-RGBA publication, 200 visible target pixels,
200 non-target occluder pixels, receipt binding, collision refusal and exact file teardown.
The representative artifact SHA-256 is
`566139db2aef3050fcc42ab843bccba0e1d6ef9696f1c6f0081ad01ee4d03b1f` and the receipt
SHA-256 is `fa307f2ba5460f73202899cfb97a478817070b5b508b1d46b176b1dd2c6fda17`.

## Known limits

This is not evaluated geometry, animation, object-ID, cryptomatte, normal, depth, SDF,
silhouette, multi-slot batching, Unity import or a quality guarantee. Framing uses the whole
base Object so multiple masks from the same reviewed source align, but it does not crop to
the selected material.
