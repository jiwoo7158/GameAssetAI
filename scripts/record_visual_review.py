"""Record an explicit, hash-bound visual decision for a structural validation report."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_review(*, report_path, output, reviewer, reviewed_at, decision, findings):
    report_path, output = Path(report_path), Path(output)
    if not reviewer.strip():
        raise ValueError("reviewer is required")
    timestamp = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
    if timestamp.tzinfo is None:
        raise ValueError("reviewed_at must include a timezone")
    if decision not in {"accepted", "rejected"}:
        raise ValueError("decision must be accepted or rejected")
    if output.exists():
        raise FileExistsError(output)
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    if report.get("status") != "structural_pass_visual_review_required":
        raise ValueError("structural report is not awaiting visual review")
    images = report.get("images")
    checks = report.get("required_visual_checks")
    if not isinstance(images, dict) or not images or not isinstance(checks, list) or not checks:
        raise ValueError("structural report must declare images and required_visual_checks")
    if set(findings) != set(checks):
        raise ValueError("findings must cover every required visual check exactly")
    allowed = {"accepted", "not_observed"} if decision == "accepted" else {"rejected", "observed"}
    if any(value not in allowed for value in findings.values()):
        raise ValueError("finding values do not match the decision")
    reviewed_images = []
    for key, raw_path in sorted(images.items()):
        path = Path(raw_path).resolve(strict=True)
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"review image is not a regular file: {key}")
        data = path.read_bytes()
        reviewed_images.append({
            "key": key, "path": str(path), "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    result = {
        "schema": "gameassetai.visual-review.v1",
        "status": decision,
        "reviewer": reviewer.strip(),
        "reviewed_at": timestamp.isoformat(),
        "structural_report": str(report_path.resolve(strict=True)),
        "structural_report_file_sha256": hashlib.sha256(report_bytes).hexdigest(),
        "reviewed_images": reviewed_images,
        "checks": findings,
    }
    result["review_sha256"] = hashlib.sha256(_canonical(result).encode()).hexdigest()
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--decision", choices=("accepted", "rejected"), required=True)
    parser.add_argument("--finding", action="append", default=[])
    args = parser.parse_args()
    findings = {}
    for item in args.finding:
        if "=" not in item:
            raise ValueError("finding must use key=value")
        key, value = item.split("=", 1)
        if not key or key in findings:
            raise ValueError("finding keys must be non-empty and unique")
        findings[key] = value
    result = record_review(
        report_path=args.report, output=args.output, reviewer=args.reviewer,
        reviewed_at=args.reviewed_at, decision=args.decision, findings=findings,
    )
    print(json.dumps({"status": result["status"], "review_sha256": result["review_sha256"]}))


if __name__ == "__main__":
    main()
