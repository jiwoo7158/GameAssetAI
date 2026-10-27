# Skill Design

## Purpose

Skills should encode reusable procedures, not one game's preferences.

A skill should answer:

> What repeatable task can Codex perform reliably?

A profile should answer:

> How should that task be constrained for this game?

## Good boundaries

Good skill candidates have:

- recognizable triggers
- clear inputs
- repeatable steps
- validation criteria
- known failure modes

Avoid building one enormous skill that tries to handle all modeling, rigging, animation, and export behavior.

## Requirement and implementation traceability

For every new production Skill and every substantially revised production Skill:

1. cite one or more stable IDs from `docs/requirements.md`;
2. state whether it is a user-facing workflow, internal backend or optional downstream tool;
3. identify the existing Skills/helpers it calls or supersedes;
4. choose Blender native, existing GameAssetAI, reviewed open source or project-owned code in
   that order, stopping as soon as a suitable option exists;
5. state external dependencies and their approval/installation status;
6. define observable completion and failure criteria on a representative Blender asset.

Do not add a second implementation of an owned responsibility merely because another library or
Skill exposes a similar operation. Prefer a thin adapter behind the existing owner. When no
candidate meets the contract, record the rejection and implement only the missing bounded part.

### Open-source review record

Before integration, record the exact project/version or commit, source URL, license, supported
Blender versions, maintenance evidence, automation/headless support, data mutation behavior,
uninstall/rollback path, and the representative isolated test. Documentation review is
`researched`, not `tested`; installation is not integration success.

### Evidence state

Use the evidence labels from `AGENTS.md`: `tested`, `representative`, `accepted` and
`engine-proven`. Keep implementation state separate (`planned`, `partial`, `implemented`,
`suspended`, `rejected`). A Skill may be implemented but only tested on a synthetic fixture.

## Incremental Skill contract

Substantially revised Skills may opt into `gameassetai.skill-contract.v1` in frontmatter metadata.
The contract requires metadata for requirement IDs, evidence and external dependencies plus these
body sections:

- `Requirements and responsibility`
- `Implementation basis and dependencies`
- `Workflow`
- `Preservation`
- `Validation and completion`
- `Boundary`

Repository validation checks the structure for opted-in Skills. Adoption is incremental so that
historical Skills are not rewritten without a real product reason.

## Recommended SKILL.md sections

A production skill should normally define:

1. Requirements and responsibility
2. Implementation basis and dependencies
3. When to use / not use
4. Preconditions and profile fields
5. Scene inspection and procedure
6. Preservation and destructive-operation policy
7. Validation and completion evidence
8. Expected outputs and downstream conditions
9. Failure / fallback behavior
10. Known limitations
11. References / scripts used

## Profile awareness

When a constraint is game-specific, the skill should inspect the current profile.

Examples:

- target engine
- poly budget
- texture budget
- rig preference
- export directory
- art style
- 2D output view, resolution and fixed palette
- outline, shading, naming and sprite-output rules

Do not duplicate these values inside the skill.

## Existing assets

Existing assets are first-class inputs.

A skill must be able to distinguish:

- creating a new asset
- modifying a current Blender object
- importing an external asset
- preserving an existing rig
- replacing a rig intentionally
- using an imported animation
- authoring a new animation

## Testing requirement

Every stable skill should have at least:

- one happy-path test
- one existing-asset preservation test where relevant
- one failure-path test
- one validation checklist

Use `tests/` to record these.
