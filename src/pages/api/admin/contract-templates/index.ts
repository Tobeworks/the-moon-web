export const prerender = false;

import type { APIContext } from 'astro';
import { getContractTemplates, createContractTemplate } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async () => {
  const templates = await getContractTemplates();
  return json(templates);
};

export const POST = async ({ request }: APIContext) => {
  let body: { name?: string; body_md?: string; is_active?: boolean } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { name, body_md, is_active } = body;
  if (!name || !body_md) return json({ error: 'name and body_md required' }, 422);

  try {
    const template = await createContractTemplate({ name, body_md, is_active });
    return json(template, 201);
  } catch (e) {
    console.error('[contract-templates] create:', e);
    return json({ error: 'Failed to create template.' }, 500);
  }
};
