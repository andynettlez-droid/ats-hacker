# Signal Script Human Review Gate

Every short must feel like a real human reviewer is looking at the resume and improving one line.

## Required Structure

1. Show the resume immediately.
2. Hook within 1.5 seconds.
3. Read one exact weak resume line.
4. React naturally.
5. Compare it to one visible job requirement.
6. Show why the starting score is low using the score rubric.
7. Point to visible source evidence already on the resume.
8. Rewrite only the same real experience from that source evidence.
9. Explain why the score improves.
10. End with: "Run the free Signal score before you apply."

## Evidence Ledger

Every generated teardown case must include `evidenceLedger` in the render props:

- `sourceLocation`: where the stronger proof appears on the resume.
- `proofLine`: the exact source line visible in the resume artifact.
- `visibleFacts`: at least three facts with `fact` and `source`.

The rewritten bullet cannot use a number, tool, platform, or outcome unless that fact appears in the evidence ledger and the full resume document. The script must say where the proof came from using human language such as:

- "The proof is lower down..."
- "I found the proof lower on the page..."
- "The right evidence is in the wrong place..."

The gate fails if a score rubric exists but the rewrite appears to invent proof.

## Score Rubric

Each props file must include `score_rubric` with six rows:

- Job keyword/tool match, max 25
- Measurable proof, max 20
- Outcome clarity, max 20
- Scope/context, max 15
- Role alignment, max 15
- Formatting/readability, max 5

The before row totals must equal `beforeScore`.
The after row totals must equal `afterScore`.
The score reveal cannot appear before the low-score reason is visible.

## Pass Examples

- "Okay, this is the line I would circle first: Worked on frontend features for internal and customer-facing tools."
- "The job post asks for React, TypeScript, and accessibility. I only see frontend."
- "So I am not giving it a 90. It starts at 41."
- "Now I can see the stack, scope, and outcome. That is why it moves to 90."

## Fail Examples

- "This resume lacks role-specific keywords."
- "This experience is invisible."
- "Here is the score receipt."
- "Same person. Better signal."
- "The ATS will reject this."

## Automatic Failure Conditions

- The script could work without showing the resume.
- The score appears before the reason is clear.
- The reviewer does not read an actual resume line.
- The rewrite adds fake experience.
- The voiceover is over 96 words or under 42 words.
- The clip takes more than 3 seconds to show the problem.
- The script repeats a prior opening.
- The script jumps from weak line to improved score without explaining the visible source evidence.
