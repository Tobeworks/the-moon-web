export const prerender = false;

import type { APIContext } from 'astro';
import {
  getSplitSheetReleases,
  getSplitsForRelease,
  createSplitSheetRelease,
  createSplit,
} from '../../../../lib/pocketbase';
import { sendSplitSigningEmail } from '../../../../lib/mailer';
import { generateSigningToken } from '../../../../lib/splitSheetHash';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

interface SplitInput {
  artist_name: string;
  artist_email?: string;
  percentage: number;
  role?: string;
}

// GET / — every release with its splits, for the admin list
export const GET = async () => {
  const releases = await getSplitSheetReleases();
  const withSplits = await Promise.all(
    releases.map(async (release) => ({ release, splits: await getSplitsForRelease(release.id) })),
  );
  return json(withSplits);
};

// POST / — new release + its splits. Sends a signing mail per split that has an email.
export const POST = async ({ request, url }: APIContext) => {
  let body: { catalog?: string; label_project?: string; distribution_platform?: string; splits?: SplitInput[] } = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const { catalog, label_project, distribution_platform, splits } = body;
  if (!catalog || !label_project) return json({ error: 'catalog and label_project required' }, 422);
  if (!splits || splits.length === 0) return json({ error: 'at least one split required' }, 422);
  for (const s of splits) {
    if (!s.artist_name || typeof s.percentage !== 'number') {
      return json({ error: 'each split needs artist_name and a numeric percentage' }, 422);
    }
  }
  // Splits must fully account for the work — a client-side check alone can be bypassed.
  const total = Math.round(splits.reduce((sum, s) => sum + s.percentage, 0) * 10) / 10;
  if (total !== 100) {
    return json({ error: `Splits must add up to 100% — currently ${total}%.` }, 422);
  }

  // .env's PUBLIC_SITE_URL is the production domain and always set — plain `??`
  // fallbacks never reach url.origin. In dev, use the actual local origin instead.
  const siteUrl = import.meta.env.DEV ? url.origin : (process.env.PUBLIC_SITE_URL ?? import.meta.env.PUBLIC_SITE_URL ?? url.origin);

  let release;
  try {
    release = await createSplitSheetRelease({
      catalog,
      label_project,
      distribution_platform,
      public_slug: catalog.toLowerCase(),
    });
  } catch (e: any) {
    // Most likely cause: a split sheet for this catalog already exists (unique public_slug).
    const msg = /already exists|validation_not_unique|400/i.test(e?.message ?? '')
      ? `A split sheet for ${catalog} already exists.`
      : 'Failed to create the release record.';
    console.error('[split-sheets] createSplitSheetRelease:', e);
    return json({ error: msg }, 409);
  }

  const mailed: string[] = [];
  const skipped: string[] = [];

  try {
    for (const s of splits) {
      const signing_token = generateSigningToken();
      await createSplit({
        release: release.id,
        artist_name: s.artist_name,
        artist_email: s.artist_email,
        percentage: s.percentage,
        role: s.role,
        signing_token,
      });

      if (s.artist_email) {
        const signingUrl = `${siteUrl}/split-sheet/sign/${signing_token}`;
        try {
          await sendSplitSigningEmail(s.artist_email, s.artist_name, catalog, s.percentage, signingUrl);
          mailed.push(s.artist_name);
        } catch (e) {
          console.error('[split-sheets] sendSplitSigningEmail:', e);
          skipped.push(s.artist_name);
        }
      } else {
        skipped.push(s.artist_name); // no email on file — admin sends the link manually
      }
    }
  } catch (e) {
    console.error('[split-sheets] createSplit:', e);
    return json({ error: 'Release was created, but one or more splits failed to save. Check the list below.' }, 500);
  }

  return json({ release, mailed, skipped }, 201);
};
