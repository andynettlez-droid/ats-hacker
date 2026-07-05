# The Ctrl+F test this resume fails

Daily packet: `2026-07-04-human-desk-resume-review-inspired-by-gohar-khan-resume-tips`
Series: Recruiter Search Test
Hook: I searched the resume. Nothing.

## Script

If I am screening this resume, I search first. Salesforce: missing here. pipeline generation: missing too. The line says: Responsible for sales opportunities in assigned territory. That makes me guess, so the match starts at 37: missing term, missing proof. I would write: generated 1.8 million in qualified Salesforce pipeline. Now the search terms and proof are visible: 88. Run the free Signal score before you apply.

## Storyboard

- Case: Account Executive Resume against Mid-Market Account Executive.
- Open on a reviewer search box over the resume, searching for Salesforce.
- Show the weak bullet that does not include the searched language.
- Search pipeline generation and show the miss again.
- Explain that the low score comes from hidden tool and result proof.
- Rewrite the bullet and rerun the search with a visible match.
- Close after the low-score rationale explains the jump.

## Render Props

`marketing\remotion\props_daily_2026-07-04_human-desk-resume-review-inspired-by-gohar-khan-resume-tips_short_2.json`

Composition: `ResumeDeskReview`

## QA

- Keep Signal mascot visible.
- Keep captions readable on mobile.
- No unsupported auto-reject, guarantee, or fake-outcome claims.
- Audio readiness: `ready via elevenlabs`.
- Queue as review_required after rendering.