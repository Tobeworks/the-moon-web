/**
 * Builds a newsletter draft (subject + markdown body) from a release's data
 * in releases.json. Pure string interpolation — no AI involved, because the
 * skeleton barely changes between releases (see workflows/release-workflow.md
 * and the actual TMR-014 "Spelrum" mail this mirrors).
 *
 * Output is a starting draft, not a finished mail — the about-text is used
 * verbatim; the editor still expects a human pass before sending.
 */

export interface ReleaseForNewsletter {
  catalog: string;
  artist: string;
  title: string;
  genre?: string;
  year?: string;
  about?: string;
  cover?: string;
  artwork?: Record<string, { jpg: string; webp: string }>;
  platforms?: { name: string; url: string }[];
  tracks?: { number: number; title: string }[];
}

const SITE_URL = 'https://the-moon-records.de';

/** Strips a leading "# Title" line from about.md-style text — the newsletter
 *  already carries its own H1, a second one would be redundant. */
function stripLeadingHeading(about: string): string {
  return about.replace(/^\s*#[^\n]*\n+/, '').trim();
}

export function buildReleaseNewsletter(release: ReleaseForNewsletter): { subject: string; bodyMd: string } {
  const { catalog, artist, title, genre, year, about, tracks = [] } = release;

  const cover = release.artwork?.['600']?.jpg || release.cover || '';
  const bandcamp = release.platforms?.find((p) => p.name === 'bandcamp')?.url;

  const metaParts = [catalog, genre, year].filter((p) => p && p.trim());
  const metaLine = metaParts.length ? `**${metaParts.join(' · ')}**\n\n` : '';

  const aboutText = about ? stripLeadingHeading(about) : '';

  const tracklist = tracks.length
    ? `**Tracklist**\n\n${tracks.map((t, i) => `${i + 1}. ${t.title}`).join('\n')}\n\n---\n\n`
    : '';

  const links = [
    bandcamp ? `[→ Listen & buy on Bandcamp](${bandcamp})` : null,
    `[→ ${SITE_URL.replace('https://', '')}](${SITE_URL})`,
  ]
    .filter(Boolean)
    .join('\n');

  const bodyMd = [
    cover ? `[![${artist} — ${title}](${cover})](${SITE_URL})\n\n` : '',
    `# New Release: ${title} - ${artist}\n\n`,
    metaLine,
    aboutText ? `${aboutText}\n\n` : '',
    '---\n\n',
    tracklist,
    `${links}\n\n`,
    '---\n\n',
    'Yours,\n*The Moon Records*',
  ].join('');

  const subject = `New Release: ${title} — ${artist}`;

  return { subject, bodyMd };
}
