"""Synthetic Blender regression for independent static source blend staging."""
from pathlib import Path
import uuid


def run_2d_source_stage_tests(artifact_root):
    root = Path(artifact_root).resolve(strict=True)
    token = uuid.uuid4().hex
    stage = root / (".gameassetai-2d-" + token + ".stage.blend")
    target = root / ("source-stage-" + token + ".png")
    collections = (bpy.data.scenes, bpy.data.objects, bpy.data.meshes, bpy.data.materials)
    before = [[item.name for item in collection] for collection in collections]
    original_scene = bpy.context.scene
    original_selection = sorted(obj.name for obj in bpy.context.selected_objects)
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    scene = bpy.data.scenes.new("GAI_StageFixture_" + token)
    mesh = bpy.data.meshes.new("GAI_StageFixtureMesh_" + token)
    mesh.from_pydata([(-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1)],
                     [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new("GAI_StageFixtureObject_" + token, mesh)
    scene.collection.objects.link(obj)
    material = bpy.data.materials.new("GAI_StageFixtureMaterial_" + token)
    mesh.materials.append(material)
    request = {"schema": SCHEMA, "scene_name": scene.name, "object_name": obj.name,
        "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
        "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                 "up": [0, 0, 1], "framing_margin": 0.1},
        "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
        "style": {"mode": "PIXEL", "resolution": [32, 24],
                  "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                  "palette_mode": "FIXED", "palette": [[0, 0, 0, 1], [1, 1, 1, 1]],
                  "max_colors": None, "outline_mode": "NONE",
                  "outline_color": None, "outline_width": 0,
                  "shading_mode": "NONE", "value_steps": None},
        "output": {"target_file": str(target), "color_mode": "RGBA",
                   "color_depth": 8, "overwrite": False}}
    try:
        preflight = validate_2d_static_render_request(request)
        candidate = inspect_2d_static_render_candidate(request, preflight)
        framing = preview_2d_orthographic_framing(request, candidate)
        check("candidate_chain", candidate["status"] == "candidate_for_review"
              and framing["status"] == "planned")
        refused = stage_2d_static_source(request, preflight, candidate, framing,
                                         str(stage), authorize=False)
        check("authorization_refused", refused["status"] == "error" and not stage.exists())
        created = stage_2d_static_source(request, preflight, candidate, framing,
                                         str(stage), authorize=True)
        check("stage_created", created["status"] == "created" and stage.is_file()
              and stage.read_bytes().startswith(b"BLENDER"))
        check("fingerprints_bound", all(created[key] == candidate[key] for key in
              ("request_sha256", "source_fingerprint", "setup_fingerprint",
               "output_fingerprint")) and created["plan_fingerprint"] ==
              framing["plan_fingerprint"])
        collision = stage_2d_static_source(request, preflight, candidate, framing,
                                           str(stage), authorize=True)
        check("stage_collision_refused", collision["status"] == "error"
              and stage.is_file())
        mesh.vertices[0].co.x -= 0.25
        stale = stage_2d_static_source(request, preflight, candidate, framing,
                                       str(root / (".gameassetai-2d-stale-" + token +
                                                   ".stage.blend")), authorize=True)
        check("stale_source_refused", stale["status"] == "error")
        mesh.vertices[0].co.x += 0.25
        check("no_png_published", not target.exists())
    finally:
        stage.unlink(missing_ok=True)
        for stale_path in root.glob(".gameassetai-2d-stale-" + token + "*"):
            stale_path.unlink()
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        bpy.data.materials.remove(material)
        bpy.data.scenes.remove(scene)
    check("context_preserved", bpy.context.scene == original_scene
          and sorted(obj.name for obj in bpy.context.selected_objects) == original_selection)
    check("exact_id_teardown", before == [[item.name for item in c] for c in collections])
    return {"status": "passed", "check_count": len(checks), "checks": checks,
            "blender_version": bpy.app.version_string}
