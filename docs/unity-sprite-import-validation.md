# Unity Sprite import validation - 2026-09-30

`scripts/prepare_unity_sprite_import_check.py` defines the first file-level Unity
Sprite import/slicing validation boundary. It converts one exact JSON request into a
no-overwrite C# file for a connected Unity Editor's `eval_file` command. It is a
development validator, not an installed Skill, importer-setting editor or Unity package.

The `gameassetai.unity-sprite-import-check.v1` request binds an existing, non-linked
`Assets/.../*.png` to its lowercase SHA-256 and explicit expectations for image size,
Single/Multiple Sprite mode, pixels per unit, Point filtering, uncompressed import,
mipmaps, alpha handling, sRGB and every Sprite's unique name, pixel rectangle, pivot and
pixels per unit. Rectangles must fit inside the image and pivots inside their rectangles.
Unknown, missing or duplicate JSON fields, non-standard/non-finite numbers, linked paths,
paths outside `Assets`, stale hashes and pre-existing C# outputs fail closed.

The generated code rechecks the connected project root and PNG hash, optionally refreshes
only the exact asset, then reads `TextureImporter`, `Texture2D` and imported `Sprite`
objects. Expected Sprite data is emitted as native C# arrays, so the check has no JSON
package dependency and compares Sprites deterministically by name. It also verifies that
the active Scene path/dirty/root state and active selection remain unchanged. It does not
change importer settings, create or save a Scene, build the project, delete an asset or
write metadata.

Six offline tests cover a successful hash-bound/no-overwrite generation, stale hash and
scope refusal, exact importer policy, rectangle/pivot/name guards, Single-mode cardinality,
and duplicate/non-standard JSON refusal. These tests do not prove that a particular Unity
version exposes identical importer behavior.

Live execution passed in Unity 6000.3.9f1 using the user-approved
`C:/Users/jiwoo/UnityProject/GameAssetAI_UnityWorkbench/Assets/Blender` folder. The project
already contained `com.unity.pipeline` 0.8.0-exp.1; Codex's Unity MCP entry was pinned to
that exact project, and direct `eval_file` calls reached its Editor at the discovered local
endpoint. The source was the retained 65x65 sprite sheet with SHA-256
`08df8fa6a876c29066ae745ef57b5f23d6db76b976191024c9b20d535adfd85a`.

Unity imported a uniquely named copy as Multiple Sprite, PPU 32, Point, Uncompressed, no
mipmaps, alpha transparency and sRGB, with three explicit 32x32 rectangles and centered
pivots. The generated hash-bound validator passed all 23 comparisons, including exact
names/rectangles/pivots/PPU and active Scene preservation. A separate read-only request
that expected a fourth Sprite failed closed with exit code 6 at `sprite_count`.

Cleanup used `AssetDatabase.DeleteAsset` on only the invocation-owned PNG. Its `.meta` was
removed with it, the approved folder returned to its original empty file inventory, and
the Scene/selection state remained unchanged. The source under `D:/Blender/MCP_Test` was
read but not modified. This evidence covers one explicit equal-cell Multiple-Sprite fixture;
it does not certify arbitrary production sheets, platform builds, atlases or runtime animation.
