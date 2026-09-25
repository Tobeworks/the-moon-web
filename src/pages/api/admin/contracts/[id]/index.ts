export const prerender = false;

import type { APIContext } from 'astro';
import { getContract, deleteContract } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// DELETE /:id — also deletes signed contracts; the admin UI asks for an explicit confirmation first.
export const DELETE = async ({ params }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  const contract = await getContract(id);
  if (!contract) return json({ error: 'Contract not found' }, 404);

  await deleteContract(id);
  return json({ ok: true });
};
