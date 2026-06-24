import { NextResponse } from 'next/server';
import OpenAI from 'openai';

// FREE front-door endpoint: returns an ATS match score + the keywords the resume is
// missing, WITHOUT charging. This is the conversion hook — it proves the problem
// before the $5 rewrite unlock. No payment gate here by design.
// (For production, add basic rate limiting / abuse protection on this route.)

export async function POST(req: Request) {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || 'dummy_key_for_build',
  });
  try {
    const { resumeText, jobDescription } = await req.json();

    if (!resumeText || !jobDescription) {
      return NextResponse.json({ error: 'Missing resume or job description' }, { status: 400 });
    }

    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      response_format: { type: 'json_object' },
      messages: [
        {
          role: 'system',
          content: `You are an ATS (Applicant Tracking System) keyword-match scorer.
Compare the candidate's resume against the target job description the way an ATS would:
score how well the resume's language/keywords match the JD.

Return a STRICT JSON object:
{
  "score": <integer 0-100, how well the resume matches the JD's keywords>,
  "matchedKeywords": [up to 8 important keywords/phrases from the JD that ARE present in the resume],
  "missingKeywords": [up to 10 important keywords/phrases from the JD that are MISSING or weakly represented in the resume, ordered by importance],
  "verdict": "one short sentence summarizing the gap"
}
Be realistic and slightly conservative so the gap feels worth fixing. Only include
keywords genuinely found in the job description. Do not invent skills.`,
        },
        {
          role: 'user',
          content: `TARGET JOB DESCRIPTION:\n${jobDescription}\n\nRESUME TEXT:\n${resumeText}`,
        },
      ],
    });

    const resultText = completion.choices[0].message.content;
    if (!resultText) throw new Error('No response from OpenAI');

    const json = JSON.parse(resultText);
    // Clamp score defensively.
    if (typeof json.score === 'number') {
      json.score = Math.max(0, Math.min(100, Math.round(json.score)));
    }
    return NextResponse.json(json);
  } catch (error: any) {
    console.error('Error scoring resume:', error);
    return NextResponse.json({ error: error.message || 'Failed to score resume' }, { status: 500 });
  }
}
