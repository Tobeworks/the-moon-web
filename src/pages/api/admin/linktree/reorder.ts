export const prerender = false;

import type { APIContext } from 'astro';
import { getLinktreeItems, updateLinktreeItem } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// POST { id, direction } — swaps this item's position with its neighbor in that
// direction. Server-side so the client never writes raw position values.
export const POST = async ({ request }: APIContext) => {
  let body: { id?: string; direction?: 'up' | 'down' } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { id, direction } = body;
  if (!id || (direction !== 'up' && direction !== 'down')) {
    return json({ error: 'id and direction ("up"|"down") required' }, 422);
  }

  const items = await getLinktreeItems(); // sorted by position ascending
  const idx = items.findIndex((i) => i.id === id);
  if (idx === -1) return json({ error: 'Item not found' }, 404);

  const neighborIdx = direction === 'up' ? idx - 1 : idx + 1;
  if (neighborIdx < 0 || neighborIdx >= items.length) {
    return json({ items }); // already at the edge — no-op, not an error
  }

  const a = items[idx];
  const b = items[neighborIdx];
  await Promise.all([
    updateLinktreeItem(a.id, { position: b.position }),
    updateLinktreeItem(b.id, { position: a.position }),
  ]);

  const updated = await getLinktreeItems();
  return json({ items: updated });
};
