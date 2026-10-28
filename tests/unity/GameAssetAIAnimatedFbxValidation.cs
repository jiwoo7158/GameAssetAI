// Isolated Unity Editor validation for an animated FBX request placed beside this file.
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class GameAssetAIAnimatedFbxValidation
{
    [Serializable]
    private sealed class Request
    {
        public string schema;
        public string project_root;
        public string asset_path;
        public string expected_sha256;
        public string report_path;
        public int frame_start;
        public int frame_end;
        public float fps;
        public bool loop;
        public string rig_policy;
    }

    [Serializable]
    private sealed class Report
    {
        public string schema = "gameassetai.unity-animated-fbx-validation.v1";
        public string status = "error";
        public string error;
        public string asset_path;
        public string sha256;
        public string unity_version;
        public string importer_animation_type;
        public string clip_name;
        public float clip_frame_rate;
        public float clip_length_seconds;
        public bool loop_time;
        public int skinned_mesh_renderers;
        public int bones;
        public int vertices;
        public float sampled_max_vertex_displacement;
        public bool generic_playback_passed;
        public bool humanoid_avatar_present;
        public bool humanoid_avatar_valid;
        public bool scene_preserved;
    }

    public static string Main()
    {
        Run();
        return "completed";
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private static string HashFile(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }

    private static void Run()
    {
        var requestFiles = Directory.GetFiles(Application.dataPath,
            "gameassetai-m4-unity-request.json", SearchOption.AllDirectories);
        if (requestFiles.Length != 1) return;
        var request = JsonUtility.FromJson<Request>(File.ReadAllText(requestFiles[0]));
        if (request == null || request.schema != "gameassetai.unity-animated-fbx-check.v1") return;
        if (File.Exists(request.report_path)) return;
        var report = new Report { asset_path = request.asset_path, unity_version = Application.unityVersion };
        try
        {
            Require(request.rig_policy == "GENERIC", "Only explicit GENERIC validation is supported");
            Require(!request.loop, "This validation requires an explicit non-loop clip");
            var project = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            Require(string.Equals(project.TrimEnd('\\', '/'), request.project_root.TrimEnd('\\', '/'),
                StringComparison.OrdinalIgnoreCase), "Connected Unity project differs from request");
            var fullPath = Path.GetFullPath(Path.Combine(project,
                request.asset_path.Replace('/', Path.DirectorySeparatorChar)));
            Require(fullPath.StartsWith(Path.GetFullPath(Application.dataPath) + Path.DirectorySeparatorChar,
                StringComparison.OrdinalIgnoreCase), "FBX is outside Assets");
            Require(File.Exists(fullPath), "FBX is missing");
            report.sha256 = HashFile(fullPath);
            Require(report.sha256 == request.expected_sha256, "FBX SHA-256 mismatch");

            AssetDatabase.ImportAsset(request.asset_path,
                ImportAssetOptions.ForceSynchronousImport | ImportAssetOptions.ForceUpdate);
            var importer = AssetImporter.GetAtPath(request.asset_path) as ModelImporter;
            Require(importer != null, "ModelImporter missing");
            importer.importAnimation = true;
            importer.animationType = ModelImporterAnimationType.Generic;
            var clips = importer.defaultClipAnimations;
            Require(clips != null && clips.Length == 1, "Expected exactly one default animation take");
            clips[0].loopTime = false;
            importer.clipAnimations = clips;
            importer.SaveAndReimport();

            var model = AssetDatabase.LoadAssetAtPath<GameObject>(request.asset_path);
            Require(model != null, "Imported model prefab missing");
            var animationClips = AssetDatabase.LoadAllAssetsAtPath(request.asset_path)
                .OfType<AnimationClip>().Where(clip => !clip.name.StartsWith("__preview__")).ToArray();
            Require(animationClips.Length == 1, "Expected exactly one imported animation clip");
            var clip = animationClips[0];
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            var expectedLength = (request.frame_end - request.frame_start) / request.fps;
            Require(Mathf.Abs(clip.frameRate - request.fps) <= 0.01f, "Clip FPS mismatch");
            Require(Mathf.Abs(clip.length - expectedLength) <= 0.02f, "Clip duration mismatch");
            Require(!settings.loopTime, "Clip was unexpectedly imported as looping");

            var before = SceneManager.GetActiveScene();
            var beforePath = before.path;
            var beforeDirty = before.isDirty;
            var beforeRoots = before.rootCount;
            var preview = EditorSceneManager.NewPreviewScene();
            GameObject instance = null;
            try
            {
                instance = UnityEngine.Object.Instantiate(model);
                SceneManager.MoveGameObjectToScene(instance, preview);
                var renderers = instance.GetComponentsInChildren<SkinnedMeshRenderer>(true);
                Require(renderers.Length == 1, "Expected one SkinnedMeshRenderer");
                var renderer = renderers[0];
                Require(renderer.sharedMesh != null && renderer.sharedMesh.vertexCount > 0,
                    "Skinned mesh missing");
                Require(renderer.bones.Length > 0 && renderer.bones.All(bone => bone != null),
                    "Skin bone references are incomplete");
                Require(renderer.sharedMesh.boneWeights.Length == renderer.sharedMesh.vertexCount,
                    "Vertex weights are incomplete");
                Require(instance.transform.localPosition.sqrMagnitude <= 1e-6f
                        && Quaternion.Angle(instance.transform.localRotation, Quaternion.identity) <= 0.1f
                        && (instance.transform.localScale - Vector3.one).magnitude <= 1e-4f,
                    "Imported root transform is not Unity-normalized");

                var bakedStart = new Mesh();
                var bakedMiddle = new Mesh();
                clip.SampleAnimation(instance, 0f);
                renderer.BakeMesh(bakedStart);
                clip.SampleAnimation(instance, clip.length * 0.5f);
                renderer.BakeMesh(bakedMiddle);
                var startVertices = bakedStart.vertices;
                var middleVertices = bakedMiddle.vertices;
                Require(startVertices.Length == middleVertices.Length && startVertices.Length > 0,
                    "Baked mesh sampling failed");
                var displacement = 0f;
                for (var index = 0; index < startVertices.Length; index++)
                    displacement = Mathf.Max(displacement,
                        (startVertices[index] - middleVertices[index]).magnitude);
                UnityEngine.Object.DestroyImmediate(bakedStart);
                UnityEngine.Object.DestroyImmediate(bakedMiddle);
                Require(displacement > 0.01f, "Animation did not deform the skinned mesh");

                var animator = instance.GetComponentInChildren<Animator>(true);
                report.skinned_mesh_renderers = renderers.Length;
                report.bones = renderer.bones.Length;
                report.vertices = renderer.sharedMesh.vertexCount;
                report.sampled_max_vertex_displacement = displacement;
                report.humanoid_avatar_present = animator != null && animator.avatar != null;
                report.humanoid_avatar_valid = report.humanoid_avatar_present
                    && animator.avatar.isValid && animator.avatar.isHuman;
            }
            finally
            {
                if (instance != null) UnityEngine.Object.DestroyImmediate(instance);
                EditorSceneManager.ClosePreviewScene(preview);
            }

            var after = SceneManager.GetActiveScene();
            report.scene_preserved = beforePath == after.path && beforeDirty == after.isDirty
                && beforeRoots == after.rootCount;
            Require(report.scene_preserved, "Active Unity Scene changed during validation");
            report.importer_animation_type = importer.animationType.ToString();
            report.clip_name = clip.name;
            report.clip_frame_rate = clip.frameRate;
            report.clip_length_seconds = clip.length;
            report.loop_time = settings.loopTime;
            report.generic_playback_passed = true;
            report.status = "pass";
        }
        catch (Exception exception)
        {
            report.error = exception.ToString();
        }
        Directory.CreateDirectory(Path.GetDirectoryName(request.report_path));
        File.WriteAllText(request.report_path, JsonUtility.ToJson(report, true));
        Debug.Log("GameAssetAI M4 Unity validation: " + report.status + " -> " + request.report_path);
    }
}
