export const prerender = false;

import type { APIContext } from 'astro';
import { updateLinktreeItem, deleteLinktreeItem } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const PATCH = async ({ params, request }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  let body: Partial<{ type: 'release' | 'link'; release_catalog: string; label: string; url: string }> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  try {
    const item = await updateLinktreeItem(id, body);
    return json(item);
  } catch (e) {
    console.error('[linktree] update:', e);
    return json({ error: 'Failed to update linktree item.' }, 500);
  }
};

export const DELETE = async ({ params }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  await deleteLinktreeItem(id);
  return json({ ok: true });
};
