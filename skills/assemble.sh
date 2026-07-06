#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$PWD}"
OUT="${OUT:-signal_pipeline_review.mp4}"
cd "$WORKDIR"

for tool in ffmpeg ffprobe; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "$tool not found. Install ffmpeg/ffprobe first." >&2
    exit 1
  }
done

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

dur(){ ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }

vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p"
segments_json="["
timeline=0
list_file="concat_list.txt"
: > "$list_file"

for i in "${!shots[@]}"; do
  idx="$(printf "%02d" "$((i + 1))")"
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
  ffmpeg -y \
    -stream_loop -1 -i "${shots[$i]}" \
    -i "${voices[$i]}" \
    -t "$duration" \
    -vf "$vf" \
    -af "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=in:st=0:d=0.04,afade=t=out:st=$fade_start:d=0.12" \
    -map 0:v -map 1:a \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
    -c:a aac -ar 48000 -ac 2 \
    "segment_$idx.mp4"
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

ffmpeg -y -f concat -safe 0 -i "$list_file" -c copy signal_pipeline_rough.mp4

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

ffmpeg -y -i signal_pipeline_rough.mp4 \
  -vf "subtitles=signal_pipeline_captions.srt:force_style='Fontsize=18,Bold=1,Alignment=2,MarginV=120,Outline=2,Shadow=1'" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy -movflags +faststart "$OUT"

ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,r_frame_rate -of default=nw=1 "$OUT"
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels -of default=nw=1 "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
echo "Done -> $(pwd)/$OUT"
