export const prerender = false;

import type { APIContext } from 'astro';
import { getSplit, getSplitSheetRelease } from '../../../../../lib/pocketbase';
import { sendSplitSigningEmail } from '../../../../../lib/mailer';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// POST /:splitId/resend — re-sends (or, without an email on file, just returns) the signing link.
export const POST = async ({ params, url }: APIContext) => {
  const splitId = params.splitId;
  if (!splitId) return json({ error: 'splitId required' }, 422);

  const split = await getSplit(splitId);
  if (!split) return json({ error: 'Split not found' }, 404);
  if (split.signed_at) return json({ error: 'Already signed — nothing to resend' }, 409);

  const release = await getSplitSheetRelease(split.release);
  if (!release) return json({ error: 'Release not found' }, 404);

  // .env's PUBLIC_SITE_URL is the production domain and always set — plain `??`
  // fallbacks never reach url.origin. In dev, use the actual local origin instead.
  const siteUrl = import.meta.env.DEV ? url.origin : (process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? url.origin);
  const signing_url = `${siteUrl}/split-sheet/sign/${split.signing_token}`;

  if (!split.artist_email) {
    return json({ ok: true, mailed: false, signing_url });
  }

  try {
    await sendSplitSigningEmail(split.artist_email, split.artist_name, release.catalog, split.percentage, signing_url);
    return json({ ok: true, mailed: true, signing_url });
  } catch (e) {
    console.error('[split-sheets] resend sendSplitSigningEmail:', e);
    return json({ error: 'Failed to send email', signing_url }, 502);
  }
};
