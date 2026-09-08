export const prerender = false;

import type { APIContext } from 'astro';
import { createHash } from 'node:crypto';
import { getContractByToken, signContract } from '../../../lib/pocketbase';

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

  const contract = await getContractByToken(token);
  if (!contract) return json({ error: 'Invalid or expired link' }, 404);

  if (contract.signed_at) return json({ error: 'This contract has already been signed' }, 409);
  if (contract.token_expires_at && new Date(contract.token_expires_at) < new Date()) {
    return json({ error: 'This signing link has expired' }, 410);
  }

  // Hashed over exactly the stored rendered_body — the text this signer actually saw,
  // independent of any later edits to the template it came from.
  const document_hash = createHash('sha256').update(contract.rendered_body).digest('hex');

  const ip_address =
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ??
    request.headers.get('x-real-ip') ??
    'unknown';

  const signed = await signContract(contract.id, { signed_name: signed_name.trim(), ip_address, document_hash });

  return json({ ok: true, signed_at: signed.signed_at, signed_name: signed.signed_name });
};
