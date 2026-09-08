export const prerender = false;

import type { APIContext } from 'astro';
import { updateContractTemplate, deleteContractTemplate, getContractsByTemplate } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const PATCH = async ({ params, request }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  let body: { name?: string; body_md?: string; is_active?: boolean } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { name, body_md, is_active } = body;
  if (!name || !body_md) return json({ error: 'name and body_md required' }, 422);

  try {
    const template = await updateContractTemplate(id, { name, body_md, is_active });
    return json(template);
  } catch (e) {
    console.error('[contract-templates] update:', e);
    return json({ error: 'Failed to update template.' }, 500);
  }
};

// DELETE /:id — refuses if any contract still references this template, so a
// contract's provenance ("which template was this") never silently disappears.
export const DELETE = async ({ params }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  const inUse = await getContractsByTemplate(id);
  if (inUse.length > 0) {
    return json({ error: 'This template is used by one or more contracts and cannot be deleted.' }, 409);
  }

  await deleteContractTemplate(id);
  return json({ ok: true });
};
