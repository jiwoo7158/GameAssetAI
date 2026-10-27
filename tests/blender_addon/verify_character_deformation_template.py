import argparse
import json
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    report = json.loads(args.report.read_text(encoding="utf-8"))
    receipt = report["creation_receipt"]
    obj = bpy.data.objects.get(receipt["object_name"])
    failures = []
    if obj is None or obj.type != "MESH":
        failures.append("saved character Mesh Object is missing")
    else:
        mesh = obj.data
        if mesh.name != receipt["mesh_name"] or len(mesh.vertices) != receipt["vertices"]:
            failures.append("saved Mesh facts differ from the creation receipt")
        if obj.get("gameassetai_character_source_kind") != "CC0_TEMPLATE":
            failures.append("saved source provenance is missing")
        if mesh.get("gameassetai_character_source_sha256") != report["source_sha256"]:
            failures.append("saved Mesh source hash differs")
        if not mesh.uv_layers or len(mesh.uv_layers.active.data) != len(mesh.loops):
            failures.append("saved active UV layer is incomplete")
        if obj.data.users != 1:
            failures.append("saved generated Mesh is not independently owned")
    rig = bpy.data.objects.get(report["rig_receipt"]["armature_object_name"])
    if rig is None or rig.type != "ARMATURE":
        failures.append("saved deformation-probe Armature is missing")
    result = {"status": "pass" if not failures else "failed", "failures": failures,
              "blend": bpy.data.filepath, "case": report["case"]}
    print("GAMEASSETAI_DEFORMATION_REOPEN " + json.dumps(result))
    if failures:
        raise AssertionError("; ".join(failures))


if __name__ == "__main__":
    main()
