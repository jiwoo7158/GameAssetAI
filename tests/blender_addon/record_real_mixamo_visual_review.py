import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


CHECKS = {
    "arms_do_not_cross_torso",
    "left_right_arm_phase_matches_source",
    "legs_do_not_over_cross",
    "hip_knee_ankle_direction",
    "head_spine_orientation",
    "severe_tearing_or_collapse",
}


def _pairs(values, label):
    result = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"{label} must use key=value")
        key, item = value.split("=", 1)
        if not key or not item or key in result:
            raise ValueError(f"{label} contains an empty or duplicate key")
        result[key] = item
    return result


def record_review(*, report_path, output, reviewer, reviewed_at, decision, images,
                  findings, notes=None):
    report_path, output = Path(report_path), Path(output)
    if not reviewer.strip():
        raise ValueError("reviewer is required")
    timestamp = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("reviewed-at must include a timezone")
    if decision not in {"accepted", "rejected"}:
        raise ValueError("decision must be accepted or rejected")
    image_args, finding_args = _pairs(images, "image"), _pairs(findings, "finding")
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    if report.get("status") != "structural_pass_visual_review_required":
        raise ValueError("structural report is not awaiting visual review")
    if output.exists():
        raise FileExistsError(output)
    expected_images = report.get("images")
    if not isinstance(expected_images, dict) or not expected_images:
        raise ValueError("structural report has no review images")
    if decision == "accepted" and set(image_args) != set(expected_images):
        raise ValueError("acceptance must identify every structural-report review image")
    if not image_args or not set(image_args).issubset(expected_images):
        raise ValueError("review images must be a non-empty subset of report images")
    image_rows = []
    for key, text in sorted(image_args.items()):
        path = Path(text).resolve(strict=True)
        expected = Path(expected_images[key]).resolve(strict=True)
        if path != expected or path.is_symlink() or not path.is_file():
            raise ValueError(f"review image does not match report image: {key}")
        data = path.read_bytes()
        image_rows.append({"key": key, "path": str(path), "bytes": len(data),
                           "sha256": hashlib.sha256(data).hexdigest()})
    if not finding_args or not set(finding_args).issubset(CHECKS):
        raise ValueError("findings contain missing or unknown checks")
    if decision == "accepted":
        if set(finding_args) != CHECKS:
            raise ValueError("acceptance requires every visual finding")
        allowed = {"accepted", "not_observed"}
        if any(value not in allowed for value in finding_args.values()):
            raise ValueError("acceptance findings must be accepted or not_observed")
    result = {
        "schema": "gameassetai.real-mixamo-visual-review.v1",
        "status": decision,
        "reviewer": reviewer.strip(),
        "reviewed_at": timestamp.isoformat(),
        "notes": notes,
        "structural_report": str(report_path.resolve(strict=True)),
        "structural_report_file_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "source_fbx_sha256": report["source_fbx_sha256"],
        "reviewed_images": image_rows,
        "checks": finding_args,
        "boundary": "IN_PLACE only; TRANSFER root motion remains unapproved",
    }
    result["review_sha256"] = hashlib.sha256(canonical(result).encode()).hexdigest()
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--decision", choices=("accepted", "rejected"), required=True)
    parser.add_argument("--image", action="append", default=[], help="report-key=exact-path")
    parser.add_argument("--finding", action="append", default=[], help="check=value")
    parser.add_argument("--notes")
    args = parser.parse_args()
    result = record_review(report_path=args.report, output=args.output,
                           reviewer=args.reviewer, reviewed_at=args.reviewed_at,
                           decision=args.decision, images=args.image,
                           findings=args.finding, notes=args.notes)
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "review_sha256": result["review_sha256"]}))


if __name__ == "__main__":
    main()
