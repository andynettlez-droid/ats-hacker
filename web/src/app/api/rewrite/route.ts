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

    const userPrompt = `TARGET JOB DESCRIPTION:\n${jobDescription}\n\nCURRENT RESUME TEXT:\n${resumeText}`;

    const generate = async (extra: string = ""): Promise<any> => {
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
keywords. Do not fabricate jobs, dates, or skills the candidate never had.` + extra,
          },
          {
            role: "user",
            content: userPrompt,
          },
        ],
      });
      const resultText = completion.choices[0].message.content;
      if (!resultText) throw new Error("No response from OpenAI");
      return JSON.parse(resultText);
    };

    // --- Validation layer: guarantee an honest, actually-optimized result ---
    const STOP = new Set(
      "the,and,for,with,you,your,our,are,will,must,that,this,have,has,role,job,team,work,years,year,experience,strong,plus,etc,use,using,ability,including,who,can,all,any,not,from,their,they,what,when,where,which,able,well,also,into,more,most,such,than,then,them,these,those,were,been,being,about,across,within,per,via".split(",")
    );
    const tokenize = (s: string) =>
      new Set(((String(s || "").toLowerCase().match(/[a-z0-9+#]{3,}/g)) || []).filter((w) => !STOP.has(w)));
    const resumeTokens = tokenize(resumeText);
    const jdTokens = [...tokenize(jobDescription)];
    const serialize = (j: any) =>
      [
        j.summary,
        (j.skills || []).join(" "),
        (j.experience || []).map((e: any) => `${e.title} ${e.company} ${(e.bullets || []).join(" ")}`).join(" "),
        (j.certifications || []).join(" "),
      ].join(" ");
    const jdMatches = (text: string) => {
      const t = tokenize(text);
      let n = 0;
      for (const k of jdTokens) if (t.has(k)) n++;
      return n;
    };

    // Remove any certification that is NOT grounded in the original resume (anti-fabrication).
    const groundCerts = (j: any) => {
      if (!Array.isArray(j.certifications)) {
        j.certifications = [];
        return;
      }
      const generic = new Set(
        "certified,certification,certificate,certificates,in,progress,pursuing,expected,exam,completed,license,licensed".split(",")
      );
      j.certifications = j.certifications.filter((c: string) => {
        const core = [...tokenize(c)].filter((t) => !generic.has(t));
        return core.length === 0 ? true : core.some((t) => resumeTokens.has(t));
      });
    };
    // Don't let the model silently drop contact info that exists in the original.
    const restoreContact = (j: any) => {
      if (!j.email) {
        const m = resumeText.match(/[\w.+-]+@[\w-]+\.[\w.-]+/);
        if (m) j.email = m[0];
      }
      if (!j.phone) {
        const m = resumeText.match(/\+?\d[\d\s().-]{7,}\d/);
        if (m) j.phone = m[0].trim();
      }
    };

    // Generate, then verify it is actually MORE aligned to the JD than the original.
    const origMatch = jdMatches(resumeText);
    let best = await generate();
    let bestScore = jdMatches(serialize(best));
    if (bestScore <= origMatch) {
      const retry = await generate(
        "\n\nThe previous attempt did not incorporate enough of the job description's keywords. Aggressively weave more of the JD's exact keywords and phrases into the summary, skills, and bullet points — strictly without fabricating any experience, dates, skills, or certifications."
      );
      if (jdMatches(serialize(retry)) > bestScore) {
        best = retry;
        bestScore = jdMatches(serialize(best));
      }
    }
    groundCerts(best);
    restoreContact(best);

    // If, after all that, the rewrite still isn't more optimized than the original, surface it
    // rather than charging for a no-op (the client can decide how to handle this).
    if (bestScore <= origMatch) {
      return NextResponse.json({ ...best, _warning: "optimization_low" });
    }
    return NextResponse.json(best);

  } catch (error: any) {
    console.error('Error rewriting resume:', error);
    return NextResponse.json({ error: error.message || 'Failed to rewrite resume' }, { status: 500 });
  }
}
