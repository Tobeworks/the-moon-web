/**
 * Fills {{placeholder}} tokens in a contract template body. Unmatched placeholders
 * are left as-is (the caller — the admin create route — validates completeness
 * before ever calling this, so an unresolved token here would be a real bug).
 */
export function renderTemplate(bodyMd: string, values: Record<string, string>): string {
  return bodyMd.replace(/\{\{(\w+)\}\}/g, (match, key) => values[key] ?? match);
}

/** All distinct {{placeholder}} names used in a template body, in first-seen order. */
export function findPlaceholders(bodyMd: string): string[] {
  return [...new Set([...bodyMd.matchAll(/\{\{(\w+)\}\}/g)].map((m) => m[1]))];
}
