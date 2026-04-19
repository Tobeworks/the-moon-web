export const prerender = false;

import type { APIContext } from 'astro';
import { getCampaigns, createCampaign } from '../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async () => {
  const campaigns = await getCampaigns();
  return json(campaigns);
};

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    const ct = request.headers.get('content-type') ?? '';
    if (ct.includes('application/json')) {
      body = await request.json();
    } else {
      const fd = await request.formData();
      body = Object.fromEntries(fd.entries()) as Record<string, string>;
    }
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { subject, body_html, body_text } = body;
  if (!subject) return json({ error: 'subject required' }, 422);

  const campaign = await createCampaign(subject, body_html, body_text ?? '');
  return json(campaign, 201);
};
