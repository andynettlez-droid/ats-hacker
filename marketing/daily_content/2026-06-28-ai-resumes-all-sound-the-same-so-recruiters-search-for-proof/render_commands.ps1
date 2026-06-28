# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

npx remotion render TeardownEpisode out/daily-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof-episode.mp4 --props=props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_episode.json
npx remotion still SignalThumbnail out/daily-ai-resumes-all-sound-the-same-so-recruiters-search-for-proof-thumbnail.png --props=props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-your-ai-resume-has-linkedin-breath.mp4 --props=props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_short_1.json
npx remotion render ResumeCrimeScene out/daily-stop-writing-helped-with-campaigns.mp4 --props=props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_short_2.json
npx remotion render ResumeCrimeScene out/daily-the-ats-is-not-a-wizard.mp4 --props=props_daily_2026-06-28_ai-resumes-all-sound-the-same-so-recruiters-search-for-proof_short_3.json
