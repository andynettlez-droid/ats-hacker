# I searched Salesforce and this resume vanished

Daily packet: `2026-07-04-recruiter-search-tests-with-real-resume-teardowns`
Series: Recruiter Search Test
Hook: I searched Salesforce. Nothing.

## Script

Recruiter search test. I am hiring for Mid-Market Account Executive. I search Salesforce. Nothing. Then pipeline generation. Still weak. Then quota attainment. Basically empty. Now look at the resume: Responsible for sales opportunities in assigned territory. That line has the personality of an empty conference room. The person actually generated 1.8 million in qualified Salesforce pipeline, but the resume made me guess. Recruiters do not guess. They search. Rewrite it as: Generated $1.8M in qualified Salesforce pipeline through 42 monthly discovery calls and MEDDICC-based account prioritization. Now the score moves from 37 to 88. Run the free Signal score before you send yours.

## Storyboard

- Case: Account Executive Resume against Mid-Market Account Executive.
- Open with a recruiter search box typing Salesforce.
- Show a weak/no-match result, then rapid-cut pipeline generation and quota attainment.
- Reveal the resume bullet as the reason the search failed.
- Signal puts a 'recruiters do not guess' note beside the line.
- Rewrite the bullet and rerun the search with a clear match.
- Close with the score jump and free score CTA.

## Render Props

`marketing\remotion\props_daily_2026-07-04_recruiter-search-tests-with-real-resume-teardowns_short_2.json`

Composition: `ResumeCrimeScene`

## QA

- Keep Signal mascot visible.
- Keep captions readable on mobile.
- No unsupported auto-reject, guarantee, or fake-outcome claims.
- Audio readiness: `ready via elevenlabs`.
- Queue as review_required after rendering.