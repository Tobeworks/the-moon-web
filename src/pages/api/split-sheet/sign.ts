export const prerender = false;

import type { APIContext } from 'astro';
import { getSplitByToken, getSplitsForRelease, signSplit, checkAndMarkFullySigned } from '../../../lib/pocketbase';
import { hashDocument } from '../../../lib/splitSheetHash';
import releasesData from '../../../../the-moon-os/data/releases.json';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// POST / — body: { token, signed_name }. The one action a signing link can take.
export const POST = async ({ request }: APIContext) => {
  let body: { token?: string; signed_name?: string } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { token, signed_name } = body;
  if (!token || !signed_name?.trim()) return json({ error: 'token and signed_name required' }, 422);

  const found = await getSplitByToken(token);
  if (!found) return json({ error: 'Invalid or expired link' }, 404);
  const { split, release } = found;

  if (split.signed_at) return json({ error: 'This split has already been signed' }, 409);
  if (split.token_expires_at && new Date(split.token_expires_at) < new Date()) {
    return json({ error: 'This signing link has expired' }, 410);
  }

  const releaseInfo = releasesData.releases.find((r) => r.catalog === release.catalog);
  const releaseTitle = releaseInfo?.title ?? release.catalog;

  const allSplits = await getSplitsForRelease(release.id);
  const document_hash = hashDocument(releaseTitle, release.catalog, allSplits);

  const ip_address =
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    request.headers.get('x-real-ip') ??
    'unknown';

  const signed = await signSplit(split.id, { signed_name: signed_name.trim(), ip_address, document_hash });
  await checkAndMarkFullySigned(release.id);

  return json({ ok: true, signed_at: signed.signed_at, signed_name: signed.signed_name });
};
