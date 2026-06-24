import { NextResponse } from 'next/server';
import OpenAI from 'openai';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

// In-memory guard against replaying the same paid session.
// NOTE: resets on cold start / scales per-instance. For production, persist
// fulfilled session IDs in a database or KV store instead.
const fulfilledSessions = new Set<string>();

export async function POST(req: Request) {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || 'dummy_key_for_build',
  });
  try {
    const { resumeText, jobDescription, sessionId } = await req.json();

    if (!resumeText || !jobDescription) {
      return NextResponse.json({ error: 'Missing resume or job description' }, { status: 400 });
    }

    // --- Payment gate: never run the optimizer without a verified, paid session ---
    if (!sessionId) {
      return NextResponse.json({ error: 'Missing payment session' }, { status: 402 });
    }

    let session;
    try {
      session = await stripe.checkout.sessions.retrieve(sessionId);
    } catch {
      return NextResponse.json({ error: 'Invalid payment session' }, { status: 402 });
    }

    if (session.payment_status !== 'paid') {
      return NextResponse.json({ error: 'Payment not completed' }, { status: 402 });
    }

    if (fulfilledSessions.has(sessionId)) {
      return NextResponse.json(
        { error: 'This payment has already been used. Please purchase again.' },
        { status: 409 }
      );
    }
    fulfilledSessions.add(sessionId);
    // ----------------------------------------------------------------------------

    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content: `You are an expert ATS (Applicant Tracking System) optimizer. 
Your job is to rewrite the provided resume to perfectly match the semantics of the target Job Description, ensuring it passes automated filters.
Output a strict JSON object with the following structure:
{
  "name": "Candidate Name",
  "email": "Email (if found, else blank)",
  "phone": "Phone (if found, else blank)",
  "location": "City, State (if found, else blank)",
  "linkedin": "LinkedIn URL or handle (if found, else blank)",
  "summary": "A powerful 2-sentence summary matching the JD keywords",
  "skills": ["Skill 1", "Skill 2"],
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "dates": "Start - End",
      "bullets": [
        "Action-oriented bullet point emphasizing skills from the JD",
        "Another bullet point..."
      ]
    }
  ],
  "education": [
    {
      "school": "School Name",
      "degree": "Degree",
      "year": "Graduation Year"
    }
  ],
  "certifications": ["Certification exactly as stated, preserving status like '(in progress)' or '(pursuing)'"]
}

HONESTY RULES (critical — do not violate):
- Never claim a credential, certification, degree, or job the candidate does not have.
- Preserve the exact status of every certification. If the resume says a cert is "in progress",
  "pursuing", "expected 2025", or similar, you MUST keep that qualifier and MUST NOT present it
  as completed. Do not move an in-progress certification into "skills" or "summary" in a way that
  implies it is earned.
- Always include EVERY real certification from the original resume in the "certifications" array.
  Do not drop any. Do not invent new ones.
- Preserve location and linkedin from the original if present.

Within those honesty rules, highlight the overlapping skills aggressively and mirror the JD's exact
keywords. Do not fabricate jobs, dates, or skills the candidate never had.`
        },
        {
          role: "user",
          content: `TARGET JOB DESCRIPTION:\n${jobDescription}\n\nCURRENT RESUME TEXT:\n${resumeText}`
        }
      ]
    });

    const resultText = completion.choices[0].message.content;
    if (!resultText) throw new Error("No response from OpenAI");

    const json = JSON.parse(resultText);
    return NextResponse.json(json);

  } catch (error: any) {
    console.error('Error rewriting resume:', error);
    return NextResponse.json({ error: error.message || 'Failed to rewrite resume' }, { status: 500 });
  }
}
