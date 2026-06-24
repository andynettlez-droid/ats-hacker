import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { isAuthedFromCookies } from '@/lib/adminAuth';

export const runtime = 'nodejs';
// Always compute fresh from Stripe; never cache financials.
export const dynamic = 'force-dynamic';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

// Window for the dashboard time-series / "current period".
const WINDOW_DAYS = 30;
const DAY_SECONDS = 24 * 60 * 60;

type Transaction = {
  id: string;
  date: string; // ISO
  email: string | null;
  amount: number; // dollars
  currency: string;
  status: string;
  paymentMethod: string;
};

function dayKey(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toISOString().slice(0, 10); // YYYY-MM-DD
}

function emptyDailySeries(startEpoch: number, days: number) {
  const series: { date: string; revenue: number; sales: number }[] = [];
  for (let i = 0; i < days; i++) {
    series.push({ date: dayKey(startEpoch + i * DAY_SECONDS), revenue: 0, sales: 0 });
  }
  return series;
}

export async function GET() {
  // ---- Auth gate: never expose financials without a valid admin cookie. ----
  if (!(await isAuthedFromCookies())) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const nowEpoch = Math.floor(Date.now() / 1000);
  const periodStart = nowEpoch - WINDOW_DAYS * DAY_SECONDS;
  const prevPeriodStart = periodStart - WINDOW_DAYS * DAY_SECONDS;

  try {
    // Pull paid Checkout Sessions across the current + previous window (for growth).
    // Stripe paginates 100 at a time; auto-pagination keeps this simple.
    const sessions: Stripe.Checkout.Session[] = [];
    for await (const s of stripe.checkout.sessions.list({
      created: { gte: prevPeriodStart },
      limit: 100,
      expand: ['data.payment_intent'],
    })) {
      sessions.push(s);
    }

    // Keep only successfully paid sessions.
    const paid = sessions.filter((s) => s.payment_status === 'paid');

    let totalRevenue = 0; // dollars, current window
    let totalSales = 0; // count, current window
    let prevRevenue = 0; // dollars, previous window
    const customerEmails = new Set<string>();
    const daily = emptyDailySeries(periodStart, WINDOW_DAYS);
    const dailyIndex = new Map(daily.map((d, i) => [d.date, i]));
    const transactions: Transaction[] = [];

    for (const s of paid) {
      const created = s.created ?? 0;
      const currency = (s.currency || 'usd').toLowerCase();
      // amount_total is in the smallest currency unit (cents for USD).
      const amountDollars = (s.amount_total ?? 0) / 100;

      if (created >= periodStart) {
        // Current window.
        totalRevenue += amountDollars;
        totalSales += 1;

        const key = dayKey(created);
        const idx = dailyIndex.get(key);
        if (idx !== undefined) {
          daily[idx].revenue += amountDollars;
          daily[idx].sales += 1;
        }

        const email =
          s.customer_details?.email ?? s.customer_email ?? null;
        if (email) customerEmails.add(email.toLowerCase());

        // Derive a human payment method label from the expanded PaymentIntent.
        let paymentMethod = 'card';
        const pi = s.payment_intent;
        if (pi && typeof pi !== 'string') {
          const types = pi.payment_method_types;
          if (Array.isArray(types) && types.length > 0) paymentMethod = types[0];
        } else if (Array.isArray(s.payment_method_types) && s.payment_method_types.length > 0) {
          paymentMethod = s.payment_method_types[0];
        }

        transactions.push({
          id: s.id,
          date: new Date(created * 1000).toISOString(),
          email,
          amount: amountDollars,
          currency,
          status: s.payment_status,
          paymentMethod,
        });
      } else if (created >= prevPeriodStart) {
        // Previous window — only needed for the growth comparison.
        prevRevenue += amountDollars;
      }
    }

    // Growth rate: current vs previous equivalent period.
    // If the previous period had no revenue, report 100% growth when we have
    // revenue now, otherwise 0 (avoids divide-by-zero / Infinity).
    let growthRate: number;
    if (prevRevenue > 0) {
      growthRate = ((totalRevenue - prevRevenue) / prevRevenue) * 100;
    } else {
      growthRate = totalRevenue > 0 ? 100 : 0;
    }

    // Most recent transactions first, capped to a sensible table size.
    transactions.sort((a, b) => (a.date < b.date ? 1 : -1));
    const recentTransactions = transactions.slice(0, 10);

    return NextResponse.json({
      currency: 'usd',
      windowDays: WINDOW_DAYS,
      totalRevenue: Math.round(totalRevenue * 100) / 100,
      totalSales,
      uniqueCustomers: customerEmails.size,
      growthRate: Math.round(growthRate * 10) / 10,
      dailySeries: daily,
      recentTransactions,
      generatedAt: new Date().toISOString(),
    });
  } catch (error: unknown) {
    const message =
      error instanceof Error ? error.message : 'Failed to load Stripe analytics.';
    console.error('Admin stats error:', message);
    // Graceful zero-state so the dashboard never crashes on a fresh/empty account.
    return NextResponse.json(
      {
        currency: 'usd',
        windowDays: WINDOW_DAYS,
        totalRevenue: 0,
        totalSales: 0,
        uniqueCustomers: 0,
        growthRate: 0,
        dailySeries: emptyDailySeries(periodStart, WINDOW_DAYS),
        recentTransactions: [],
        generatedAt: new Date().toISOString(),
        error: 'stripe_unavailable',
      },
      { status: 200 },
    );
  }
}
