export const prerender = false;

import type { APIContext } from 'astro';
import { getSplit, deleteSplit } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// DELETE /:splitId — removes a mis-entered split. Refuses if it's already signed
// (deleting it would destroy the signature record, not just fix a typo).
export const DELETE = async ({ params }: APIContext) => {
  const splitId = params.splitId;
  if (!splitId) return json({ error: 'splitId required' }, 422);

  const split = await getSplit(splitId);
  if (!split) return json({ error: 'Split not found' }, 404);
  if (split.signed_at) return json({ error: 'This split is already signed and cannot be deleted.' }, 409);

  await deleteSplit(splitId);
  return json({ ok: true });
};
