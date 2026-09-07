export const prerender = false;

import type { APIContext } from 'astro';
import { getSplitsForRelease, deleteSplitSheetRelease } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// DELETE /:id — removes a mis-entered release and cascades its splits. Refuses if
// any split is already signed, to avoid destroying a signature record.
export const DELETE = async ({ params }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  const splits = await getSplitsForRelease(id);
  if (splits.some((s) => s.signed_at)) {
    return json({ error: 'This release has signed splits and cannot be deleted.' }, 409);
  }

  await deleteSplitSheetRelease(id);
  return json({ ok: true });
};
