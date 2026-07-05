# Score Rubric QA Report

Packet: `2026-07-05-human-recruiter-reads-and-fixes-resume-bullets-with-visible-scor`

Status: passed. Each short now earns the score reveal on screen before the final number appears. The score is no longer an arbitrary `34 -> 92` jump; it is calculated from the visible six-part Signal Fit Score rubric in the render props.

## I would circle this line first

- Role: Data Analyst Resume against Product Data Analyst.
- Weak line read on screen: `Created reports for business teams and leadership.`
- Rewrite: `Built a SQL churn dashboard that saved six hours a week and flagged 18 at-risk accounts.`
- Score movement: `32 -> 89`.

Why the score starts low:

- Job keyword/tool match: `8/25`, because the line only says reports.
- Measurable proof: `2/20`, because there is no number.
- Outcome clarity: `4/20`, because the leadership benefit is vague.
- Scope/context: `7/15`, because only the audience is visible.
- Role alignment: `8/15`, because analytics is implied, not proven.
- Formatting/readability: `3/5`, because the line is readable but generic.

Why the score improves:

- SQL and Tableau become explicit.
- The result includes `6 hours saved`.
- The business outcome includes `18 at-risk accounts flagged`.
- The dashboard scope makes the product analytics fit visible.

## I searched the resume. Bad news.

- Role: Account Executive Resume against Mid-Market Account Executive.
- Weak line read on screen: `Responsible for sales opportunities in assigned territory.`
- Rewrite: `Generated $1.8M in qualified Salesforce pipeline through 42 monthly discovery calls and MEDDICC-based account prioritization.`
- Score movement: `37 -> 88`.

Why the score starts low:

- Job keyword/tool match: `7/25`, because Salesforce and MEDDICC are missing.
- Measurable proof: `3/20`, because there is no quota, dollars, or volume.
- Outcome clarity: `5/20`, because the sales result is unclear.
- Scope/context: `8/15`, because territory is the only context.
- Role alignment: `11/15`, because the sales role is visible but thin.
- Formatting/readability: `3/5`, because the line is readable but weak.

Why the score improves:

- Salesforce and MEDDICC appear directly.
- Pipeline value becomes measurable at `$1.8M`.
- The activity volume is specific with `42 monthly discovery calls`.
- The rewrite connects the action to qualified pipeline, not generic ownership.

## The job post gave the answer key

- Role: Frontend Engineer Resume against Frontend Software Engineer.
- Weak line read on screen: `Worked on frontend features for internal and customer-facing tools.`
- Rewrite: `Shipped React and TypeScript checkout components in Next.js, reducing form drop-off 14% and closing 11 accessibility issues.`
- Score movement: `41 -> 90`.

Why the score starts low:

- Job keyword/tool match: `9/25`, because it says frontend but not React, TypeScript, or Next.js.
- Measurable proof: `4/20`, because there is no metric.
- Outcome clarity: `7/20`, because feature work is too broad.
- Scope/context: `8/15`, because internal/customer tools are vague.
- Role alignment: `10/15`, because engineer fit is implied.
- Formatting/readability: `3/5`, because the line is readable but generic.

Why the score improves:

- React, TypeScript, and Next.js are visible.
- Accessibility is tied to `11 issues`.
- The user outcome is measurable with `14%` reduced drop-off.
- The scope narrows from vague frontend work to checkout components.

## Gate Notes

- All three props files include `score_rubric` and `scoreRubric`.
- Rubric before totals match `beforeScore`.
- Rubric after totals match `afterScore`.
- The score label is `Signal Fit Score`, avoiding unsupported ATS ranking language.
- The rewrite constraints are still prompt- and gate-based; real user resumes must go through consent and PII review before becoming content.
