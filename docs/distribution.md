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
path.

```powershell
python -B scripts/gameassetai.py package build . <new-bundle-directory>
python -B scripts/gameassetai.py package validate <bundle-directory>
python -B scripts/gameassetai.py package zip <bundle-directory> <new-archive.zip>
```

The destination must not exist. Installation is no-overwrite; explicit update requires a new
backup location and preserves the prior four Skill directories there.

Bundle-based project onboarding remains available for development and recovery. It creates or
connects and validates the Workspace before creating `.agents/skills`, then installs and validates
all four Skills. Profile creation happens afterward.

```powershell
python -B scripts/gameassetai.py package install-project <bundle> <workspace> `
  --template workspace-template
python -B scripts/gameassetai.py package validate-install <workspace>\.agents\skills
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
results are excluded.

Development and CI can build and validate this tree without publishing it:

```powershell
python -B scripts/gameassetai.py package build-workspace-dist . <new-directory> `
  --source-commit <full-git-sha>
python -B scripts/gameassetai.py package validate-workspace-dist <directory>
```

The branch is generated output and must not be edited directly. Pull requests run the same build
and validation in temporary directories. `.github/workflows/publish-workspace.yml` runs only for
a push to `master`, repeats repository and offline tests, builds and
validates the tree, then appends a normal commit to `dist/workspace`. It uses the job-scoped
`GITHUB_TOKEN` `contents: write` permission, a concurrency group, and never force-pushes. A failed
test or build cannot replace the prior distribution. The branch is not created or updated merely
because a draft PR exists.

The generated `.gitattributes` fixes product text to LF, while distribution and Skill hashes
canonicalize text line endings. This keeps ordinary Windows and Linux clones verifiable without
weakening binary-file hashes.

## Project-scoped Clone and initialization

After the approved `master` change has published the branch:

```powershell
git clone --branch dist/workspace --single-branch `
  https://github.com/jiwoo7158/GameAssetAI.git <workspace>
python -B <workspace>\.agents\skills\gameassetai-workspace\scripts\gameassetai.py `
  workspace init-clone <workspace>
```

`init-clone` accepts only a real Git clone whose distribution metadata, product hashes, Skills,
and templates validate. It creates only missing personal `config/` and `profiles/` state, assigns
the Workspace marker, and validates the result. It is idempotent and refuses conflicting or linked
personal paths rather than overwriting them. `outputs/` and `notes/` remain absent until needed.

The distribution `.gitignore` excludes `/config/`, `/profiles/`, `/notes/`, `/outputs/`, and
`/AGENTS.local.md`. Templates live under tracked `/templates/`, never at personal destinations.
Ignore rules do not protect a file that was already tracked, so the publisher's allowlist and
tests also verify that personal paths are absent from the distribution commit.

## User-scoped installation

Download or extract the same `dist/workspace` tree and copy only its four `.agents/skills/*`
directories to `$HOME/.agents/skills/`. Each copied Skill contains its own Runtime, catalog, and
template and can create a separate Workspace without the development Repository. Use the existing
bundle validation/update commands when performing a managed replacement; do not overwrite an
unknown or locally modified Skill silently.

## Updates and recovery

Project-scoped users update product files with GitHub Desktop **Fetch origin** and **Pull origin**,
or `git pull --ff-only`. Git does not modify ignored personal state during a normal fast-forward.
If a conflict or incompatible Workspace schema is reported, stop and inspect it; never automate
`reset --hard`, `clean -fdx`, Profile deletion, or output deletion. Product and Workspace schema
versions are separate, and any destructive migration requires backup and explicit user approval.

User-scoped users download the newer distribution and perform a verified four-Skill update with a
separate backup. The project and user update procedures are intentionally different; no background
updater, installer wizard, release server, or second distribution branch exists.

Skill distribution does not install or configure Blender, Blender MCP, the Blender Add-on, AI
models, credentials, Unity, or UnityWorkbench. Those remain separate explicit environment gates.
