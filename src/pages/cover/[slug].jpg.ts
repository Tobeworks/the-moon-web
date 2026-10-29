export const prerender = false;

import type { APIRoute } from 'astro';
import { findRelease, squareCover } from '../../lib/release';

// Same-origin cover for the Instagram-story canvas: the CDN sends no CORS headers,
// so drawing its image directly would taint the canvas and toBlob() would throw.
export const GET: APIRoute = async ({ params }) => {
  const release = findRelease(params.slug);
  const cover = release && (await squareCover(release, 880));
  if (!cover) return new Response('Not found', { status: 404 });

  return new Response(cover, {
    headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=86400' },
  });
};
