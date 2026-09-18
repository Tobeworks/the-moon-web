export const prerender = false;

import type { APIContext } from 'astro';
import { getLinktreeItems, createLinktreeItem } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async () => {
  const items = await getLinktreeItems();
  return json(items);
};

export const POST = async ({ request }: APIContext) => {
  let body: { type?: 'release' | 'link'; release_catalog?: string; label?: string; url?: string } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { type, release_catalog, label, url } = body;
  if (type !== 'release' && type !== 'link') return json({ error: 'type must be "release" or "link"' }, 422);
  if (type === 'release' && !release_catalog) return json({ error: 'release_catalog required for type=release' }, 422);
  if (type === 'link' && (!label || !url)) return json({ error: 'label and url required for type=link' }, 422);

  const existing = await getLinktreeItems();
  // ponytail: position starts at 1, not 0 — PocketBase's "required" check on a
  // number field treats 0 as blank, so a first item at position 0 would 422.
  const position = existing.length > 0 ? Math.max(...existing.map((i) => i.position)) + 1 : 1;

  try {
    const item = await createLinktreeItem({ type, position, release_catalog, label, url });
    return json(item, 201);
  } catch (e) {
    console.error('[linktree] create:', e);
    return json({ error: 'Failed to create linktree item.' }, 500);
  }
};
