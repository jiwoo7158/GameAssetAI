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
    failures = []
    for key in ("creation_receipt", "revision_receipt"):
        receipt = report[key]
        obj = bpy.data.objects.get(receipt["object_name"])
        if obj is None or obj.type != "MESH" or obj.data.name != receipt["mesh_name"]:
            failures.append(f"{key} Mesh is missing")
            continue
        if len(obj.data.vertices) != receipt["vertices"] or not obj.data.uv_layers:
            failures.append(f"{key} Mesh/UV facts differ")
        if obj.data.users != 1:
            failures.append(f"{key} Mesh is not independently owned")
    original = bpy.data.objects.get(report["creation_receipt"]["object_name"])
    revised = bpy.data.objects.get(report["revision_receipt"]["object_name"])
    if original and revised and original.data is revised.data:
        failures.append("saved original and revision share mutable Mesh data")
    result = {"status": "pass" if not failures else "failed", "failures": failures,
              "blend": bpy.data.filepath}
    print("GAMEASSETAI_B6_REOPEN " + json.dumps(result))
    if failures:
        raise AssertionError("; ".join(failures))


if __name__ == "__main__":
    main()
