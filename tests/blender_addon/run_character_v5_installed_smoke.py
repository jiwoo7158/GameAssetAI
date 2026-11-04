import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--script-root", type=Path, required=True)
    parser.add_argument("--source-blend", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    sys.path.insert(0, str(args.script_root))
    from create_character_base import create_character, remove_created_character, revise_character_copy

    before = {name: sorted(item.name for item in getattr(bpy.data, name))
              for name in ("collections", "objects", "meshes", "materials", "images")}
    digest = hashlib.sha256(args.source_blend.read_bytes()).hexdigest()
    creation = {
        "schema": "gameassetai.character-base-request.v5", "scene_name": bpy.context.scene.name,
        "character_name": "Installed B6 Smoke", "collection_name": "Installed B6 Smoke Collection",
        "object_name": "Installed B6 Smoke Object", "mesh_name": "Installed B6 Smoke Mesh",
        "pose": "A_POSE", "topology_mode": "DEFORMATION_TEMPLATE",
        "template": {"source_file": str(args.source_blend), "source_sha256": digest,
                     "mesh_name": "GEO-body_male_stylized", "source_name": "Blender Studio Human Base Meshes",
                     "source_version": "1.4.1", "license": "CC0-1.0", "front_axis": "-Y"},
        "proportions": {"height": 1.55, "shoulder_width_ratio": 0.36, "hip_width_ratio": 0.25,
                        "body_depth_ratio": 0.18, "limb_thickness_ratio": 0.06, "head_height_ratio": 0.21},
        "regions": {"head_scale": 1.15, "head_width_scale": 1.04, "head_depth_scale": 1.03,
                    "torso_width_scale": 1.03, "arm_length_scale": 0.94, "arm_thickness_scale": 1.03,
                    "leg_length_scale": 0.95, "hand_scale": 1.1, "foot_scale": 1.1},
        "colors": {"skin": [0.7, 0.4, 0.25, 1], "primary": [0.1, 0.2, 0.35, 1],
                   "secondary": [0.5, 0.15, 0.08, 1], "boots": [0.04, 0.03, 0.02, 1]},
        "art_direction": {"style_family": "STYLIZED_LOW_POLY_SD", "silhouette": "compact readable humanoid",
                          "shape_language": "rounded primary masses", "polygon_budget": 30000,
                          "palette": [[0.7, 0.4, 0.25, 1], [0.1, 0.2, 0.35, 1],
                                      [0.5, 0.15, 0.08, 1], [0.04, 0.03, 0.02, 1]],
                          "provenance": {"source": "USER_REQUEST", "source_ref": "installed smoke",
                                         "profile_sha256": None},
                          "unsupported": ["hair", "clothing", "facial rig"]},
        "policy": {"existing_names": "REFUSE", "source_scene": "PRESERVE",
                   "creation": "NEW_SINGLE_MESH_CHARACTER", "failure": "ROLL_BACK_OWNED_DATA",
                   "rigging": "NOT_INCLUDED"},
    }
    source = create_character(creation, authorized=True)
    revision = {
        "schema": "gameassetai.character-base-revision-request.v1", "scene_name": bpy.context.scene.name,
        "source_collection_name": source["collection_name"], "source_object_name": source["object_name"],
        "character_name": "Installed B6 Smoke Revised", "collection_name": "Installed B6 Smoke Revised Collection",
        "object_name": "Installed B6 Smoke Revised Object", "mesh_name": "Installed B6 Smoke Revised Mesh",
        "regional_adjustments": {"head_scale": 1.05, "arm_length_scale": 0.92, "hand_scale": 1.08},
        "policy": {"existing_names": "REFUSE", "source": "PRESERVE",
                   "revision": "NEW_COLLECTION_OBJECT_MESH_SHARED_MATERIALS_PRESERVE_UV_TOPOLOGY",
                   "failure": "ROLL_BACK_OWNED_DATA", "rigging": "NOT_INCLUDED"},
    }
    revised = revise_character_copy(revision, authorized=True)
    remove_created_character(revised)
    remove_created_character(source)
    after = {name: sorted(item.name for item in getattr(bpy.data, name)) for name in before}
    if before != after:
        raise AssertionError("installed Character v5 smoke did not restore factory baseline")
    print("GAMEASSETAI_CHARACTER_V5_INSTALLED " + json.dumps({"status": "pass", "script_root": str(args.script_root)}))


if __name__ == "__main__":
    main()
