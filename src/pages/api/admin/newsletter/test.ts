export const prerender = false;

import type { APIContext } from 'astro';
import { getCampaign } from '../../../../lib/pocketbase';
import { sendCampaignEmail } from '../../../../lib/mailer';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { id, email } = body;
  if (!id || !email) return json({ error: 'id and email required' }, 422);

  const campaign = await getCampaign(id);
  if (!campaign) return json({ error: 'Campaign not found' }, 404);

  const siteUrl = process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? 'http://localhost:4321';

  try {
    await sendCampaignEmail(
      email,
      'Admin',
      `[TEST] ${campaign.subject}`,
      campaign.body_html,
      campaign.body_text ?? '',
      'test-unsubscribe-token',
      siteUrl,
    );
    return json({ ok: true, sent: 1, failed: 0 });
  } catch (e) {
    console.error('[campaign/test]', e);
    return json({ ok: false, sent: 0, failed: 1, error: String(e) });
  }
};
