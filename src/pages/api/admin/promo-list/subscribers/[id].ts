export const prerender = false;

import type { APIContext } from 'astro';
import { deletePromoSubscriber } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const DELETE = async ({ params }: APIContext) => {
  const { id } = params;
  if (!id) return json({ error: 'ID required' }, 422);
  await deletePromoSubscriber(id);
  return json({ ok: true });
};
