# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

node scripts/generate_episode_voiceover.mjs --props props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_episode.json --script marketing/daily_content/2026-07-04-recruiter-reacts-to-real-resumes-against-real-job-descriptions/longform_voiceover.md --manifest marketing/daily_content/2026-07-04-recruiter-reacts-to-real-resumes-against-real-job-descriptions/channel_manifest.json --require-elevenlabs
npx remotion render TeardownEpisode out/daily-recruiter-reacts-to-real-resumes-against-real-job-descriptions-episode.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_episode.json
npx remotion still SignalThumbnail out/daily-recruiter-reacts-to-real-resumes-against-real-job-descriptions-thumbnail.png --props=props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-this-marketing-resume-hid-the-actual-revenue-proof.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_short_1.json
npx remotion render ResumeCrimeScene out/daily-this-sales-resume-forgot-to-say-sales.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_short_2.json
npx remotion render ResumeCrimeScene out/daily-this-developer-resume-hides-the-stack.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-real-resumes-against-real-job-descriptions_short_3.json
