# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

node scripts/generate_episode_voiceover.mjs --props props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_episode.json --script marketing/daily_content/2026-07-04-recruiter-search-tests-with-real-resume-teardowns/longform_voiceover.md --manifest marketing/daily_content/2026-07-04-recruiter-search-tests-with-real-resume-teardowns/channel_manifest.json --require-elevenlabs
npx remotion render TeardownEpisode out/daily-recruiter-search-tests-with-real-resume-teardowns-episode.mp4 --props=props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_episode.json
npx remotion still SignalThumbnail out/daily-recruiter-search-tests-with-real-resume-teardowns-thumbnail.png --props=props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-this-resume-sentence-is-quietly-expensive.mp4 --props=props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_short_1.json
npx remotion render ResumeCrimeScene out/daily-i-searched-salesforce-and-this-resume-vanished.mp4 --props=props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_short_2.json
npx remotion render ResumeCrimeScene out/daily-this-resume-failed-an-open-book-test.mp4 --props=props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_short_3.json