#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$PWD}"
OUT="${OUT:-signal_pipeline_review.mp4}"
BACKGROUND_CLIP="${BACKGROUND_CLIP:-}"
BURN_CAPTIONS="${BURN_CAPTIONS:-false}"
USE_HAND_PLATES="${USE_HAND_PLATES:-false}"
cd "$WORKDIR"

if command -v ffmpeg >/dev/null 2>&1; then
  FFMPEG="$(command -v ffmpeg)"
else
  FFMPEG="$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())' 2>/dev/null || true)"
fi
[[ -n "$FFMPEG" && -x "$FFMPEG" ]] || { echo "ffmpeg not found. Install ffmpeg or imageio-ffmpeg first." >&2; exit 1; }

FFPROBE="$(command -v ffprobe || true)"

shots=(shot01.mp4 shot02.mp4 shot03.mp4 shot04.mp4)
voices=(vo_hook.mp3 vo_search.mp3 vo_demo.mp3 vo_cta.mp3)
texts=(vo_hook.txt vo_search.txt vo_demo.txt vo_cta.txt)
fallbacks=(
  "Let's look at this resume."
  "The recruiter search misses it."
  "Now rewrite the weak bullet."
  "Need yours fixed? Link in bio."
)

for i in "${!shots[@]}"; do
  [[ -f "${shots[$i]}" ]] || { echo "Missing input: ${shots[$i]}" >&2; exit 1; }
  [[ -f "${voices[$i]}" ]] || { echo "Missing input: ${voices[$i]}" >&2; exit 1; }
done

dur(){
  if [[ -n "$FFPROBE" ]]; then
    "$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$1"
  else
    "$FFMPEG" -i "$1" 2>&1 | sed -nE 's/.*Duration: ([0-9]+):([0-9]+):([0-9.]+).*/\1 \2 \3/p' | awk '{print ($1*3600)+($2*60)+$3; exit}'
  fi
}

vf="scale=1188:2112:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)/2:(ih-oh)/2,fps=30,setsar=1,format=yuv420p"
hand_vf="scale=1188:2112:force_original_aspect_ratio=increase,crop=1080:1920:(iw-ow)/2:(ih-oh)/2,fps=30,setsar=1,format=rgba,colorkey=0x23B82E:0.34:0.03"
segments_json="["
timeline=0
list_file="concat_list.txt"
: > "$list_file"

for i in "${!shots[@]}"; do
  idx="$(printf "%02d" "$((i + 1))")"
  overlay="overlay$idx.png"
  overlay_frame_dir="overlay${idx}_frames"
  overlay_frame_pattern="$overlay_frame_dir/%04d.png"
  handplate="handplate$idx.mp4"
  use_handplate=false
  if [[ "$USE_HAND_PLATES" == "true" || "$USE_HAND_PLATES" == "1" ]]; then
    [[ -f "$handplate" ]] && use_handplate=true
  fi
  shot="${shots[$i]}"
  if [[ -n "$BACKGROUND_CLIP" ]]; then
    shot="$BACKGROUND_CLIP"
  fi
  duration="$(dur "${voices[$i]}")"
  fade_start="$(python3 - "$duration" <<'PY'
import sys
print(f"{max(0.0, float(sys.argv[1]) - 0.12):.3f}")
PY
)"
  caption="${fallbacks[$i]}"
  if [[ -f "${texts[$i]}" ]]; then
    caption="$(tr '\n' ' ' < "${texts[$i]}" | sed 's/[[:space:]]\+/ /g;s/^ //;s/ $//')"
  fi
  if [[ -d "$overlay_frame_dir" && "$use_handplate" == "true" ]]; then
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -framerate 30 -i "$overlay_frame_pattern" \
      -stream_loop -1 -i "$handplate" \
      -t "$duration" \
      -filter_complex "[0:v]$vf[base];[base][2:v]overlay=0:0:format=auto[doc];[3:v]$hand_vf[hand];[doc][hand]overlay=0:0:format=auto[v]" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map "[v]" -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  elif [[ -d "$overlay_frame_dir" ]]; then
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -framerate 30 -i "$overlay_frame_pattern" \
      -t "$duration" \
      -filter_complex "[0:v]$vf[base];[base][2:v]overlay=0:0:format=auto[v]" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map "[v]" -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  elif [[ -f "$overlay" && "$use_handplate" == "true" ]]; then
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -i "$overlay" \
      -stream_loop -1 -i "$handplate" \
      -t "$duration" \
      -filter_complex "[0:v]$vf[base];[base][2:v]overlay=0:0:format=auto[doc];[3:v]$hand_vf[hand];[doc][hand]overlay=0:0:format=auto[v]" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map "[v]" -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  elif [[ -f "$overlay" ]]; then
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -i "$overlay" \
      -t "$duration" \
      -filter_complex "[0:v]$vf[base];[base][2:v]overlay=0:0:format=auto[v]" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map "[v]" -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  elif [[ "$use_handplate" == "true" ]]; then
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -stream_loop -1 -i "$handplate" \
      -t "$duration" \
      -filter_complex "[0:v]$vf[base];[2:v]$hand_vf[hand];[base][hand]overlay=0:0:format=auto[v]" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map "[v]" -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  else
    "$FFMPEG" -y \
      -stream_loop -1 -i "$shot" \
      -i "${voices[$i]}" \
      -t "$duration" \
      -vf "$vf" \
      -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
      -map 0:v -map 1:a \
      -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 \
      "segment_$idx.mp4"
  fi
  printf "file 'segment_%s.mp4'\n" "$idx" >> "$list_file"
  end="$(python3 - "$timeline" "$duration" <<'PY'
import sys
print(float(sys.argv[1]) + float(sys.argv[2]))
PY
)"
  escaped_caption="$(python3 - "$caption" <<'PY'
import json, sys
print(json.dumps(sys.argv[1]))
PY
)"
  if [[ "$i" != "0" ]]; then segments_json+=","; fi
  segments_json+="{\"start\":$timeline,\"end\":$end,\"caption\":$escaped_caption}"
  timeline="$end"
done
segments_json+="]"

"$FFMPEG" -y -f concat -safe 0 -i "$list_file" -c copy signal_pipeline_rough.mp4

python3 - "$segments_json" <<'PY'
import json, sys
segments = json.loads(sys.argv[1])

def ts(value):
    ms = round(value * 1000)
    hh = ms // 3600000
    mm = (ms % 3600000) // 60000
    ss = (ms % 60000) // 1000
    mmm = ms % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{mmm:03d}"

def chunks(text, size=7):
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)] or [text]

lines = []
cue = 1
for segment in segments:
    parts = chunks(segment["caption"])
    span = (segment["end"] - segment["start"]) / len(parts)
    for index, part in enumerate(parts):
        start = segment["start"] + span * index
        end = segment["end"] if index == len(parts) - 1 else segment["start"] + span * (index + 1)
        lines.extend([str(cue), f"{ts(start)} --> {ts(end)}", part, ""])
        cue += 1

with open("signal_pipeline_captions.srt", "w", encoding="utf-8") as handle:
    handle.write("\r\n".join(lines))
PY

if [[ "$BURN_CAPTIONS" == "true" || "$BURN_CAPTIONS" == "1" ]]; then
  "$FFMPEG" -y -i signal_pipeline_rough.mp4 \
    -vf "subtitles=signal_pipeline_captions.srt:force_style='Fontsize=10,Bold=1,Alignment=2,MarginV=76,Outline=1,Shadow=0'" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -c:a copy -movflags +faststart "$OUT"
else
  "$FFMPEG" -y -i signal_pipeline_rough.mp4 \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -c:a copy -movflags +faststart "$OUT"
fi

if [[ -n "$FFPROBE" ]]; then
  "$FFPROBE" -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$OUT"
  "$FFPROBE" -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 "$OUT"
  "$FFPROBE" -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
else
  echo "ffprobe not found; assembled with embedded ffmpeg and skipped stream summary."
fi
echo "Done -> $(pwd)/$OUT"
