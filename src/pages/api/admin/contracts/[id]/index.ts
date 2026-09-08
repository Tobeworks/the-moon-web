export const prerender = false;

import type { APIContext } from 'astro';
import { getContract, deleteContract } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// DELETE /:id — refuses if already signed, so a signature record is never destroyed.
export const DELETE = async ({ params }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  const contract = await getContract(id);
  if (!contract) return json({ error: 'Contract not found' }, 404);
  if (contract.signed_at) return json({ error: 'This contract is already signed and cannot be deleted.' }, 409);

  await deleteContract(id);
  return json({ ok: true });
};
