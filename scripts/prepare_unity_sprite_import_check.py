"""Validate one Unity PNG Sprite check request and emit a no-overwrite C# eval file."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import stat


SCHEMA = "gameassetai.unity-sprite-import-check.v1"
FIELDS = {"schema", "project_root", "asset_path", "expected_sha256",
          "allow_import_refresh", "expected"}
EXPECTED_FIELDS = {"image_size", "sprite_mode", "pixels_per_unit", "filter_mode",
                   "compression", "mipmap_enabled", "alpha_is_transparency",
                   "srgb_texture", "sprites", "tolerance"}
SPRITE_FIELDS = {"name", "rect", "pivot", "pixels_per_unit"}


def _is_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def _finite(value, *, positive=False):
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and math.isfinite(float(value)) and (not positive or value > 0))


def read_request(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError("non-standard JSON constant: " + value)))


def validate_request(request):
    errors, asset_file = [], None
    if not isinstance(request, dict):
        return ["request must be an object"], None
    missing, unknown = FIELDS - request.keys(), request.keys() - FIELDS
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("unknown fields: " + ", ".join(sorted(unknown)))
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    project_text, asset_text = request.get("project_root"), request.get("asset_path")
    if not isinstance(project_text, str) or not project_text or project_text != project_text.strip():
        errors.append("project_root must be an exact absolute path")
    else:
        project = Path(project_text)
        try:
            if (not project.is_absolute() or not project.is_dir()
                    or any(_is_link(item) for item in (project, *project.parents))):
                errors.append("project_root must be an existing real directory")
        except OSError:
            errors.append("project_root could not be inspected")
    if not isinstance(asset_text, str) or not asset_text or "\\" in asset_text or "\x00" in asset_text:
        errors.append("asset_path must use Unity forward-slash form")
    else:
        relative = PurePosixPath(asset_text)
        if (relative.is_absolute() or not relative.parts or relative.parts[0] != "Assets"
                or ".." in relative.parts or relative.suffix.lower() != ".png"):
            errors.append("asset_path must be an Assets/... .png path")
        elif isinstance(project_text, str) and Path(project_text).is_absolute():
            asset_file = Path(project_text).joinpath(*relative.parts)
            try:
                if (_is_link(asset_file) or not asset_file.is_file()
                        or any(_is_link(item) for item in asset_file.parents
                               if item != Path(asset_file.anchor))):
                    errors.append("PNG must be an existing non-linked regular file")
            except OSError:
                errors.append("PNG could not be inspected")
    digest = request.get("expected_sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(ch not in "0123456789abcdef" for ch in digest)):
        errors.append("expected_sha256 must be lowercase SHA-256")
    elif asset_file is not None and asset_file.is_file():
        try:
            if hashlib.sha256(asset_file.read_bytes()).hexdigest() != digest:
                errors.append("PNG SHA-256 mismatch")
        except OSError:
            errors.append("PNG hash could not be read")
    if not isinstance(request.get("allow_import_refresh"), bool):
        errors.append("allow_import_refresh must be an explicit boolean")
    expected = request.get("expected")
    if not isinstance(expected, dict):
        errors.append("expected must be an object")
        return errors, asset_file
    if set(expected) != EXPECTED_FIELDS:
        errors.append("expected fields must be exact")
    size = expected.get("image_size")
    if (not isinstance(size, list) or len(size) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value < 1
                   for value in size)):
        errors.append("image_size must contain two positive integers")
    if expected.get("sprite_mode") not in {"SINGLE", "MULTIPLE"}:
        errors.append("sprite_mode must be SINGLE or MULTIPLE")
    if expected.get("filter_mode") != "POINT":
        errors.append("filter_mode must be POINT")
    if expected.get("compression") != "UNCOMPRESSED":
        errors.append("compression must be UNCOMPRESSED")
    for key in ("mipmap_enabled", "alpha_is_transparency", "srgb_texture"):
        if not isinstance(expected.get(key), bool):
            errors.append(key + " must be boolean")
    if not _finite(expected.get("pixels_per_unit"), positive=True):
        errors.append("pixels_per_unit must be finite and positive")
    if not _finite(expected.get("tolerance"), positive=True):
        errors.append("tolerance must be finite and positive")
    sprites = expected.get("sprites")
    if not isinstance(sprites, list) or not sprites:
        errors.append("sprites must contain at least one expected Sprite")
        sprites = []
    if expected.get("sprite_mode") == "SINGLE" and len(sprites) != 1:
        errors.append("SINGLE mode requires exactly one expected Sprite")
    names = set()
    for index, sprite in enumerate(sprites):
        label = f"sprites[{index}]"
        if not isinstance(sprite, dict) or set(sprite) != SPRITE_FIELDS:
            errors.append(label + " fields must be exact")
            continue
        name = sprite.get("name")
        if not isinstance(name, str) or not name or name != name.strip():
            errors.append(label + ".name must be a nonempty exact name")
        elif name in names:
            errors.append("Sprite names must be unique")
        else:
            names.add(name)
        rect = sprite.get("rect")
        if (not isinstance(rect, list) or len(rect) != 4
                or any(not _finite(value) or value < 0 for value in rect)
                or (_finite(rect[2]) and rect[2] <= 0) or (_finite(rect[3]) and rect[3] <= 0)):
            errors.append(label + ".rect must be finite [x,y,width,height] with positive size")
        pivot = sprite.get("pivot")
        if not isinstance(pivot, list) or len(pivot) != 2 or any(not _finite(value) for value in pivot):
            errors.append(label + ".pivot must contain two finite pixel coordinates")
        if (isinstance(size, list) and len(size) == 2
                and isinstance(rect, list) and len(rect) == 4
                and all(_finite(value) for value in rect)):
            if rect[0] + rect[2] > size[0] or rect[1] + rect[3] > size[1]:
                errors.append(label + ".rect must stay inside image_size")
            if (isinstance(pivot, list) and len(pivot) == 2
                    and all(_finite(value) for value in pivot)
                    and (pivot[0] < 0 or pivot[1] < 0
                         or pivot[0] > rect[2] or pivot[1] > rect[3])):
                errors.append(label + ".pivot must stay inside its rect")
        if not _finite(sprite.get("pixels_per_unit"), positive=True):
            errors.append(label + ".pixels_per_unit must be finite and positive")
    return errors, asset_file


def _csharp(value):
    return json.dumps(value, ensure_ascii=True)


def build_code(request):
    expected = request["expected"]
    expected_sprites = sorted(expected["sprites"], key=lambda item: item["name"])
    names = ", ".join(_csharp(item["name"]) for item in expected_sprites)
    rects = ", ".join(
        "new UnityEngine.Rect(" + ", ".join(
            format(float(value), ".17g") + "f" for value in item["rect"]
        ) + ")" for item in expected_sprites)
    pivots = ", ".join(
        "new UnityEngine.Vector2(" + ", ".join(
            format(float(value), ".17g") + "f" for value in item["pivot"]
        ) + ")" for item in expected_sprites)
    ppus = ", ".join(
        format(float(item["pixels_per_unit"]), ".17g") + "f"
        for item in expected_sprites)
    refresh = "true" if request["allow_import_refresh"] else "false"
    return f'''var projectRoot = {_csharp(str(Path(request["project_root"]).resolve()))};
var assetPath = {_csharp(request["asset_path"])};
var expectedHash = {_csharp(request["expected_sha256"])};
var tolerance = {format(float(expected["tolerance"]), ".17g")}f;
var currentProject = System.IO.Path.GetFullPath(System.IO.Path.Combine(UnityEngine.Application.dataPath, ".."));
if (!string.Equals(currentProject.TrimEnd('\\\\', '/'), projectRoot.TrimEnd('\\\\', '/'), System.StringComparison.OrdinalIgnoreCase)) throw new System.Exception("Connected Unity project does not match request");
var fullPath = System.IO.Path.GetFullPath(System.IO.Path.Combine(projectRoot, assetPath.Replace('/', System.IO.Path.DirectorySeparatorChar)));
var assetsRoot = System.IO.Path.GetFullPath(UnityEngine.Application.dataPath) + System.IO.Path.DirectorySeparatorChar;
if (!fullPath.StartsWith(assetsRoot, System.StringComparison.OrdinalIgnoreCase) || !System.IO.File.Exists(fullPath)) throw new System.Exception("Requested PNG is missing or outside Assets");
string actualHash; using (var stream = System.IO.File.OpenRead(fullPath)) using (var sha = System.Security.Cryptography.SHA256.Create()) actualHash = System.BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
if (actualHash != expectedHash) throw new System.Exception("PNG SHA-256 changed since offline request");
var before = UnityEngine.SceneManagement.SceneManager.GetActiveScene(); var beforePath = before.path; var beforeDirty = before.isDirty; var beforeRoots = before.rootCount; var beforeSelection = UnityEditor.Selection.activeObject == null ? null : UnityEditor.Selection.activeObject.name;
if ({refresh}) UnityEditor.AssetDatabase.ImportAsset(assetPath, UnityEditor.ImportAssetOptions.ForceSynchronousImport | UnityEditor.ImportAssetOptions.ForceUpdate);
var importer = UnityEditor.AssetImporter.GetAtPath(assetPath) as UnityEditor.TextureImporter;
var texture = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.Texture2D>(assetPath);
if (importer == null || texture == null) throw new System.Exception("TextureImporter or Texture2D missing");
var sprites = UnityEditor.AssetDatabase.LoadAllAssetsAtPath(assetPath).OfType<UnityEngine.Sprite>().OrderBy(x => x.name).ToArray();
var expectedNames = new string[] {{ {names} }};
var expectedRects = new UnityEngine.Rect[] {{ {rects} }};
var expectedPivots = new UnityEngine.Vector2[] {{ {pivots} }};
var expectedPpu = new float[] {{ {ppus} }};
var report = new System.Text.StringBuilder(); System.Action<string, bool> check = (name, ok) => {{ if (!ok) throw new System.Exception("Unity Sprite check failed: " + name); report.AppendLine(name + "=pass"); }};
check("texture_type", importer.textureType == UnityEditor.TextureImporterType.Sprite);
check("image_size", texture.width == {expected["image_size"][0]} && texture.height == {expected["image_size"][1]});
check("sprite_mode", importer.spriteImportMode == UnityEditor.SpriteImportMode.{expected["sprite_mode"].title()});
check("pixels_per_unit", UnityEngine.Mathf.Abs(importer.spritePixelsPerUnit - {format(float(expected["pixels_per_unit"]), ".17g")}f) <= tolerance);
check("filter_mode", importer.filterMode == UnityEngine.FilterMode.Point);
check("compression", importer.textureCompression == UnityEditor.TextureImporterCompression.Uncompressed);
check("mipmap", importer.mipmapEnabled == {str(expected["mipmap_enabled"]).lower()});
check("alpha_is_transparency", importer.alphaIsTransparency == {str(expected["alpha_is_transparency"]).lower()});
check("srgb", importer.sRGBTexture == {str(expected["srgb_texture"]).lower()});
check("sprite_count", sprites.Length == expectedNames.Length);
for (var i = 0; i < sprites.Length; i++) {{ check("sprite_name_" + i, sprites[i].name == expectedNames[i]); check("sprite_rect_" + i, UnityEngine.Mathf.Max(UnityEngine.Mathf.Abs(sprites[i].rect.x - expectedRects[i].x), UnityEngine.Mathf.Abs(sprites[i].rect.y - expectedRects[i].y), UnityEngine.Mathf.Abs(sprites[i].rect.width - expectedRects[i].width), UnityEngine.Mathf.Abs(sprites[i].rect.height - expectedRects[i].height)) <= tolerance); check("sprite_pivot_" + i, (sprites[i].pivot - expectedPivots[i]).magnitude <= tolerance); check("sprite_ppu_" + i, UnityEngine.Mathf.Abs(sprites[i].pixelsPerUnit - expectedPpu[i]) <= tolerance); }}
var after = UnityEngine.SceneManagement.SceneManager.GetActiveScene(); var afterSelection = UnityEditor.Selection.activeObject == null ? null : UnityEditor.Selection.activeObject.name; check("active_scene_preserved", beforePath == after.path && beforeDirty == after.isDirty && beforeRoots == after.rootCount && beforeSelection == afterSelection);
report.Insert(0, "status=passed\\nasset=" + assetPath + "\\nsha256=" + actualHash + "\\n"); report.AppendLine("size=" + texture.width + "x" + texture.height + ";sprites=" + sprites.Length); return report.ToString();'''


def prepare(request, output):
    errors, _ = validate_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    output = Path(output)
    if not output.is_absolute() or output.suffix.lower() != ".cs":
        raise ValueError("output must be an absolute .cs path")
    if not output.parent.is_dir() or any(_is_link(item) for item in (output.parent, *output.parent.parents)):
        raise ValueError("output parent must be an existing real directory")
    if output.exists() or _is_link(output):
        raise FileExistsError("output already exists")
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    data = build_code(request).encode("utf-8")
    try:
        with output.open("xb") as handle:
            handle.write(data)
        if output.read_bytes() != data:
            raise OSError("generated C# readback mismatch")
    except BaseException:
        if output.is_file() and not _is_link(output):
            output.unlink()
        raise
    return {"schema": SCHEMA, "status": "prepared", "output": str(output),
            "request_sha256": hashlib.sha256(canonical).hexdigest(),
            "code_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "allow_import_refresh": request["allow_import_refresh"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path); parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = prepare(read_request(args.request), args.output.expanduser().absolute())
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError,
            json.JSONDecodeError) as exc:
        parser.exit(1, f"Unity Sprite check preparation failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
