# Subframe pose-evaluation experiment — 2026-09-28

## Question

Can Blender 5.0.1 deterministically evaluate pose transforms at fractional frames through
the Python API, while preserving the original Scene and Action? This capability is needed
before extending loop inspection beyond integer-frame finite differences.

## Experiment

`tests/animation/run_subframe_pose_probe.py` creates an owned temporary Scene, one-bone
Armature and a LINEAR location Action with values 0 and 1 at frames 1 and 2. It evaluates
the pose bone through the dependency graph at frames 1, 1.25, 1.75 and 2.

The fixture is development-only. It removes only IDs carrying its ownership token and
compares the original Scene/Object/Armature/Action lists and frame/subframe after teardown.

## Result

Blender 5.0.1 passed seven checks:

- integer endpoints evaluated as 0 and 1
- fractional frames 1.25 and 1.75 evaluated as 0.25 and 0.75
- the requested subframe state was reported correctly
- Action key content and interpolation were unchanged
- fixture teardown and original Scene restoration were exact

The original Cube/Light/Camera Scene and current one-material inventory remained unchanged.

## Decision and limits

Fractional-frame pose sampling is viable for the next bounded experiment. This result does
not choose a sampling density, detect every Bezier extremum, validate deformation, render
frames, or certify visual/Unity loop quality. A future implementation must use explicit
sampling inputs and preserve the same isolated-copy and teardown boundaries.
