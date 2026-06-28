import { NextResponse } from 'next/server';
import OpenAI from 'openai';
import Stripe from 'stripe';
import { buildFulfillmentBaseName, readFulfillment, writeFulfillment } from '@/lib/fulfillmentStore';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

const PRODUCT_CONFIG = {
  resume: { amount: 999 },
  cover_letter: { amount: 999 },
  bundle: { amount: 1499 },
} as const;

type ProductType = keyof typeof PRODUCT_CONFIG;

type ResumeExperience = {
  company?: string;
  title?: string;
  dates?: string;
  bullets?: string[];
};

type ResumeEducation = {
  school?: string;
  degree?: string;
  year?: string;
};

type CoverLetter = {
  recipientName?: string;
  companyName?: string;
  salutation?: string;
  bodyParagraphs?: string[];
  signOff?: string;
};

type ResumeJson = {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  summary?: string;
  skills?: string[];
  experience?: ResumeExperience[];
  education?: ResumeEducation[];
  certifications?: string[];
  coverLetter?: CoverLetter;
  productType?: ProductType;
  _warning?: string;
};

type CandidateFacts = {
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  certifications: string[];
  numberTokens: Set<string>;
};

const MAX_INPUT_CHARS = 60_000;
const STOP_WORDS = new Set(
  "the,and,for,with,you,your,our,are,will,must,that,this,have,has,role,job,team,work,years,year,experience,strong,plus,etc,use,using,ability,including,who,can,all,any,not,from,their,they,what,when,where,which,able,well,also,into,more,most,such,than,then,them,these,those,were,been,being,about,across,within,per,via,resume,candidate,professional".split(",")
);
const GENERIC_CERT_WORDS = new Set(
  "certified,certification,certificate,certificates,in,progress,pursuing,expected,exam,completed,license,licensed,credential,credentials".split(",")
);

function isProductType(value: unknown): value is ProductType {
  return typeof value === 'string' && value in PRODUCT_CONFIG;
}

function validatePaidSession(session: Stripe.Checkout.Session): ProductType | NextResponse {
  if (session.metadata?.app !== 'atshacker') {
    return NextResponse.json({ error: 'Payment session is not for Signal by ATSHacker' }, { status: 402 });
  }

  const productType = session.metadata?.product_type;
  if (!isProductType(productType)) {
    return NextResponse.json({ error: 'Payment session has an invalid product' }, { status: 402 });
  }

  if (session.mode !== 'payment' || session.status !== 'complete' || session.payment_status !== 'paid') {
    return NextResponse.json({ error: 'Payment not completed' }, { status: 402 });
  }

  const expected = PRODUCT_CONFIG[productType];
  if (session.currency?.toLowerCase() !== 'usd' || session.amount_total !== expected.amount) {
    return NextResponse.json({ error: 'Payment amount does not match this product' }, { status: 402 });
  }

  return productType;
}

function cleanText(value: unknown): string {
  return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : '';
}

function uniqueStrings(values: string[]): string[] {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))];
}

function tokenize(text: string, minLength = 3): Set<string> {
  const pattern = minLength <= 2 ? /[a-z0-9+#.]{2,}/g : /[a-z0-9+#.]{3,}/g;
  return new Set((text.toLowerCase().match(pattern) || []).filter((word) => !STOP_WORDS.has(word)));
}

function hasTokenOverlap(value: string, sourceTokens: Set<string>, minLength = 3): boolean {
  const tokens = [...tokenize(value, minLength)];
  return tokens.length > 0 && tokens.some((token) => sourceTokens.has(token));
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? uniqueStrings(value.map(cleanText)) : [];
}

function normalizeNumberToken(value: string): string {
  return value.toLowerCase().replace(/\s+/g, '').replace(/,/g, '');
}

function extractNumberTokens(text: string): Set<string> {
  const matches = text.match(/[\u0024\u20ac\u00a3]?\s*\d+(?:[.,]\d+)*(?:\s*(?:%|k|m|million|billion))?/gi) || [];
  return new Set(matches.map(normalizeNumberToken));
}

function extractPhone(text: string): string | undefined {
  const candidates = text.match(/\+?\d[\d\s().-]{7,}\d/g) || [];
  for (const candidate of candidates) {
    const digits = candidate.replace(/\D/g, '');
    if (digits.length >= 10 && digits.length <= 15) return candidate.trim();
  }
}

function extractLocation(text: string): string | undefined {
  const firstLines = text.split(/\r?\n/).slice(0, 12).join(' ');
  const match = firstLines.match(/\b[A-Z][a-zA-Z .'-]{2,},\s*(?:[A-Z]{2}|[A-Z][a-zA-Z .'-]{2,})\b/);
  return match?.[0]?.trim();
}

function extractCertifications(text: string): string[] {
  const credentialPattern =
    /\b(certifications?|licenses?|credentials?|certified|certificate|CISSP|PMP|CPA|CFA|RN|LPN|LVN|CNA|ACLS|BLS|CCNA|CCNP|AWS|Azure|GCP|Security\+|Network\+|A\+|SHRM(?:-CP|-SCP)?|PHR|SPHR|P\.?E\.?|CSM|Six Sigma)\b/i;
  const chunks = text
    .split(/\r?\n|[\u2022\u00b7]|;/)
    .map((line) => line.replace(/^[\s\-\u2013\u2014*]+/, '').trim())
    .filter((line) => line.length >= 2 && line.length <= 180);

  return uniqueStrings(
    chunks
      .filter((line) => credentialPattern.test(line) && !/^[A-Z ]{2,}:?$/.test(line))
      .map((line) => line.replace(/^(certifications?|licenses?|credentials?)\s*:\s*/i, '').trim())
  );
}

function extractCandidateFacts(resumeText: string): CandidateFacts {
  const email = resumeText.match(/[\w.+-]+@[\w-]+\.[\w.-]+/)?.[0];
  const linkedin = resumeText.match(/(?:https?:\/\/)?(?:www\.)?linkedin\.com\/[^\s)]+/i)?.[0];
  return {
    email,
    phone: extractPhone(resumeText),
    location: extractLocation(resumeText),
    linkedin,
    certifications: extractCertifications(resumeText),
    numberTokens: extractNumberTokens(resumeText),
  };
}

function sanitizeExperience(value: unknown): ResumeExperience[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    const record = asRecord(item);
    return {
      company: cleanText(record.company),
      title: cleanText(record.title),
      dates: cleanText(record.dates),
      bullets: asStringArray(record.bullets),
    };
  }).filter((item) => item.company || item.title || item.bullets.length);
}

function sanitizeEducation(value: unknown): ResumeEducation[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    const record = asRecord(item);
    return {
      school: cleanText(record.school),
      degree: cleanText(record.degree),
      year: cleanText(record.year),
    };
  }).filter((item) => item.school || item.degree);
}

function sanitizeResumeJson(value: unknown): ResumeJson {
  const record = asRecord(value);
  return {
    name: cleanText(record.name),
    email: cleanText(record.email),
    phone: cleanText(record.phone),
    location: cleanText(record.location),
    linkedin: cleanText(record.linkedin),
    summary: cleanText(record.summary),
    skills: asStringArray(record.skills),
    experience: sanitizeExperience(record.experience),
    education: sanitizeEducation(record.education),
    certifications: asStringArray(record.certifications),
  };
}

function sanitizeCoverLetter(value: unknown): CoverLetter {
  const record = asRecord(value);
  return {
    recipientName: cleanText(record.recipientName),
    companyName: cleanText(record.companyName),
    salutation: cleanText(record.salutation),
    bodyParagraphs: asStringArray(record.bodyParagraphs),
    signOff: cleanText(record.signOff),
  };
}

function parseResumeJson(text: string): ResumeJson {
  return sanitizeResumeJson(JSON.parse(text));
}

function parseCoverLetter(text: string): CoverLetter {
  return sanitizeCoverLetter(JSON.parse(text));
}

function unsupportedNumbers(text: string, facts: CandidateFacts): string[] {
  return [...extractNumberTokens(text)].filter((token) => !facts.numberTokens.has(token));
}

function serializeResume(j: ResumeJson): string {
  return [
    j.summary,
    (j.skills || []).join(" "),
    (j.experience || []).map((e) => `${e.title} ${e.company} ${e.dates} ${(e.bullets || []).join(" ")}`).join(" "),
    (j.certifications || []).join(" "),
    (j.education || []).map((e) => `${e.school} ${e.degree} ${e.year}`).join(" "),
  ].join(" ");
}

function applyFactGrounding(j: ResumeJson, facts: CandidateFacts, resumeText: string): ResumeJson {
  const sourceTokens = tokenize(resumeText, 2);

  if (facts.email) j.email = facts.email;
  if (facts.phone) j.phone = facts.phone;
  if (facts.location) j.location = facts.location;
  if (facts.linkedin) j.linkedin = facts.linkedin;

  j.skills = (j.skills || []).filter((skill) => hasTokenOverlap(skill, sourceTokens, 2));

  if (facts.certifications.length > 0) {
    j.certifications = facts.certifications;
  } else {
    j.certifications = (j.certifications || []).filter((cert) => {
      const certTokens = [...tokenize(cert, 2)].filter((token) => !GENERIC_CERT_WORDS.has(token));
      return certTokens.length > 0 && certTokens.some((token) => sourceTokens.has(token));
    });
  }

  j.experience = (j.experience || [])
    .map((exp) => ({
      ...exp,
      bullets: (exp.bullets || []).filter((bullet) => bullet.length >= 20 && unsupportedNumbers(bullet, facts).length === 0),
    }))
    .filter((exp) => (exp.company || exp.title) && (exp.bullets || []).length > 0);

  return j;
}

function resumeQualityErrors(j: ResumeJson, facts: CandidateFacts, resumeText: string): string[] {
  const errors: string[] = [];

  if (!j.summary || j.summary.length < 80) errors.push("summary is missing or too thin");
  if (!j.skills || j.skills.length < 3) errors.push("not enough grounded skills");
  if (!j.experience || j.experience.length === 0) errors.push("no grounded experience entries");

  const bulletCount = (j.experience || []).reduce((count, exp) => count + (exp.bullets || []).length, 0);
  if (bulletCount < 2) errors.push("not enough grounded experience bullets");

  const generatedNumbers = unsupportedNumbers(serializeResume(j), facts);
  if (generatedNumbers.length > 0) errors.push(`unsupported numbers: ${generatedNumbers.slice(0, 4).join(", ")}`);

  if (facts.email && j.email !== facts.email) errors.push("email was not preserved");
  if (facts.phone && j.phone !== facts.phone) errors.push("phone was not preserved");
  if (facts.linkedin && j.linkedin !== facts.linkedin) errors.push("linkedin was not preserved");
  if (facts.location && j.location !== facts.location) errors.push("location was not preserved");

  const sourceTokens = tokenize(resumeText, 2);
  const unsupportedSkills = (j.skills || []).filter((skill) => !hasTokenOverlap(skill, sourceTokens, 2));
  if (unsupportedSkills.length > 0) errors.push(`unsupported skills: ${unsupportedSkills.slice(0, 4).join(", ")}`);

  return errors;
}

function coverLetterQualityErrors(coverLetter: CoverLetter | undefined, facts: CandidateFacts, resumeText: string, jobDescription: string): string[] {
  const errors: string[] = [];
  if (!coverLetter) return ["cover letter missing"];

  const paragraphs = coverLetter.bodyParagraphs || [];
  const body = paragraphs.join(" ");
  if (!coverLetter.salutation) errors.push("salutation missing");
  if (!coverLetter.companyName) errors.push("company name missing");
  if (!coverLetter.signOff) errors.push("sign-off missing");
  if (paragraphs.length < 3) errors.push("fewer than 3 body paragraphs");
  if (body.length < 500) errors.push("cover letter is too thin");
  if (unsupportedNumbers(body, facts).length > 0) errors.push("cover letter introduced unsupported numbers");

  const bodyTokens = tokenize(body, 3);
  const jdOverlap = [...tokenize(jobDescription, 3)].filter((token) => bodyTokens.has(token)).length;
  if (jdOverlap < 4) errors.push("cover letter does not reference enough job-description specifics");

  const resumeOverlap = [...tokenize(resumeText, 3)].filter((token) => bodyTokens.has(token)).length;
  if (resumeOverlap < 4) errors.push("cover letter does not include enough resume-backed proof");

  return errors;
}

function candidateFactsPrompt(facts: CandidateFacts): string {
  return JSON.stringify({
    email: facts.email || "",
    phone: facts.phone || "",
    location: facts.location || "",
    linkedin: facts.linkedin || "",
    certifications: facts.certifications,
  });
}

async function validatePaidSessionId(sessionId: string): Promise<ProductType | NextResponse> {
  let session;
  try {
    session = await stripe.checkout.sessions.retrieve(sessionId);
  } catch {
    return NextResponse.json({ error: 'Invalid payment session' }, { status: 402 });
  }

  return validatePaidSession(session);
}

export async function GET(req: Request) {
  try {
    const url = new URL(req.url);
    const sessionId = url.searchParams.get('sessionId')?.trim();
    if (!sessionId) {
      return NextResponse.json({ error: 'Missing payment session' }, { status: 402 });
    }

    const productType = await validatePaidSessionId(sessionId);
    if (productType instanceof NextResponse) return productType;

    const cachedFulfillment = await readFulfillment(sessionId);
    if (!cachedFulfillment) {
      return NextResponse.json({ error: 'No saved optimization found for this session' }, { status: 404 });
    }

    return NextResponse.json(cachedFulfillment);
  } catch (error: unknown) {
    console.error('Error reading fulfillment:', error);
    const message = error instanceof Error ? error.message : 'Failed to read fulfillment';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const { resumeText, jobDescription, sessionId, fileName } = await req.json();

    if (typeof resumeText !== 'string' || typeof jobDescription !== 'string') {
      return NextResponse.json({ error: 'Missing resume or job description' }, { status: 400 });
    }

    if (!resumeText.trim() || !jobDescription.trim()) {
      return NextResponse.json({ error: 'Missing resume or job description' }, { status: 400 });
    }

    if (resumeText.length > MAX_INPUT_CHARS || jobDescription.length > MAX_INPUT_CHARS) {
      return NextResponse.json({ error: 'Resume or job description is too large' }, { status: 413 });
    }

    if (typeof sessionId !== 'string' || !sessionId.trim()) {
      return NextResponse.json({ error: 'Missing payment session' }, { status: 402 });
    }
    const normalizedSessionId = sessionId.trim();

    const productType = await validatePaidSessionId(normalizedSessionId);
    if (productType instanceof NextResponse) {
      return productType;
    }

    const cachedFulfillment = await readFulfillment(normalizedSessionId);
    if (cachedFulfillment) {
      return NextResponse.json(cachedFulfillment.resumeData);
    }

    const openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY || 'dummy_key_for_build',
    });
    const baseName = buildFulfillmentBaseName(fileName);
    const candidateFacts = extractCandidateFacts(resumeText);
    const userPrompt = `TARGET JOB DESCRIPTION:\n${jobDescription}\n\nCURRENT RESUME TEXT:\n${resumeText}\n\nEXTRACTED CANDIDATE FACTS TO PRESERVE:\n${candidateFactsPrompt(candidateFacts)}`;

    const generate = async (extra: string = ""): Promise<ResumeJson> => {
      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content: `You are an expert ATS (Applicant Tracking System) optimizer. 
Your job is to rewrite the provided resume to closely match the semantics of the target Job Description so it ranks well in recruiter searches.
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

HONESTY RULES (critical - do not violate):
- Never claim a credential, certification, degree, or job the candidate does not have.
- Never add a metric, percentage, dollar amount, date, title, company, tool, or skill unless it is supported by the original resume text.
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
      return parseResumeJson(resultText);
    };

    const generateCoverLetter = async (resumeJson: ResumeJson, extra: string = ""): Promise<CoverLetter> => {
      const completion = await openai.chat.completions.create({
        model: "gpt-4o-mini",
        response_format: { type: "json_object" },
        messages: [
          {
            role: "system",
            content: `You are an expert career consultant and cover letter writer.
Your job is to draft a professional cover letter tailored to the target Job Description, utilizing the candidate's real experience from their Resume.

Output a strict JSON object with the following structure:
{
  "recipientName": "Hiring Team or Hiring Manager",
  "companyName": "Company Name (extract from Job Description if possible, else 'the company')",
  "salutation": "Dear Hiring Manager,",
  "bodyParagraphs": [
    "Paragraph 1 (Clear hook: state interest in the role, reference the company by name, and state a brief overview of why you are a fit)",
    "Paragraph 2 (Highlight your experience matching the JD keywords. Keep it factual and aligned with the resume's experience, without fabricating any details)",
    "Paragraph 3 (Discuss how your core competencies and soft/hard skills will solve their immediate business needs)",
    "Paragraph 4 (Call to action: request an interview, thank them for their time, and state that you look forward to discussing further)"
  ],
  "signOff": "Sincerely,\\n\\nCandidate Name"
}

HONESTY RULES (critical - do not violate):
- Never claim a credential, experience, or skill the candidate does not have in their resume.
- Use only the achievements and background present in the candidate's resume.
- Reference the target role, company when available, and at least 2-3 concrete job-description requirements.
- Anchor every proof point in the candidate resume details. Do not add unsupported metrics or credentials.
- Keep the language professional, direct, specific, and free of hype.` + extra
          },
          {
            role: "user",
            content: `TARGET JOB DESCRIPTION:\n${jobDescription}\n\nCURRENT RESUME TEXT:\n${resumeText}\n\nSTRUCTURED RESUME DETAILS:\n${JSON.stringify(resumeJson)}\n\nEXTRACTED CANDIDATE FACTS TO PRESERVE:\n${candidateFactsPrompt(candidateFacts)}`
          }
        ]
      });
      const resultText = completion.choices[0].message.content;
      if (!resultText) throw new Error("No response from OpenAI");
      return parseCoverLetter(resultText);
    };

    // --- Validation layer: guarantee an honest, actually-optimized result ---
    const jdTokens = [...tokenize(jobDescription)];
    const jdMatches = (text: string) => {
      const t = tokenize(text);
      let n = 0;
      for (const k of jdTokens) if (t.has(k)) n++;
      return n;
    };

    // Generate, then verify it is actually MORE aligned to the JD than the original.
    const origMatch = jdMatches(resumeText);
    const includesResumeRewrite = productType !== 'cover_letter';
    let best = applyFactGrounding(await generate(), candidateFacts, resumeText);
    let bestScore = jdMatches(serializeResume(best));
    let bestErrors = resumeQualityErrors(best, candidateFacts, resumeText);
    if (bestScore <= origMatch) {
      const retry = await generate(
        "\n\nThe previous attempt did not incorporate enough of the job description's keywords. Aggressively weave more of the JD's exact keywords and phrases into the summary, skills, and bullet points - strictly without fabricating any experience, dates, skills, or certifications."
      );
      const groundedRetry = applyFactGrounding(retry, candidateFacts, resumeText);
      const retryScore = jdMatches(serializeResume(groundedRetry));
      const retryErrors = resumeQualityErrors(groundedRetry, candidateFacts, resumeText);
      if (retryErrors.length < bestErrors.length || (retryErrors.length === bestErrors.length && retryScore > bestScore)) {
        best = groundedRetry;
        bestScore = retryScore;
        bestErrors = retryErrors;
      }
    }
    best = applyFactGrounding(best, candidateFacts, resumeText);
    bestScore = jdMatches(serializeResume(best));
    bestErrors = resumeQualityErrors(best, candidateFacts, resumeText);
    if (includesResumeRewrite && bestErrors.length > 0) {
      throw new Error(`Could not produce a grounded, complete resume rewrite: ${bestErrors.join("; ")}`);
    }

    let coverLetter: CoverLetter | undefined;
    if (productType === 'cover_letter' || productType === 'bundle') {
      coverLetter = await generateCoverLetter(best);
      let coverErrors = coverLetterQualityErrors(coverLetter, candidateFacts, resumeText, jobDescription);
      if (coverErrors.length > 0) {
        coverLetter = await generateCoverLetter(
          best,
          `\n\nThe previous cover letter failed quality checks: ${coverErrors.join("; ")}.
Regenerate it with 3-4 substantive paragraphs, exact job-description requirements, and resume-backed proof points only.`
        );
        coverErrors = coverLetterQualityErrors(coverLetter, candidateFacts, resumeText, jobDescription);
      }
      if (coverErrors.length > 0) {
        throw new Error(`Could not produce a specific, grounded cover letter: ${coverErrors.join("; ")}`);
      }
    }

    const response =
      productType === 'cover_letter'
        ? {
            productType,
            name: best.name || '',
            email: best.email || '',
            phone: best.phone || '',
            location: best.location || '',
            linkedin: best.linkedin || '',
            coverLetter,
          }
        : {
            ...best,
            productType,
            ...(coverLetter ? { coverLetter } : {}),
          };

    // If, after all that, the rewrite still isn't more optimized than the original, surface it
    // rather than charging for a no-op (the client can decide how to handle this).
    if (includesResumeRewrite && (bestScore <= origMatch || bestErrors.length > 0)) {
      const lowOptimizationResponse =
        { ...response, _warning: "optimization_low" };
      await writeFulfillment(normalizedSessionId, {
        createdAt: Date.now(),
        baseName,
        resumeData: lowOptimizationResponse,
      });
      return NextResponse.json(lowOptimizationResponse);
    }
    await writeFulfillment(normalizedSessionId, {
      createdAt: Date.now(),
      baseName,
      resumeData: response,
    });
    return NextResponse.json(response);

  } catch (error: unknown) {
    console.error('Error rewriting resume:', error);
    const message = error instanceof Error ? error.message : 'Failed to rewrite resume';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
