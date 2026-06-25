import type { MetadataRoute } from 'next';

// Set NEXT_PUBLIC_SITE_URL in your env (e.g. https://atshacker.com).
const BASE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://ats-hacker-swart.vercel.app').replace(/\/$/, '');

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/admin', '/api'],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
    host: BASE_URL,
  };
}
