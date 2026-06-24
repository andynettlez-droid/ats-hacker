import { cookies } from 'next/headers';
import { createHmac, timingSafeEqual } from 'crypto';

/**
 * Admin auth for the analytics dashboard.
 *
 * We never store the raw password in the cookie. Instead we store an HMAC of a
 * fixed marker keyed by ADMIN_PASSWORD. To verify, we recompute the HMAC with the
 * current ADMIN_PASSWORD and compare in constant time. If ADMIN_PASSWORD is unset,
 * access is always denied.
 */

export const ADMIN_COOKIE = 'atsh_admin';
const COOKIE_MARKER = 'atshacker-admin-v1';

function expectedToken(): string | null {
  const pw = process.env.ADMIN_PASSWORD;
  if (!pw || pw.length === 0) return null;
  return createHmac('sha256', pw).update(COOKIE_MARKER).digest('hex');
}

/** Constant-time string comparison that tolerates length differences. */
function safeEqual(a: string, b: string): boolean {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ab.length !== bb.length) {
    // Still run a comparison to avoid a trivial early-exit, then fail.
    timingSafeEqual(ab, ab);
    return false;
  }
  return timingSafeEqual(ab, bb);
}

/** True only when ADMIN_PASSWORD is set AND matches the supplied password. */
export function passwordMatches(candidate: string): boolean {
  const pw = process.env.ADMIN_PASSWORD;
  if (!pw || pw.length === 0) return false;
  if (typeof candidate !== 'string' || candidate.length === 0) return false;
  return safeEqual(candidate, pw);
}

/** The opaque token value we set in the httpOnly cookie after a correct login. */
export function sessionToken(): string | null {
  return expectedToken();
}

/** Verify a request is authenticated by checking the httpOnly cookie. */
export async function isAuthedFromCookies(): Promise<boolean> {
  const expected = expectedToken();
  if (!expected) return false; // ADMIN_PASSWORD unset -> always locked
  const store = await cookies();
  const got = store.get(ADMIN_COOKIE)?.value;
  if (!got) return false;
  return safeEqual(got, expected);
}
