var scene = UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
var meshes = new System.Collections.Generic.List<UnityEngine.Mesh>();
UnityEngine.GameObject root = null;
try
{
    root = new UnityEngine.GameObject("GAA_LODGroup_Probe");
    UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(root, scene);
    var group = root.AddComponent<UnityEngine.LODGroup>();
    var vertices = new[]
    {
        new UnityEngine.Vector3[]
        {
            new UnityEngine.Vector3(-1,-1,-1), new UnityEngine.Vector3(1,-1,-1),
            new UnityEngine.Vector3(1,1,-1), new UnityEngine.Vector3(-1,1,-1),
            new UnityEngine.Vector3(-1,-1,1), new UnityEngine.Vector3(1,-1,1),
            new UnityEngine.Vector3(1,1,1), new UnityEngine.Vector3(-1,1,1)
        },
        new UnityEngine.Vector3[]
        {
            new UnityEngine.Vector3(1,0,0), new UnityEngine.Vector3(-1,0,0),
            new UnityEngine.Vector3(0,1,0), new UnityEngine.Vector3(0,-1,0),
            new UnityEngine.Vector3(0,0,1), new UnityEngine.Vector3(0,0,-1)
        },
        new UnityEngine.Vector3[]
        {
            new UnityEngine.Vector3(1,1,1), new UnityEngine.Vector3(-1,-1,1),
            new UnityEngine.Vector3(-1,1,-1), new UnityEngine.Vector3(1,-1,-1)
        }
    };
    var triangles = new[]
    {
        new int[] {0,3,2,0,2,1,4,5,6,4,6,7,0,1,5,0,5,4,1,2,6,1,6,5,2,3,7,2,7,6,3,0,4,3,4,7},
        new int[] {0,2,4,2,1,4,1,3,4,3,0,4,2,0,5,1,2,5,3,1,5,0,3,5},
        new int[] {0,1,2,0,3,1,0,2,3,1,3,2}
    };
    var renderers = new UnityEngine.Renderer[3];
    for (var index = 0; index < 3; index++)
    {
        var mesh = new UnityEngine.Mesh { name = "GAA_LOD" + index + "_Mesh" };
        mesh.vertices = vertices[index];
        mesh.triangles = triangles[index];
        mesh.RecalculateBounds();
        mesh.RecalculateNormals();
        meshes.Add(mesh);
        var child = new UnityEngine.GameObject("LOD" + index);
        UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(child, scene);
        child.transform.SetParent(root.transform, false);
        child.AddComponent<UnityEngine.MeshFilter>().sharedMesh = mesh;
        renderers[index] = child.AddComponent<UnityEngine.MeshRenderer>();
    }
    group.SetLODs(new[]
    {
        new UnityEngine.LOD(0.6f, new[] {renderers[0]}),
        new UnityEngine.LOD(0.3f, new[] {renderers[1]}),
        new UnityEngine.LOD(0.1f, new[] {renderers[2]})
    });
    group.RecalculateBounds();
    var lods = group.GetLODs();
    return "{\"previewScene\":"
        + UnityEditor.SceneManagement.EditorSceneManager.IsPreviewScene(scene).ToString().ToLowerInvariant()
        + ",\"levels\":" + lods.Length
        + ",\"triangles\":[" + (meshes[0].triangles.Length / 3) + ","
        + (meshes[1].triangles.Length / 3) + "," + (meshes[2].triangles.Length / 3) + "]"
        + ",\"transitions\":["
        + lods[0].screenRelativeTransitionHeight.ToString(System.Globalization.CultureInfo.InvariantCulture) + ","
        + lods[1].screenRelativeTransitionHeight.ToString(System.Globalization.CultureInfo.InvariantCulture) + ","
        + lods[2].screenRelativeTransitionHeight.ToString(System.Globalization.CultureInfo.InvariantCulture) + "]"
        + ",\"renderersPerLevel\":[" + lods[0].renderers.Length + ","
        + lods[1].renderers.Length + "," + lods[2].renderers.Length + "]"
        + ",\"sizePositive\":" + (group.size > 0f).ToString().ToLowerInvariant() + "}";
}
finally
{
    if (root != null) UnityEngine.Object.DestroyImmediate(root);
    foreach (var mesh in meshes)
        if (mesh != null) UnityEngine.Object.DestroyImmediate(mesh);
    UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);
}
