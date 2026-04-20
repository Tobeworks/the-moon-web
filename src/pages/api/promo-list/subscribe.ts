export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoSubscriberByEmail, createPromoSubscriber } from '../../../lib/pocketbase';
import { sendPromoWelcomeEmail } from '../../../lib/mailer';
import { randomBytes } from 'node:crypto';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    const ct = request.headers.get('content-type') ?? '';
    body = ct.includes('application/json')
      ? await request.json()
      : Object.fromEntries(await request.formData()) as Record<string, string>;
  } catch {
    return json({ ok: false, error: 'Invalid body' }, 400);
  }

  const email = (body.email ?? '').trim().toLowerCase();
  const name  = (body.name  ?? '').trim();

  if (!email) return json({ ok: false, error: 'Email required' }, 422);

  const siteUrl = process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? 'http://localhost:4321';

  // Silent if already subscribed (no enumeration leak)
  const existing = await getPromoSubscriberByEmail(email);
  if (existing) return json({ ok: true });

  const token = randomBytes(32).toString('hex');
  await createPromoSubscriber(email, name, token);

  // Fire-and-forget welcome mail
  sendPromoWelcomeEmail(email, name, token, siteUrl).catch(console.error);

  return json({ ok: true });
};
