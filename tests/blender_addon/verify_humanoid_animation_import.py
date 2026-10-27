import argparse
import json
import sys
from pathlib import Path

import bpy


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    report = json.loads(args.report.read_text(encoding="utf-8")); receipt = report["receipt"]
    target = bpy.data.objects.get(receipt["target_armature"])
    action = bpy.data.actions.get(receipt["result_action"])
    collection = bpy.data.collections.get(receipt["import_collection"])
    failures = []
    if target is None or target.type != "ARMATURE" or action is None:
        failures.append("saved target Armature or result Action is missing")
    elif target.animation_data is None or target.animation_data.action != action:
        failures.append("saved result Action is not bound to the target")
    if collection is None or not any(obj.type == "ARMATURE" for obj in collection.objects):
        failures.append("saved imported source collection/Armature is missing")
    result = {"status": "pass" if not failures else "failed", "failures": failures,
              "blend": bpy.data.filepath, "action": receipt["result_action"]}
    print("GAMEASSETAI_M3_REOPEN " + json.dumps(result))
    if failures: raise AssertionError("; ".join(failures))


if __name__ == "__main__": main()
