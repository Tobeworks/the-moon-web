export const prerender = false;

import type { APIContext } from 'astro';
import { getCampaign, updateCampaign, getConfirmedSubscribers } from '../../../../lib/pocketbase';
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

  const { id } = body;
  if (!id) return json({ error: 'Campaign id required' }, 422);

  const campaign = await getCampaign(id);
  if (!campaign) return json({ error: 'Campaign not found' }, 404);
  if (campaign.status === 'sent') return json({ error: 'Campaign already sent' }, 409);

  await updateCampaign(id, { status: 'sending' });

  const subscribers = await getConfirmedSubscribers();
  const siteUrl = process.env.PUBLIC_SITE_URL ?? 'https://the-moon-records.de';

  let sent = 0;
  let failed = 0;

  for (const sub of subscribers) {
    try {
      await sendCampaignEmail(
        sub.email,
        sub.name ?? '',
        campaign.subject,
        campaign.body_html,
        campaign.body_text ?? '',
        sub.unsubscribe_token,
        siteUrl,
      );
      sent++;
    } catch (e) {
      console.error(`[campaign] failed to send to ${sub.email}:`, e);
      failed++;
    }
  }

  await updateCampaign(id, {
    status: 'sent',
    sent_at: new Date().toISOString().replace('T', ' '),
    sent_count: sent,
    failed_count: failed,
  } as any);

  return json({ ok: true, sent, failed });
};
