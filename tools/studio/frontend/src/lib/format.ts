import type { ReleaseRow, StepKey, StepState } from '@/api/types';

export const STEP_NAMES: Record<StepKey, string> = {
  A: 'Assets', V: 'Daten vollständig', K: 'Konvertiert', P: 'Gepusht (CDN)', G: 'Git committet', D: 'DSP-Links',
};
export const NEXT_LABEL: Record<StepKey, string> = {
  A: 'Dateien', V: 'Metadaten', K: 'Konvertieren', P: 'Pushen', G: 'Committen', D: 'DSP-Links',
};
export const GLYPH: Record<StepState, string> = { ok: '✓', open: '·', stale: '↻', na: '–', warn: '!' };
export const STEPS = Object.keys(STEP_NAMES) as StepKey[];

export const fmtDate = (s?: string | null) => (s ? new Date(`${s.slice(0, 10)}T00:00:00`).toLocaleDateString('de-DE') : '—');
export const fmtMB = (n: number) => `${(n / 1048576).toFixed(1)} MB`;
export const mmss = (s: number) => (isFinite(s) ? `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}` : '0:00');

export function whenOf(r: Pick<ReleaseRow, 'days_until'>): { text: string; up: boolean } {
  if (r.days_until == null) return { text: 'kein Datum', up: false };
  if (r.days_until > 0) return { text: `in ${r.days_until} ${r.days_until === 1 ? 'Tag' : 'Tagen'}`, up: true };
  if (r.days_until === 0) return { text: 'heute', up: true };
  return { text: 'veröffentlicht', up: false };
}
