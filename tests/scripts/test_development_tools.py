"""Offline invariants for payload preparation and portable source bundles."""
import json
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from package_skill import package_skill, skill_files
from prepare_blender_check import build_payload
from deploy_skill import deploy_skill
from update_skill import apply_update, plan_update, restore_update
from validate_skill_deployment import validate_skill_deployment


def _hashes(root):
    import hashlib
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in skill_files(root)}


class DevelopmentToolsTests(unittest.TestCase):
    def test_coplanar_packaged_helpers_match_development_sources(self):
        skill=REPO/"skills"/"blender-simplify-coplanar"/"scripts"
        for name in ("check_affine_uv.py","preview_coplanar.py","apply_coplanar.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())
        cleanup=(REPO/"skills"/"blender-cleanup-loose-geometry"/"scripts"/"cleanup_loose.py").read_text(encoding="utf-8")
        expected=cleanup[cleanup.index("def _loose_surface"):cleanup.index("def _loose_write")].strip()
        packaged=(skill/"state_helpers.py").read_text(encoding="utf-8")
        self.assertEqual(expected,packaged[packaged.index("def _loose_surface"):].strip())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gameassetai-tools-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.skill = self.base / "blender-inspect-asset"
        shutil.copytree(REPO / "skills" / self.skill.name, self.skill)

    def test_payload_suites_compile_and_track_sources(self):
        for suite, count in (("inspection",2),("static-mesh",4),("loose-cleanup",4),("humanoid-inspection",4),("mixamo-preflight",5),("animation-inventory",4),("action-copy-plan",5),("action-copy",6),("action-range-extraction",6),("action-loop",5),("root-motion",6),("evaluated-root-motion",8),("evaluated-pose-loop",9),("subframe-pose-probe",3),("2d-render-capabilities",4),("2d-render-candidate",6),("2d-action-sequence-candidate",9),("2d-action-sequence-skill",13),("2d-source-stage",7),("2d-static-pixel-skill",9),("root-translation-bake",9),("retarget-action-composition",7),("action-binding",4),("action-replacement",5),("retarget-readiness",7),("aligned-retarget",10),("rotation-retarget-bake",11),("coplanar-experiment",7),("coplanar-skill",7),("transform-preflight",6),("scale-copy-skill",6),("pivot-preview",7),("pivot-skill",7),("export-context",6),("fbx-probe",4),("fbx-staged",8),("fbx-staged-skill",9),("all",6)):
            payload = build_payload(REPO, suite)
            self.assertEqual(count, len(payload["source_sha256"]))
            compile(payload["code"], "<payload>", "exec")
            self.assertEqual(payload, json.loads(json.dumps(payload)))

    def test_unknown_suite_rejected(self):
        with self.assertRaises(ValueError):
            build_payload(REPO, "unknown")

    def test_scale_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-prepare-positive-scale"/"scripts"
        for name in ("inspect_static_transform.py", "preview_scale_copy.py", "apply_scale_copy.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_pivot_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-relocate-pivot-copy"/"scripts"
        for name in ("inspect_static_transform.py", "preview_scale_copy.py",
                     "preview_pivot_copy.py", "apply_pivot_copy.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_static_fbx_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-export-static-fbx"/"scripts"
        for name in ("validate_static_fbx_request.py", "inspect_static_transform.py",
                     "inspect_static_export_context.py", "inspect_static_fbx_candidate.py",
                     "promote_export_artifact.py", "export_static_fbx_staged.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_static_pixel_png_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-static-pixel-png"/"scripts"
        for name in ("validate_2d_static_render_request.py",
                     "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                     "inspect_2d_static_render_candidate.py",
                     "preview_2d_orthographic_framing.py",
                     "stage_2d_static_source.py", "build_2d_staged_render_job.py",
                     "quantize_rgba.py", "build_2d_render_receipt.py",
                     "render_2d_staged_source.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_action_sequence_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-action-png-sequence"/"scripts"
        for name in ("validate_2d_static_render_request.py",
                     "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                     "validate_2d_action_sequence_request.py",
                     "inspect_2d_action_sequence_candidate.py",
                     "preview_2d_action_sequence_framing.py",
                     "stage_2d_action_sequence_source.py",
                     "build_2d_action_sequence_job.py", "quantize_rgba.py",
                     "render_2d_action_sequence.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_sprite_sheet_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"assemble-png-sprite-sheet"/"scripts"
        for name in ("validate_2d_static_render_request.py",
                     "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                     "validate_2d_sprite_sheet_request.py", "quantize_rgba.py",
                     "assemble_2d_sprite_sheet.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_2d_batch_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-2d-batch"/"scripts"
        for name in ("validate_2d_static_render_request.py",
                     "extract_2d_profile_preset.py", "resolve_2d_profile_preset.py",
                     "inspect_2d_static_render_candidate.py",
                     "preview_2d_orthographic_framing.py", "stage_2d_static_source.py",
                     "build_2d_staged_render_job.py", "quantize_rgba.py",
                     "build_2d_render_receipt.py", "render_2d_staged_source.py",
                     "validate_2d_action_sequence_request.py",
                     "inspect_2d_action_sequence_candidate.py",
                     "preview_2d_action_sequence_framing.py",
                     "stage_2d_action_sequence_source.py", "build_2d_action_sequence_job.py",
                     "render_2d_action_sequence.py", "validate_2d_render_batch_request.py",
                     "build_2d_render_batch_job.py", "run_2d_render_batch.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_impostor_bundle_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-impostor-bundle"/"scripts"
        for name in (
                "validate_2d_static_render_request.py",
                "inspect_2d_static_render_candidate.py",
                "preview_2d_orthographic_framing.py",
                "stage_2d_static_source.py", "build_2d_staged_render_job.py",
                "render_2d_staged_source.py",
                "validate_2d_normal_pass_request.py",
                "inspect_2d_normal_pass_candidate.py",
                "preview_2d_normal_pass_framing.py",
                "stage_2d_normal_pass_source.py", "build_2d_normal_pass_job.py",
                "render_2d_normal_pass.py",
                "validate_2d_depth_pass_request.py",
                "inspect_2d_depth_pass_candidate.py",
                "preview_2d_depth_pass_framing.py",
                "stage_2d_depth_pass_source.py", "build_2d_depth_pass_job.py",
                "render_2d_depth_pass.py", "quantize_rgba.py",
                "build_2d_render_receipt.py",
                "validate_2d_impostor_bundle_request.py",
                "preview_2d_impostor_shared_framing.py",
                "validate_2d_impostor_result_manifest.py",
                "build_2d_impostor_bundle_job.py", "run_2d_impostor_bundle.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_static_collider_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-inspect-static-colliders"/"scripts"
        for name in ("validate_static_collider_request.py",
                     "inspect_static_collider_candidate.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_static_lod_chain_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-inspect-static-lod-chain"/"scripts"
        for name in ("validate_static_lod_chain_request.py",
                     "inspect_static_lod_chain_candidate.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_static_lod_copy_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-create-static-lod-copy"/"scripts"
        for name in ("validate_static_lod_copy_request.py", "preview_static_lod_copy.py",
                     "apply_static_lod_copy.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_silhouette_mask_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"derive-png-silhouette-mask"/"scripts"
        for name in ("validate_2d_silhouette_mask_request.py",
                     "derive_2d_silhouette_mask.py", "quantize_rgba.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_material_mask_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-material-mask-png"/"scripts"
        for name in ("validate_2d_material_mask_request.py",
                     "inspect_2d_material_mask_candidate.py",
                     "preview_2d_material_mask_framing.py",
                     "stage_2d_material_mask_source.py",
                     "build_2d_material_mask_job.py", "render_2d_material_mask.py",
                     "quantize_rgba.py", "build_2d_render_receipt.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_object_mask_packaged_helpers_match_development_sources(self):
        skill = REPO/"skills"/"blender-render-object-mask-png"/"scripts"
        for name in ("validate_2d_object_mask_request.py",
                     "inspect_2d_object_mask_candidate.py",
                     "preview_2d_object_mask_framing.py",
                     "stage_2d_object_mask_source.py", "build_2d_object_mask_job.py",
                     "render_2d_object_mask.py", "quantize_rgba.py",
                     "build_2d_render_receipt.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (skill/name).read_text(encoding="utf-8").strip())

    def test_humanoid_packaged_helper_matches_development_source(self):
        self.assertEqual((REPO/"scripts"/"inspect_humanoid.py").read_text(encoding="utf-8").strip(),
                         (REPO/"skills"/"blender-inspect-humanoid"/"scripts"/
                          "inspect_humanoid.py").read_text(encoding="utf-8").strip())

    def test_mixamo_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-mixamo-preflight"/"scripts"
        for name in ("inspect_humanoid.py", "inspect_mixamo_preflight.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_animation_packaged_helper_matches_development_source(self):
        self.assertEqual((REPO/"scripts"/"inspect_animation.py").read_text(encoding="utf-8").strip(),
                         (REPO/"skills"/"blender-inspect-animation"/"scripts"/
                          "inspect_animation.py").read_text(encoding="utf-8").strip())

    def test_action_copy_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-copy-action"/"scripts"
        for name in ("inspect_animation.py", "plan_action_copy.py", "action_copy.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_action_range_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-extract-action-range"/"scripts"
        for name in ("inspect_animation.py", "action_copy.py", "extract_action_range.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_action_loop_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-animation-loop"/"scripts"
        for name in ("inspect_animation.py", "inspect_action_loop.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_root_motion_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-root-motion"/"scripts"
        for name in ("inspect_animation.py", "inspect_action_loop.py", "inspect_root_motion.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_evaluated_root_motion_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-evaluated-root-motion"/"scripts"
        for name in ("inspect_animation.py", "inspect_action_loop.py", "inspect_root_motion.py",
                     "action_copy.py", "inspect_evaluated_root_motion.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_evaluated_pose_loop_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-evaluated-pose-loop"/"scripts"
        for name in ("inspect_animation.py", "inspect_action_loop.py", "inspect_root_motion.py",
                     "action_copy.py", "inspect_evaluated_root_motion.py",
                     "inspect_evaluated_pose_loop.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_root_translation_bake_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-bake-root-translation-copy"/"scripts"
        for name in ("inspect_animation.py", "inspect_action_loop.py", "inspect_root_motion.py",
                     "action_copy.py", "inspect_evaluated_root_motion.py",
                     "bake_root_translation.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_retarget_action_composition_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-compose-retarget-actions"/"scripts"
        for name in ("inspect_animation.py", "action_copy.py",
                     "inspect_evaluated_root_motion.py", "compose_retarget_actions.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_action_binding_packaged_helper_matches_development_source(self):
        self.assertEqual((REPO/"scripts"/"bind_action_empty.py").read_text(encoding="utf-8").strip(),
                         (REPO/"skills"/"blender-bind-action-empty"/"scripts"/
                          "bind_action_empty.py").read_text(encoding="utf-8").strip())

    def test_action_replacement_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-replace-current-action"/"scripts"
        for name in ("bind_action_empty.py", "replace_action_current.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_retarget_readiness_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-inspect-retarget-readiness"/"scripts"
        for name in ("inspect_humanoid.py", "inspect_animation.py",
                     "inspect_action_loop.py", "inspect_retarget_readiness.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_aligned_retarget_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-retarget-aligned-action-copy"/"scripts"
        for name in ("inspect_humanoid.py", "inspect_animation.py",
                     "inspect_action_loop.py", "inspect_retarget_readiness.py",
                     "plan_action_copy.py", "action_copy.py",
                     "aligned_retarget_action.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_rotation_retarget_packaged_helpers_match_development_sources(self):
        packaged = REPO/"skills"/"blender-bake-rotation-retarget-copy"/"scripts"
        for name in ("inspect_humanoid.py", "inspect_animation.py",
                     "inspect_action_loop.py", "inspect_retarget_readiness.py",
                     "plan_action_copy.py", "action_copy.py",
                     "aligned_retarget_action.py", "bake_rotation_retarget.py"):
            self.assertEqual((REPO/"scripts"/name).read_text(encoding="utf-8").strip(),
                             (packaged/name).read_text(encoding="utf-8").strip())

    def test_installed_payload_reads_exact_helpers_without_writes(self):
        installed = self.base/"installed"
        deployment = Path(deploy_skill(self.skill, installed)["destination"])
        helper = deployment/"scripts"/"inspect_asset.py"
        helper.write_bytes(helper.read_bytes() + b"\n# installation-specific marker\n")
        before = {p.relative_to(deployment): p.read_bytes() for p in skill_files(deployment)}
        payload = build_payload(REPO, "inspection", installed_skills_dir=installed)
        self.assertEqual("installed-skills", payload["helper_origin"])
        self.assertIn("installation-specific marker", payload["code"])
        self.assertNotEqual(build_payload(REPO, "inspection")["source_sha256"], payload["source_sha256"])
        self.assertEqual(before, {p.relative_to(deployment): p.read_bytes() for p in skill_files(deployment)})

    def test_missing_installed_skill_never_falls_back(self):
        with self.assertRaises(ValueError):
            build_payload(REPO, "inspection", installed_skills_dir=self.base/"missing")

    def test_missing_installed_helper_never_falls_back(self):
        installed = self.base/"installed"
        deployment = Path(deploy_skill(self.skill, installed)["destination"])
        (deployment/"scripts"/"inspect_asset.py").unlink()
        with self.assertRaises(ValueError):
            build_payload(REPO, "inspection", installed_skills_dir=installed)

    def test_installed_and_bundle_origins_cannot_mix(self):
        with self.assertRaises(ValueError):
            build_payload(REPO, "inspection", self.base, installed_skills_dir=self.base)

    def test_linked_installed_ancestor_rejected(self):
        installed = self.base/"installed"
        with patch("prepare_blender_check.is_link", side_effect=lambda p: p == installed), self.assertRaises(ValueError):
            build_payload(REPO, "inspection", installed_skills_dir=installed)

    def test_installed_payload_cli_from_other_working_directory(self):
        installed = self.base/"installed"
        deploy_skill(self.skill, installed)
        result = subprocess.run([sys.executable, "-B", str(REPO/"scripts"/"prepare_blender_check.py"),
                                 "--suite", "inspection", "--installed-skills-dir", str(installed)],
                                cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("installed-skills", json.loads(result.stdout)["helper_origin"])

    def test_payload_imports_visible_to_functions_and_future_imports_isolated(self):
        def synthetic_source(path, **kwargs):
            if path.name=="inspect_asset.py":
                return "from __future__ import annotations\nimport math\n"
            if path.name=="run_inspection.py":
                return "def run_inspection_tests():\n    return math.sqrt(4)\n"
            if path.name=="run_diagnostics.py":
                return "def run_diagnostics_tests():\n    return math.sqrt(9)\n"
            if path.name=="run_loose_cleanup.py":
                return "def run_loose_cleanup_tests():\n    return math.sqrt(16)\n"
            return "from __future__ import annotations\nimport math\n"
        with patch.object(Path,"read_text",synthetic_source):
            payload=build_payload(REPO,"all")
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(payload["code"],{})
        self.assertEqual({"inspection":2.0,"static-mesh":3.0,"loose-cleanup":4.0},json.loads(output.getvalue()))

    def test_payload_cli_from_other_working_directory(self):
        result = subprocess.run([sys.executable,"-B",str(REPO/"scripts"/"prepare_blender_check.py"),
                                 "--suite","inspection"], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("inspection", json.loads(result.stdout)["suite"])

    def test_source_bundle_preserves_bytes_and_is_reproducible(self):
        a, b = self.base/"a.zip", self.base/"b.zip"
        first, second = package_skill(self.skill,a), package_skill(self.skill,b)
        self.assertEqual(first["sha256"], second["sha256"])
        with zipfile.ZipFile(a) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual({f"{self.skill.name}/{p.relative_to(self.skill).as_posix()}" for p in skill_files(self.skill)},
                             set(archive.namelist()))
            for p in skill_files(self.skill):
                self.assertEqual(p.read_bytes(), archive.read(f"{self.skill.name}/{p.relative_to(self.skill).as_posix()}"))

    def test_existing_archive_never_overwritten(self):
        target = self.base/"keep.zip"
        target.write_bytes(b"keep")
        with self.assertRaises(ValueError):
            package_skill(self.skill,target)
        self.assertEqual(b"keep",target.read_bytes())

    def test_archive_inside_source_rejected(self):
        target = self.skill/"self.zip"
        with self.assertRaises(ValueError):
            package_skill(self.skill,target)
        self.assertFalse(target.exists())

    def test_missing_entrypoint_rejected(self):
        (self.skill/"SKILL.md").unlink()
        with self.assertRaises(ValueError):
            skill_files(self.skill)

    def test_bad_python_resource_rejected_before_output(self):
        (self.skill/"scripts"/"broken.py").write_text("def (")
        target=self.base/"bad.zip"
        with self.assertRaises(SyntaxError):
            package_skill(self.skill,target)
        self.assertFalse(target.exists())

    def test_incremental_skill_contract_rejects_missing_sections(self):
        entry = self.skill / "SKILL.md"
        entry.write_text(
            "---\nname: blender-inspect-asset\ndescription: test\nmetadata:\n"
            "  contract: gameassetai.skill-contract.v1\n"
            "  requirements: REQ-SAFE\n  evidence: tested\n"
            "  external-dependencies: none\n---\n# Test\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "missing sections"):
            skill_files(self.skill)

    def test_character_skill_uses_incremental_contract(self):
        files = skill_files(REPO / "skills" / "blender-create-character-base")
        self.assertIn(REPO / "skills" / "blender-create-character-base" / "SKILL.md", files)

    def test_cache_files_not_bundled(self):
        cache=self.skill/"scripts"/"__pycache__"
        cache.mkdir()
        (cache/"cache.pyc").write_bytes(b"unused")
        self.assertFalse(any(p.suffix==".pyc" for p in skill_files(self.skill)))

    def test_bundle_payload_matches_repository_helpers(self):
        for name in ("blender-inspect-asset", "blender-validate-static-mesh", "blender-cleanup-loose-geometry"):
            package_skill(REPO/"skills"/name, self.base/f"{name}.zip")
        repo, bundle = build_payload(REPO,"all"), build_payload(REPO,"all",self.base)
        self.assertEqual(repo["source_sha256"],bundle["source_sha256"])
        self.assertEqual(repo["code"],bundle["code"])
        self.assertEqual("source-bundles",bundle["helper_origin"])

    def test_missing_bundle_does_not_fall_back_to_repository(self):
        with self.assertRaises(FileNotFoundError):
            build_payload(REPO,"inspection",self.base)

    def test_missing_bundle_helper_does_not_fall_back(self):
        with zipfile.ZipFile(self.base/f"{self.skill.name}.zip","w") as archive:
            archive.writestr("unrelated.txt", "not a helper")
        with self.assertRaises(KeyError):
            build_payload(REPO,"inspection",self.base)

    def test_deployment_bytes_and_nested_resources(self):
        nested=self.skill/"references"/"nested"
        nested.mkdir(parents=True)
        (nested/"note.md").write_text("test")
        result=deploy_skill(self.skill,self.base/"workspace"/".agents"/"skills")
        destination=Path(result["destination"])
        self.assertEqual("not_verified",result["client_discovery"])
        for path in skill_files(self.skill):
            self.assertEqual(path.read_bytes(),(destination/path.relative_to(self.skill)).read_bytes())

    def test_deployment_never_overwrites_existing_folder(self):
        deploy_skill(self.skill,self.base/"installed")
        entry=self.base/"installed"/self.skill.name/"SKILL.md"
        entry.write_text("personal")
        with self.assertRaises(ValueError):
            deploy_skill(self.skill,self.base/"installed")
        self.assertEqual("personal",entry.read_text())

    def test_deployment_overlap_rejected(self):
        with self.assertRaises(ValueError):
            deploy_skill(self.skill,self.skill)

    def test_linked_deployment_ancestor_rejected_before_changes(self):
        destination=self.base/"installed"
        with patch("deploy_skill.is_link",side_effect=lambda p: p==destination), self.assertRaises(ValueError):
            deploy_skill(self.skill,destination)
        self.assertFalse(destination.exists())

    def test_deployment_cli_from_other_directory(self):
        destination=self.base/"installed"
        result=subprocess.run([sys.executable,"-B",str(REPO/"scripts"/"deploy_skill.py"),
                               str(self.skill),"--skills-dir",str(destination)],
                              cwd=self.base,capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual("not_verified",json.loads(result.stdout)["client_discovery"])

    def test_failed_new_deployment_cleans_only_owned_paths(self):
        original=Path.open
        def denied(path,*args,**kwargs):
            if path.name=="inspect_asset.py" and args and args[0]=="xb":
                raise OSError("simulated output failure")
            return original(path,*args,**kwargs)
        with patch.object(Path,"open",denied), self.assertRaises(OSError):
            deploy_skill(self.skill,self.base/"installed")
        self.assertFalse((self.base/"installed"/self.skill.name).exists())

    def test_deployment_readback_failure_preserves_sibling(self):
        installed = self.base/"installed"
        sibling = installed/"personal-skill"
        sibling.mkdir(parents=True)
        keep = sibling/"SKILL.md"
        keep.write_bytes(b"personal bytes\r\n")
        original = Path.read_bytes
        def corrupted(path):
            contents = original(path)
            if installed in path.parents and path.name == "inspect_asset.py":
                return contents + b"corrupted readback"
            return contents
        with patch.object(Path, "read_bytes", corrupted), self.assertRaises(OSError):
            deploy_skill(self.skill, installed)
        self.assertFalse((installed/self.skill.name).exists())
        self.assertEqual(b"personal bytes\r\n", keep.read_bytes())
        self.assertEqual(["personal-skill"], sorted(p.name for p in installed.iterdir()))

    def test_deployment_partial_write_failure_rolls_back(self):
        installed = self.base/"installed"
        original = Path.open
        class InterruptedWrite:
            def __init__(self, handle):
                self.handle = handle
            def __enter__(self):
                self.handle.__enter__()
                return self
            def __exit__(self, *args):
                return self.handle.__exit__(*args)
            def write(self, contents):
                self.handle.write(contents[:7])
                raise OSError("simulated partial write")
        def interrupted(path, *args, **kwargs):
            handle = original(path, *args, **kwargs)
            if path.name == "inspect_asset.py" and args and args[0] == "xb":
                return InterruptedWrite(handle)
            return handle
        source_before = {p.relative_to(self.skill): p.read_bytes() for p in skill_files(self.skill)}
        with patch.object(Path, "open", interrupted), self.assertRaises(OSError):
            deploy_skill(self.skill, installed)
        self.assertFalse((installed/self.skill.name).exists())
        self.assertEqual(source_before, {p.relative_to(self.skill): p.read_bytes() for p in skill_files(self.skill)})

    def _update_fixture(self):
        installed_root = self.base/"installed"
        installed = Path(deploy_skill(self.skill, installed_root)["destination"])
        old = {p.relative_to(installed).as_posix(): p.read_bytes() for p in skill_files(installed)}
        (self.skill/"SKILL.md").write_bytes((self.skill/"SKILL.md").read_bytes()+b"\nUpdate fixture\n")
        backup = self.base/"recovery"/self.skill.name
        backup.parent.mkdir()
        return installed, backup, old

    def test_update_plan_is_read_only_and_hash_bound(self):
        installed, backup, old = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        self.assertEqual("update_needed", plan["status"])
        self.assertEqual("not_verified", plan["client_discovery"])
        self.assertFalse(backup.exists())
        self.assertEqual(old, {p.relative_to(installed).as_posix():p.read_bytes()
                               for p in skill_files(installed)})

    def test_update_apply_retains_exact_backup(self):
        installed, backup, old = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        result = apply_update(plan)
        self.assertEqual("updated", result["status"])
        self.assertEqual(plan["source_sha256"], _hashes(installed))
        self.assertEqual(plan["installed_sha256"], _hashes(backup))
        self.assertEqual(old, {p.relative_to(backup).as_posix():p.read_bytes()
                               for p in skill_files(backup)})

    def test_update_refuses_source_or_install_drift(self):
        installed, backup, _ = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        (installed/"SKILL.md").write_bytes((installed/"SKILL.md").read_bytes()+b"drift")
        with self.assertRaises(ValueError):
            apply_update(plan)
        self.assertFalse(backup.exists())
        self.assertFalse(any(p.name.startswith("."+self.skill.name+".gameassetai-stage-")
                             for p in installed.parent.iterdir()))

    def test_update_refuses_existing_backup(self):
        installed, backup, _ = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        backup.mkdir()
        (backup/"keep.txt").write_text("keep")
        with self.assertRaises(ValueError):
            apply_update(plan)
        self.assertEqual("keep", (backup/"keep.txt").read_text())

    def test_update_promotion_failure_restores_original(self):
        installed, backup, old = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        original = Path.rename
        def fail_stage(path, target):
            if path.name.startswith("."+self.skill.name+".gameassetai-stage-"):
                raise OSError("simulated promotion failure")
            return original(path, target)
        with patch.object(Path, "rename", fail_stage), self.assertRaises(OSError):
            apply_update(plan)
        self.assertFalse(backup.exists())
        self.assertEqual(old, {p.relative_to(installed).as_posix():p.read_bytes()
                               for p in skill_files(installed)})
        self.assertFalse(any(p.name.startswith("."+self.skill.name+".gameassetai-stage-")
                             for p in installed.parent.iterdir()))

    def test_update_restore_keeps_replaced_new_version(self):
        installed, backup, _ = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        apply_update(plan)
        replaced = self.base/"replaced"/self.skill.name
        replaced.parent.mkdir()
        result = restore_update(plan, replaced)
        self.assertEqual("restored", result["status"])
        self.assertEqual(plan["installed_sha256"], _hashes(installed))
        self.assertEqual(plan["source_sha256"], _hashes(replaced))
        self.assertFalse(backup.exists())

    def test_update_restore_refuses_changed_current_or_backup(self):
        installed, backup, _ = self._update_fixture()
        plan = plan_update(self.skill, installed, backup)
        apply_update(plan)
        (backup/"SKILL.md").write_bytes((backup/"SKILL.md").read_bytes()+b"changed")
        replaced = self.base/"replaced"/self.skill.name
        replaced.parent.mkdir()
        with self.assertRaises(ValueError):
            restore_update(plan, replaced)
        self.assertFalse(replaced.exists())

    def test_aligned_update_is_noop_without_backup(self):
        installed_root = self.base/"installed"
        installed = Path(deploy_skill(self.skill, installed_root)["destination"])
        backup = self.base/"recovery"/self.skill.name
        backup.parent.mkdir()
        plan = plan_update(self.skill, installed, backup)
        self.assertEqual("already_aligned", plan["status"])
        self.assertEqual("already_aligned", apply_update(plan)["status"])
        self.assertFalse(backup.exists())

    def test_update_cli_plan_apply_restore_from_other_directory(self):
        installed, backup, _ = self._update_fixture()
        script = REPO/"scripts"/"update_skill.py"
        planned = subprocess.run(
            [sys.executable, "-B", str(script), "plan", str(self.skill), str(installed),
             "--backup", str(backup)], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, planned.returncode, planned.stderr)
        plan = json.loads(planned.stdout)
        plan_file = self.base/"update-plan.json"
        plan_file.write_text(json.dumps(plan), encoding="utf-8")
        applied = subprocess.run([sys.executable, "-B", str(script), "apply", str(plan_file)],
                                 cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, applied.returncode, applied.stderr)
        self.assertEqual("updated", json.loads(applied.stdout)["status"])
        replaced = self.base/"replaced"/self.skill.name
        replaced.parent.mkdir()
        restored = subprocess.run(
            [sys.executable, "-B", str(script), "restore", str(plan_file),
             "--replaced", str(replaced)], cwd=self.base, capture_output=True, text=True)
        self.assertEqual(0, restored.returncode, restored.stderr)
        self.assertEqual("restored", json.loads(restored.stdout)["status"])

    def test_aligned_deployment_does_not_imply_discovery(self):
        destination=Path(deploy_skill(self.skill,self.base/"installed")["destination"])
        report=validate_skill_deployment(self.skill,destination)
        self.assertEqual("aligned",report["status"])
        self.assertEqual("not_verified",report["client_discovery"])

    def test_changed_missing_extra_detected_without_writes(self):
        destination=Path(deploy_skill(self.skill,self.base/"installed")["destination"])
        (destination/"SKILL.md").write_text((destination/"SKILL.md").read_text()+"\nPersonal change\n")
        (destination/"scripts"/"inspect_asset.py").unlink()
        (destination/"personal.md").write_text("keep")
        report=validate_skill_deployment(self.skill,destination)
        self.assertEqual("drift",report["status"])
        self.assertEqual(["SKILL.md"],report["changed"])
        self.assertEqual(["scripts/inspect_asset.py"],report["missing"])
        self.assertEqual(["personal.md"],report["extra"])
        self.assertEqual("keep",(destination/"personal.md").read_text())

    def test_missing_deployment_reported(self):
        self.assertEqual("error",validate_skill_deployment(self.skill,self.base/"missing"/self.skill.name)["status"])

    def test_source_is_not_its_own_deployment(self):
        self.assertEqual("error",validate_skill_deployment(self.skill,self.skill)["status"])

    def test_bad_deployed_python_is_not_aligned(self):
        destination=Path(deploy_skill(self.skill,self.base/"installed")["destination"])
        (destination/"scripts"/"inspect_asset.py").write_text("def (")
        self.assertEqual("error",validate_skill_deployment(self.skill,destination)["status"])

    def test_deployment_validator_cli_exit_codes_from_other_cwd(self):
        destination=Path(deploy_skill(self.skill,self.base/"installed")["destination"])
        command=[sys.executable,"-B",str(REPO/"scripts"/"validate_skill_deployment.py"),str(self.skill),str(destination)]
        result=subprocess.run(command,cwd=self.base,capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        (destination/"personal.md").write_text("keep")
        result=subprocess.run(command,cwd=self.base,capture_output=True,text=True)
        self.assertEqual(1,result.returncode,result.stderr)
        self.assertEqual("drift",json.loads(result.stdout)["status"])


if __name__ == "__main__":
    unittest.main()
