export const prerender = false;

import type { APIContext } from 'astro';
import {
  getSubscriberByEmail,
  createSubscriber,
  refreshConfirmationToken,
} from '../../../lib/pocketbase';
import {
  sendConfirmationEmail,
  sendAlreadySubscribedEmail,
} from '../../../lib/mailer';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const POST = async ({ request, url }: APIContext) => {
  const siteUrl = url.origin;
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
    return json({ error: 'Invalid request body' }, 400);
  }

  const email = (body.email ?? '').trim().toLowerCase();
  const name  = (body.name  ?? '').trim().slice(0, 100);

  if (!email || !EMAIL_RE.test(email)) {
    return json({ error: 'Invalid email address' }, 422);
  }

  // Always return ok — no email enumeration possible from the outside
  try {
    const existing = await getSubscriberByEmail(email);

    if (existing) {
      if (existing.confirmed) {
        await sendAlreadySubscribedEmail(email, existing.name ?? '', existing.unsubscribe_token, siteUrl).catch((e) => console.error('[newsletter] sendAlreadySubscribedEmail:', e));
      } else {
        // Resend with a fresh token
        const updated = await refreshConfirmationToken(existing.id);
        await sendConfirmationEmail(email, existing.name ?? '', updated.confirmation_token, siteUrl).catch((e) => console.error('[newsletter] sendConfirmationEmail (resend):', e));
      }
    } else {
      const subscriber = await createSubscriber(email, name);
      await sendConfirmationEmail(email, name, subscriber.confirmation_token, siteUrl).catch((e) => console.error('[newsletter] sendConfirmationEmail:', e));
    }
  } catch (e) {
    console.error('[newsletter] subscribe error:', e);
  }

  return json({ ok: true }, 200);
};

function json(data: unknown, status: number) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'content-type': 'application/json' },
  });
}
