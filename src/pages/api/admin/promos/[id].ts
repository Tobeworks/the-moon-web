export const prerender = false;

import type { APIContext } from 'astro';
import { deletePromoRecord } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const DELETE = async ({ params }: APIContext) => {
  const { id } = params;
  if (!id) return json({ error: 'id required' }, 422);
  await deletePromoRecord(id);
  return json({ ok: true });
};
