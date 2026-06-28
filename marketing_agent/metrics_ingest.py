import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METRICS_PATH = ROOT / "marketing" / "content_metrics.json"

NUMERIC_FIELDS = [
    "views",
    "clicks",
    "scoreCompletions",
    "checkoutStarts",
    "purchases",
    "likes",
    "comments",
    "shares",
    "averageViewDuration",
    "retentionPercent",
]


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def parse_number(value):
    if value in (None, ""):
        return 0
    try:
        if isinstance(value, str) and "." in value:
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0


def metric_key(platform: str, file: str) -> str:
    return f"{platform}:{file}"


def normalize_row(row: dict) -> tuple[str, dict] | None:
    platform = str(row.get("platform", "")).strip().lower()
    file = str(row.get("file", "")).strip()
    if not platform or not file:
        return None

    metric = {
        field: parse_number(row.get(field, 0))
        for field in NUMERIC_FIELDS
        if row.get(field, "") not in ("", None)
    }
    metric["source"] = str(row.get("source", "manual")).strip() or "manual"
    metric["capturedAt"] = str(row.get("capturedAt", "")).strip()
    metric["notes"] = str(row.get("notes", "")).strip()
    return metric_key(platform, file), metric


def load_rows(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            if isinstance(data.get("metrics"), list):
                return [item for item in data["metrics"] if isinstance(item, dict)]
            return [data]
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_sample(path: Path) -> None:
    rows = [
        {
            "platform": "youtube",
            "file": "videos/resume-crime-scene-demand-gen.mp4",
            "views": 0,
            "clicks": 0,
            "scoreCompletions": 0,
            "checkoutStarts": 0,
            "purchases": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "averageViewDuration": 0,
            "retentionPercent": 0,
            "source": "manual",
            "capturedAt": "",
            "notes": "Replace with 24-hour platform metrics.",
        }
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import social/video metrics into marketing/content_metrics.json.")
    parser.add_argument("--input", type=Path, help="CSV or JSON file with platform,file,views,clicks,scoreCompletions,purchases...")
    parser.add_argument("--sample", type=Path, help="Write a sample CSV or JSON metrics import file.")
    parser.add_argument("--replace", action="store_true", help="Replace existing metrics instead of merging.")
    args = parser.parse_args()

    if args.sample:
        write_sample(args.sample)
        print(f"Sample metrics file written: {args.sample}")
        return

    if not args.input:
        parser.error("--input is required unless --sample is used.")

    existing = {} if args.replace else read_json(METRICS_PATH, {})
    if not isinstance(existing, dict):
        existing = {}

    imported = 0
    for row in load_rows(args.input):
        normalized = normalize_row(row)
        if not normalized:
            continue
        key, metric = normalized
        existing[key] = {**existing.get(key, {}), **metric}
        imported += 1

    METRICS_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(json.dumps({"imported": imported, "metricsPath": str(METRICS_PATH.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
