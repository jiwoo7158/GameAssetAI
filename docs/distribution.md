# Skill and Workspace Distribution

## Product surface and official Codex roots

GameAssetAI keeps four task-oriented Skills:

- `gameassetai-workspace`
- `gameassetai-create-asset`
- `gameassetai-modify-asset`
- `gameassetai-output-asset`

Current official Codex documentation scans repository Skills under `.agents/skills` from the
working directory up to the repository root and user Skills under `$HOME/.agents/skills`. See
[Build skills](https://developers.openai.com/codex/skills/). Codex may show two entries when the
same Skill name exists at more than one scope, so choose project or user scope deliberately.

GameAssetAI does not move or delete an existing legacy `.codex/skills` installation. File and
manifest validation also do not prove that Codex Desktop or VS Code discovered a Skill; check the
host's Skill list or invoke `$gameassetai-workspace`, restarting the host if a changed Skill is not
rediscovered.

## Development source and self-contained Skill bundles

The development Repository retains the canonical Runtime in `src/gameassetai/`, Skill instructions
in `skills/`, catalogs in `catalog/`, and Workspace source template in `workspace-template/`.
Generated Skills vendor these sources so they never require the development checkout's absolute
path. `archive/legacy/` is never a Runtime, catalog, template, test, or distribution input.

```powershell
$DevelopmentCli = "scripts/gameassetai.py"
python -B $DevelopmentCli package build . <new-bundle-directory>
python -B $DevelopmentCli package validate <bundle-directory>
python -B $DevelopmentCli package zip <bundle-directory> <new-archive.zip>
```

The destination must not exist. Installation is no-overwrite; explicit update requires a new
backup location and preserves the prior four Skill directories there.

Bundle-based project onboarding remains available for development and recovery. It creates or
connects and validates the Workspace before creating `.agents/skills`, then installs and validates
all four Skills. Profile creation happens afterward.

```powershell
python -B $DevelopmentCli package install-project <bundle> <workspace> `
  --template workspace-template
python -B $DevelopmentCli package validate-install <workspace>\.agents\skills
```

## Generated `dist/workspace` product tree

The normal project-scoped product uses one generated branch, `dist/workspace`. It is built from an
explicit allowlist rather than by merging the development tree:

```text
GameAssetAI-Workspace/
├── .agents/skills/<four self-contained Skills>/
├── templates/workspace/
├── AGENTS.md
├── README.md
├── .gitattributes
├── .gitignore
└── distribution.json
```

`distribution.json` records the product version, full source `master` commit SHA, layout version,
four Skill names, and hashes of every product-managed file. Development tests, CI implementation,
roadmaps, source checkout layout, development `output/`, personal settings, Profiles, notes, and
results are excluded. The product version is authored once in `gameassetai.__version__`; Python
package metadata and both distribution manifests consume that value.

Development and CI can build and validate this tree without publishing it:

```powershell
python -B $DevelopmentCli package build-workspace-dist . <new-directory> `
  --source-commit <full-git-sha>
python -B $DevelopmentCli package validate-workspace-dist <directory>
```

The branch is generated output and must not be edited directly. Pull requests run the same build
and validation in temporary directories. `.github/workflows/publish-workspace.yml` runs only for
a push to `master`, repeats repository and offline tests, builds and
validates the tree, then appends a normal commit to `dist/workspace`. It uses the job-scoped
`GITHUB_TOKEN` `contents: write` permission, a concurrency group, and never force-pushes. A failed
test or build cannot replace the prior distribution. The branch is not created or updated merely
because a draft PR exists.

The initial hosted publication succeeded on 2026-11-11: source `master` commit
`128a657f54776cbef6af1572f4125ae2a8fbab94` produced `dist/workspace` commit
`2196a0e9952399727d7d1981dca0cde603ac7e2f`, product version `0.2.0`, layout version `1`.
This is deployment evidence for that release, not evidence for live Codex discovery or Blender.

After pull request #4, `master` advanced to
`3331bb9ed8f1c46b837800a55d20527867703be3` and the master-only workflow published
`dist/workspace` commit `07f14acaf15b330c754bf0afe97f1eacefc2cbfc`. These hashes describe the
pre-current-work baseline, not the unmerged work branch.

The generated `.gitattributes` fixes product text to LF, while distribution and Skill hashes
canonicalize text line endings. This keeps ordinary Windows and Linux clones verifiable without
weakening binary-file hashes.

## Project-scoped Clone and initialization

After the approved `master` change has published the branch:

```powershell
git clone --branch dist/workspace --single-branch `
  https://github.com/jiwoo7158/GameAssetAI.git <workspace>
Set-Location <workspace>
$GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"
python -B $GameAssetAICli workspace init-clone .
python -B $GameAssetAICli workspace validate .
```

`init-clone` accepts only a real Git clone whose distribution metadata, product hashes, Skills,
and templates validate. It creates only missing personal `config/` and `profiles/` state, assigns
the Workspace marker, and validates the result. It is idempotent and refuses conflicting or linked
personal paths rather than overwriting them. `outputs/` and `notes/` remain absent until needed.

The distribution `.gitignore` excludes `/config/`, `/profiles/`, `/notes/`, `/outputs/`,
`/AGENTS.local.md`, and local environment configuration under `/.local/`, plus common Python caches/environments, editor/OS noise, temporary files, and
Blender backup files. It never ignores `.agents/skills`. Templates live under tracked
`/templates/`, never at personal destinations. Ignore rules do not protect a file that was already
tracked, so the publisher's allowlist and tests also verify that personal paths are absent from the
distribution commit.

## User-scoped installation

Download or extract the same `dist/workspace` tree and copy only its four `.agents/skills/*`
directories to `$HOME/.agents/skills/`. Each copied Skill contains its own Runtime, catalog, and
template and can create a separate Workspace without the development Repository. Use the existing
bundle validation/update commands when performing a managed replacement; do not overwrite an
unknown or locally modified Skill silently. For manual CLI use, resolve the actual copied
`gameassetai-workspace/scripts/gameassetai.py` and invoke that path; `scripts/gameassetai.py` at the
Workspace root is a development-checkout path and is not present in this installation.

## Updates and recovery

Project-scoped users update product files with GitHub Desktop **Fetch origin** and **Pull origin**,
or `git pull --ff-only`. Git does not modify ignored personal state during a normal fast-forward.
If a conflict or incompatible Workspace schema is reported, stop and inspect it; never automate
`reset --hard`, `clean -fdx`, Profile deletion, or output deletion. Product and Workspace schema
versions are separate, and any destructive migration requires backup and explicit user approval.

The offline regression constructs two generated releases, changes vendored Runtime code and its
Skill/distribution hashes in the second release, performs a normal fast-forward Pull, executes the
updated bundled CLI, and verifies byte-for-byte preservation of ignored Profile, settings, note,
Manifest, and synthetic result files. This does not authorize force-reset recovery for real Pull
conflicts.

User-scoped users download the newer distribution and perform a verified four-Skill update with a
separate backup. The project and user update procedures are intentionally different; no background
updater, installer wizard, release server, or second distribution branch exists.

Skill distribution does not install or configure Blender, Blender MCP, the Blender Add-on, AI
models, credentials, Unity, or UnityWorkbench. Those remain separate explicit environment gates.
Before asset work, users must separately confirm Python, Codex Skill discovery, Blender version,
and Blender MCP connectivity. The bundled CLI can record and validate a local Blender executable
under an ignored root-specific `.local/environment.json`; that diagnostic does not install Blender
or prove MCP connectivity, modeling, rendering, export, or quality. File/package validation alone
is not a live-host or Blender test.
