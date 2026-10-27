# Game Asset Profile

## Identity

- Name:
- Target engine:
- Target platform:

## Art direction

- Style:
- Shape / silhouette notes:
- Material / shading notes:
- Texture notes:

## Modeling

- Typical topology expectations:
- Triangle / polygon budgets:
- LOD policy:
- Collider policy:

## Characters

- Rig policy:
- Mixamo usage:
- Existing skeleton policy:
- Bone/export notes:

## Animation

- Existing animation reuse:
- Mixamo animation usage:
- Root motion policy:
- Retargeting notes:
- Custom animation notes:

## Export

- Preferred format:
- Scale / axis notes:
- Default export destination:
- Engine-specific notes:

## Preservation

- What should normally be preserved:
- What may be regenerated:

## Other durable rules

-

## Optional exact 2D output preset

Leave this section absent when the game has no durable 2D defaults. When used, keep exactly
one complete `gameassetai-2d-preset` block. Do not fill unknown values speculatively.

Copy the indented skeleton, remove its indentation, and replace every placeholder with an
explicit game decision before using it:

    ```gameassetai-2d-preset
    {
      "schema": "gameassetai.2d-profile-preset.v1",
      "view": "<complete view object>",
      "lighting": "<complete lighting object>",
      "style": "<complete static-v3 style object>",
      "sequence": {"playback_fps": "<explicit number>"},
      "sprite_sheet": {"padding": "<explicit integer>", "order": "ROW_MAJOR_TOP_LEFT"}
    }
    ```
