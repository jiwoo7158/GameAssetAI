# Unity static FBX validator — 2026-09-21

`scripts/prepare_unity_static_fbx_check.py` converts one explicit JSON request into a
no-overwrite C# file for the connected Unity Editor's `eval_file` command. It is a
development validator, not a Unity package or installed Skill.

The request binds an existing `Assets/.../*.fbx` to its SHA-256 and explicit expected
Mesh count, vertices, triangles, UV-coordinate count, submeshes, material slots,
animation clips, root location/rotation/scale, Preview Scene world bounds and tolerance.
It also requires an explicit `allow_import_refresh` boolean. The generator refuses
unknown/missing/duplicate JSON fields, non-standard numeric constants, non-finite values,
paths outside `Assets`, linked/missing files, changed hashes and existing output files.

Generated Unity code rechecks the connected project root and file hash, optionally calls
only the exact asset's synchronous import, reads `ModelImporter`/prefab data, instantiates
only in a temporary Preview Scene, compares every expected value, closes the Preview Scene
and verifies active Scene path/dirty/root/selection state. Any mismatch throws with the
specific check name. It does not change importer settings, save a Scene, build the game,
or delete the checked asset.

Live evidence used the installed `blender-export-static-fbx` helpers to stage one owned
texture-free quad into the user-authorized `Assets/Blender` folder. The positive Unity
check passed 12 named comparisons: 1 Mesh, 4 vertices, 2 triangles, 4 UV coordinates,
1 submesh/material slot, 0 clips, identity root transform, `2 x 0 x 1` world bounds and
active Scene preservation. A second request intentionally expected 3 triangles and failed
closed with `Unity FBX check failed: total_triangles` without import refresh.

The first generated C# attempt exposed an escaping defect in the Windows backslash
character literal and failed at compilation before execution. The generator now emits
the correct C# `\\` literal and an offline regression asserts it. After the successful
and negative tests, Unity `AssetDatabase.DeleteAsset` removed only the exact fixture and
its generated `.meta`. `Assets/Blender` returned to its two original Scene files with
unchanged hashes; `Blender.unity` stayed active, not dirty and at two roots.

A second live gate used the FBX created by the actual refreshed Workspace Skill host,
not a direct helper harness. Offline verification matched the reported 15,020-byte file
and SHA-256 `c88378061c4b1de95bb0cc9d38e5344ce59ebcd1a2fdaff279ebaea291294136`.
Unity observation was converted into a new hash-bound request, then the generated
validator passed all 12 checks: 1 Mesh, 24 imported vertices, 12 triangles, 24 UV
coordinates, 1 submesh/material slot, 0 clips, identity root, `2 x 2 x 2` world bounds
and active Scene preservation. Blender's eight Cube control vertices splitting to 24
Unity vertices reflects per-corner normal/UV representation; the 12-triangle surface
count stayed unchanged. Exact `AssetDatabase` cleanup restored the original two-file
folder and their established hashes.

This does not validate materials visually, textures, colliders, LOD, rigs, animation
quality, platform builds or arbitrary production assets. Expected values must come from
the explicit export request/Profile and Blender inspection, not from this fixture.
