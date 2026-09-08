export const prerender = false;

import type { APIContext } from 'astro';
import { getContracts, getContractTemplate, createContract } from '../../../../lib/pocketbase';
import { sendContractSigningEmail } from '../../../../lib/mailer';
import { generateSigningToken } from '../../../../lib/splitSheetHash';
import { renderTemplate, findPlaceholders } from '../../../../lib/contractTemplate';
import releasesData from '../../../../../the-moon-os/data/releases.json';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

// GET / — every contract, for the admin list
export const GET = async () => {
  const contracts = await getContracts();
  return json(contracts);
};

// POST / — renders the chosen template with the given values and creates one contract.
// Sends the signing mail if artist_email is present.
export const POST = async ({ request, url }: APIContext) => {
  let body: {
    template?: string;
    catalog?: string;
    artist_name?: string;
    artist_email?: string;
    values?: Record<string, string>;
  } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { template: templateId, catalog, artist_name, artist_email, values = {} } = body;
  if (!templateId || !catalog || !artist_name) {
    return json({ error: 'template, catalog and artist_name required' }, 422);
  }

  const template = await getContractTemplate(templateId);
  if (!template) return json({ error: 'Template not found' }, 404);

  const releaseInfo = releasesData.releases.find((r) => r.catalog === catalog);
  const allValues: Record<string, string> = {
    artist_name,
    release_title: releaseInfo?.title ?? '',
    catalog,
    release_date: releaseInfo?.release_date ?? '',
    ...values,
  };

  // A contract with an unresolved {{placeholder}} in the signed text would be a real
  // bug, not a cosmetic one — refuse before it's ever rendered.
  const missing = findPlaceholders(template.body_md).filter((key) => !allValues[key]?.trim());
  if (missing.length > 0) {
    return json({ error: `Missing values for: ${missing.join(', ')}` }, 422);
  }

  const rendered_body = renderTemplate(template.body_md, allValues);
  const signing_token = generateSigningToken();

  let contract;
  try {
    contract = await createContract({
      template: templateId,
      catalog,
      artist_name,
      artist_email,
      rendered_body,
      signing_token,
    });
  } catch (e) {
    console.error('[contracts] create:', e);
    return json({ error: 'Failed to create the contract.' }, 500);
  }

  // .env's PUBLIC_SITE_URL is the production domain and always set — plain `??`
  // fallbacks never reach url.origin. In dev, use the actual local origin instead.
  const siteUrl = import.meta.env.DEV ? url.origin : (process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? url.origin);
  const signingUrl = `${siteUrl}/contract/sign/${signing_token}`;

  let mailed = false;
  if (artist_email) {
    try {
      await sendContractSigningEmail(artist_email, artist_name, allValues.release_title || catalog, signingUrl);
      mailed = true;
    } catch (e) {
      console.error('[contracts] sendContractSigningEmail:', e);
    }
  }

  return json({ contract, mailed }, 201);
};
