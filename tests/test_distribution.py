from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gameassetai.distribution import (  # noqa: E402
    PRODUCT_SKILLS, build_product_bundle, build_workspace_distribution,
    install_product_bundle,
    update_product_bundle, validate_installed_product, validate_product_bundle,
    validate_workspace_distribution, write_bundle_zip,
)
from gameassetai.errors import SafetyError, ValidationError  # noqa: E402
from gameassetai.outputs import begin_output_task  # noqa: E402
from gameassetai.workspace import (  # noqa: E402
    create_profile, initialize_distribution_workspace, select_profile, validate_workspace,
)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gameassetai-distribution-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"

    def build(self):
        build_product_bundle(ROOT, self.bundle)

    def test_bundle_is_self_contained_reproducible_and_executable(self):
        self.build()
        self.assertEqual("valid", validate_product_bundle(self.bundle)["status"])
        for name in PRODUCT_SKILLS:
            skill = self.bundle / "skills" / name
            self.assertTrue((skill / "runtime" / "gameassetai" / "cli.py").is_file())
            all_text = "\n".join(
                path.read_text(encoding="utf-8-sig")
                for path in skill.rglob("*") if path.is_file() and path.suffix in {".py", ".md", ".json"}
            )
            self.assertNotIn(str(ROOT), all_text)
        entry = self.bundle / "skills" / "gameassetai-workspace" / "scripts" / "gameassetai.py"
        result = subprocess.run(
            [sys.executable, "-B", str(entry), "catalog", "validate"],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('"status": "valid"', result.stdout)

        workspace = self.root / "installed-workspace"
        commands = (
            ["workspace", "create", str(workspace)],
            [
                "profile", "create", str(workspace), "game-one", "--name", "Game One",
                "--description", "Installed runtime smoke test",
            ],
            ["profile", "select", str(workspace), "game-one"],
            [
                "profile", "set", str(workspace), "art_direction.palette",
                "--value-json", '["moss", "bark"]',
            ],
            ["profile", "get", str(workspace), "art_direction.palette"],
        )
        last = None
        for arguments in commands:
            last = subprocess.run(
                [sys.executable, "-B", str(entry), *arguments],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, last.returncode, last.stderr)
        self.assertEqual(["moss", "bark"], json.loads(last.stdout)["value"])

        invalid_style = subprocess.run(
            [
                sys.executable, "-B", str(entry), "profile", "create", str(workspace),
                "wrong-style", "--name", "Wrong Style", "--description", "Must fail",
                "--three-d-style", "animated-sprite-sheet",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(1, invalid_style.returncode)
        self.assertFalse((workspace / "profiles" / "wrong-style.json").exists())

        output = subprocess.run(
            [
                sys.executable, "-B", str(entry), "outputs", "begin", str(workspace),
                "--space", "workspace", "--category", "equipment-prop",
                "--asset", "bronze-sword", "--purpose", "initial-model",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, output.returncode, output.stderr)
        output_report = json.loads(output.stdout)
        self.assertEqual("001-initial-model", Path(output_report["task"]).name)

        artifact_plan = subprocess.run(
            [
                sys.executable, "-B", str(entry), "outputs", "artifact-path",
                output_report["task"], "--kind", "model", "--filename", "bronze-sword.blend",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, artifact_plan.returncode, artifact_plan.stderr)
        artifact = Path(json.loads(artifact_plan.stdout)["artifact"])
        artifact.write_bytes(b"installed runtime artifact contract")
        for arguments in (
            ["outputs", "register", output_report["task"], str(artifact)],
            ["outputs", "status", output_report["task"], "complete"],
        ):
            lifecycle = subprocess.run(
                [sys.executable, "-B", str(entry), *arguments],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, lifecycle.returncode, lifecycle.stderr)

        archive_a, archive_b = self.root / "a.zip", self.root / "b.zip"
        first = write_bundle_zip(self.bundle, archive_a)
        second = write_bundle_zip(self.bundle, archive_b)
        self.assertEqual(first["sha256"], second["sha256"])

    def test_install_refuses_overwrite_and_update_retains_backup(self):
        self.build()
        installed = self.root / "user-home" / ".agents" / "skills"
        self.assertEqual("installed", install_product_bundle(self.bundle, installed)["status"])
        with self.assertRaises(SafetyError):
            install_product_bundle(self.bundle, installed)
        personal = installed / PRODUCT_SKILLS[0] / "personal.txt"
        personal.write_text("preserve old installation", encoding="utf-8")

        rebuilt = self.root / "rebuilt"
        build_product_bundle(ROOT, rebuilt)
        backup = self.root / "backup" / "product-0.2.0-old"
        result = update_product_bundle(rebuilt, installed, backup)
        self.assertEqual("updated", result["status"])
        self.assertEqual("preserve old installation", (backup / PRODUCT_SKILLS[0] / "personal.txt").read_text())
        self.assertFalse((installed / PRODUCT_SKILLS[0] / "personal.txt").exists())
        self.assertEqual("valid", validate_product_bundle(rebuilt)["status"])

    def test_project_install_creates_and_validates_workspace_before_skills_then_profile(self):
        self.build()
        workspace = self.root / "fresh-project-workspace"
        self.assertFalse(workspace.exists())
        command = subprocess.run(
            [
                sys.executable, "-B", str(ROOT / "scripts" / "gameassetai.py"),
                "package", "install-project", str(self.bundle), str(workspace),
                "--template", str(ROOT / "workspace-template"),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, command.returncode, command.stderr)
        result = json.loads(command.stdout)
        self.assertEqual(
            [
                "workspace-created-or-connected",
                "workspace-validated",
                "skills-installed",
                "installation-validated",
            ],
            result["steps"],
        )
        self.assertIsNone(validate_workspace(workspace)["active_profile"])
        skills_dir = workspace / ".agents" / "skills"
        self.assertEqual("valid", validate_installed_product(skills_dir)["status"])
        validate_install = subprocess.run(
            [
                sys.executable, "-B", str(ROOT / "scripts" / "gameassetai.py"),
                "package", "validate-install", str(skills_dir),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, validate_install.returncode, validate_install.stderr)
        for name in PRODUCT_SKILLS:
            self.assertTrue((skills_dir / name / "SKILL.md").is_file())

        entry = skills_dir / "gameassetai-workspace" / "scripts" / "gameassetai.py"
        for arguments in (
            [
                "profile", "create", str(workspace), "game-one", "--name", "Game One",
                "--description", "Post-install Profile",
            ],
            ["profile", "select", str(workspace), "game-one"],
            ["workspace", "validate", str(workspace), "--require-profile"],
        ):
            installed_command = subprocess.run(
                [sys.executable, "-B", str(entry), *arguments],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, installed_command.returncode, installed_command.stderr)
        self.assertEqual(
            "game-one", validate_workspace(workspace, require_profile=True)["active_profile"],
        )

    def test_workspace_distribution_clone_initialization_and_user_skill_copy(self):
        distribution = self.root / "workspace-distribution"
        source_commit = "a" * 40
        build_workspace_distribution(ROOT, distribution, source_commit=source_commit)
        report = validate_workspace_distribution(distribution)
        self.assertEqual(source_commit, report["source_commit"])
        self.assertTrue((distribution / ".agents" / "skills").is_dir())
        self.assertTrue((distribution / "templates" / "workspace").is_dir())
        self.assertFalse((distribution / "src").exists())
        self.assertFalse((distribution / "tests").exists())
        self.assertFalse((distribution / "output").exists())

        clone = self.root / "project-clone"
        shutil.copytree(distribution, clone)
        git_init = subprocess.run(
            ["git", "init", "-b", "dist/workspace"],
            cwd=clone,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, git_init.returncode, git_init.stderr)
        initialized = initialize_distribution_workspace(clone)
        self.assertEqual("initialized", initialized["status"])
        self.assertFalse((clone / "outputs").exists())
        self.assertFalse((clone / "notes").exists())
        create_profile(clone, "game-one", "Game One", "Persistent personal data")
        select_profile(clone, "game-one")
        profile = clone / "profiles" / "game-one.json"
        before = profile.read_bytes()
        self.assertEqual(
            "already-initialized", initialize_distribution_workspace(clone)["status"],
        )
        self.assertEqual(before, profile.read_bytes())

        entry = (
            clone / ".agents" / "skills" / "gameassetai-workspace"
            / "scripts" / "gameassetai.py"
        )
        command = subprocess.run(
            [sys.executable, "-B", str(entry), "workspace", "validate", str(clone)],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, command.returncode, command.stderr)

        user_skills = self.root / "user-home" / ".agents" / "skills"
        shutil.copytree(distribution / ".agents" / "skills", user_skills)
        self.assertEqual("valid", validate_installed_product(user_skills)["status"])
        user_entry = user_skills / "gameassetai-workspace" / "scripts" / "gameassetai.py"
        user_command = subprocess.run(
            [sys.executable, "-B", str(user_entry), "catalog", "validate"],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, user_command.returncode, user_command.stderr)

    def test_clone_initialization_refuses_unverified_or_invalid_personal_state_without_mutation(self):
        unrelated = self.root / "unrelated-repository"
        unrelated.mkdir()
        (unrelated / ".git").mkdir()
        before = {path.name for path in unrelated.iterdir()}
        with self.assertRaises(ValidationError):
            initialize_distribution_workspace(unrelated)
        self.assertEqual(before, {path.name for path in unrelated.iterdir()})

        distribution = self.root / "workspace-distribution"
        build_workspace_distribution(ROOT, distribution, source_commit="a" * 40)
        fake_clone = self.root / "fake-clone-marker"
        shutil.copytree(distribution, fake_clone)
        (fake_clone / ".git").mkdir()
        with self.assertRaisesRegex(ValidationError, "valid Git worktree"):
            initialize_distribution_workspace(fake_clone)
        self.assertFalse((fake_clone / "config").exists())

        clone = self.root / "invalid-partial-clone"
        shutil.copytree(distribution, clone)
        git_init = subprocess.run(
            ["git", "init", "-b", "dist/workspace"],
            cwd=clone,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, git_init.returncode, git_init.stderr)
        (clone / "profiles").mkdir()
        broken = clone / "profiles" / "broken.json"
        broken.write_text("not-json", encoding="utf-8")
        before_broken = broken.read_bytes()
        with self.assertRaises(ValidationError):
            initialize_distribution_workspace(clone)
        self.assertEqual(before_broken, broken.read_bytes())
        self.assertFalse((clone / "config").exists())

        tampered = self.root / "tampered-distribution"
        shutil.copytree(distribution, tampered)
        (tampered / "README.md").write_text("tampered", encoding="utf-8")
        with self.assertRaises(ValidationError):
            validate_workspace_distribution(tampered)

        unexpected = self.root / "unexpected-distribution-file"
        shutil.copytree(distribution, unexpected)
        (unexpected / "src").mkdir()
        with self.assertRaisesRegex(ValidationError, "Unexpected"):
            validate_workspace_distribution(unexpected)

    def test_fast_forward_product_update_preserves_ignored_personal_data(self):
        distribution = self.root / "workspace-distribution"
        build_workspace_distribution(ROOT, distribution, source_commit="a" * 40)
        publisher = self.root / "publisher"
        shutil.copytree(distribution, publisher)
        commands = (
            ["git", "init", "-b", "dist/workspace"],
            ["git", "config", "user.name", "Test Publisher"],
            ["git", "config", "user.email", "publisher@example.invalid"],
            ["git", "add", "-A"],
            ["git", "commit", "-m", "initial distribution"],
        )
        for command in commands:
            result = subprocess.run(command, cwd=publisher, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
        clone = self.root / "git-clone"
        result = subprocess.run(
            ["git", "clone", "--branch", "dist/workspace", "--single-branch", str(publisher), str(clone)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        initialize_distribution_workspace(clone)
        create_profile(clone, "game-one", "Game One", "Preserved through pull")
        select_profile(clone, "game-one")
        task = Path(begin_output_task(
            "workspace", clone, asset_category="equipment-prop",
            asset_id="bronze-sword", purpose="initial-model",
        )["task"])
        (clone / "notes").mkdir()
        (clone / "notes" / "personal.md").write_text("keep note", encoding="utf-8")
        before_profile = (clone / "profiles" / "game-one.json").read_bytes()
        before_manifest = (task / "manifest.json").read_bytes()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=clone, capture_output=True, text=True,
        )
        self.assertEqual("", status.stdout.strip())

        readme = publisher / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nProduct update fixture.\n", encoding="utf-8")
        metadata_path = publisher / "distribution.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["source_commit"] = "b" * 40
        canonical_readme = readme.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        metadata["files"]["README.md"] = hashlib.sha256(
            canonical_readme.encode("utf-8")
        ).hexdigest()
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        for command in (
            ["git", "add", "README.md", "distribution.json"],
            ["git", "commit", "-m", "update product files"],
        ):
            update = subprocess.run(command, cwd=publisher, capture_output=True, text=True)
            self.assertEqual(0, update.returncode, update.stderr)
        pull = subprocess.run(
            ["git", "pull", "--ff-only"], cwd=clone, capture_output=True, text=True,
        )
        self.assertEqual(0, pull.returncode, pull.stderr)
        self.assertEqual(before_profile, (clone / "profiles" / "game-one.json").read_bytes())
        self.assertEqual(before_manifest, (task / "manifest.json").read_bytes())
        self.assertEqual("keep note", (clone / "notes" / "personal.md").read_text())
        self.assertEqual("valid", validate_workspace_distribution(clone)["status"])
        self.assertEqual("valid", validate_workspace(clone, require_profile=True)["status"])

    def test_bundle_is_independent_of_present_or_deleted_development_output(self):
        checkout = self.root / "isolated-checkout"
        checkout.mkdir()
        for relative in ("src", "skills", "catalog", "workspace-template", "packaging"):
            shutil.copytree(ROOT / relative, checkout / relative)
        development_output = checkout / "output" / "experiments" / "local-only"
        development_output.mkdir(parents=True)
        (development_output / "never-package.txt").write_text("local result", encoding="utf-8")

        with_output = self.root / "bundle-with-local-output"
        without_output = self.root / "bundle-without-local-output"
        build_product_bundle(checkout, with_output)
        self.assertFalse(any(path.name == "never-package.txt" for path in with_output.rglob("*")))
        shutil.rmtree(checkout / "output")
        build_product_bundle(checkout, without_output)
        self.assertEqual(
            json.loads((with_output / "manifest.json").read_text(encoding="utf-8"))["files"],
            json.loads((without_output / "manifest.json").read_text(encoding="utf-8"))["files"],
        )

    def test_install_refuses_linked_target_component(self):
        self.build()
        external = self.root / "external-skills"
        external.mkdir()
        linked = self.root / "linked-parent"
        try:
            linked.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")
        with self.assertRaises(SafetyError):
            install_product_bundle(self.bundle, linked / "skills")
        self.assertEqual([], list(external.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_install_refuses_windows_junction_component(self):
        self.build()
        external = self.root / "external-skills"
        external.mkdir()
        junction = self.root / "linked-parent"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(external)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            self.skipTest(f"Cannot create a test junction: {result.stderr or result.stdout}")
        try:
            with self.assertRaises(SafetyError):
                install_product_bundle(self.bundle, junction / "skills")
            self.assertEqual([], list(external.iterdir()))
        finally:
            if junction.exists():
                os.rmdir(junction)


if __name__ == "__main__":
    unittest.main()
