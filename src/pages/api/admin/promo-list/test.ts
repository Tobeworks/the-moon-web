export const prerender = false;

import type { APIContext } from 'astro';
import { randomBytes } from 'node:crypto';
import { createPromoRecord } from '../../../../lib/pocketbase';
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

  const { releaseSlug, releaseTitle, releaseArtist, testEmail } = body as Record<string, string>;
  if (!releaseSlug || !releaseTitle || !releaseArtist || !testEmail) {
    return json({ error: 'releaseSlug, releaseTitle, releaseArtist and testEmail are required' }, 422);
  }

  const siteUrl = process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? 'http://localhost:4321';

  try {
    const token = randomBytes(6).toString('base64url').toUpperCase().replace(/[^A-Z]/g, '').padEnd(8, 'X').slice(0, 8);
    await createPromoRecord({
      token,
      release_slug: releaseSlug.toLowerCase(),
      recipient_name: 'TEST',
      recipient_email: testEmail,
    });
    const promoUrl = `${siteUrl}/promo/${releaseSlug.toLowerCase()}?t=${token}`;
    // Use a dummy unsubscribe token for test mails
    await sendPromoEmail(testEmail, 'TEST', releaseTitle, releaseArtist, promoUrl, 'test-token', siteUrl);
    return json({ ok: true, promoUrl });
  } catch (e: any) {
    return json({ ok: false, error: e.message }, 500);
  }
};
