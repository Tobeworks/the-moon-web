export const prerender = false;

import type { APIContext } from 'astro';
import { getCampaign, updateCampaign, deleteCampaign } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async ({ params }: APIContext) => {
  const campaign = await getCampaign(params.id!);
  if (!campaign) return json({ error: 'Not found' }, 404);
  return json(campaign);
};

export const PATCH = async ({ params, request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }
  const campaign = await updateCampaign(params.id!, body);
  return json(campaign);
};

export const DELETE = async ({ params }: APIContext) => {
  await deleteCampaign(params.id!);
  return json({ ok: true });
};
