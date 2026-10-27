---
name: replace-with-skill-name
description: Replace with a short description of the repeatable task.
metadata:
  contract: gameassetai.skill-contract.v1
  requirements: REQ-REPLACE
  evidence: tested
  external-dependencies: none
---

# Skill Name

## Requirements and responsibility

List requirement IDs, whether this is a workflow/backend/optional tool, and the exact repeatable
task it owns. Identify related Skills whose implementation must be reused rather than copied.

## Implementation basis and dependencies

Record the selected Blender-native, existing GameAssetAI, approved open-source or project-owned
implementation. For external code, record the reviewed version, license and approval status.

## Use when

- condition 1
- condition 2

## Do not use when

- condition 1
- condition 2

## Preconditions

- Blender state required
- MCP capability required
- profile fields required, if any

## Inputs

Describe expected user intent, selected objects, files, or profile values.

## Procedure

1. Inspect the current Blender state.
2. Confirm the target.
3. Apply the workflow.
4. Validate the result.

Replace the generic steps above with tested steps.

## Preservation

State what may be modified or deleted.

Default rule:
preserve existing user data unless modification is necessary and intentional.

## Validation and completion

Define focused tests, representative Blender validation, observable success/failure conditions and
the strongest evidence level currently earned. Do not equate implementation with completion.

## Outputs

Define what should exist when the task is complete.

### Failure / fallback

Explain what to do if:

- expected Blender data is missing
- the MCP cannot perform an operation
- imported asset structure differs from expectations
- profile data is missing

## Known limitations

List tested limitations.

## References

List internal files under this skill directory, if any.

## Scripts

List scripts used by this skill, if any.
