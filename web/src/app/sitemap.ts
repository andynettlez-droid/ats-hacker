import type { MetadataRoute } from 'next';
import { roles } from '@/data/roles';

// Set NEXT_PUBLIC_SITE_URL in your env (e.g. https://atshacker.com).
const BASE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://ats-hacker-swart.vercel.app').replace(/\/$/, '');

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    { url: `${BASE_URL}/`, lastModified: now, changeFrequency: 'weekly', priority: 1 },
  ];

  const roleRoutes: MetadataRoute.Sitemap = roles.map((r) => ({
    url: `${BASE_URL}/tailor/${r.slug}`,
    lastModified: now,
    changeFrequency: 'monthly',
    priority: 0.8,
  }));

  return [...staticRoutes, ...roleRoutes];
}
