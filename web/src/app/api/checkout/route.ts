import { NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

const PRODUCT_CONFIG = {
  resume: {
    productName: 'Signal by ATSHacker - Resume Optimization',
    productDesc: '1x semantic job-description resume optimization',
    amount: 999,
  },
  cover_letter: {
    productName: 'Signal by ATSHacker - Cover Letter Generation',
    productDesc: '1x semantic job-description cover letter tailoring',
    amount: 999,
  },
  bundle: {
    productName: 'Signal by ATSHacker - Resume & Cover Letter Bundle',
    productDesc: '1x semantic job-description resume & matching cover letter tailoring',
    amount: 1499,
  },
} as const;

type ProductType = keyof typeof PRODUCT_CONFIG;

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

function isProductType(value: unknown): value is ProductType {
  return typeof value === 'string' && value in PRODUCT_CONFIG;
}

function resolveAppOrigin(req: Request): string {
  const configured = process.env.NEXT_PUBLIC_APP_URL || process.env.APP_URL;
  const vercel = process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : undefined;
  const fallback = 'https://ats-hacker-swart.vercel.app';
  const allowed = new Set([configured, vercel, fallback, 'http://localhost:3000'].filter(Boolean));
  const origin = req.headers.get('origin');

  return origin && allowed.has(origin) ? origin : configured || vercel || fallback;
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const type = body.type || 'resume';
    if (!isProductType(type)) {
      return NextResponse.json({ error: 'Invalid product type' }, { status: 400 });
    }

    const utms = utmMetadata(body);
    const origin = resolveAppOrigin(req);
    const { productName, productDesc, amount } = PRODUCT_CONFIG[type];

    const session = await stripe.checkout.sessions.create({
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
        statement_descriptor_suffix: 'SIGNAL',
        metadata: { app: 'atshacker', product_type: type, ...utms },
      },
      metadata: { app: 'atshacker', product_type: type, ...utms },
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error: unknown) {
    console.error('Error creating Stripe session:', error);
    const message = error instanceof Error ? error.message : 'Internal Server Error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
