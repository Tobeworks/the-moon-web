export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoByToken, createFeedback } from '../../../lib/pocketbase';

export const POST = async ({ request }: APIContext) => {
  // Parse body (JSON or form)
  let body: Record<string, string>;
  try {
    const ct = request.headers.get('content-type') ?? '';
    if (ct.includes('application/json')) {
      body = await request.json();
    } else {
      const fd = await request.formData();
      body = Object.fromEntries(fd.entries()) as Record<string, string>;
    }
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid request body' }), {
      status: 400,
      headers: { 'content-type': 'application/json' },
    });
  }

  const { token, name, email, comment } = body;

  if (!token || !name || !email || !comment) {
    return new Response(JSON.stringify({ error: 'Missing required fields' }), {
      status: 422,
      headers: { 'content-type': 'application/json' },
    });
  }

  const promo = await getPromoByToken(token);
  if (!promo) {
    return new Response(JSON.stringify({ error: 'Invalid promo token' }), {
      status: 403,
      headers: { 'content-type': 'application/json' },
    });
  }
  if (promo.expires_at && new Date(promo.expires_at) < new Date()) {
    return new Response(JSON.stringify({ error: 'Promo link expired' }), {
      status: 410,
      headers: { 'content-type': 'application/json' },
    });
  }

  const ip =
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    request.headers.get('x-real-ip') ??
    'unknown';
  const user_agent = request.headers.get('user-agent') ?? 'unknown';

  try {
    await createFeedback({ promo: promo.id, name, email, comment, ip, user_agent });
  } catch {
    return new Response(JSON.stringify({ error: 'Failed to save feedback' }), {
      status: 500,
      headers: { 'content-type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  });
};
