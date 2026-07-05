# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

node scripts/generate_episode_voiceover.mjs --props props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_episode.json --script marketing/daily_content/2026-07-05-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor/longform_voiceover.md --manifest marketing/daily_content/2026-07-05-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor/channel_manifest.json --require-elevenlabs
npx remotion render TeardownEpisode out/daily-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor-episode.mp4 --props=props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_episode.json
npx remotion still SignalThumbnail out/daily-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor-thumbnail.png --props=props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_thumbnail.json

npx remotion render ResumeDeskReview out/daily-i-would-circle-this-line-first.mp4 --props=props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_short_1.json
npx remotion render ResumeDeskReview out/daily-i-searched-the-resume-bad-news.mp4 --props=props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_short_2.json
npx remotion render ResumeDeskReview out/daily-the-job-post-gave-the-answer-key.mp4 --props=props_daily_2026-07-05_human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor_short_3.json