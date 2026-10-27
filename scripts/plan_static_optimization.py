"""Advisory planning from fresh base diagnostics; no Blender access or modification."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def plan_static_optimization(diagnostics: dict, target_triangles: int | None = None) -> dict:
    """Target is explicitly supplied data, not inferred from Markdown or other budgets."""
    report = {"schema": "gameassetai.optimization-plan.v1", "status": "error",
              "errors": [], "mutation_authorized": False,
              "scope": "advisory_base_mesh_only", "freshness": "not_verified",
              "optimization_method": None}
    try:
        if target_triangles is not None and (type(target_triangles) is not int or target_triangles < 0):
            raise ValueError("target_triangles must be a nonnegative integer or None")
        if not isinstance(diagnostics, dict) or diagnostics.get("schema") != "gameassetai.mesh-diagnostics.v1":
            raise ValueError("Expected mesh-diagnostics.v1 report")
        if diagnostics.get("status") != "ok" or diagnostics.get("errors") != []:
            raise ValueError("Diagnostics did not complete successfully")
        if diagnostics.get("basis") != "base":
            raise ValueError("Require base diagnostics; evaluated topology is not a copy-edit plan")
        for key in ("object", "scene"):
            if not isinstance(diagnostics.get(key), str) or not diagnostics[key]:
                raise ValueError(f"Missing explicit {key}")
        metrics = diagnostics.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError("Missing metrics")
        for key in ("triangles", "polygons"):
            if type(metrics.get(key)) is not int or metrics[key] < 0:
                raise ValueError(f"Unverified {key}")
        if type(diagnostics.get("preservation_sensitive")) is not bool:
            raise ValueError("Missing preservation sensitivity")
        findings = diagnostics.get("findings")
        if not isinstance(findings, list) or any(not isinstance(f, dict)
                or not isinstance(f.get("code"), str) or not f["code"]
                or f.get("severity") not in {"info", "review", "error"} for f in findings):
            raise ValueError("Invalid findings")
        # Triangle budget excess is the reason to plan, not a geometry defect.
        blockers = sorted({f["code"] for f in findings
                           if f["severity"] == "error" and f["code"] != "triangle_budget_exceeded"})
        reviews = sorted({f["code"] for f in findings if f["severity"] == "review"})
        if diagnostics["preservation_sensitive"]:
            blockers.append("preservation_sensitive")
        if metrics["polygons"] == 0:
            blockers.append("empty_surface")
        report.update({"object": diagnostics["object"], "scene": diagnostics["scene"],
                       "current_triangles": metrics["triangles"], "target_triangles": target_triangles,
                       "blockers": sorted(set(blockers)), "review_items": reviews})
        if blockers:
            report["status"] = "blocked"
        elif reviews:
            report["status"] = "needs_review"
        elif target_triangles is None:
            report["status"] = "needs_target"
        elif metrics["triangles"] <= target_triangles:
            report["status"] = "within_target"
        elif target_triangles == 0:
            report["status"] = "needs_review"
            report["review_items"].append("zero_target_would_remove_surface")
        else:
            report["status"] = "candidate_for_copy_preview"
        # No method, ratio, apply command or authorization follows from a budget.
        report["next_step"] = "Reinspect live source and Profile; establish preservation goals before any copy experiment"
    except (ValueError, TypeError) as exc:
        report["errors"].append(str(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diagnostics", type=Path, help="UTF-8 JSON from fresh base diagnostics")
    parser.add_argument("--target-triangles", type=int)
    args = parser.parse_args()
    try:
        result = plan_static_optimization(json.loads(args.diagnostics.read_text(encoding="utf-8-sig")),
                                          args.target_triangles)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(1, f"Cannot read diagnostics: {exc}\n")
    print(json.dumps(result, allow_nan=False))
    return 1 if result["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
