# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

npx remotion render TeardownEpisode out/daily-ai-looking-resume-bullets-recruiters-ignore-episode.mp4 --props=props_daily_2026-06-29_ai-looking-resume-bullets-recruiters-ignore_episode.json
npx remotion still SignalThumbnail out/daily-ai-looking-resume-bullets-recruiters-ignore-thumbnail.png --props=props_daily_2026-06-29_ai-looking-resume-bullets-recruiters-ignore_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-corporate-weather-report-resume.mp4 --props=props_daily_2026-06-29_ai-looking-resume-bullets-recruiters-ignore_short_1.json
npx remotion render ResumeCrimeScene out/daily-would-your-resume-appear-in-search.mp4 --props=props_daily_2026-06-29_ai-looking-resume-bullets-recruiters-ignore_short_2.json
npx remotion render ResumeCrimeScene out/daily-resume-crime-scene-hidden-proof.mp4 --props=props_daily_2026-06-29_ai-looking-resume-bullets-recruiters-ignore_short_3.json