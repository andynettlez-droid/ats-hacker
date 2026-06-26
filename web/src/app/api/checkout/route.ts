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
    const body = await req.json();
    const type = body.type || 'resume'; // 'resume', 'cover_letter', or 'bundle'
    const utms = utmMetadata(body);
    const origin = req.headers.get('origin') || 'https://ats-hacker-swart.vercel.app';
    
    let productName = 'ATSHacker — Resume Optimization';
    let productDesc = '1x semantic job-description resume optimization';
    let amount = 999; // $9.99

    if (type === 'cover_letter') {
      productName = 'ATSHacker — Cover Letter Generation';
      productDesc = '1x semantic job-description cover letter tailoring';
      amount = 999; // $9.99
    } else if (type === 'bundle') {
      productName = 'ATSHacker — Resume & Cover Letter Bundle';
      productDesc = '1x semantic job-description resume & matching cover letter tailoring';
      amount = 1499; // $14.99
    }

    // Create a Stripe Checkout Session
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: productName,
              description: productDesc,
            },
            unit_amount: amount,
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      payment_intent_data: {
        description: productName,
        statement_descriptor_suffix: 'ATSHacker',
        metadata: { app: 'atshacker', product_type: type, ...utms },
      },
      metadata: { app: 'atshacker', product_type: type, ...utms },
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error('Error creating Stripe session:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
