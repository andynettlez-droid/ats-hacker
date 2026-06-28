import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETING_DIR = ROOT / "marketing"
CALENDAR_PATH = MARKETING_DIR / "content_calendar.json"
POSTS_PATH = MARKETING_DIR / "autopost" / "posts.json"
METRICS_PATH = MARKETING_DIR / "content_metrics.json"
REPORTS_DIR = MARKETING_DIR / "content_reports"
AUDIO_DIR = MARKETING_DIR / "remotion" / "public" / "audio"
TREND_INTAKE_PATH = MARKETING_DIR / "content_research" / "trend_intake_latest.json"


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def as_list(value):
    return value if isinstance(value, list) else []


def metric_key(platform: str, file: str) -> str:
    return f"{platform}:{file}"


def load_metrics():
    metrics = read_json(METRICS_PATH, {})
    return metrics if isinstance(metrics, dict) else {}


def summarize_post(post: dict, metrics: dict) -> dict:
    file = post.get("file", "")
    platforms = as_list(post.get("platforms"))
    platform_metrics = {}
    for platform in platforms:
        platform_metrics[platform] = metrics.get(metric_key(platform, file), {})

    return {
        "title": post.get("title") or (post.get("caption", "")[:80]),
        "file": file,
        "platforms": platforms,
        "status": post.get("status", "queued"),
        "scheduleDate": post.get("scheduleDate"),
        "postedAt": post.get("postedAt"),
        "lastError": post.get("lastError"),
        "metrics": platform_metrics,
    }


def score_asset(post: dict, metrics: dict) -> dict:
    status = post.get("status", "queued")
    file = post.get("file", "")
    platforms = as_list(post.get("platforms"))
    all_metrics = [metrics.get(metric_key(platform, file), {}) for platform in platforms]
    views = sum(int(item.get("views", 0) or 0) for item in all_metrics)
    clicks = sum(int(item.get("clicks", 0) or 0) for item in all_metrics)
    score_completions = sum(int(item.get("scoreCompletions", 0) or 0) for item in all_metrics)
    purchases = sum(int(item.get("purchases", 0) or 0) for item in all_metrics)

    if status in {"review_required", "draft"}:
        next_action = "Review the exact video, caption, and CTA before posting."
    elif status == "failed":
        next_action = "Fix upload failure and retry dry run."
    elif status == "scheduled":
        next_action = "Wait for publish, then add platform metrics after 24 hours."
    elif status == "posted" and views == 0:
        next_action = "Add 24-hour metrics from platform dashboards or APIs."
    elif purchases > 0:
        next_action = "Study and remix this format; it produced revenue."
    elif score_completions > 0:
        next_action = "Improve checkout bridge; viewers are trying the score."
    elif clicks > 0:
        next_action = "Improve landing-page/message match; clicks are not becoming scores yet."
    elif views > 0:
        next_action = "Improve hook/CTA; views are not turning into clicks yet."
    else:
        next_action = "No performance data yet."

    return {
        "file": file,
        "status": status,
        "views": views,
        "clicks": clicks,
        "scoreCompletions": score_completions,
        "purchases": purchases,
        "nextAction": next_action,
    }


def build_report() -> dict:
    calendar = as_list(read_json(CALENDAR_PATH, []))
    posts = as_list(read_json(POSTS_PATH, []))
    metrics = load_metrics()
    post_grade_packets = [
        entry
        for entry in calendar
        if isinstance(entry.get("creativeQuality"), dict) and entry["creativeQuality"].get("passed")
    ]
    render_ready_shorts = sum(len(as_list(entry.get("shorts"))) for entry in calendar)
    has_calendar_voiceover = any(
        isinstance(short.get("audioReadiness"), dict) and short["audioReadiness"].get("studioVoiceover")
        for entry in calendar
        for short in as_list(entry.get("shorts"))
        if isinstance(short, dict)
    )
    trend_intake = read_json(TREND_INTAKE_PATH, {})
    has_source_backed_trend_intake = bool(
        isinstance(trend_intake, dict)
        and trend_intake.get("topCandidate")
        and any(
            isinstance(note, dict) and note.get("url")
            for note in as_list(trend_intake.get("topCandidate", {}).get("sourceNotes"))
        )
    )
    has_studio_voiceover = (
        has_calendar_voiceover
        or any(AUDIO_DIR.glob("daily-*-voiceover.mp3"))
        or (AUDIO_DIR / "signal-studio-voiceover.mp3").exists()
    )
    has_quiet_music = (AUDIO_DIR / "signal-quiet-orbit.wav").exists() or (AUDIO_DIR / "signal-studio-bed.mp3").exists()

    queue_counts = {}
    for post in posts:
        status = post.get("status", "queued")
        queue_counts[status] = queue_counts.get(status, 0) + 1

    calendar_counts = {}
    for entry in calendar:
        status = entry.get("reviewStatus", "unknown")
        calendar_counts[status] = calendar_counts.get(status, 0) + 1

    scored_assets = [score_asset(post, metrics) for post in posts]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "calendarPath": str(CALENDAR_PATH.relative_to(ROOT)),
        "postsPath": str(POSTS_PATH.relative_to(ROOT)),
        "metricsPath": str(METRICS_PATH.relative_to(ROOT)),
        "trendIntakePath": str(TREND_INTAKE_PATH.relative_to(ROOT)),
        "calendarCounts": calendar_counts,
        "queueCounts": queue_counts,
        "dailyPackets": calendar,
        "queuedPosts": [summarize_post(post, metrics) for post in posts],
        "assetScorecards": scored_assets,
        "creativeReadiness": {
            "postGradePackets": len(post_grade_packets),
            "renderReadyShorts": render_ready_shorts,
            "hasStudioVoiceover": has_studio_voiceover,
            "hasQuietMusic": has_quiet_music,
            "hasSourceBackedTrendIntake": has_source_backed_trend_intake,
            "needsFullRenderReview": any(entry.get("reviewStatus") == "needs_render_and_review" for entry in calendar),
        },
        "monetizationReadiness": {
            "hasDailyPacket": bool(calendar),
            "hasPostGradeCreativePacket": bool(post_grade_packets),
            "hasReviewQueue": any(post.get("status") == "review_required" for post in posts),
            "hasPostedAssets": any(post.get("status") == "posted" for post in posts),
            "hasMetrics": bool(metrics),
            "hasStudioVoiceover": has_studio_voiceover,
            "hasQuietMusic": has_quiet_music,
            "hasSourceBackedTrendIntake": has_source_backed_trend_intake,
            "missing": [
                item
                for item, ok in [
                    ("platform metrics feed", bool(metrics)),
                    ("studio voiceover for daily shorts", has_studio_voiceover),
                    ("long-form 16:9 renderer", False),
                    ("thumbnail generator", False),
                    ("source-backed trend intake", has_source_backed_trend_intake),
                    ("automated live trend API connector", False),
                ]
                if not ok
            ],
        },
    }


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Signal Content Monitor",
        "",
        f"Generated: {report['generatedAt']}",
        "",
        "## Queue Counts",
        "",
    ]
    for status, count in sorted(report["queueCounts"].items()):
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Monetization Readiness", ""])
    readiness = report["monetizationReadiness"]
    lines.extend([
        f"- Daily packet exists: {readiness['hasDailyPacket']}",
        f"- Post-grade creative packet exists: {readiness['hasPostGradeCreativePacket']}",
        f"- Review queue exists: {readiness['hasReviewQueue']}",
        f"- Posted assets exist: {readiness['hasPostedAssets']}",
        f"- Metrics available: {readiness['hasMetrics']}",
        f"- Studio voiceover available: {readiness['hasStudioVoiceover']}",
        f"- Quiet music available: {readiness['hasQuietMusic']}",
        f"- Source-backed trend intake available: {readiness['hasSourceBackedTrendIntake']}",
        "",
        "Missing:",
    ])
    lines.extend(f"- {item}" for item in readiness["missing"])
    lines.extend(["", "## Creative Readiness", ""])
    creative = report["creativeReadiness"]
    lines.extend([
        f"- Post-grade packets: {creative['postGradePackets']}",
        f"- Render-ready shorts: {creative['renderReadyShorts']}",
        f"- Studio voiceover: {creative['hasStudioVoiceover']}",
        f"- Quiet music: {creative['hasQuietMusic']}",
        f"- Source-backed trend intake: {creative['hasSourceBackedTrendIntake']}",
        f"- Needs full render review: {creative['needsFullRenderReview']}",
    ])
    lines.extend(["", "## Daily Packets", ""])
    for entry in report["dailyPackets"]:
        quality = entry.get("creativeQuality") if isinstance(entry.get("creativeQuality"), dict) else {}
        lines.extend([
            f"### {entry.get('date', '')} - {entry.get('topic', '')}",
            "",
            f"- Review status: {entry.get('reviewStatus', 'unknown')}",
            f"- Creative verdict: {quality.get('verdict', 'unknown')}",
            f"- Creative score: {quality.get('overallScore', 'n/a')}/100",
            "",
        ])
    lines.extend(["", "## Asset Scorecards", ""])
    for asset in report["assetScorecards"]:
        lines.extend([
            f"### {asset['file']}",
            "",
            f"- Status: {asset['status']}",
            f"- Views: {asset['views']}",
            f"- Clicks: {asset['clicks']}",
            f"- Score completions: {asset['scoreCompletions']}",
            f"- Purchases: {asset['purchases']}",
            f"- Next action: {asset['nextAction']}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Monitor Signal content pipeline readiness and performance.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    parser.add_argument("--write", action="store_true", help="Write a markdown report to marketing/content_reports.")
    args = parser.parse_args()

    report = build_report()
    if args.write:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_path = REPORTS_DIR / f"content-monitor-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md"
        write_markdown(report, report_path)
        report["reportPath"] = str(report_path.relative_to(ROOT))

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("Signal content monitor")
        print(f"Queue counts: {report['queueCounts']}")
        print(f"Missing: {', '.join(report['monetizationReadiness']['missing']) or 'none'}")
        if args.write:
            print(f"Report: {report['reportPath']}")


if __name__ == "__main__":
    main()
