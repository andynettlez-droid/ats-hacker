import { NextResponse } from 'next/server';
import OpenAI from 'openai';
import { PDFDocument, StandardFonts, rgb } from 'pdf-lib';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'sk-mock-key',
});

export async function POST(req: Request) {
  try {
    const { rawResumeText, jobDescription } = await req.json();

    if (!rawResumeText || !jobDescription) {
      return NextResponse.json({ error: 'Missing inputs' }, { status: 400 });
    }

    // 1. Call OpenAI to optimize the resume
    const completion = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: "You are an expert ATS (Applicant Tracking System) optimizer. Take the user's raw resume and rewrite it to perfectly match the semantic keywords of the provided Job Description. Do not lie or invent experience, but ruthlessly rephrase existing experience to match the exact verbiage of the JD. Output ONLY the new resume text in a clean, readable format."
        },
        {
          role: "user",
          content: `JOB DESCRIPTION:\n${jobDescription}\n\nORIGINAL RESUME:\n${rawResumeText}`
        }
      ],
      temperature: 0.2,
    });

    const optimizedText = completion.choices[0].message.content || "";

    // 2. Generate PDF output using pdf-lib
    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage();
    const { width, height } = page.getSize();
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

    // Super simple layout logic for demo purposes
    const lines = optimizedText.split('\n');
    let y = height - 50;
    
    for (const line of lines) {
      if (y < 50) {
        // We need a new page logic in a real app, clipping for demo
        break; 
      }
      page.drawText(line, { x: 50, y, size: 10, font, color: rgb(0, 0, 0) });
      y -= 14;
    }

    const pdfBytes = await pdfDoc.save();
    
    // 3. Return the PDF file
    return new NextResponse(pdfBytes, {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="ATS_Optimized_Resume.pdf"',
      },
    });

  } catch (error) {
    console.error('Error processing resume:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
