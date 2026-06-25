import { NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

// Pull UTM params out of the request body, sanitize, and cap length so we never
// blow Stripe's 500-char metadata limit. Omits any that are absent/empty.
function utmMetadata(body: Record<string, unknown>): Record<string, string> {
  const out: Record<string, string> = {};
  for (const key of ['utm_source', 'utm_medium', 'utm_campaign']) {
    const raw = body?.[key];
    if (typeof raw === 'string') {
      const trimmed = raw.trim().slice(0, 200);
      if (trimmed) out[key] = trimmed;
    }
  }
  return out;
}

export async function POST(req: Request) {
  try {
    // We would normally parse the resume URL here to pass to metadata
    const body = await req.json();

    const utms = utmMetadata(body);

    const origin = req.headers.get('origin') || 'https://ats-hacker-swart.vercel.app';
    
    // Create a Stripe Checkout Session for $9.99
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: 'ATSHacker — Resume Optimization',
              description: '1x semantic job-description optimization',
            },
            unit_amount: 999, // $9.99
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      // Branding for the charge itself. NOTE: the business name shown at the TOP of
      // the hosted Checkout page comes from your Stripe Dashboard "Public business
      // name", not from here — update it there if it still reads "wificheckout".
      payment_intent_data: {
        description: 'ATSHacker resume optimization',
        statement_descriptor_suffix: 'ATSHacker',
        // Tag every ATSHacker charge so analytics can exclude unrelated revenue
        // (this Stripe account also carries legacy WiFiCheckup sales).
        metadata: { app: 'atshacker', ...utms },
      },
      metadata: { app: 'atshacker', ...utms },
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error('Error creating Stripe session:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
