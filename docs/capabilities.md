# Capability Status

Status terms: `available` means the foundation feature is usable offline; `bounded` means a narrow
Blender contract exists; `planned` means catalog/design only. Evidence labels follow `AGENTS.md`.

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Catalog and style registry | available | tested | JSON registration and validation; no generator implied. |
| Asset Specification | available | tested | Provider-neutral validation; no automatic production orchestration yet. |
| Workspace create/connect/update | available | tested | Current v2 plus non-mutating legacy recognition; no automatic legacy migration. |
| Profile persistence/switching | available | tested | JSON Profiles and exact active selection. |
| Disposable output runs | available | tested | Unique path and manifest only; no artifact lifecycle deletion API. |
| Product Skill bundle/install/update | available | tested | Self-contained local bundle; client discovery not yet verified. |
| Static Blender creation/revision | bounded | accepted | Explicit primitive/profile/profile-beveled assemblies, generated texture patterns, owned semantic copy revision, and one narrow external GLB region edit. Not general modeling. |
| Humanoid base creation/revision | bounded | tested | Template proportion/region workflow; its prior visual candidate was rejected and is not a target style. |
| Nonhumanoid/creature generation | planned | none | Catalog only. |
| Rig and weights | bounded | representative | One explicit-landmark 18-bone humanoid path; no general skeleton or fingers/facial Rig. |
| Mixamo/Action workflows | bounded | accepted | Narrow 17-role target, Action preparation/copy/bake helpers; not universal retargeting. |
| Static FBX | bounded | tested | Explicit no-overwrite static contract; material/texture breadth remains limited. |
| Animated FBX | bounded | engine-proven | One Generic Unity path; Unity Humanoid Avatar and broad root motion are unproven. |
| Static/action PNG and sprite sheet | bounded | tested | Deterministic render/sequence/grid helpers; art-direction acceptance and complete 8-direction orchestration are unproven. |
| Four target 3D styles | planned | none | Specifications exist; no style has an accepted autonomous generator. |
| 8-direction pixel sprite | planned | none | Style registered; existing helpers are components, not an end-to-end accepted workflow. |
| Blender Add-on | bounded | tested | Retained installable UI mainly for 2D preview/output; not the full product workflow. |
| UnityWorkbench | planned | none | Optional explicit review environment; not created or configured. |
| External/local AI generation | planned | none | Replaceable provider entries only; no model, subscription, or API integrated. |

The previous 45 narrow Skill folders were implementation modules rather than 45 product features.
Their reusable code is consolidated under the shared Blender runtime; obsolete diagnostic/pass
surfaces and milestone harnesses were removed from the active product.
