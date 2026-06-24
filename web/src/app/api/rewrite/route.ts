import { NextResponse } from 'next/server';
import OpenAI from 'openai';

export async function POST(req: Request) {
  const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY || "dummy_key_for_build",
  });
  try {
    const { resumeText, jobDescription } = await req.json();

    if (!resumeText || !jobDescription) {
      return NextResponse.json({ error: 'Missing resume or job description' }, { status: 400 });
    }

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
  ]
}
Be honest but highlight the overlapping skills aggressively. Do not fabricate jobs they never had.`
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
