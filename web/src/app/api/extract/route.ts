import { NextResponse } from 'next/server';
import pdf from 'pdf-parse';

export async function POST(req: Request) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File;
    if (!file) {
      return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
    }
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const data = await pdf(buffer);
    return NextResponse.json({ text: data.text });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: "Failed to extract text from PDF" }, { status: 500 });
  }
}
