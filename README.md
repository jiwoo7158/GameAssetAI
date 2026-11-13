# GameAssetAI

GameAssetAI is a four-Skill Codex system for style-driven game-asset creation, revision, and
output through Blender. A persistent Workspace Profile keeps each game's art direction across
Codex sessions. Catalog registration describes intended coverage; it does not claim that every
asset, style, Rig, animation, export, or 2D workflow is implemented.

Codex reasoning is the core authoring path. It may direct Blender native operations and compose
bounded task-specific Python for the selected asset. Verified helpers and local/external providers
may be adopted later, but a prewritten generator is not required for every asset noun. Current
support boundaries are recorded in [Capability Status](docs/capabilities.md).

## Repository layout

```text
catalog/                 canonical asset, style, and provider data
src/gameassetai/         active shared Runtime
skills/                  four task-oriented source Skills
packaging/               generated Skill/Workspace distribution sources
workspace-template/      personal Workspace template
scripts/                 development-checkout entrypoints
tests/                   formal product tests
docs/                    current product and engineering authority
archive/legacy/          optional unverified historical code, never product input
output/                  optional ignored development experiment results
```

Repository source, generated Skills, user Workspace data, existing Blender/game projects, and
result trees are separate ownership domains. `output/` and Workspace `outputs/` may be partially
or completely moved or deleted without breaking Profiles, catalogs, packaging, tests, or new
independent work.

## Project-scoped installation

The normal project product is generated on `dist/workspace` after an approved `master` change:

```powershell
git clone --branch dist/workspace --single-branch `
  https://github.com/jiwoo7158/GameAssetAI.git <workspace>
Set-Location <workspace>
$GameAssetAICli = ".agents/skills/gameassetai-workspace/scripts/gameassetai.py"
python -B $GameAssetAICli workspace init-clone .
python -B $GameAssetAICli workspace validate .
```

Initialization validates the generated product and creates only missing ignored personal state.
It does not replace Profiles, settings, notes, outputs, or local instructions. User-scoped use
copies the same four Skill directories to `$HOME/.agents/skills`; resolve the copied Workspace
Skill's `scripts/gameassetai.py` rather than assuming a personal absolute path.

## Profile and local Blender setup

```powershell
python -B $GameAssetAICli profile create . my-game `
  --name "My Game" --description "Persistent game art profile" `
  --three-d-style stylized-chibi-low-poly
python -B $GameAssetAICli profile select . my-game
python -B $GameAssetAICli workspace validate . --require-profile

python -B $GameAssetAICli environment blender set . <absolute-blender-executable>
python -B $GameAssetAICli environment blender validate .
```

The Blender command stores the path only in ignored `.local/environment.json`. Validation uses an
unsaved factory-startup background process and verifies Python error propagation. It neither
installs Blender/Add-ons/MCP nor creates an asset. Installed Skills do not depend on a development
Repository's local setting.

## Asset work and results

The normal request combines text, an official style preset, and user-provided reference images
with explicit roles. References may be omitted when the request and Profile are sufficient; the
system must ask for missing visual information instead of inventing it.

For a new 3D asset, preserve an editable `.blend` as the first primary artifact unless the user
chooses another bounded source contract. FBX, previews, pixel frames, and sprite sheets are
explicit downstream steps. Report the exact registered `.blend` path; GUI opening is an optional
user-selected review step and never implicit permission to overwrite it. See
[`docs/workspace.md`](docs/workspace.md) for the safe launch procedure. Allocate every result
through the Runtime:

```powershell
python -B $GameAssetAICli outputs begin . --space workspace `
  --category equipment-prop --asset bronze-sword --purpose initial-model
```

User tasks use:

```text
outputs/<active-game>/<category>/<asset-id>/<number>-<purpose>/
```

Development experiments use:

```text
output/experiments/<experiment-id>/<category>/<asset-id>/<number>-<purpose>/
```

An experiment id is one validation goal, an asset id is one concrete target, and the numbered
purpose is one preserved result. Do not create an experiment for every request, merge different
goals because they share an asset, or create a new asset id for a revision. Artifact paths are
reserved and registered without overwrite; `complete` is not quality acceptance.

## Development validation

Development-checkout commands run from the Repository root:

```powershell
python -B scripts/validate_repo.py
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B scripts/gameassetai.py package build-workspace-dist . <temporary-directory> `
  --source-commit <full-git-sha>
python -B scripts/gameassetai.py package validate-workspace-dist <temporary-directory>
```

Formal tests use temporary directories and include an archive-absent checkout regression. They do
not run the historical `archive/legacy/` tests and do not prove visual quality, live Codex Skill
discovery, Blender MCP connectivity, export behavior, or engine import.

## Current documents

- [Product definition](docs/product-definition.md)
- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Capabilities](docs/capabilities.md)
- [Workspace](docs/workspace.md)
- [Distribution](docs/distribution.md)
- [Quality and testing](docs/quality.md)
- [Roadmap](docs/roadmap.md)
