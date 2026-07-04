# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

npx remotion render TeardownEpisode out/daily-recruiter-reacts-to-invisible-resumes-with-real-job-description--episode.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-invisible-resumes-with-real-job-description-_episode.json
npx remotion still SignalThumbnail out/daily-recruiter-reacts-to-invisible-resumes-with-real-job-description--thumbnail.png --props=props_daily_2026-07-04_recruiter-reacts-to-invisible-resumes-with-real-job-description-_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-this-marketing-resume-hid-the-actual-revenue-proof.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-invisible-resumes-with-real-job-description-_short_1.json
npx remotion render ResumeCrimeScene out/daily-this-sales-resume-forgot-to-say-sales.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-invisible-resumes-with-real-job-description-_short_2.json
npx remotion render ResumeCrimeScene out/daily-this-developer-resume-hides-the-stack.mp4 --props=props_daily_2026-07-04_recruiter-reacts-to-invisible-resumes-with-real-job-description-_short_3.json