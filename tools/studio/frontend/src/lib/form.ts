import type { ReleaseDetail } from '@/api/types';

/** The editable metadata of a release (the Metadaten panel). */
export interface MetaForm {
  artist: string;
  title: string;
  release_date: string;
  genre: string;
  bandcamp: string;
  about: string;
  titles: Record<number, string>; // track number → title
}

export function formFrom(d: ReleaseDetail): MetaForm {
  const r = d.release ?? {};
  const bandcamp = r.platforms?.bandcamp || d.entry?.platforms?.find((p) => p.name === 'bandcamp')?.url || '';
  return {
    artist: r.artist ?? '',
    title: r.title ?? '',
    release_date: /^\d{4}-/.test(r.release_date ?? '') ? (r.release_date as string).slice(0, 10) : '',
    genre: r.genre ?? '',
    bandcamp,
    about: d.about,
    titles: Object.fromEntries(d.tracks.map((t) => [t.number, t.title])),
  };
}

/** Body of PUT /meta for the form (without the about text). */
export const fieldsOf = (f: MetaForm) => ({
  artist: f.artist, title: f.title, release_date: f.release_date, genre: f.genre, bandcamp: f.bandcamp,
  track_titles: f.titles,
});
