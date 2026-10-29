/**
 * Shared release helpers: ordering, platform logos, cover fetching.
 * Used by the release page, the OG-image / story-cover endpoints and DspLinks.
 */
import sharp from 'sharp';
import releasesData from '../../the-moon-os/data/releases.json';

export type Platform = { name: string; url: string };
export type Release = (typeof releasesData.releases)[number];

export const SITE_DOMAIN = 'the-moon-records.de';

/** Mirrors the @theme tokens in global.css — for server-side images that can't read CSS. */
export const COLORS = { bg: '#0C0C0C', surface: '#1C1C1C', accent: '#C4B98A', fg: '#E8E4D8' };

// Eagerly inlined so the SVGs ship as markup and inherit currentColor.
const logos = import.meta.glob<string>('../assets/dsp/*.svg', {
  query: '?raw',
  import: 'default',
  eager: true,
});

export const dspLogo = (name: string): string | null =>
  logos[`../assets/dsp/${name}.svg`] ?? null;

// Bandcamp first (label's own store), then streaming services in a fixed order
// so the row doesn't reshuffle between releases.
const ORDER = ['bandcamp', 'spotify', 'apple_music', 'amazon_music', 'soundcloud', 'deezer', 'beatport'];
const rank = (n: string) => {
  const i = ORDER.indexOf(n);
  return i === -1 ? ORDER.length : i;
};

export const sortPlatforms = (platforms: Platform[] = []) =>
  platforms.filter((p) => p?.url).sort((a, b) => rank(a.name) - rank(b.name));

export const slugOf = (r: Release) => r.catalog.toLowerCase();
export const findRelease = (slug?: string) =>
  releasesData.releases.find((r) => slugOf(r) === slug?.toLowerCase());

export const isReleased = (r: Release) => (r.release_date ? new Date(r.release_date) <= new Date() : true);

/** Platform links are hidden until the release date (see AGENTS.md). */
export const visiblePlatforms = (r: Release) =>
  isReleased(r) ? sortPlatforms(r.platforms as Platform[]) : [];

export const yearOf = (r: Release) => r.year || r.release_date?.slice(0, 4) || '';

/** "A & B, C" → ["A", "B", "C"] */
export const splitArtists = (artist: string) =>
  artist.split(/\s*[&,]\s*/).map((a) => a.trim()).filter(Boolean);

/** Previous = older, next = newer. Catalog order is the release order (release_date has swapped entries). */
export const adjacent = (r: Release) => {
  const ordered = [...releasesData.releases].sort((a, b) =>
    a.catalog.localeCompare(b.catalog, undefined, { numeric: true }),
  );
  const i = ordered.findIndex((x) => x.catalog === r.catalog);
  return { prev: ordered[i - 1], next: ordered[i + 1] };
};

/** Standalone SVG strings for the visible platforms, usable as <img>/canvas source (needs xmlns). */
export const platformIconSvgs = (r: Release) =>
  visiblePlatforms(r)
    .map((p) => dspLogo(p.name))
    .filter((svg): svg is string => !!svg)
    .map((svg) => (svg.includes('xmlns=') ? svg : svg.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')));

export const coverSource = (r: Release) => r.artwork?.['1500']?.jpg || r.cover;

/** Fetches the cover from the CDN and crops it to a square. Null when there is none. */
export async function squareCover(r: Release, size: number): Promise<Buffer | null> {
  const src = coverSource(r);
  if (!src) return null;
  const res = await fetch(src);
  if (!res.ok) return null;
  return sharp(Buffer.from(await res.arrayBuffer()))
    .resize(size, size, { fit: 'cover' })
    .jpeg({ quality: 90 })
    .toBuffer();
}
