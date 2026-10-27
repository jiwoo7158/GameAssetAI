"""Blender 5 regression for mixed static/Action batch success and cross-child rollback."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
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


def _load(root, names, label):
    namespace = {"__name__": label}
    for name in names:
        source = (root / name).read_text(encoding="utf-8-sig")
        exec(compile(source, name, "exec"), namespace, namespace)
    return namespace


def main():
    args = _arguments()
    root, repo = args.artifact_root.resolve(strict=True), args.repo_root.resolve(strict=True)
    helpers = (args.helper_root or (repo / "scripts")).resolve(strict=True)
    sys.path.insert(0, str(helpers))
    from build_2d_render_batch_job import build_2d_render_batch_job
    from run_2d_render_batch import run_2d_render_batch_job
    from validate_2d_render_batch_request import validate_2d_render_batch_request

    static_ns = _load(helpers, (
        "validate_2d_static_render_request.py", "inspect_2d_static_render_candidate.py",
        "preview_2d_orthographic_framing.py", "stage_2d_static_source.py",
        "build_2d_staged_render_job.py"), "gai_batch_static")
    action_ns = _load(helpers, (
        "validate_2d_static_render_request.py", "validate_2d_action_sequence_request.py",
        "inspect_2d_action_sequence_candidate.py", "preview_2d_action_sequence_framing.py",
        "stage_2d_action_sequence_source.py", "build_2d_action_sequence_job.py"),
        "gai_batch_action")
    token = uuid.uuid4().hex
    paths, checks = [], []
    broken_root = root / (".gameassetai-2d-batch-broken-" + token)
    before = sorted(path.name for path in root.iterdir())

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    try:
        scene = bpy.context.scene
        for existing in list(scene.objects):
            bpy.data.objects.remove(existing, do_unlink=True)
        material = bpy.data.materials.new("GAI_BatchMaterial_" + token)
        material.diffuse_color = (0.4, 0.65, 0.8, 1.0)

        static_mesh = bpy.data.meshes.new("GAI_BatchStaticMesh_" + token)
        static_mesh.from_pydata([(-0.5, 0, 0), (0.5, 0, 0),
                                 (0.5, 0, 1), (-0.5, 0, 1)], [], [(0, 1, 2, 3)])
        static_mesh.materials.append(material)
        static_obj = bpy.data.objects.new("GAI_BatchStatic_" + token, static_mesh)
        scene.collection.objects.link(static_obj)

        rig_data = bpy.data.armatures.new("GAI_BatchRigData_" + token)
        rig = bpy.data.objects.new("GAI_BatchRig_" + token, rig_data)
        action_mesh = bpy.data.meshes.new("GAI_BatchActionMesh_" + token)
        action_mesh.from_pydata([(-0.5, 0, 0), (0.5, 0, 0),
                                 (0.5, 0, 1), (-0.5, 0, 1)], [], [(0, 1, 2, 3)])
        action_mesh.materials.append(material)
        action_obj = bpy.data.objects.new("GAI_BatchAction_" + token, action_mesh)
        scene.collection.objects.link(rig); scene.collection.objects.link(action_obj)
        scene.view_layers[0].objects.active = rig; rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")
        bone = rig_data.edit_bones.new("Root"); bone.head, bone.tail = (0, 0, 0), (0, 0, 1)
        bpy.ops.object.mode_set(mode="POSE")
        pose = rig.pose.bones["Root"]
        for frame, x in ((1, -0.5), (2, 0.0), (3, 0.5)):
            pose.location = (x, 0, 0); pose.keyframe_insert(data_path="location", frame=frame)
        bpy.ops.object.mode_set(mode="OBJECT")
        action = rig.animation_data.action
        group = action_obj.vertex_groups.new(name="Root"); group.add(range(4), 1.0, "REPLACE")
        modifier = action_obj.modifiers.new("Armature", "ARMATURE"); modifier.object = rig
        slot = action.slots[0].identifier if len(action.slots) else None

        profile = {"name": None, "reference_sha256": None, "profile_sha256": None}
        style = {"mode": "PIXEL", "resolution": [24, 24],
                 "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                 "palette_mode": "NONE", "palette": [], "max_colors": None,
                 "outline_mode": "NONE", "outline_color": None, "outline_width": 0,
                 "shading_mode": "NONE", "value_steps": None}
        lighting = {"mode": "OWNED_NEUTRAL", "transparent_background": True}
        static_target = root / ("batch-static-" + token + ".png")
        static_request = {"schema": static_ns["SCHEMA"], "scene_name": scene.name,
                          "object_name": static_obj.name, "profile": profile,
                          "view": {"projection": "ORTHOGRAPHIC", "direction": [0, -1, 0],
                                   "up": [0, 0, 1], "framing_margin": 0.1},
                          "lighting": lighting, "style": style,
                          "output": {"target_file": str(static_target), "color_mode": "RGBA",
                                     "color_depth": 8, "overwrite": False}}
        action_request = {
            "schema": action_ns["SCHEMA"],
            "static_template": {"schema": action_ns["STATIC_SCHEMA"],
                                "scene_name": scene.name, "object_name": action_obj.name,
                                "profile": profile,
                                "view": {"projection": "ORTHOGRAPHIC",
                                         "direction": [0.7071067811865476,
                                                       -0.7071067811865476, 0],
                                         "up": [0, 0, 1],
                                         "framing_margin": 0.1},
                                "lighting": lighting, "style": style},
            "animation": {"armature_name": rig.name, "action_name": action.name,
                          "slot_identifier": slot, "frame_start": 1, "frame_end": 3,
                          "frame_step": 1, "playback_fps": 12},
            "framing": {"bounds_policy": "ACTION_RANGE", "anchor_policy": "OBJECT_ORIGIN"},
            "output": {"target_directory": str(root),
                       "filename_prefix": "batch-action-" + token + "-",
                       "index_start": 0, "index_padding": 4, "overwrite": False}}

        static_stage = root / (".gameassetai-2d-" + token + ".stage.blend")
        static_job = root / (".gameassetai-2d-" + token + ".job.json")
        static_pre = static_ns["validate_2d_static_render_request"](static_request)
        static_candidate = static_ns["inspect_2d_static_render_candidate"](
            static_request, static_pre)
        static_framing = static_ns["preview_2d_orthographic_framing"](
            static_request, static_candidate)
        static_staged = static_ns["stage_2d_static_source"](
            static_request, static_pre, static_candidate, static_framing,
            str(static_stage), authorize=True)
        static_prepared = static_ns["build_2d_staged_render_job"](
            static_request, static_candidate, static_framing, static_staged,
            str(static_job), authorize=True)

        action_stage = root / (".gameassetai-2d-sequence-" + token + ".stage.blend")
        action_job = root / (".gameassetai-2d-sequence-" + token + ".job.json")
        action_pre = action_ns["validate_2d_action_sequence_request"](action_request)
        action_candidate = action_ns["inspect_2d_action_sequence_candidate"](
            action_request, action_pre)
        action_framing = action_ns["preview_2d_action_sequence_framing"](
            action_request, action_pre, action_candidate)
        action_staged = action_ns["stage_2d_action_sequence_source"](
            action_request, action_pre, action_candidate, action_framing,
            str(action_stage), authorize=True)
        action_prepared = action_ns["build_2d_action_sequence_job"](
            action_request, action_pre, action_candidate, action_framing, action_staged,
            str(action_job), authorize=True)
        paths.extend((static_stage, static_job, action_stage, action_job))
        check("both_children_staged", static_prepared["status"] == "created"
              and action_prepared["status"] == "created")

        batch_request = {"schema": "gameassetai.2d-render-batch-request.v1",
                         "items": [{"id": "front-static", "kind": "STATIC",
                                    "settings_source": "EXPLICIT",
                                    "profile_binding": {"name": None,
                                                        "reference_sha256": None,
                                                        "profile_sha256": None,
                                                        "preset_sha256": None},
                                    "request": static_request},
                                   {"id": "side-walk", "kind": "ACTION_SEQUENCE",
                                    "settings_source": "EXPLICIT",
                                    "profile_binding": {"name": None,
                                                        "reference_sha256": None,
                                                        "profile_sha256": None,
                                                        "preset_sha256": None},
                                    "request": action_request}],
                         "policy": {"execution_order": "LIST_ORDER",
                                    "publication": "ALL_OR_NOTHING",
                                    "on_failure": "ROLL_BACK_BATCH_OUTPUTS"}}
        preview = validate_2d_render_batch_request(batch_request)
        check("mixed_batch_ready", preview["status"] == "ready" and preview["output_count"] == 4)
        children = [
            {"id": "front-static", "kind": "STATIC", "stage_file": str(static_stage),
             "stage_sha256": static_staged["stage_sha256"], "job_file": str(static_job),
             "job_sha256": static_prepared["job_sha256"], "helper_root": str(helpers)},
            {"id": "side-walk", "kind": "ACTION_SEQUENCE", "stage_file": str(action_stage),
             "stage_sha256": action_staged["stage_sha256"], "job_file": str(action_job),
             "job_sha256": action_prepared["job_sha256"], "helper_root": str(helpers)},
        ]

        broken_root.mkdir()
        for name in ("quantize_rgba.py", "build_2d_action_sequence_job.py"):
            (broken_root / name).write_bytes((helpers / name).read_bytes())
        (broken_root / "render_2d_action_sequence.py").write_text(
            "raise SystemExit(7)\n", encoding="utf-8")
        broken_children = json.loads(json.dumps(children))
        broken_children[1]["helper_root"] = str(broken_root)
        failed_job = root / (".gameassetai-2d-batch-fail-" + token + ".job.json")
        failed_prepared = build_2d_render_batch_job(
            batch_request, preview, broken_children, str(failed_job), authorize=True)
        paths.append(failed_job)
        failed = run_2d_render_batch_job(
            str(failed_job), failed_prepared["job_sha256"], bpy.app.binary_path)
        check("later_child_failure_rolls_back_static", failed["status"] == "error"
              and failed["published_count"] == 0
              and not any(Path(output).exists() for output in preview["outputs"]))

        batch_job = root / (".gameassetai-2d-batch-ok-" + token + ".job.json")
        prepared = build_2d_render_batch_job(
            batch_request, preview, children, str(batch_job), authorize=True)
        paths.append(batch_job)
        rendered = run_2d_render_batch_job(
            str(batch_job), prepared["job_sha256"], bpy.app.binary_path)
        if not (rendered["status"] == "created" and rendered["published_count"] == 4
                and all(Path(output).is_file() for output in preview["outputs"])):
            raise AssertionError("mixed_batch_published: "
                                 + json.dumps(rendered, sort_keys=True))
        checks.append("mixed_batch_published")
        check("ordered_child_receipts", [item["id"] for item in rendered["child_receipts"]]
              == ["front-static", "side-walk"])
        check("batch_receipt_bound", len(rendered["receipt_sha256"]) == 64
              and all(artifact["sha256"] == hashlib.sha256(
                  Path(artifact["path"]).read_bytes()).hexdigest()
                      for artifact in rendered["artifacts"]))
        paths.extend(Path(output) for output in preview["outputs"])
        result = {"status": "passed", "check_count": len(checks), "checks": checks,
                  "receipt_sha256": rendered["receipt_sha256"],
                  "artifact_sha256": [item["sha256"] for item in rendered["artifacts"]],
                  "blender_version": bpy.app.version_string}
    finally:
        for path in reversed(paths):
            path.unlink(missing_ok=True)
        if broken_root.is_dir():
            shutil.rmtree(broken_root)
    check("exact_file_teardown", sorted(path.name for path in root.iterdir()) == before)
    result["check_count"], result["checks"] = len(checks), checks
    print("GAMEASSETAI_RESULT=" + json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
