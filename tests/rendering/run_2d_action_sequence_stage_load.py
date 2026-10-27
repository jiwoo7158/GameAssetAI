"""Background regression: stage an Action sequence, reopen it, and verify evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

import bpy


def _arguments():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--helper-root", type=Path)
    return parser.parse_args(tail)


def _world_bounds(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    try:
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        return {
            "minimum": [min(float(point[index]) for point in points) for index in range(3)],
            "maximum": [max(float(point[index]) for point in points) for index in range(3)],
        }
    finally:
        evaluated.to_mesh_clear()


def main():
    args = _arguments()
    if not bpy.app.background or bpy.data.filepath:
        raise RuntimeError("Action stage-load test requires background factory startup")
    root = args.artifact_root.resolve(strict=True)
    repo = args.repo_root.resolve(strict=True)
    helper_root = (args.helper_root or (repo / "scripts")).resolve(strict=True)
    sys.path.insert(0, str(helper_root))
    namespace = {"__name__": "gameassetai_2d_action_stage_load_helpers"}
    for name in ("validate_2d_static_render_request.py",
                 "validate_2d_action_sequence_request.py",
                 "inspect_2d_action_sequence_candidate.py",
                 "preview_2d_action_sequence_framing.py",
                 "stage_2d_action_sequence_source.py",
                 "build_2d_action_sequence_job.py",
                 "quantize_rgba.py",
                 "render_2d_action_sequence.py"):
        source = (helper_root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    SCHEMA = namespace["SCHEMA"]
    STATIC_SCHEMA = namespace["STATIC_SCHEMA"]
    validate_2d_action_sequence_request = namespace["validate_2d_action_sequence_request"]
    inspect_2d_action_sequence_candidate = namespace["inspect_2d_action_sequence_candidate"]
    preview_2d_action_sequence_framing = namespace["preview_2d_action_sequence_framing"]
    stage_2d_action_sequence_source = namespace["stage_2d_action_sequence_source"]
    build_2d_action_sequence_job = namespace["build_2d_action_sequence_job"]
    render_2d_action_sequence_job = namespace["render_2d_action_sequence_job"]

    token = uuid.uuid4().hex
    stage = root / (".gameassetai-2d-sequence-" + token + ".stage.blend")
    job = root / (".gameassetai-2d-sequence-" + token + ".job.json")
    before = sorted(path.name for path in root.iterdir())
    checks = []

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        rig_data = bpy.data.armatures.new("GAI_SequenceStageRigData_" + token)
        rig = bpy.data.objects.new("GAI_SequenceStageRig_" + token, rig_data)
        mesh_data = bpy.data.meshes.new("GAI_SequenceStageMesh_" + token)
        mesh_data.from_pydata([(-0.5, 0, 0), (0.5, 0, 0),
                               (0.5, 0, 1), (-0.5, 0, 1)], [], [(0, 1, 2, 3)])
        mesh_obj = bpy.data.objects.new("GAI_SequenceStageObject_" + token, mesh_data)
        scene.collection.objects.link(rig)
        scene.collection.objects.link(mesh_obj)
        scene.view_layers[0].objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bone = rig_data.edit_bones.new("Root")
        bone.head, bone.tail = (0, 0, 0), (0, 0, 1)
        bpy.ops.object.mode_set(mode="POSE")
        pose = rig.pose.bones["Root"]
        for frame, x in ((1, -1.0), (2, 0.0), (3, 1.0)):
            pose.location = (x, 0, 0)
            pose.keyframe_insert(data_path="location", frame=frame)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action
        group = mesh_obj.vertex_groups.new(name="Root")
        group.add(range(4), 1.0, "REPLACE")
        modifier = mesh_obj.modifiers.new("Armature", "ARMATURE")
        modifier.object = rig
        slot = action.slots[0].identifier if len(action.slots) else None
        request = {
            "schema": SCHEMA,
            "static_template": {
                "schema": STATIC_SCHEMA, "scene_name": scene.name,
                "object_name": mesh_obj.name,
                "profile": {"name": None, "reference_sha256": None,
                            "profile_sha256": None},
                "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                         "up": [0, 0, 1], "framing_margin": 0.1},
                "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
                "style": {"mode": "PIXEL", "resolution": [32, 32],
                          "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                          "palette_mode": "NONE", "palette": [], "max_colors": None,
                          "outline_mode": "NONE", "outline_color": None,
                          "outline_width": 0, "shading_mode": "NONE",
                          "value_steps": None}},
            "animation": {"armature_name": rig.name, "action_name": action.name,
                          "slot_identifier": slot, "frame_start": 1, "frame_end": 3,
                          "frame_step": 1, "playback_fps": 12.5},
            "framing": {"bounds_policy": "ACTION_RANGE",
                        "anchor_policy": "OBJECT_ORIGIN"},
            "output": {"target_directory": str(root),
                       "filename_prefix": "sequence-stage-load-" + token + "-",
                       "index_start": 0, "index_padding": 4, "overwrite": False},
        }
        preflight = validate_2d_action_sequence_request(request)
        candidate = inspect_2d_action_sequence_candidate(request, preflight)
        framing = preview_2d_action_sequence_framing(request, preflight, candidate)
        staged = stage_2d_action_sequence_source(
            request, preflight, candidate, framing, str(stage), authorize=True)
        check("stage_created", staged["status"] == "created" and stage.is_file())
        prepared = build_2d_action_sequence_job(
            request, preflight, candidate, framing, staged, str(job), authorize=True)
        check("job_created", prepared["status"] == "created" and job.is_file())
        expected_size = stage.stat().st_size
        expected_sha = hashlib.sha256(stage.read_bytes()).hexdigest()

        bpy.ops.wm.open_mainfile(filepath=str(stage), load_ui=False)
        check("stage_loaded", Path(bpy.data.filepath) == stage)
        meshes = [item for item in bpy.context.scene.objects if item.type == "MESH"]
        rigs = [item for item in bpy.context.scene.objects if item.type == "ARMATURE"]
        check("isolated_ids", len(bpy.data.scenes) == 1 and len(meshes) == 1
              and len(rigs) == 1 and len(bpy.data.actions) == 1)
        loaded_mesh, loaded_rig = meshes[0], rigs[0]
        loaded_action = bpy.data.actions[0]
        check("action_bound", loaded_rig.animation_data is not None
              and loaded_rig.animation_data.action == loaded_action)
        modifiers = [item for item in loaded_mesh.modifiers if item.type == "ARMATURE"]
        check("modifier_retargeted", len(modifiers) == 1
              and modifiers[0].object == loaded_rig)
        check("geometry_and_weights_preserved", len(loaded_mesh.data.vertices) == 4
              and len(loaded_mesh.data.polygons) == 1
              and len(loaded_mesh.vertex_groups) == 1)
        effective_fps = (bpy.context.scene.render.fps /
                         bpy.context.scene.render.fps_base)
        if not (bpy.context.scene.frame_start == 1
                and bpy.context.scene.frame_end == 3
                and abs(effective_fps - 12.5) <= 1e-6):
            raise AssertionError(
                "range_and_fractional_fps_preserved: "
                f"{bpy.context.scene.frame_start}, {bpy.context.scene.frame_end}, "
                f"{bpy.context.scene.render.fps}, {bpy.context.scene.render.fps_base}, "
                f"{effective_fps}")
        checks.append("range_and_fractional_fps_preserved")
        observed = []
        for planned, expected in zip(preflight["frames"], candidate["evaluation"]["frames"]):
            bpy.context.scene.frame_set(planned["source_frame"])
            bounds = _world_bounds(loaded_mesh)
            observed.append(bounds)
            check("frame_%s_evaluates" % planned["source_frame"], all(
                abs(bounds[side][axis] - expected["bounds"][side][axis]) <= 1e-6
                for side in ("minimum", "maximum") for axis in range(3)))
        check("animation_changes_loaded_mesh", observed[0] != observed[1]
              and observed[1] != observed[2])
        check("stage_identity_preserved", stage.stat().st_size == expected_size
              and hashlib.sha256(stage.read_bytes()).hexdigest() == expected_sha)
        check("no_png_created", not any(Path(frame["target_file"]).exists()
                                        for frame in preflight["frames"]))
        targets = [Path(frame["target_file"]) for frame in preflight["frames"]]
        real_link = namespace["os"].link
        link_calls = 0

        def fail_second_link(source, target):
            nonlocal link_calls
            link_calls += 1
            if link_calls == 2:
                raise OSError("synthetic second-publication failure")
            return real_link(source, target)

        namespace["os"].link = fail_second_link
        try:
            rolled_back = render_2d_action_sequence_job(
                str(job), prepared["job_sha256"], authorize=True)
        finally:
            namespace["os"].link = real_link
        check("partial_publication_rolled_back", rolled_back["status"] == "error"
              and rolled_back["published_count"] == 0
              and not any(target.exists() for target in targets))
        rendered = render_2d_action_sequence_job(
            str(job), prepared["job_sha256"], authorize=True)
        check("sequence_published", rendered["status"] == "created"
              and rendered["pngs_published"] and rendered["published_count"] == 3
              and all(target.is_file() for target in targets))
        check("stable_dimensions_and_anchor", all(
              artifact["width"] == 32 and artifact["height"] == 32
              and artifact["anchor_pixel_from_bottom_left"]
                  == framing["plan"]["anchor_pixel_from_bottom_left"]
              for artifact in rendered["artifacts"]))
        check("ordered_receipt_bound", len(rendered["receipt_sha256"]) == 64
              and [item["source_frame"] for item in rendered["artifacts"]] == [1, 2, 3]
              and all(item["sha256"] == hashlib.sha256(
                  Path(item["path"]).read_bytes()).hexdigest()
                      for item in rendered["artifacts"]))
        published_bytes = [target.read_bytes() for target in targets]
        collision = render_2d_action_sequence_job(
            str(job), prepared["job_sha256"], authorize=True)
        check("published_collision_refused", collision["status"] == "error"
              and [target.read_bytes() for target in targets] == published_bytes)
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "stage_sha256": expected_sha,
                  "receipt_sha256": rendered["receipt_sha256"],
                  "artifact_sha256": [item["sha256"] for item in rendered["artifacts"]],
                  "blender_version": bpy.app.version_string}
    finally:
        for path in locals().get("targets", []):
            path.unlink(missing_ok=True)
        job.unlink(missing_ok=True)
        stage.unlink(missing_ok=True)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"] = len(checks)
    result["checks"] = checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
