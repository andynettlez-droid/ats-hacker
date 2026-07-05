# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

node scripts/generate_episode_voiceover.mjs --props props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_episode.json --script marketing/daily_content/2026-07-04-human-desk-resume-review-inspired-by-gohar-khan-resume-tips/longform_voiceover.md --manifest marketing/daily_content/2026-07-04-human-desk-resume-review-inspired-by-gohar-khan-resume-tips/channel_manifest.json --require-elevenlabs
npx remotion render TeardownEpisode out/daily-human-desk-resume-review-inspired-by-gohar-khan-resume-tips-episode.mp4 --props=props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_episode.json
npx remotion still SignalThumbnail out/daily-human-desk-resume-review-inspired-by-gohar-khan-resume-tips-thumbnail.png --props=props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_thumbnail.json

npx remotion render ResumeDeskReview out/daily-i-would-rewrite-this-bullet-immediately.mp4 --props=props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_short_1.json
npx remotion render ResumeDeskReview out/daily-the-ctrl-f-test-this-resume-fails.mp4 --props=props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_short_2.json
npx remotion render ResumeDeskReview out/daily-this-resume-missed-the-job-posting.mp4 --props=props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_short_3.json