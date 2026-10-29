export const prerender = false;

import type { APIRoute } from 'astro';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import satori from 'satori';
import sharp from 'sharp';
import { COLORS, SITE_DOMAIN, findRelease, platformIconSvgs, squareCover, yearOf } from '../../lib/release';

// 1200x630 link preview (Facebook, X, ...). Square covers get cropped to 1.91:1 by
// the networks, so every release gets a purpose-built image instead.
// Rendered on request (the release page is SSR too) and cached by the browser/CDN;
// the fonts come from node_modules, which the runtime image copies as a whole.
const W = 1200;
const H = 630;
const ICON = 40;

const font = (pkg: string, file: string) =>
  readFile(path.join(process.cwd(), 'node_modules/@fontsource', pkg, 'files', file));

// satori wants ttf/otf/woff, not woff2 — the fontsource .woff files fit.
const fonts = Promise.all([
  font('josefin-sans', 'josefin-sans-latin-400-normal.woff'),
  font('josefin-sans', 'josefin-sans-latin-700-normal.woff'),
  font('space-mono', 'space-mono-latin-400-normal.woff'),
]);

const dataUri = (mime: string, data: Buffer | string) =>
  `data:${mime};base64,${Buffer.from(data).toString('base64')}`;

const el = (type: string, style: Record<string, unknown>, children?: unknown) => ({
  type,
  props: { style, children },
});

export const GET: APIRoute = async ({ params }) => {
  const release = findRelease(params.slug);
  if (!release) return new Response('Not found', { status: 404 });

  const artist = release.artist.toUpperCase();
  const title = release.title.toUpperCase();
  const titleSize = title.length <= 14 ? 64 : title.length <= 28 ? 52 : 42;

  const cover = await squareCover(release, H);
  const icons = platformIconSvgs(release).map((svg) =>
    dataUri(
      'image/svg+xml',
      svg.replaceAll('currentColor', COLORS.accent).replace('<svg', `<svg width="${ICON}" height="${ICON}"`),
    ),
  );

  const [josefin400, josefin700, mono400] = await fonts;
  const meta = [yearOf(release), SITE_DOMAIN.toUpperCase()].filter(Boolean).join('  ·  ');

  const tree = el('div', { display: 'flex', width: W, height: H, background: COLORS.bg, fontFamily: 'Josefin Sans' }, [
    cover
      ? { type: 'img', props: { src: dataUri('image/jpeg', cover), width: H, height: H } }
      : el('div', { display: 'flex', width: H, height: H, background: COLORS.surface }, ''),
    el(
      'div',
      { display: 'flex', flexDirection: 'column', justifyContent: 'center', flex: 1, padding: '0 56px', gap: 28 },
      [
        el('div', { fontSize: 20, letterSpacing: 5, color: COLORS.accent }, artist),
        el('div', { fontSize: titleSize, fontWeight: 700, lineHeight: 1.1, letterSpacing: 1, color: COLORS.fg }, title),
        icons.length
          ? el('div', { display: 'flex', gap: 28 }, icons.map((src) => ({ type: 'img', props: { src, width: ICON, height: ICON } })))
          : el('div', { display: 'flex' }, ''),
        el('div', { fontFamily: 'Space Mono', fontSize: 18, letterSpacing: 4, color: COLORS.accent }, meta),
      ],
    ),
  ]);

  const svg = await satori(tree as Parameters<typeof satori>[0], {
    width: W,
    height: H,
    fonts: [
      { name: 'Josefin Sans', data: josefin400, weight: 400, style: 'normal' },
      { name: 'Josefin Sans', data: josefin700, weight: 700, style: 'normal' },
      { name: 'Space Mono', data: mono400, weight: 400, style: 'normal' },
    ],
  });

  const jpeg = await sharp(Buffer.from(svg)).jpeg({ quality: 88 }).toBuffer();
  return new Response(jpeg, {
    headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=86400' },
  });
};
