# Product Definition

## Vision and scope

GameAssetAI is an installable Codex Skill system for producing usable game assets under a
persistent game-specific art direction. Natural-language requests flow through a structured Asset
Specification to one of several replaceable production providers, primarily Blender-native tools.
It supports creation and revision rather than assuming every asset starts from nothing.

The product aims to support 3D source assets and optional 2D outputs while keeping external AI
providers optional. It is not currently a universal 3D generator. Quality is judged by visible,
semantic, and game-use acceptance, not by file creation or tests alone.

## Asset catalog

`catalog/asset-types/` registers extensible asset types in four areas:

- characters and lifeforms: humanoids, nonhuman humanoids, animals, creatures, amorphous and
  plant creatures, mechanical lifeforms, and animated-object characters;
- equipment and props: weapons, shields, armor/clothing, hair/accessories, tools, furniture,
  containers, devices, general props, and attachable parts;
- environments and structures: buildings, architectural and dungeon modules, terrain,
  vegetation, geology, natural objects, and modular environment sets;
- VFX meshes: slashes, shockwaves, magic circles, energy rings, debris, and beam/energy forms.

Registration, implementation, and evidence are separate fields. New nouns should normally be
catalog data or children of an existing type. Add code only for a production technique not covered
by a reusable provider. Asset type and production method are many-to-many.

## Initial styles

The initial 3D specifications are:

1. Stylized Chibi Low-Poly
2. Faceted / Angular Low-Poly
3. Soft Chibi / Cartoon 3D
4. Simplified Stylized

Commercial products and creators may be visual references, never source content to copy or bundle.
The independent presets prioritize silhouette, character, controlled detail, and clean color
separation rather than minimum polygon count or primitive-only construction.

The initial 2D styles are:

5. 8-Direction Pixel Sprite
6. Animated Sprite Sheet

3D and 2D style ids are selected independently. A game's specific palette, camera, scale, budget,
and design rules belong in its Workspace Profile, not the reusable style registry.

## Inputs and Asset Specification

The normal creation flow combines a text description, a selected style preset, and reference
images supplied by the user, commonly created with an external image-generation tool. The same
flow applies to characters, props/equipment, environments, and VFX meshes. Each reference records
an explicit role such as front, side, back, three-quarter, concept, or source; references need not
live in a forced folder and more than one role may be provided.

References remain optional in the data contract so bounded work is not rejected mechanically when
an active Profile and the text request are sufficient. When visual information is required, the
workflow explains the missing view or design decision instead of inventing a reference. It never
claims an image was supplied when it was not, and it does not require GameAssetAI to install or
call an image-generation API. Future concept-image providers may be added behind the provider
boundary without changing this input contract.

Other common inputs are asset type, required outputs, and task options.

`gameassetai.asset-specification.v1` separates:

- identity, game, create/modify operation, and asset type;
- description and references;
- 3D style, 2D styles, and game/request overrides;
- requested or automatic generation provider;
- existing source and preservation contract;
- Rig/animation intent;
- requested output formats.

The same input contract applies to characters, static assets, environments, and VFX meshes. It
does not force one provider or humanoid assumptions.

## Logical pipeline

```text
request + active Profile + references
  -> validated Asset Specification
  -> implemented provider selection
  -> create or copy-first revise in Blender
  -> structural and preservation checks
  -> visible/semantic review and revision
  -> optional asset-appropriate Rig/animation
  -> optional 2D direction/action render
  -> explicit no-overwrite numbered output task
  -> optional engine review
```

User-supplied or future AI-generated concept/reference images before 3D work, Blender preview
renders used to review the 3D source, and final game PNG/pixel/sprite outputs are three different
stages. Future local or external AI concept/3D providers must sit behind the provider registry and
must not become mandatory Workspace dependencies.

## Creation and modification providers

Candidate techniques include Blender modeling, Python procedural modeling, Geometry Nodes,
templates/parameters, modular parts, existing-model editing, local AI, external AI APIs, and
reference-image-conditioned 3D generation. Only providers marked implemented may execute.

Modification goals include proportion, silhouette, parts, materials/colors, structure, equipment,
hair/clothing, and natural-language semantic changes. Present implementation is narrower; the
system must report that boundary rather than pretend free-form editing exists.

## Rig and animation

Existing Rigs and Actions are first-class inputs. Humanoid characters may use Mixamo where the
actual skeleton and workflow are eligible. Nonhumanoids, creatures, mechanical lifeforms, and
animated objects require asset-specific policies. No global skeleton, limb count, or Rig system is
mandatory.

## Outputs

Planned formats are `.blend`, `.fbx`, `.png`, PNG sequences, 8-direction sprites, and sprite sheets.
Files should remain editable in Blender where practical. Support and evidence are tracked by
format and asset scope; successful Generic FBX does not imply Unity Humanoid support.

Development experiments and user game results are separate disposable domains. Development paths
start with a validation-goal experiment id; user paths start with the active game Profile id. Both
then use a catalog category, concrete asset id, and local numbered purpose. Dates, UUIDs, and a
global result registry are not part of user-facing folder names. Result manifests describe only
their local task and may disappear with it; no independent work depends on prior results.

User results default to the Workspace `outputs/` tree, but the user may select an existing external
root for one task or persist one in a Profile or Workspace preference. Product code never infers an
external root from a project bookmark or recreates one after it was moved or deleted. Artifact
directories are created only when needed, and only actual nonempty files are registered. A
`complete` task has no quality meaning; accepted/rejected status requires recorded visual/semantic
review evidence.

The normal project-scoped product is a generated `dist/workspace` clone containing the four
self-contained Skills under `.agents/skills`, initialization templates, product instructions, and
source/version hashes. Profile, setting, note, and result paths are ignored personal ownership and
survive ordinary product Pulls. User-scoped use copies the same four Skills to
`$HOME/.agents/skills`. The development checkout and the generated product branch remain separate
ownership domains.

## Explicitly deferred in this foundation

- selection of the first new production generator and representative asset;
- general prompt-to-3D and arbitrary semantic mesh editing;
- full production coverage for every catalog type;
- automatic external model/API installation or paid calls;
- automatic UnityWorkbench creation or real game-project modification;
- public distribution and release;
- long-running Blender art-quality experiments.
