# Run from marketing/remotion
# These render-ready props produce the daily YouTube episode, thumbnail, and Shorts.
# Review still frames before posting.

node scripts/generate_episode_voiceover.mjs --props props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_episode.json --script marketing/daily_content/2026-07-04-online-native-recruiter-roast-score-receipt-clips/longform_voiceover.md --manifest marketing/daily_content/2026-07-04-online-native-recruiter-roast-score-receipt-clips/channel_manifest.json --require-elevenlabs
npx remotion render TeardownEpisode out/daily-online-native-recruiter-roast-score-receipt-clips-episode.mp4 --props=props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_episode.json
npx remotion still SignalThumbnail out/daily-online-native-recruiter-roast-score-receipt-clips-thumbnail.png --props=props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_thumbnail.json

npx remotion render ResumeCrimeScene out/daily-this-data-bullet-has-npc-energy.mp4 --props=props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_short_1.json
npx remotion render ResumeCrimeScene out/daily-recruiter-ctrl-f-found-absolutely-nothing.mp4 --props=props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_short_2.json
npx remotion render ResumeCrimeScene out/daily-this-resume-failed-an-open-book-test.mp4 --props=props_daily_2026-07-04_online-native-recruiter-roast-score-receipt-clips_short_3.json