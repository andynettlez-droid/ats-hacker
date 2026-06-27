"""
CapCut Desktop Project Exporter
================================
Generates a valid CapCut Desktop draft project folder from a rendered MP4
and voiceover script. The project appears in CapCut's "My Drafts" and
includes the video clip + pre-timed viral-style captions on the timeline.

Usage (standalone):
    py capcut_exporter.py --video path/to/video.mp4 --text "voiceover script" --name "my-ad"

Usage (from video_pipeline.py):
    from capcut_exporter import export_to_capcut
    export_to_capcut(video_path, voiceover_text, project_name, props)
"""

import os
import sys
import json
import uuid
import time
import shutil
import argparse
import subprocess

# CapCut default drafts directory on Windows
DEFAULT_CAPCUT_DRAFTS_DIR = os.path.join(
    os.path.expanduser("~"),
    "AppData", "Local", "CapCut", "User Data", "Projects", "com.lveditor.draft"
)


def generate_id():
    """Generate a CapCut-compatible UUID (uppercase, no hyphens)."""
    return uuid.uuid4().hex.upper()


def microseconds(seconds):
    """Convert seconds to microseconds (CapCut's native time unit)."""
    return int(seconds * 1_000_000)


def get_video_duration_ms(video_path):
    """
    Attempt to get video duration in microseconds using ffprobe.
    Falls back to a default 17 seconds if ffprobe is unavailable.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            duration_sec = float(data["format"]["duration"])
            print(f"    [ffprobe] Detected video duration: {duration_sec:.2f}s")
            return microseconds(duration_sec)
    except Exception as e:
        print(f"    [!] ffprobe unavailable ({e}), using default duration.")

    # Default: 17 seconds (matches our Remotion AvatarReveal)
    return microseconds(17.0)


def generate_caption_segments(voiceover_text, total_duration_us, words_per_group=3):
    """
    Split voiceover text into timed caption groups.
    Returns a list of dicts: {text, start_us, duration_us}
    """
    words = voiceover_text.split()
    if not words:
        return []

    groups = []
    for i in range(0, len(words), words_per_group):
        group_text = " ".join(words[i:i + words_per_group])
        groups.append(group_text)

    if not groups:
        return []

    # Distribute evenly across the video with small padding
    padding_us = microseconds(0.5)  # 0.5s padding at start/end
    usable_duration = total_duration_us - (padding_us * 2)
    segment_duration = usable_duration // len(groups)

    segments = []
    for idx, text in enumerate(groups):
        segments.append({
            "text": text,
            "start_us": padding_us + (idx * segment_duration),
            "duration_us": segment_duration,
        })

    return segments


def build_text_material(mat_id, text, font_size=12.0):
    """Build a CapCut text material entry for the materials.texts array."""
    # CapCut uses a rich content JSON string inside the text material
    content = json.dumps({
        "styles": [{
            "font": {
                "id": "",
                "path": "",
                "name": "Inter"
            },
            "size": font_size,
            "bold": True,
            "italic": False,
            "underline": False,
            "color": [1.0, 1.0, 1.0],  # White RGB normalized
            "useLetterColor": True,
            "range": [0, len(text)]
        }],
        "text": text
    })

    return {
        "id": mat_id,
        "type": "text",
        "content": content,
        "font_path": "",
        "font_size": font_size,
        "font_name": "Inter",
        "font_color": [1.0, 1.0, 1.0],
        "background_color": [0.0, 0.0, 0.0, 0.0],
        "alignment": 1,  # Center
        "bold": True,
        "italic": False,
        "underline": False,
        "shadow": {
            "color": [0.0, 0.0, 0.0, 0.75],
            "point": [0.0, 2.0],
            "blur": 4.0,
            "enabled": True
        },
        "stroke": {
            "color": [0.0, 0.0, 0.0, 1.0],
            "width": 3.0,
            "enabled": True
        },
        "letter_spacing": 0.0,
        "line_spacing": 0.02,
    }


def build_draft_content(video_path, voiceover_text, total_duration_us, props=None):
    """
    Build the complete draft_content.json structure.
    """
    # === IDs ===
    video_material_id = generate_id()
    canvas_id = generate_id()

    # === Materials ===
    video_material = {
        "id": video_material_id,
        "type": "video",
        "path": os.path.abspath(video_path).replace("/", "\\"),
        "duration": total_duration_us,
        "width": 1080,
        "height": 1920,
        "category_name": "local",
        "material_name": os.path.basename(video_path),
    }

    # Text materials for captions
    caption_segments = generate_caption_segments(voiceover_text, total_duration_us)
    text_materials = []
    text_track_segments = []

    for idx, seg in enumerate(caption_segments):
        mat_id = generate_id()
        seg_id = generate_id()

        text_materials.append(
            build_text_material(mat_id, seg["text"], font_size=10.0)
        )

        text_track_segments.append({
            "id": seg_id,
            "material_id": mat_id,
            "target_timerange": {
                "start": seg["start_us"],
                "duration": seg["duration_us"]
            },
            "source_timerange": {
                "start": 0,
                "duration": seg["duration_us"]
            },
            "extra_material_refs": [],
            "enable_adjust": True,
            "enable_color_correct_adjust": False,
            "enable_lut": False,
            "clip": {
                "alpha": 1.0,
                "flip": {"horizontal": False, "vertical": False},
                "rotation": 0.0,
                "scale": {"x": 1.0, "y": 1.0},
                "transform": {"x": 0.0, "y": 0.35}  # Lower-third position
            },
            "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
            "render_index": 20000 + idx,
            "speed": 1.0,
            "volume": 0.0,
            "visible": True
        })

    # === Video Track Segment ===
    video_segment_id = generate_id()
    video_track_segment = {
        "id": video_segment_id,
        "material_id": video_material_id,
        "target_timerange": {
            "start": 0,
            "duration": total_duration_us
        },
        "source_timerange": {
            "start": 0,
            "duration": total_duration_us
        },
        "extra_material_refs": [],
        "enable_adjust": True,
        "enable_color_correct_adjust": False,
        "enable_lut": False,
        "clip": {
            "alpha": 1.0,
            "flip": {"horizontal": False, "vertical": False},
            "rotation": 0.0,
            "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}
        },
        "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000},
        "render_index": 10000,
        "speed": 1.0,
        "volume": 1.0,
        "visible": True
    }

    # === Tracks ===
    video_track = {
        "id": generate_id(),
        "type": "video",
        "attribute": 0,
        "flag": 0,
        "segments": [video_track_segment]
    }

    text_track = {
        "id": generate_id(),
        "type": "text",
        "attribute": 0,
        "flag": 0,
        "segments": text_track_segments
    }

    # === Full Draft ===
    draft = {
        "id": generate_id(),
        "canvas_config": {
            "height": 1920,
            "width": 1080,
            "ratio": "original"
        },
        "color_space": 0,
        "create_time": int(time.time()),
        "duration": total_duration_us,
        "fps": 30.0,
        "free_render_index_mode_on": False,
        "group_container": None,
        "keyframe_graph_list": [],
        "keyframes": {"adjusts": [], "audios": [], "effects": [], "filters": [], "stickers": [], "texts": [], "videos": []},
        "materials": {
            "audios": [],
            "canvases": [{
                "id": canvas_id,
                "type": "canvas_color",
                "color": "",
                "image": "",
                "image_id": "",
                "image_name": "",
                "blur": 0.0
            }],
            "drafts": [],
            "effects": [],
            "flowers": [],
            "handwrites": [],
            "material_animations": [],
            "material_colors": [],
            "placeholders": [],
            "realtime_denoises": [],
            "smart_crops": [],
            "smart_relayouts": [],
            "sound_channel_mappings": [],
            "speeds": [],
            "stickers": [],
            "tail_leaders": [],
            "text_templates": [],
            "texts": text_materials,
            "transitions": [],
            "video_effects": [],
            "video_trackings": [],
            "videos": [video_material],
            "vocal_beautifys": [],
            "vocal_separations": []
        },
        "mutable_config": None,
        "name": "",
        "new_version": "113.0.0",
        "platform": {
            "app_id": 359289,
            "app_source": "cc_windows",
            "app_version": "5.9.0",
            "device_id": "",
            "hard_disk_id": "",
            "mac_address": "",
            "os": "windows",
            "os_version": "10.0"
        },
        "relationships": [],
        "render_index_track_mode_on": False,
        "retouch_cover": None,
        "source": "default",
        "static_cover_image_path": "",
        "tracks": [video_track, text_track],
        "update_time": int(time.time()),
        "version": 360000
    }

    return draft


def build_meta_info(project_name, total_duration_us):
    """Build the draft_meta_info.json file."""
    return {
        "draft_fold_path": "",
        "draft_id": generate_id(),
        "draft_name": project_name,
        "draft_removable_storage_device": "",
        "draft_root_path": "",
        "draft_timeline_materials_size_": 0,
        "draft_materials_copied_": False,
        "tm_draft_create": int(time.time()),
        "tm_draft_modified": int(time.time()),
        "tm_duration": total_duration_us // 1000,  # milliseconds
    }


def build_settings():
    """Build the draft_settings.json file."""
    return {
        "canvas_config": {
            "height": 1920,
            "width": 1080,
            "ratio": "original"
        },
        "has_music": False
    }


def export_to_capcut(video_path, voiceover_text, project_name="ats-hacker-viral-ad", props=None,
                     capcut_drafts_dir=None, auto_launch=False):
    """
    Main export function. Creates a CapCut draft project folder and copies it
    into CapCut's drafts directory.

    Args:
        video_path: Path to the rendered MP4 file.
        voiceover_text: The voiceover script text for caption generation.
        project_name: Name for the CapCut project.
        props: Optional dict of video props (hook1, hook2, etc.) for metadata.
        capcut_drafts_dir: Override for CapCut's drafts directory path.
        auto_launch: If True, attempt to open CapCut after export.

    Returns:
        str: Path to the created CapCut project folder.
    """
    drafts_dir = capcut_drafts_dir or os.getenv("CAPCUT_DRAFTS_DIR", DEFAULT_CAPCUT_DRAFTS_DIR)

    print(f"\n{'=' * 65}")
    print(f"[*] CapCut Exporter: Starting project generation...")
    print(f"{'=' * 65}")
    print(f"    Video source : {video_path}")
    print(f"    Project name : {project_name}")
    print(f"    CapCut drafts: {drafts_dir}")

    # Validate inputs
    if not os.path.exists(video_path):
        print(f"[-] ERROR: Video file not found: {video_path}")
        return None

    if not os.path.isdir(drafts_dir):
        print(f"[-] ERROR: CapCut drafts directory not found: {drafts_dir}")
        print(f"    Make sure CapCut Desktop is installed and has been opened at least once.")
        return None

    # Get video duration
    abs_video_path = os.path.abspath(video_path)
    total_duration_us = get_video_duration_ms(abs_video_path)
    duration_sec = total_duration_us / 1_000_000
    print(f"    Duration     : {duration_sec:.1f}s ({total_duration_us} µs)")

    # Create unique project folder
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    folder_name = f"{project_name}_{timestamp}"
    project_dir = os.path.join(drafts_dir, folder_name)
    resources_dir = os.path.join(project_dir, "resources")
    os.makedirs(resources_dir, exist_ok=True)

    print(f"    Project dir  : {project_dir}")

    # Copy video into resources
    dest_video = os.path.join(resources_dir, os.path.basename(video_path))
    shutil.copy2(abs_video_path, dest_video)
    print(f"[+] Copied video to: {dest_video}")

    # Build and write draft_content.json
    draft = build_draft_content(dest_video, voiceover_text, total_duration_us, props)
    draft_path = os.path.join(project_dir, "draft_content.json")
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(draft, f, ensure_ascii=False, indent=2)
    print(f"[+] Written: draft_content.json ({len(json.dumps(draft))} bytes)")

    # Build and write draft_meta_info.json
    meta = build_meta_info(project_name, total_duration_us)
    meta_path = os.path.join(project_dir, "draft_meta_info.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"[+] Written: draft_meta_info.json")

    # Build and write draft_settings.json
    settings = build_settings()
    settings_path = os.path.join(project_dir, "draft_settings.json")
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    print(f"[+] Written: draft_settings.json")

    # Caption summary
    caption_segments = generate_caption_segments(voiceover_text, total_duration_us)
    print(f"[+] Generated {len(caption_segments)} caption segments")

    # Summary
    print(f"\n{'=' * 65}")
    print(f"[+] CapCut project created successfully!")
    print(f"    Path: {project_dir}")
    print(f"    Open CapCut Desktop -> 'My Drafts' -> '{project_name}'")
    print(f"    Tips: Use CapCut's Auto-Captions, effects, and trending music")
    print(f"{'=' * 65}\n")

    # Auto-launch CapCut if requested
    if auto_launch and sys.platform == "win32":
        try:
            capcut_exe = os.path.join(
                os.path.expanduser("~"),
                "AppData", "Local", "CapCut", "Apps", "CapCut.exe"
            )
            if os.path.exists(capcut_exe):
                print(f"[*] Launching CapCut Desktop...")
                subprocess.Popen([capcut_exe], shell=False)
            else:
                print(f"[!] CapCut executable not found at expected path. Open CapCut manually.")
        except Exception as e:
            print(f"[!] Could not auto-launch CapCut: {e}")

    return project_dir


def main():
    """CLI entry point for standalone use."""
    parser = argparse.ArgumentParser(description="CapCut Desktop Project Exporter")
    parser.add_argument("--video", type=str, required=True, help="Path to the MP4 video file")
    parser.add_argument("--text", type=str, default="", help="Voiceover text for caption generation")
    parser.add_argument("--name", type=str, default="ats-hacker-viral-ad", help="CapCut project name")
    parser.add_argument("--capcut-dir", type=str, default=None, help="Override CapCut drafts directory")
    parser.add_argument("--launch", action="store_true", help="Auto-launch CapCut after export")

    args = parser.parse_args()

    export_to_capcut(
        video_path=args.video,
        voiceover_text=args.text,
        project_name=args.name,
        capcut_drafts_dir=args.capcut_dir,
        auto_launch=args.launch
    )


if __name__ == "__main__":
    main()
