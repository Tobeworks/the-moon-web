export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoRecords, createPromoRecord } from '../../../../lib/pocketbase';
import { randomBytes } from 'node:crypto';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async ({ url }: APIContext) => {
  const release_slug = url.searchParams.get('release_slug') ?? undefined;
  const records = await getPromoRecords(release_slug);
  return json(records);
};

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { release_slug, recipient_name, recipient_email, expires_at } = body;
  if (!release_slug || !recipient_name) return json({ error: 'release_slug and recipient_name required' }, 422);

  const token = randomBytes(16).toString('hex');
  const record = await createPromoRecord({ token, release_slug, recipient_name, recipient_email: recipient_email ?? '', expires_at });
  return json(record, 201);
};
