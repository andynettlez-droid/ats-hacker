# Signal Studio Video Upgrade Plan

## Verdict

The winning direction is not a polished AI SaaS demo. It is a recruiter-reacts resume teardown.

The default format should be **Resume Crime Scene**:

1. A recruiter-style narrator opens with a blunt hook.
2. The resume is the star of the frame, not the avatar.
3. Red circles and yellow highlights expose why the resume is invisible.
4. A real job description supplies the missing role language.
5. One weak bullet is rewritten live without adding fake experience.
6. The score jumps from low match to optimized match.
7. Signal appears as the tool that reveals and fixes the issue.

HeyGen should be optional face-cam authority, not the whole video. Signal mascot should appear as brand memory and payoff, not as a replacement for the teardown. ElevenLabs should carry the studio-quality voice, quiet bed, and very restrained SFX.

## Research Notes

- YouTube now classifies square or vertical uploads up to three minutes as Shorts, but Shorts over one minute with active Content ID claims can be blocked globally. Generated or royalty-free audio matters, especially for 60-180 second cuts. Source: https://support.google.com/youtube/answer/15424877
- ElevenLabs TTS returns speech audio from a voice ID, which fits our need for repeatable studio-quality voiceover. Source: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
- ElevenLabs sound generation can generate MP3 sound effects from text prompts with duration and prompt-influence controls. This lets us create quiet brand-consistent pulses instead of harsh stock effects. Source: https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert
- Short-form recommendation systems reward repeatable engagement loops and steady viewer attention. That argues for serialized formats, clear visual payoff, and direct captions instead of generic talking-head clips. Source: https://arxiv.org/abs/2301.04945

## Production Standard

Use a two-lane content system.

Shorts lane:
- Length: 22-45 seconds.
- Format: vertical 1080x1920.
- Hook: readable in the first second.
- Avatar: optional face-cam bubble for 2-4 seconds, then resume/job description takes over.
- Audio: ElevenLabs voice at high clarity, music under 22% volume, SFX under 10%.
- Captions: every major claim appears on-screen.
- Claim rules: no job guarantees, no unsupported callback multipliers, no "ATS auto-rejected you" claims.

Serious YouTube lane:
- Length: 6-12 minutes.
- Format: 16:9 primary, with 3-5 vertical clips extracted from each episode.
- Structure: cold open, test method, proof screen, before/after, ranking table, practical takeaway.
- Example episodes: "Claude vs Codex vs Signal resume test", "Top 10 resume builders tested", "Why your resume is invisible in recruiter search".

## Implemented Pipeline

The marketing agent now has two upgraded modes:

```powershell
python marketing_agent/video_pipeline.py --crime-scene
```

Use this as the default for viral Shorts/Reels/TikTok. It renders the recruiter-reacts teardown format with red/yellow markups, weak bullet fix, and score reveal.

```powershell
python marketing_agent/video_pipeline.py --studio-breakthrough
```

Use this for the mascot-heavy brand visual where Signal breaks company filters and phases the resume into a hiring manager screen.

With API keys present, the studio pipeline:

- Generates an ElevenLabs voiceover from the script.
- Generates a quiet cinematic bed with ElevenLabs sound generation.
- Generates a restrained Signal pulse/SFX asset.
- Generates or reuses a HeyGen avatar intro.
- Renders the chosen Remotion composition.
- Copies the rendered video to the social queue as review-required.

Useful options:

```powershell
python marketing_agent/video_pipeline.py --crime-scene --force-audio
python marketing_agent/video_pipeline.py --studio-breakthrough --force-audio
python marketing_agent/video_pipeline.py --crime-scene --mock-heygen
python marketing_agent/video_pipeline.py --crime-scene --dry-run
```

## Primary Recurring Series

### Resume Crime Scene

Anonymous resume teardown. Find 2-3 mistakes. Fix one bullet. Reveal score jump.

### ATS Myth Lab

Debunk common myths while building trust. Example: an ATS usually stores and indexes resumes for recruiter search, not an automatic robot rejection story.

### Job Description Translation

Take one job posting and show the exact role language a resume needs to reflect.

### One Bullet Fix

Before/after bullet rewrite in under 30 seconds.

### Recruiter Search Test

Ask whether a resume would surface for terms like HubSpot, CAC, demand gen, lifecycle marketing, SQL, or Kubernetes.

## First Upgraded Clip

Working title: `This resume got a 34/100`

Voiceover:

> This resume looks fine, which is exactly the problem. The job description asks for demand gen, LinkedIn Ads, HubSpot, and CAC analysis. But the resume says helped with campaigns. That is not bad experience. It is invisible experience. Same person. Same work. Better signal. Before, 34 out of 100. After, 92.

Visual sequence:

1. Hook: "This resume got a 34/100."
2. Show resume beside target job description.
3. Highlight missing terms: Demand Gen, LinkedIn Ads, HubSpot, CAC.
4. Red circle the weak bullet: "Helped with marketing campaigns."
5. Rewrite it live: "Cut CAC by 32% through LinkedIn Ads audience segmentation and HubSpot lead scoring."
6. Reveal 34/100 to 92/100.
7. CTA: Paste the job description and check your free Signal score.

## Next Upgrades

- Add ElevenLabs timing metadata or forced alignment for word-perfect captions.
- Generate HeyGen avatar from the same ElevenLabs audio once the exact HeyGen audio-upload endpoint is wired, so lip sync matches the final studio voice.
- Add A/B export presets for three hook variants per video.
- Add a weekly topic agent that outputs one serious YouTube episode and five Shorts from the same research packet.
