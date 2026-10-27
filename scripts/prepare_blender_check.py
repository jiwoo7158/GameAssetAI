"""Print a self-contained MCP Python test payload; never connect to or install Blender."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from package_skill import skill_files
from validate_workspace import is_link


def build_payload(root: Path, suite: str, bundle_dir: Path | None = None,
                  *, installed_skills_dir: Path | None = None) -> dict:
    if bundle_dir is not None and installed_skills_dir is not None:
        raise ValueError("Choose either bundled or installed helpers, not both")
    if installed_skills_dir is not None:
        installed_skills_dir = installed_skills_dir.expanduser().absolute()
        if any(is_link(p) for p in (installed_skills_dir, *installed_skills_dir.parents)):
            raise ValueError("Linked installed-skills path is not supported")
    if suite not in {"inspection", "static-mesh", "loose-cleanup", "humanoid-inspection", "mixamo-preflight", "animation-inventory", "action-copy-plan", "action-copy", "action-range-extraction", "action-loop", "root-motion", "evaluated-root-motion", "evaluated-pose-loop", "subframe-pose-probe", "2d-render-capabilities", "2d-render-candidate", "2d-action-sequence-candidate", "2d-action-sequence-skill", "2d-source-stage", "2d-static-pixel-skill", "root-translation-bake", "retarget-action-composition", "action-binding", "action-replacement", "retarget-readiness", "aligned-retarget", "rotation-retarget-bake", "coplanar-experiment", "coplanar-skill", "transform-preflight", "scale-copy-skill", "pivot-preview", "pivot-skill", "export-context", "fbx-probe", "fbx-staged", "fbx-staged-skill", "all"}:
        raise ValueError(f"Unknown suite: {suite}")
    paths = ["skills/blender-inspect-asset/scripts/inspect_asset.py",
             "tests/blender-scene/run_inspection.py"]
    if suite in {"static-mesh", "all"}:
        paths.extend(["skills/blender-validate-static-mesh/scripts/validate_mesh.py",
                      "tests/static-mesh/run_diagnostics.py"])
    if suite in {"loose-cleanup", "all"}:
        paths.extend(["skills/blender-cleanup-loose-geometry/scripts/cleanup_loose.py",
                      "tests/static-mesh/run_loose_cleanup.py"])
    if suite == "humanoid-inspection":
        paths.extend(["skills/blender-inspect-humanoid/scripts/inspect_humanoid.py",
                      "tests/rigging/run_humanoid_inspection.py"])
    if suite == "mixamo-preflight":
        paths.extend(["skills/blender-inspect-mixamo-preflight/scripts/inspect_humanoid.py",
                      "skills/blender-inspect-mixamo-preflight/scripts/inspect_mixamo_preflight.py",
                      "tests/rigging/run_mixamo_preflight.py"])
    if suite == "animation-inventory":
        paths.extend(["skills/blender-inspect-animation/scripts/inspect_animation.py",
                      "tests/animation/run_animation_inventory.py"])
    if suite == "action-copy-plan":
        paths.extend(["skills/blender-copy-action/scripts/inspect_animation.py",
                      "skills/blender-copy-action/scripts/plan_action_copy.py",
                      "tests/animation/run_action_copy_plan.py"])
    if suite == "action-copy":
        paths.extend(["skills/blender-copy-action/scripts/inspect_animation.py",
                      "skills/blender-copy-action/scripts/plan_action_copy.py",
                      "skills/blender-copy-action/scripts/action_copy.py",
                      "tests/animation/run_action_copy_apply.py"])
    if suite == "action-range-extraction":
        paths.extend(["skills/blender-extract-action-range/scripts/inspect_animation.py",
                      "skills/blender-extract-action-range/scripts/action_copy.py",
                      "skills/blender-extract-action-range/scripts/extract_action_range.py",
                      "tests/animation/run_action_range_extraction.py"])
    if suite == "action-loop":
        paths.extend(["skills/blender-inspect-animation-loop/scripts/inspect_animation.py",
                      "skills/blender-inspect-animation-loop/scripts/inspect_action_loop.py",
                      "tests/animation/run_action_loop_inspection.py"])
    if suite == "root-motion":
        paths.extend(["skills/blender-inspect-root-motion/scripts/inspect_animation.py",
                      "skills/blender-inspect-root-motion/scripts/inspect_action_loop.py",
                      "skills/blender-inspect-root-motion/scripts/inspect_root_motion.py",
                      "tests/animation/run_root_motion_inspection.py"])
    if suite == "evaluated-root-motion":
        paths.extend(["skills/blender-inspect-evaluated-root-motion/scripts/inspect_animation.py",
                      "skills/blender-inspect-evaluated-root-motion/scripts/inspect_action_loop.py",
                      "skills/blender-inspect-evaluated-root-motion/scripts/inspect_root_motion.py",
                      "skills/blender-inspect-evaluated-root-motion/scripts/action_copy.py",
                      "skills/blender-inspect-evaluated-root-motion/scripts/inspect_evaluated_root_motion.py",
                      "tests/animation/run_evaluated_root_motion.py"])
    if suite == "evaluated-pose-loop":
        paths.extend(["skills/blender-inspect-evaluated-pose-loop/scripts/inspect_animation.py",
                      "skills/blender-inspect-evaluated-pose-loop/scripts/inspect_action_loop.py",
                      "skills/blender-inspect-evaluated-pose-loop/scripts/inspect_root_motion.py",
                      "skills/blender-inspect-evaluated-pose-loop/scripts/action_copy.py",
                      "skills/blender-inspect-evaluated-pose-loop/scripts/inspect_evaluated_root_motion.py",
                      "skills/blender-inspect-evaluated-pose-loop/scripts/inspect_evaluated_pose_loop.py",
                      "tests/animation/run_evaluated_pose_loop.py"])
    if suite == "subframe-pose-probe":
        paths.append("tests/animation/run_subframe_pose_probe.py")
    if suite == "2d-render-capabilities":
        paths.extend(["scripts/inspect_2d_render_capabilities.py",
                      "tests/rendering/run_2d_render_capabilities.py"])
    if suite == "2d-render-candidate":
        paths.extend(["scripts/validate_2d_static_render_request.py",
                      "scripts/inspect_2d_static_render_candidate.py",
                      "scripts/preview_2d_orthographic_framing.py",
                      "tests/rendering/run_2d_static_render_candidate.py"])
    if suite == "2d-action-sequence-candidate":
        paths.extend(["scripts/validate_2d_static_render_request.py",
                      "scripts/validate_2d_action_sequence_request.py",
                      "scripts/inspect_2d_action_sequence_candidate.py",
                      "scripts/preview_2d_action_sequence_framing.py",
                      "scripts/stage_2d_action_sequence_source.py",
                      "scripts/build_2d_action_sequence_job.py",
                      "tests/rendering/run_2d_action_sequence_candidate.py"])
    if suite == "2d-action-sequence-skill":
        paths.extend("skills/blender-render-action-png-sequence/scripts/" + name for name in
                     ("validate_2d_static_render_request.py",
                      "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                      "validate_2d_action_sequence_request.py",
                      "inspect_2d_action_sequence_candidate.py",
                      "preview_2d_action_sequence_framing.py",
                      "stage_2d_action_sequence_source.py",
                      "build_2d_action_sequence_job.py",
                      "quantize_rgba.py", "render_2d_action_sequence.py"))
        paths.append("tests/rendering/run_2d_action_sequence_candidate.py")
    if suite == "2d-source-stage":
        paths.extend(["scripts/validate_2d_static_render_request.py",
                      "scripts/inspect_2d_static_render_candidate.py",
                      "scripts/preview_2d_orthographic_framing.py",
                      "scripts/stage_2d_static_source.py",
                      "tests/rendering/run_2d_source_stage.py"])
    if suite == "2d-static-pixel-skill":
        paths.extend("skills/blender-render-static-pixel-png/scripts/" + name for name in
                     ("validate_2d_static_render_request.py",
                      "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                      "inspect_2d_static_render_candidate.py",
                      "preview_2d_orthographic_framing.py",
                      "stage_2d_static_source.py"))
        paths.append("tests/rendering/run_2d_source_stage.py")
    if suite == "root-translation-bake":
        paths.extend(["skills/blender-bake-root-translation-copy/scripts/inspect_animation.py",
                      "skills/blender-bake-root-translation-copy/scripts/inspect_action_loop.py",
                      "skills/blender-bake-root-translation-copy/scripts/inspect_root_motion.py",
                      "skills/blender-bake-root-translation-copy/scripts/action_copy.py",
                      "skills/blender-bake-root-translation-copy/scripts/inspect_evaluated_root_motion.py",
                      "skills/blender-bake-root-translation-copy/scripts/bake_root_translation.py",
                      "tests/animation/run_root_translation_bake.py"])
    if suite == "retarget-action-composition":
        paths.extend(["skills/blender-compose-retarget-actions/scripts/inspect_animation.py",
                      "skills/blender-compose-retarget-actions/scripts/action_copy.py",
                      "skills/blender-compose-retarget-actions/scripts/inspect_evaluated_root_motion.py",
                      "skills/blender-compose-retarget-actions/scripts/compose_retarget_actions.py",
                      "tests/animation/run_retarget_action_composition.py"])
    if suite == "action-binding":
        paths.extend(["skills/blender-bind-action-empty/scripts/bind_action_empty.py",
                      "tests/animation/run_action_binding.py"])
    if suite == "action-replacement":
        paths.extend(["skills/blender-replace-current-action/scripts/bind_action_empty.py",
                      "skills/blender-replace-current-action/scripts/replace_action_current.py",
                      "tests/animation/run_action_replacement.py"])
    if suite == "retarget-readiness":
        paths.extend(["skills/blender-inspect-retarget-readiness/scripts/inspect_humanoid.py",
                      "skills/blender-inspect-retarget-readiness/scripts/inspect_animation.py",
                      "skills/blender-inspect-retarget-readiness/scripts/inspect_action_loop.py",
                      "skills/blender-inspect-retarget-readiness/scripts/inspect_retarget_readiness.py",
                      "tests/animation/run_retarget_readiness.py"])
    if suite == "aligned-retarget":
        paths.extend(["skills/blender-retarget-aligned-action-copy/scripts/inspect_humanoid.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/inspect_animation.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/inspect_action_loop.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/inspect_retarget_readiness.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/plan_action_copy.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/action_copy.py",
                      "skills/blender-retarget-aligned-action-copy/scripts/aligned_retarget_action.py",
                      "tests/animation/run_aligned_retarget.py"])
    if suite == "rotation-retarget-bake":
        paths.extend(["skills/blender-bake-rotation-retarget-copy/scripts/inspect_humanoid.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/inspect_animation.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/inspect_action_loop.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/inspect_retarget_readiness.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/plan_action_copy.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/action_copy.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/aligned_retarget_action.py",
                      "skills/blender-bake-rotation-retarget-copy/scripts/bake_rotation_retarget.py",
                      "tests/animation/run_rotation_retarget_bake.py"])
    if suite == "coplanar-experiment":
        paths.append("skills/blender-cleanup-loose-geometry/scripts/cleanup_loose.py")
        paths.append("scripts/check_affine_uv.py")
        paths.append("scripts/preview_coplanar.py")
        paths.append("scripts/apply_coplanar.py")
        paths.append("tests/static-mesh/run_coplanar_experiment.py")
    if suite == "coplanar-skill":
        paths.extend("skills/blender-simplify-coplanar/scripts/"+name for name in
                     ("state_helpers.py","check_affine_uv.py","preview_coplanar.py","apply_coplanar.py"))
        paths.append("tests/static-mesh/run_coplanar_experiment.py")
    if suite == "transform-preflight":
        paths.extend(["scripts/inspect_static_transform.py", "scripts/preview_scale_copy.py", "scripts/apply_scale_copy.py",
                      "tests/static-mesh/run_transform_preflight.py"])
    if suite == "scale-copy-skill":
        paths.extend("skills/blender-prepare-positive-scale/scripts/" + name for name in
                     ("inspect_static_transform.py", "preview_scale_copy.py", "apply_scale_copy.py"))
        paths.append("tests/static-mesh/run_transform_preflight.py")
    if suite == "pivot-preview":
        paths.extend(["scripts/inspect_static_transform.py", "scripts/preview_scale_copy.py",
                      "scripts/preview_pivot_copy.py",
                      "scripts/apply_pivot_copy.py", "tests/static-mesh/run_pivot_preview.py"])
    if suite == "pivot-skill":
        paths.extend("skills/blender-relocate-pivot-copy/scripts/" + name for name in
                     ("inspect_static_transform.py", "preview_scale_copy.py",
                      "preview_pivot_copy.py", "apply_pivot_copy.py"))
        paths.append("tests/static-mesh/run_pivot_preview.py")
    if suite == "export-context":
        paths.extend(["scripts/inspect_static_transform.py", "scripts/inspect_static_export_context.py",
                      "scripts/inspect_static_fbx_candidate.py",
                      "tests/static-mesh/run_export_context.py"])
    if suite == "fbx-probe":
        paths.extend(["scripts/promote_export_artifact.py",
                      "tests/static-mesh/run_fbx_export_probe.py"])
    if suite == "fbx-staged":
        paths.extend(["scripts/inspect_static_transform.py",
                      "scripts/inspect_static_export_context.py",
                      "scripts/inspect_static_fbx_candidate.py",
                      "scripts/promote_export_artifact.py",
                      "scripts/export_static_fbx_staged.py",
                      "tests/static-mesh/run_fbx_staged_export.py"])
    if suite == "fbx-staged-skill":
        paths.extend("skills/blender-export-static-fbx/scripts/" + name for name in
                     ("validate_static_fbx_request.py", "inspect_static_transform.py",
                      "inspect_static_export_context.py", "inspect_static_fbx_candidate.py",
                      "promote_export_artifact.py", "export_static_fbx_staged.py"))
        paths.append("tests/static-mesh/run_fbx_staged_export.py")
    hashes = {}
    chunks = ["_gai_test_namespace = {}"]
    checked_installed = {}
    for relative in paths:
        if installed_skills_dir is not None and relative.startswith("skills/"):
            _, skill_name, resource = relative.split("/", 2)
            installed = installed_skills_dir / skill_name
            if skill_name not in checked_installed:
                checked_installed[skill_name] = set(skill_files(installed))
            helper = installed / resource
            if helper not in checked_installed[skill_name]:
                raise ValueError(f"Installed helper is missing: {helper}")
            source = helper.read_text(encoding="utf-8-sig")
        elif bundle_dir is not None and relative.startswith("skills/"):
            _, skill_name, resource = relative.split("/", 2)
            with zipfile.ZipFile(bundle_dir / f"{skill_name}.zip") as archive:
                source = archive.read(f"{skill_name}/{resource}").decode("utf-8-sig")
        else:
            source = (root / relative).read_text(encoding="utf-8-sig")
        compile(source, relative, "exec")
        hashes[relative] = hashlib.sha256(source.encode()).hexdigest()
        chunks.append(f"exec(compile({source!r}, {relative!r}, 'exec'), _gai_test_namespace, _gai_test_namespace)")
    chunks.append("_gai_test_results = {}")
    if suite in {"inspection", "all"}:
        chunks.append("_gai_test_results['inspection'] = _gai_test_namespace['run_inspection_tests']()")
    if suite in {"static-mesh", "all"}:
        chunks.append("_gai_test_results['static-mesh'] = _gai_test_namespace['run_diagnostics_tests']()")
    if suite in {"loose-cleanup", "all"}:
        chunks.append("_gai_test_results['loose-cleanup'] = _gai_test_namespace['run_loose_cleanup_tests']()")
    if suite == "humanoid-inspection":
        chunks.append("_gai_test_results['humanoid-inspection'] = _gai_test_namespace['run_humanoid_inspection_tests']()")
    if suite == "mixamo-preflight":
        chunks.append("_gai_test_results['mixamo-preflight'] = _gai_test_namespace['run_mixamo_preflight_tests']()")
    if suite == "animation-inventory":
        chunks.append("_gai_test_results['animation-inventory'] = _gai_test_namespace['run_animation_inventory_tests']()")
    if suite == "action-copy-plan":
        chunks.append("_gai_test_results['action-copy-plan'] = _gai_test_namespace['run_action_copy_plan_tests']()")
    if suite == "action-copy":
        chunks.append("_gai_test_results['action-copy'] = _gai_test_namespace['run_action_copy_apply_tests']()")
    if suite == "action-range-extraction":
        chunks.append("_gai_test_results['action-range-extraction'] = _gai_test_namespace['run_action_range_extraction_tests']()")
    if suite == "action-loop":
        chunks.append("_gai_test_results['action-loop'] = _gai_test_namespace['run_action_loop_inspection_tests']()")
    if suite == "root-motion":
        chunks.append("_gai_test_results['root-motion'] = _gai_test_namespace['run_root_motion_inspection_tests']()")
    if suite == "evaluated-root-motion":
        chunks.append("_gai_test_results['evaluated-root-motion'] = _gai_test_namespace['run_evaluated_root_motion_tests']()")
    if suite == "evaluated-pose-loop":
        chunks.append("_gai_test_results['evaluated-pose-loop'] = _gai_test_namespace['run_evaluated_pose_loop_tests']()")
    if suite == "subframe-pose-probe":
        chunks.append("_gai_test_results['subframe-pose-probe'] = _gai_test_namespace['run_subframe_pose_probe']()")
    if suite == "2d-render-capabilities":
        chunks.append("_gai_test_results['2d-render-capabilities'] = _gai_test_namespace['run_2d_render_capability_tests']()")
    if suite == "2d-render-candidate":
        chunks.append(f"_gai_test_results['2d-render-candidate'] = _gai_test_namespace['run_2d_static_render_candidate_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite == "2d-action-sequence-candidate":
        chunks.append(f"_gai_test_results['2d-action-sequence-candidate'] = _gai_test_namespace['run_2d_action_sequence_candidate_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite == "2d-action-sequence-skill":
        chunks.append(f"_gai_test_results['2d-action-sequence-skill'] = _gai_test_namespace['run_2d_action_sequence_candidate_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite == "2d-source-stage":
        chunks.append(f"_gai_test_results['2d-source-stage'] = _gai_test_namespace['run_2d_source_stage_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite == "2d-static-pixel-skill":
        chunks.append(f"_gai_test_results['2d-static-pixel-skill'] = _gai_test_namespace['run_2d_source_stage_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite == "root-translation-bake":
        chunks.append("_gai_test_results['root-translation-bake'] = _gai_test_namespace['run_root_translation_bake_tests']()")
    if suite == "retarget-action-composition":
        chunks.append("_gai_test_results['retarget-action-composition'] = _gai_test_namespace['run_retarget_action_composition_tests']()")
    if suite == "action-binding":
        chunks.append("_gai_test_results['action-binding'] = _gai_test_namespace['run_action_binding_tests']()")
    if suite == "action-replacement":
        chunks.append("_gai_test_results['action-replacement'] = _gai_test_namespace['run_action_replacement_tests']()")
    if suite == "retarget-readiness":
        chunks.append("_gai_test_results['retarget-readiness'] = _gai_test_namespace['run_retarget_readiness_tests']()")
    if suite == "aligned-retarget":
        chunks.append("_gai_test_results['aligned-retarget'] = _gai_test_namespace['run_aligned_retarget_tests']()")
    if suite == "rotation-retarget-bake":
        chunks.append("_gai_test_results['rotation-retarget-bake'] = _gai_test_namespace['run_rotation_retarget_bake_tests']()")
    if suite in {"coplanar-experiment","coplanar-skill"}:
        chunks.append("_gai_test_results['coplanar-experiment'] = _gai_test_namespace['run_coplanar_experiment']()")
        chunks.append("_gai_test_results['coplanar-failures'] = _gai_test_namespace['run_coplanar_failure_tests']()")
    if suite in {"transform-preflight", "scale-copy-skill"}:
        chunks.append("_gai_test_results['transform-preflight'] = _gai_test_namespace['run_transform_preflight_tests']()")
    if suite in {"pivot-preview", "pivot-skill"}:
        chunks.append("_gai_test_results['pivot-preview'] = _gai_test_namespace['run_pivot_preview_tests']()")
    if suite == "export-context":
        chunks.append("_gai_test_results['export-context'] = _gai_test_namespace['run_export_context_tests']()")
    if suite == "fbx-probe":
        chunks.append(f"_gai_test_results['fbx-probe'] = _gai_test_namespace['run_fbx_export_probe'](artifact_root={str(root / '.local' / 'validation')!r})")
    if suite in {"fbx-staged", "fbx-staged-skill"}:
        chunks.append(f"_gai_test_results['fbx-staged'] = _gai_test_namespace['run_fbx_staged_export_tests'](artifact_root={str(root / '.local' / 'validation')!r})")
    chunks.append("print(__import__('json').dumps(_gai_test_results, allow_nan=False))")
    code = "\n".join(chunks)
    compile(code, "<Blender-check-payload>", "exec")
    return {"schema": "gameassetai.blender-test-payload.v1", "suite": suite,
            "helper_origin": ("installed-skills" if installed_skills_dir is not None else
                              "source-bundles" if bundle_dir is not None else "repository"),
            "source_sha256": hashes, "code": code}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("inspection", "static-mesh", "loose-cleanup", "humanoid-inspection", "mixamo-preflight", "animation-inventory", "action-copy-plan", "action-copy", "action-range-extraction", "action-loop", "root-motion", "evaluated-root-motion", "evaluated-pose-loop", "subframe-pose-probe", "2d-render-capabilities", "2d-render-candidate", "2d-action-sequence-candidate", "2d-action-sequence-skill", "2d-source-stage", "2d-static-pixel-skill", "root-translation-bake", "retarget-action-composition", "action-binding", "action-replacement", "retarget-readiness", "aligned-retarget", "rotation-retarget-bake", "coplanar-experiment", "coplanar-skill", "transform-preflight", "scale-copy-skill", "pivot-preview", "pivot-skill", "export-context", "fbx-probe", "fbx-staged", "fbx-staged-skill", "all"), default="all")
    origin = parser.add_mutually_exclusive_group()
    origin.add_argument("--bundle-dir", type=Path, help="Load helpers from named source ZIPs; tests remain repository sources")
    origin.add_argument("--installed-skills-dir", type=Path, help="Read helpers from an explicit installation; no install or writes, tests remain repository sources")
    args = parser.parse_args()
    try:
        payload = build_payload(Path(__file__).resolve().parents[1], args.suite, args.bundle_dir,
                                installed_skills_dir=args.installed_skills_dir)
    except (OSError, UnicodeError, ValueError, SyntaxError, KeyError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Payload preparation failed: {exc}\n")
    print(json.dumps(payload, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
