"""Validate an explicit Unity FBX check request and emit a no-overwrite C# eval file."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import stat


SCHEMA = "gameassetai.unity-static-fbx-check.v1"
FIELDS = frozenset(("schema", "project_root", "asset_path", "expected_sha256",
                    "allow_import_refresh", "expected"))
EXPECTED_FIELDS = frozenset(("mesh_count", "total_vertices", "total_triangles",
                             "total_uv_coordinates", "total_submeshes",
                             "material_slot_count", "animation_clip_count",
                             "root_location", "root_rotation", "root_scale",
                             "world_bounds_size", "tolerance"))


def _is_link(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(info.st_mode)
            or bool(getattr(info, "st_file_attributes", 0)
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)))


def _vector(value: object, *, nonnegative: bool = False) -> bool:
    return (isinstance(value, list) and len(value) == 3
            and all(not isinstance(item, bool) and isinstance(item, (int, float))
                    and math.isfinite(float(item))
                    and (not nonnegative or item >= 0) for item in value))


def read_request(path: Path) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def reject_constant(value):
        raise ValueError("non-standard JSON constant: " + value)
    data = json.loads(path.read_text(encoding="utf-8-sig"),
                      object_pairs_hook=unique, parse_constant=reject_constant)
    if not isinstance(data, dict):
        raise ValueError("request must be a JSON object")
    return data


def validate_request(request: object) -> tuple[list[str], Path | None]:
    errors = []
    asset_file = None
    if not isinstance(request, dict):
        return ["request must be an object"], None
    missing, unknown = FIELDS - request.keys(), request.keys() - FIELDS
    if missing:
        errors.append("missing fields: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("unknown fields: " + ", ".join(sorted(unknown)))
    if request.get("schema") != SCHEMA:
        errors.append("schema mismatch")
    project_text = request.get("project_root")
    asset_text = request.get("asset_path")
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
    if (not isinstance(asset_text, str) or not asset_text or "\\" in asset_text
            or "\x00" in asset_text):
        errors.append("asset_path must use Unity forward-slash form")
    else:
        relative = PurePosixPath(asset_text)
        if (relative.is_absolute() or not relative.parts or relative.parts[0] != "Assets"
                or ".." in relative.parts or relative.suffix.lower() != ".fbx"):
            errors.append("asset_path must be an Assets/... .fbx path")
        elif isinstance(project_text, str) and Path(project_text).is_absolute():
            asset_file = Path(project_text).joinpath(*relative.parts)
            try:
                if (_is_link(asset_file) or not asset_file.is_file()
                        or any(_is_link(item) for item in asset_file.parents
                               if item != Path(asset_file.anchor))):
                    errors.append("asset file must be an existing non-linked regular file")
            except OSError:
                errors.append("asset file could not be inspected")
    digest = request.get("expected_sha256")
    if (not isinstance(digest, str) or len(digest) != 64
            or any(ch not in "0123456789abcdefABCDEF" for ch in digest)):
        errors.append("expected_sha256 must be 64 hexadecimal characters")
    elif asset_file is not None and asset_file.is_file():
        try:
            if hashlib.sha256(asset_file.read_bytes()).hexdigest() != digest.lower():
                errors.append("asset file SHA-256 mismatch")
        except OSError:
            errors.append("asset file hash could not be read")
    if not isinstance(request.get("allow_import_refresh"), bool):
        errors.append("allow_import_refresh must be an explicit boolean")
    expected = request.get("expected")
    if not isinstance(expected, dict):
        errors.append("expected must be an object")
    else:
        missing_expected = EXPECTED_FIELDS - expected.keys()
        unknown_expected = expected.keys() - EXPECTED_FIELDS
        if missing_expected:
            errors.append("missing expected fields: " + ", ".join(sorted(missing_expected)))
        if unknown_expected:
            errors.append("unknown expected fields: " + ", ".join(sorted(unknown_expected)))
        for key in ("mesh_count", "total_vertices", "total_triangles",
                    "total_uv_coordinates", "total_submeshes", "material_slot_count",
                    "animation_clip_count"):
            value = expected.get(key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(key + " must be a nonnegative integer")
        for key, minimum in (("mesh_count", 1), ("total_vertices", 3),
                             ("total_triangles", 1), ("total_submeshes", 1)):
            value = expected.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value < minimum:
                errors.append(key + f" must be at least {minimum}")
        for key in ("root_location", "root_rotation", "root_scale"):
            if not _vector(expected.get(key)):
                errors.append(key + " must be a finite three-number vector")
        if not _vector(expected.get("world_bounds_size"), nonnegative=True):
            errors.append("world_bounds_size must be a finite nonnegative vector")
        tolerance = expected.get("tolerance")
        if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                or not math.isfinite(float(tolerance)) or tolerance <= 0):
            errors.append("tolerance must be finite and positive")
    return errors, asset_file


def _csharp_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def build_code(request: dict) -> str:
    expected = request["expected"]
    vec = lambda value: "new UnityEngine.Vector3(" + ",".join(
        format(float(item), ".17g") + "f" for item in value) + ")"
    refresh = "true" if request["allow_import_refresh"] else "false"
    return f'''var projectRoot = {_csharp_string(str(Path(request["project_root"]).resolve()))};
var assetPath = {_csharp_string(request["asset_path"])};
var expectedHash = {_csharp_string(request["expected_sha256"].lower())};
var tolerance = {format(float(expected["tolerance"]), ".17g")}f;
var currentProject = System.IO.Path.GetFullPath(System.IO.Path.Combine(UnityEngine.Application.dataPath, ".."));
if (!string.Equals(currentProject.TrimEnd('\\\\', '/'), projectRoot.TrimEnd('\\\\', '/'), System.StringComparison.OrdinalIgnoreCase))
    throw new System.Exception("Connected Unity project does not match request");
var fullPath = System.IO.Path.GetFullPath(System.IO.Path.Combine(projectRoot, assetPath.Replace('/', System.IO.Path.DirectorySeparatorChar)));
var assetsRoot = System.IO.Path.GetFullPath(UnityEngine.Application.dataPath) + System.IO.Path.DirectorySeparatorChar;
if (!fullPath.StartsWith(assetsRoot, System.StringComparison.OrdinalIgnoreCase) || !System.IO.File.Exists(fullPath))
    throw new System.Exception("Requested FBX is missing or outside Assets");
string actualHash;
using (var stream = System.IO.File.OpenRead(fullPath))
using (var sha = System.Security.Cryptography.SHA256.Create())
    actualHash = System.BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
if (actualHash != expectedHash)
    throw new System.Exception("FBX SHA-256 changed since offline request");
var before = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var beforePath = before.path;
var beforeDirty = before.isDirty;
var beforeRoots = before.rootCount;
var beforeSelection = UnityEditor.Selection.activeObject == null ? null : UnityEditor.Selection.activeObject.name;
if ({refresh})
    UnityEditor.AssetDatabase.ImportAsset(assetPath, UnityEditor.ImportAssetOptions.ForceSynchronousImport | UnityEditor.ImportAssetOptions.ForceUpdate);
var importer = UnityEditor.AssetImporter.GetAtPath(assetPath) as UnityEditor.ModelImporter;
var model = UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.GameObject>(assetPath);
if (importer == null || model == null)
    throw new System.Exception("ModelImporter or imported GameObject missing");
var filters = model.GetComponentsInChildren<UnityEngine.MeshFilter>(true);
var renderers = model.GetComponentsInChildren<UnityEngine.Renderer>(true);
var clips = UnityEditor.AssetDatabase.LoadAllAssetsAtPath(assetPath).OfType<UnityEngine.AnimationClip>().Where(x => !x.name.StartsWith("__preview__")).ToArray();
var meshCount = filters.Count(x => x.sharedMesh != null);
var totalVertices = filters.Where(x => x.sharedMesh != null).Sum(x => x.sharedMesh.vertexCount);
var totalTriangles = filters.Where(x => x.sharedMesh != null).Sum(x => x.sharedMesh.triangles.Length / 3);
var totalUv = filters.Where(x => x.sharedMesh != null).Sum(x => x.sharedMesh.uv.Length);
var totalSubmeshes = filters.Where(x => x.sharedMesh != null).Sum(x => x.sharedMesh.subMeshCount);
var materialSlots = renderers.Sum(x => x.sharedMaterials.Length);
var report = new System.Text.StringBuilder();
System.Action<string, bool> check = (name, ok) => {{ if (!ok) throw new System.Exception("Unity FBX check failed: " + name); report.AppendLine(name + "=pass"); }};
check("mesh_count", meshCount == {expected["mesh_count"]});
check("total_vertices", totalVertices == {expected["total_vertices"]});
check("total_triangles", totalTriangles == {expected["total_triangles"]});
check("total_uv_coordinates", totalUv == {expected["total_uv_coordinates"]});
check("total_submeshes", totalSubmeshes == {expected["total_submeshes"]});
check("material_slot_count", materialSlots == {expected["material_slot_count"]});
check("animation_clip_count", clips.Length == {expected["animation_clip_count"]});
check("root_location", (model.transform.localPosition - {vec(expected["root_location"])}).magnitude <= tolerance);
var expectedRotation = {vec(expected["root_rotation"])};
var actualRotation = model.transform.localEulerAngles;
check("root_rotation", UnityEngine.Mathf.Max(UnityEngine.Mathf.Abs(UnityEngine.Mathf.DeltaAngle(actualRotation.x, expectedRotation.x)), UnityEngine.Mathf.Abs(UnityEngine.Mathf.DeltaAngle(actualRotation.y, expectedRotation.y)), UnityEngine.Mathf.Abs(UnityEngine.Mathf.DeltaAngle(actualRotation.z, expectedRotation.z))) <= tolerance);
check("root_scale", (model.transform.localScale - {vec(expected["root_scale"])}).magnitude <= tolerance);
var preview = UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
UnityEngine.GameObject instance = null;
var haveBounds = false;
var worldBounds = new UnityEngine.Bounds();
try {{
    instance = UnityEngine.Object.Instantiate(model);
    UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(instance, preview);
    foreach (var renderer in instance.GetComponentsInChildren<UnityEngine.Renderer>(true)) {{
        if (!haveBounds) {{ worldBounds = renderer.bounds; haveBounds = true; }} else worldBounds.Encapsulate(renderer.bounds);
    }}
}} finally {{
    if (instance != null) UnityEngine.Object.DestroyImmediate(instance);
    UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(preview);
}}
if (!haveBounds) throw new System.Exception("Imported model has no Renderer bounds");
var expectedBounds = {vec(expected["world_bounds_size"])};
check("world_bounds_size", UnityEngine.Mathf.Max(UnityEngine.Mathf.Abs(worldBounds.size.x - expectedBounds.x), UnityEngine.Mathf.Abs(worldBounds.size.y - expectedBounds.y), UnityEngine.Mathf.Abs(worldBounds.size.z - expectedBounds.z)) <= tolerance);
var after = UnityEngine.SceneManagement.SceneManager.GetActiveScene();
var afterSelection = UnityEditor.Selection.activeObject == null ? null : UnityEditor.Selection.activeObject.name;
check("active_scene_preserved", beforePath == after.path && beforeDirty == after.isDirty && beforeRoots == after.rootCount && beforeSelection == afterSelection);
report.Insert(0, "status=passed\\nasset=" + assetPath + "\\nsha256=" + actualHash + "\\n");
report.AppendLine("mesh_count=" + meshCount + ";vertices=" + totalVertices + ";triangles=" + totalTriangles + ";uv=" + totalUv + ";submeshes=" + totalSubmeshes + ";materials=" + materialSlots + ";clips=" + clips.Length);
report.AppendLine("root_location=" + model.transform.localPosition.ToString("R") + ";root_rotation=" + model.transform.localEulerAngles.ToString("R") + ";root_scale=" + model.transform.localScale.ToString("R"));
report.AppendLine("world_bounds_size=" + worldBounds.size.ToString("R"));
return report.ToString();'''


def prepare(request: object, output: Path) -> dict:
    errors, _ = validate_request(request)
    if errors:
        raise ValueError("; ".join(errors))
    if not output.is_absolute() or output.suffix.lower() != ".cs":
        raise ValueError("output must be an absolute .cs path")
    if not output.parent.is_dir() or any(_is_link(item) for item in (output.parent, *output.parent.parents)):
        raise ValueError("output parent must be an existing real directory")
    if output.exists() or _is_link(output):
        raise FileExistsError("output already exists")
    canonical = json.dumps(request, sort_keys=True, ensure_ascii=True,
                           separators=(",", ":"), allow_nan=False)
    code = build_code(request)
    data = code.encode("utf-8")
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
            "request_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "code_sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "allow_import_refresh": request["allow_import_refresh"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        request = read_request(args.request)
        result = prepare(request, args.output.expanduser().absolute())
    except (OSError, UnicodeError, ValueError, TypeError, OverflowError,
            json.JSONDecodeError) as exc:
        parser.exit(1, f"Unity check preparation failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
