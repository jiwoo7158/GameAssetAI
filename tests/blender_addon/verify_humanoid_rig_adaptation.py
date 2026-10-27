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
    rig_receipt = report["rig_receipt"]
    obj = bpy.data.objects.get(rig_receipt["mesh_object_name"])
    armature = bpy.data.objects.get(rig_receipt["armature_object_name"])
    failures = []
    if obj is None or obj.type != "MESH":
        failures.append("saved Mesh Object is missing")
    elif not obj.data.uv_layers or len(obj.data.uv_layers.active.data) != len(obj.data.loops):
        failures.append("saved UV layer is incomplete")
    if armature is None or armature.type != "ARMATURE":
        failures.append("saved Armature is missing")
    elif sorted(bone.name for bone in armature.data.bones) != rig_receipt["bone_names"]:
        failures.append("saved bone inventory differs from receipt")
    if obj is not None:
        modifier = obj.modifiers.get(rig_receipt["modifier_name"])
        if modifier is None or modifier.object != armature:
            failures.append("saved Armature modifier binding is missing")
    result = {"status": "pass" if not failures else "failed", "failures": failures,
              "case": report["case"], "blend": bpy.data.filepath}
    print("GAMEASSETAI_M2_REOPEN " + json.dumps(result))
    if failures:
        raise AssertionError("; ".join(failures))


if __name__ == "__main__":
    main()
