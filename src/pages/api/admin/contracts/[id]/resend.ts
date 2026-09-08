export const prerender = false;

import type { APIContext } from 'astro';
import { getContract } from '../../../../../lib/pocketbase';
import { sendContractSigningEmail } from '../../../../../lib/mailer';
import releasesData from '../../../../../../the-moon-os/data/releases.json';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// POST /:id/resend — re-sends (or, without an email on file, just returns) the signing link.
export const POST = async ({ params, url }: APIContext) => {
  const id = params.id;
  if (!id) return json({ error: 'id required' }, 422);

  const contract = await getContract(id);
  if (!contract) return json({ error: 'Contract not found' }, 404);
  if (contract.signed_at) return json({ error: 'Already signed — nothing to resend' }, 409);

  // .env's PUBLIC_SITE_URL is the production domain and always set — plain `??`
  // fallbacks never reach url.origin. In dev, use the actual local origin instead.
  const siteUrl = import.meta.env.DEV ? url.origin : (process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? url.origin);
  const signing_url = `${siteUrl}/contract/sign/${contract.signing_token}`;

  if (!contract.artist_email) {
    return json({ ok: true, mailed: false, signing_url });
  }

  const releaseInfo = releasesData.releases.find((r) => r.catalog === contract.catalog);
  const releaseTitle = releaseInfo?.title ?? contract.catalog;

  try {
    await sendContractSigningEmail(contract.artist_email, contract.artist_name, releaseTitle, signing_url);
    return json({ ok: true, mailed: true, signing_url });
  } catch (e) {
    console.error('[contracts] resend sendContractSigningEmail:', e);
    return json({ error: 'Failed to send email', signing_url }, 502);
  }
};
