import json
from pathlib import Path
import subprocess
import sys
import uuid

import bpy


HELPERS = (
    "validate_2d_static_render_request.py",
    "validate_2d_action_sequence_request.py",
    "inspect_2d_action_sequence_candidate.py",
    "preview_2d_action_sequence_framing.py",
    "stage_2d_action_sequence_source.py",
    "build_2d_action_sequence_job.py",
)


def _view(preset):
    return {
        "FRONT": ([0.0, -1.0, 0.0], [0.0, 0.0, 1.0]),
        "SIDE": ([1.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        "QUARTER": ([0.577350269, -0.577350269, 0.577350269], [-0.40824829, 0.40824829, 0.816496581]),
        "TOP": ([0.0, 0.0, 1.0], [0.0, 1.0, 0.0]),
    }[preset]


def _request(scene, settings):
    mesh = settings.material_target
    rig = settings.animation_armature
    action = settings.animation_action
    start, end = (int(round(value)) for value in action.frame_range)
    direction, up = _view(settings.view_preset)
    slots = list(getattr(action, "slots", ()))
    slot_identifier = slots[0].identifier if len(slots) == 1 else None
    return {
        "schema": "gameassetai.2d-action-sequence-request.v1",
        "static_template": {
            "schema": "gameassetai.2d-static-render-request.v3",
            "scene_name": scene.name,
            "object_name": mesh.name,
            "profile": {"name": None, "reference_sha256": None, "profile_sha256": None},
            "view": {"projection": "ORTHOGRAPHIC", "direction": direction, "up": up,
                     "framing_margin": settings.framing_margin},
            "lighting": {"mode": "OWNED_NEUTRAL", "transparent_background": True},
            "style": {"mode": "PIXEL", "resolution": [settings.resolution_x, settings.resolution_y],
                      "anti_aliasing": "DISABLED", "nearest_neighbor": True,
                      "palette_mode": "NONE", "palette": [], "max_colors": None,
                      "outline_mode": "NONE", "outline_color": None, "outline_width": 0,
                      "shading_mode": "NONE", "value_steps": None},
        },
        "animation": {"armature_name": rig.name, "action_name": action.name,
                      "slot_identifier": slot_identifier, "frame_start": start,
                      "frame_end": end, "frame_step": settings.sequence_frame_step,
                      "playback_fps": scene.render.fps / scene.render.fps_base},
        "framing": {"bounds_policy": "ACTION_RANGE", "anchor_policy": "OBJECT_ORIGIN"},
        "output": {"target_directory": str(Path(bpy.path.abspath(settings.sequence_output_directory)).resolve()),
                   "filename_prefix": settings.sequence_prefix, "index_start": 0,
                   "index_padding": settings.sequence_index_padding, "overwrite": False},
    }


def _load_helpers(root):
    root_text = str(root)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    namespace = {"__builtins__": __builtins__, "bpy": bpy}
    for name in HELPERS:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Missing sequence helper: {name}")
        source = path.read_text(encoding="utf-8-sig")
        exec(compile(source, str(path), "exec"), namespace, namespace)
    renderer = root / "render_2d_action_sequence.py"
    quantizer = root / "quantize_rgba.py"
    if not renderer.is_file() or not quantizer.is_file():
        raise ValueError("Sequence renderer or quantizer is missing")
    return namespace, renderer


class GAA_OT_render_action_sequence(bpy.types.Operator):
    bl_idname = "gameassetai.render_action_sequence"
    bl_label = "Render Action Sequence"
    bl_description = "Dispatch the selected Action through the existing hash-bound background renderer"

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "gameassetai", None)
        return bool(settings and settings.material_target and settings.animation_armature
                    and settings.animation_action and settings.sequence_helper_root.strip()
                    and settings.sequence_output_directory.strip() and settings.sequence_prefix.strip())

    def execute(self, context):
        scene = context.scene
        settings = scene.gameassetai
        output = Path(bpy.path.abspath(settings.sequence_output_directory)).resolve()
        helper_root = Path(bpy.path.abspath(settings.sequence_helper_root)).resolve()
        if not output.is_dir():
            self.report({"ERROR"}, "Sequence output directory does not exist")
            return {"CANCELLED"}
        request = _request(scene, settings)
        token = uuid.uuid4().hex
        stage = output / f".gameassetai-2d-sequence-{token}.stage.blend"
        job = output / f".gameassetai-2d-sequence-{token}.job.json"
        try:
            ns, renderer = _load_helpers(helper_root)
            preflight = ns["validate_2d_action_sequence_request"](request)
            if not preflight["ready_for_blender_inspection"]:
                raise ValueError("; ".join(preflight["errors"]))
            candidate = ns["inspect_2d_action_sequence_candidate"](request, preflight)
            if candidate.get("status") != "candidate_for_review":
                raise ValueError("Sequence candidate blocked: " + ", ".join(candidate.get("blockers", candidate.get("errors", []))))
            framing = ns["preview_2d_action_sequence_framing"](request, preflight, candidate)
            if framing.get("status") != "planned":
                raise ValueError("Sequence framing failed: " + "; ".join(framing.get("errors", [])))
            staged = ns["stage_2d_action_sequence_source"](
                request, preflight, candidate, framing, stage, authorize=True)
            if staged.get("status") != "created":
                raise ValueError("Sequence staging failed: " + "; ".join(staged.get("errors", [])))
            built = ns["build_2d_action_sequence_job"](
                request, preflight, candidate, framing, staged, job, authorize=True)
            if built.get("status") != "created":
                raise ValueError("Sequence job failed: " + "; ".join(built.get("errors", [])))
            process = subprocess.run(
                [bpy.app.binary_path, "--background", str(stage), "--python", str(renderer), "--",
                 "--job", str(job), "--job-sha256", built["job_sha256"],
                 "--helper-root", str(helper_root)],
                capture_output=True, text=True, timeout=900, check=False)
            marker = "GAMEASSETAI_RESULT="
            line = next((item for item in reversed(process.stdout.splitlines()) if item.startswith(marker)), None)
            if process.returncode or line is None:
                raise RuntimeError((process.stderr or process.stdout or "Background renderer failed").strip()[-2000:])
            result = json.loads(line[len(marker):])
            if result.get("status") != "created" or not result.get("pngs_published"):
                raise RuntimeError("Background renderer did not publish a complete sequence")
            scene["gaa_last_sequence_receipt"] = json.dumps(result, separators=(",", ":"))
            self.report({"INFO"}, f"Created {result['published_count']} sequence frames")
            return {"FINISHED"}
        except (ValueError, RuntimeError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            for path in (job, stage):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass


CLASSES = (GAA_OT_render_action_sequence,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
