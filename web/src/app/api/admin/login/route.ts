import { NextResponse } from 'next/server';
import { ADMIN_COOKIE, passwordMatches, sessionToken } from '@/lib/adminAuth';

export const runtime = 'nodejs';

export async function POST(req: Request) {
  // Reject outright if no admin password is configured on the server.
  if (!process.env.ADMIN_PASSWORD) {
    return NextResponse.json(
      { error: 'Admin access is not configured.' },
      { status: 503 },
    );
  }

  let password = '';
  try {
    const body = await req.json();
    password = typeof body?.password === 'string' ? body.password : '';
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  if (!passwordMatches(password)) {
    return NextResponse.json({ error: 'Incorrect password.' }, { status: 401 });
  }

  const token = sessionToken();
  if (!token) {
    return NextResponse.json({ error: 'Admin access is not configured.' }, { status: 503 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 8, // 8 hours
  });
  return res;
}

/** Logout: clear the cookie. */
export async function DELETE() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_COOKIE, '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 0,
  });
  return res;
}
