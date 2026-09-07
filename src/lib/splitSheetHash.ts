import { randomBytes, createHash } from 'node:crypto';

/** Unguessable per-split signing token. Hex, like every other token in this codebase
 *  (promo tokens, unsubscribe tokens) — see api/admin/promos/index.ts, api/promo-list/subscribe.ts. */
export function generateSigningToken(): string {
  return randomBytes(24).toString('hex');
}

export interface SplitForHash {
  artist_name: string;
  percentage: number;
  role?: string;
}

/**
 * SHA-256 over the document content a signer actually saw, so it stays provable
 * even if release title or split percentages are edited afterwards.
 * Canonical, deterministic string — same inputs always produce the same hash.
 */
export function hashDocument(releaseTitle: string, catalog: string, splits: SplitForHash[]): string {
  const canonical = JSON.stringify({
    title: releaseTitle,
    catalog,
    splits: splits.map((s) => ({
      artist_name: s.artist_name,
      percentage: s.percentage,
      role: s.role ?? '',
    })),
  });
  return createHash('sha256').update(canonical).digest('hex');
}
