export const prerender = false;

import type { APIContext } from 'astro';
import { randomBytes } from 'node:crypto';
import { getPromoSubscribers, createPromoRecord } from '../../../../lib/pocketbase';
import { sendPromoEmail } from '../../../../lib/mailer';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { releaseSlug, releaseTitle, releaseArtist, expiresAt } = body as Record<string, string>;
  if (!releaseSlug || !releaseTitle || !releaseArtist) {
    return json({ error: 'releaseSlug, releaseTitle and releaseArtist are required' }, 422);
  }

  const siteUrl = process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? 'http://localhost:4321';
  const subscribers = await getPromoSubscribers();

  let sent = 0;
  let failed = 0;
  const errors: string[] = [];

  for (const sub of subscribers) {
    try {
      const token = randomBytes(32).toString('hex');
      await createPromoRecord({
        token,
        release_slug: releaseSlug,
        recipient_name: sub.name ?? sub.email,
        recipient_email: sub.email,
        ...(expiresAt ? { expires_at: expiresAt } : {}),
      });
      const promoUrl = `${siteUrl}/promo/${token}`;
      await sendPromoEmail(sub.email, sub.name ?? '', releaseTitle, releaseArtist, promoUrl, sub.unsubscribe_token, siteUrl);
      sent++;
    } catch (e: any) {
      failed++;
      errors.push(`${sub.email}: ${e.message}`);
    }
  }

  return json({ ok: true, sent, failed, errors });
};
