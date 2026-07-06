#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${WORKDIR:-$PWD}"
HOOK="${HOOK:-Woman_talking_about_resume_keywords_202607060959.mp4}"
SEARCH="${SEARCH:-Resume_cards_in_dark_void_202607060958.mp4}"
DEMO_VIDEO="${DEMO_VIDEO:-signal_feature_demo_recording.mp4}"
DEMO_IMAGE="${DEMO_IMAGE:-signal_landing_demo.png}"
CTA="${CTA:-Woman_speaking_to_camera_202607060956.mp4}"
VO1="${VO1:-ElevenLabs_2026-07-06T15_01_46_Abby_ivc_sp100_s50_sb75_se0_b_m2.mp3}"
VO2="${VO2:-ElevenLabs_2026-07-06T14_58_04_Abby_ivc_sp100_s50_sb75_se0_b_m2.mp3}"
OUT="${OUT:-signal_ad_final.mp4}"

cd "$WORKDIR"

dur(){ ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }

D_HOOK="$(dur "$HOOK")"
D_CTA="$(dur "$CTA")"
D_VO1="$(dur "$VO1")"
D_VO2="$(dur "$VO2")"
DEMO_FRAMES="$(python3 - <<PY
import math
print(math.ceil(float("$D_VO2") * 30))
PY
)"

VF="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1"
VF_DEMO="fps=30,scale=1215:2160,crop=1080:1920:(iw-ow)/2:min(220\\,n*220/$DEMO_FRAMES),setsar=1"
AENC=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -ar 48000 -ac 2)

ffmpeg -y -i "$HOOK" -vf "$VF" "${AENC[@]}" s1.mp4
ffmpeg -y -stream_loop -1 -i "$SEARCH" -i "$VO1" -t "$D_VO1" -vf "$VF" -map 0:v -map 1:a "${AENC[@]}" s2.mp4
if [[ -f "$DEMO_VIDEO" ]]; then
  ffmpeg -y -stream_loop -1 -i "$DEMO_VIDEO" -i "$VO2" -t "$D_VO2" -vf "$VF" -map 0:v -map 1:a "${AENC[@]}" s3.mp4
else
  ffmpeg -y -loop 1 -i "$DEMO_IMAGE" -i "$VO2" -t "$D_VO2" -vf "$VF_DEMO" -map 0:v -map 1:a "${AENC[@]}" s3.mp4
fi
ffmpeg -y -i "$CTA" -vf "$VF" "${AENC[@]}" s4.mp4

printf "file 's1.mp4'\nfile 's2.mp4'\nfile 's3.mp4'\nfile 's4.mp4'\n" > list.txt
ffmpeg -y -f concat -safe 0 -i list.txt -c copy signal_ad_rough.mp4

python3 - "$D_HOOK" "$D_VO1" "$D_VO2" "$D_CTA" <<'PY'
import sys
h,v1,v2,c = map(float, sys.argv[1:5])
b=[0,h,h+v1,h+v1+v2,h+v1+v2+c]
lines=[
 'The viral "ATS hack" is a myth',
 "Recruiters SEARCH. You're not ranking.",
 'Resume Crime Scene: 34 to 92',
 'Free score in bio - $9.99, no subscription',
]
def ts(t):
    ms=int(round(t*1000)); hh=ms//3600000; mm=ms//60000%60; ss=ms//1000%60; ms%=1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"
with open("signal_captions.srt","w",encoding="utf-8") as f:
    for i,line in enumerate(lines):
        f.write(f"{i+1}\n{ts(b[i])} --> {ts(b[i+1])}\n{line}\n\n")
PY

ffmpeg -y -i signal_ad_rough.mp4 \
  -vf "subtitles=signal_captions.srt:force_style='Fontsize=16,Bold=1,Alignment=2,MarginV=90,Outline=2,Shadow=1'" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart "$OUT"

echo "Done -> $OUT"
