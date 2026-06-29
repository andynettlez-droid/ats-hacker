import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REMOTION_OUT = ROOT / "marketing" / "remotion" / "out"
AUTOPOST_DIR = ROOT / "marketing" / "autopost"
AUTOPOST_VIDEOS = AUTOPOST_DIR / "videos"
POSTS_PATH = AUTOPOST_DIR / "posts.json"
DAILY_DIR = ROOT / "marketing" / "daily_content"


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def latest_drafts_path() -> Path:
    drafts = sorted(DAILY_DIR.glob("*/autopost_drafts.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not drafts:
        raise FileNotFoundError("No autopost_drafts.json found under marketing/daily_content.")
    return drafts[0]


def is_youtube_longform(draft: dict) -> bool:
    return draft.get("contentType") == "youtube_long_form" or draft.get("youtubeKind") == "long_form"


def promoted_qa_gate(draft: dict) -> dict:
    qa_gate = draft.get("qaGate") if isinstance(draft.get("qaGate"), dict) else {}
    if is_youtube_longform(draft):
        return {
            **qa_gate,
            "required": True,
            "passed": bool(qa_gate.get("passed", False)),
            "status": qa_gate.get("status") or "rendered_needs_human_qa",
        }
    return qa_gate


def promote(drafts_path: Path, only: str | None = None, replace_posted: bool = False) -> dict:
    drafts = read_json(drafts_path, [])
    if not isinstance(drafts, list):
        raise ValueError(f"Drafts file must contain a list: {drafts_path}")

    posts = read_json(POSTS_PATH, [])
    if not isinstance(posts, list):
        posts = []

    AUTOPOST_VIDEOS.mkdir(parents=True, exist_ok=True)
    promoted = []
    skipped = []
    missing = []

    for draft in drafts:
        if not isinstance(draft, dict):
            continue
        file_ref = str(draft.get("file", ""))
        if only and file_ref != only and draft.get("title") != only:
            skipped.append({"file": file_ref, "reason": "not selected"})
            continue

        filename = Path(file_ref).name
        source = REMOTION_OUT / filename
        if not source.exists():
            missing.append({"file": file_ref, "expectedRender": str(source.relative_to(ROOT))})
            continue

        post = {
            "title": draft.get("title", filename)[:96],
            "caption": draft.get("caption", ""),
            "file": f"videos/{filename}",
            "platforms": draft.get("platforms", ["tiktok", "instagram", "youtube"]),
            "scheduleDate": draft.get("scheduleDate"),
            "status": "review_required",
            "contentType": draft.get("contentType"),
            "youtubeKind": draft.get("youtubeKind"),
            "target": draft.get("target"),
            "youtubeTitle": draft.get("youtubeTitle"),
            "youtubeDescription": draft.get("youtubeDescription"),
            "thumbnail": draft.get("thumbnail"),
            "thumbnailProps": draft.get("thumbnailProps"),
            "renderStatus": "rendered_review_required" if is_youtube_longform(draft) else draft.get("renderStatus"),
            "reviewStatus": "review_required",
            "composition": draft.get("composition"),
            "renderProps": draft.get("renderProps"),
            "audioReadiness": draft.get("audioReadiness", {}),
            "qaGate": promoted_qa_gate(draft),
            "expertViralGate": draft.get("expertViralGate"),
            "expertViralScore": draft.get("expertViralScore"),
            "reviewChecklist": draft.get("reviewChecklist", []),
        }
        post = {key: value for key, value in post.items() if value not in (None, {}, [])}

        existing_index = next((idx for idx, item in enumerate(posts) if item.get("file") == post["file"]), None)
        if existing_index is None:
            posts.append(post)
        else:
            if posts[existing_index].get("status") == "posted" and not replace_posted:
                skipped.append({
                    "file": post["file"],
                    "reason": "existing post is already marked posted; use --replace-posted only for an intentional repost",
                })
                continue
            posts[existing_index] = {**posts[existing_index], **post}

        dest = AUTOPOST_VIDEOS / filename
        shutil.copyfile(source, dest)
        promoted.append({"file": post["file"], "status": post["status"]})

    if promoted:
        POSTS_PATH.write_text(json.dumps(posts, indent=4) + "\n", encoding="utf-8")

    return {
        "drafts": str(drafts_path.relative_to(ROOT)),
        "promoted": promoted,
        "missing": missing,
        "skipped": skipped,
        "postsPath": str(POSTS_PATH.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy rendered daily videos to autopost/videos and register review-gated posts.")
    parser.add_argument("--drafts", type=Path, default=None, help="Path to autopost_drafts.json. Defaults to newest daily packet.")
    parser.add_argument("--only", default=None, help="Only promote a specific draft file ref or title.")
    parser.add_argument("--replace-posted", action="store_true", help="Allow a draft to overwrite a post record that is already marked posted.")
    args = parser.parse_args()

    result = promote(args.drafts or latest_drafts_path(), args.only, args.replace_posted)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
