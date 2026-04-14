export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoByToken, logDownload } from '../../../lib/pocketbase';
import releasesData from '../../../../../the-moon-os/data/releases.json';
import { Zip, ZipPassThrough } from 'fflate';

export const GET = async ({ request, url }: APIContext) => {
  const token      = url.searchParams.get('t');
  const quality    = url.searchParams.get('q');
  const trackParam = url.searchParams.get('track'); // null = all tracks ZIP, number = single

  if (!token || (quality !== '128' && quality !== '320')) {
    return new Response('Bad request', { status: 400 });
  }

  const promo = await getPromoByToken(token);
  if (!promo) return new Response('Forbidden', { status: 403 });
  if (promo.expires_at && new Date(promo.expires_at) < new Date()) {
    return new Response('Gone — promo link expired', { status: 410 });
  }

  const release = releasesData.releases.find(
    (r) => r.catalog.toLowerCase() === promo.release_slug
  );
  if (!release) return new Response('Release not found', { status: 404 });

  const ip         = request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? request.headers.get('x-real-ip') ?? 'unknown';
  const user_agent = request.headers.get('user-agent') ?? 'unknown';

  // ── Single track — proxy with Content-Disposition ─────────────────────────
  if (trackParam !== null) {
    const trackNum = Number(trackParam);
    const track    = release.tracks.find((t) => t.number === trackNum);
    if (!track) return new Response('Track not found', { status: 404 });

    const cdnUrl = quality === '320' ? track.url_320 : track.url;
    if (!cdnUrl) return new Response('Audio file not available', { status: 404 });

    const trackLabel = track.title.replace(/^.*?\s{2,}/, '').trim() || track.title;
    const filename   = `${String(track.number).padStart(2, '0')}_${trackLabel.replace(/[^a-zA-Z0-9_\-]/g, '_').toLowerCase()}_${quality}k.mp3`;

    const cdnRes = await fetch(cdnUrl);
    if (!cdnRes.ok) return new Response('Audio file not available', { status: 502 });

    logDownload({ promo: promo.id, quality, ip, user_agent });

    return new Response(cdnRes.body, {
      status: 200,
      headers: {
        'content-type':        'audio/mpeg',
        'content-disposition': `attachment; filename="${filename}"`,
        'content-length':      cdnRes.headers.get('content-length') ?? '',
        'cache-control':       'private, no-store',
      },
    });
  }

  // ── ZIP: all tracks — streaming, one track at a time ─────────────────────
  const zipLabel    = quality === '320' ? '320k' : '128k';
  const artistSlug  = release.artist.toLowerCase().replace(/\s+/g, '_');
  const zipFilename = `${release.catalog.toLowerCase()}_${artistSlug}_${zipLabel}.zip`;

  logDownload({ promo: promo.id, quality, ip, user_agent });

  const tracks = release.tracks;

  const stream = new ReadableStream({
    async start(controller) {
      const zip = new Zip((err, chunk, final) => {
        if (err) { controller.error(err); return; }
        controller.enqueue(chunk);
        if (final) controller.close();
      });

      for (const track of tracks) {
        const cdnUrl = quality === '320' ? track.url_320 : track.url;
        if (!cdnUrl) continue;

        let cdnRes: Response;
        try {
          cdnRes = await fetch(cdnUrl);
          if (!cdnRes.ok || !cdnRes.body) continue;
        } catch {
          continue;
        }

        const trackLabel = track.title.replace(/^.*?\s{2,}/, '').trim() || track.title;
        const filename   = `${String(track.number).padStart(2, '0')}_${trackLabel.replace(/[^a-zA-Z0-9_\-]/g, '_').toLowerCase()}.mp3`;

        const file = new ZipPassThrough(filename);
        zip.add(file);

        const reader = cdnRes.body.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) { file.push(new Uint8Array(0), true); break; }
          file.push(value!);
        }
      }

      zip.end();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: {
      'content-type':        'application/zip',
      'content-disposition': `attachment; filename="${zipFilename}"`,
      'cache-control':       'private, no-store',
      'x-content-type-options': 'nosniff',
    },
  });
};
