import { NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_key', {
  apiVersion: '2026-05-27.dahlia',
});

export async function POST(req: Request) {
  try {
    // We would normally parse the resume URL here to pass to metadata
    const body = await req.json();
    
    const origin = req.headers.get('origin') || 'https://ats-hacker-swart.vercel.app';
    
    // Create a Stripe Checkout Session for $5
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [
        {
          price_data: {
            currency: 'usd',
            product_data: {
              name: 'ATS Resume Hacker',
              description: '1x Semantic Job Description Optimization',
            },
            unit_amount: 500, // $5.00
          },
          quantity: 1,
        },
      ],
      mode: 'payment',
      success_url: `${origin}/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error: any) {
    console.error('Error creating Stripe session:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
