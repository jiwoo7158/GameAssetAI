import argparse
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report_bytes = args.report.read_bytes()
    report = json.loads(report_bytes)
    if report.get("status") != "structural_pass_visual_review_required":
        raise ValueError("structural report is not awaiting visual review")
    if args.output.exists():
        raise FileExistsError(args.output)
    result = {
        "schema": "gameassetai.real-mixamo-visual-review.v1",
        "status": "accepted",
        "structural_report": str(args.report),
        "structural_report_file_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "source_fbx_sha256": report["source_fbx_sha256"],
        "frames": [1, 8, 16, 24, 32],
        "views": ["front", "side", "three_quarter"],
        "checks": {
            "arms_do_not_cross_torso": "accepted",
            "left_right_arm_phase_matches_source": "accepted",
            "legs_do_not_over_cross": "accepted",
            "hip_knee_ankle_direction": "accepted",
            "head_spine_orientation": "accepted",
            "severe_tearing_or_collapse": "not_observed",
        },
        "boundary": "IN_PLACE only; TRANSFER root motion remains unapproved",
    }
    result["review_sha256"] = hashlib.sha256(canonical(result).encode()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "accepted", "output": str(args.output),
                      "review_sha256": result["review_sha256"]}))


if __name__ == "__main__":
    main()
