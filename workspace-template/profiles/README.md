# Profiles

Each game Profile is a UTF-8 JSON file named `<profile-id>.json`. Create it through the installed
Workspace Skill so the schema and portable id are validated. Selecting a Profile only changes
`config/active-profile.json`; it never deletes another Profile.

Use `profile get` and `profile set` for an explicit field-level change. The setter accepts a JSON
value, preserves all unnamed fields, validates the complete candidate, and publishes it atomically.
Do not replace a personal Profile with `_template.json`.

Older Workspaces may contain Markdown Profiles. The current Runtime detects the Workspace as
legacy and does not convert it automatically. Back up the legacy Workspace, review every durable
rule, create a separate v2 Workspace or JSON Profile, compare the result, and switch only after the
user approves it. Never delete the original as part of migration review.
