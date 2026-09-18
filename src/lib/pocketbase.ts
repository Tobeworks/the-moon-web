const PB_URL = process.env.POCKETBASE_URL ?? import.meta.env.POCKETBASE_URL ?? 'http://pocketbase:8090';

export interface PromoRecord {
  id: string;
  token: string;
  release_slug: string;
  recipient_name: string;
  recipient_email?: string;
  notes?: string;
  expires_at?: string;
}

/** Finds a promo record by token. Returns null if not found. */
export async function getPromoByToken(token: string): Promise<PromoRecord | null> {
  const filter = encodeURIComponent(`token='${token}'`);
  try {
    const res = await fetch(
      `${PB_URL}/api/collections/promos/records?filter=${filter}&perPage=1`,
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return (data.items?.[0] as PromoRecord) ?? null;
  } catch {
    return null;
  }
}

export interface FeedbackRecord {
  id: string;
  name: string;
  comment: string;
  url?: string;
  created: string;
}

/** Loads all feedback for a given release slug (via promo relation). */
export async function getFeedbackForRelease(releaseSlug: string): Promise<FeedbackRecord[]> {
  const filter = encodeURIComponent(`release_slug='${releaseSlug}'`);
  try {
    const authHeader = {};

    const promosRes = await fetch(
      `${PB_URL}/api/collections/promos/records?filter=${filter}&perPage=100&fields=id`,
      { headers: { 'Content-Type': 'application/json', ...authHeader } }
    );
    const promosData = await promosRes.json();
    const promoIds: string[] = (promosData.items ?? []).map((p: { id: string }) => p.id);
    if (promoIds.length === 0) return [];

    const feedbackRes = await fetch(
      `${PB_URL}/api/collections/feedback/records?perPage=100`,
      { headers: { 'Content-Type': 'application/json', ...authHeader } }
    );
    const feedbackData = await feedbackRes.json();
    const promoIdSet = new Set(promoIds);
    return (feedbackData.items ?? [])
      .filter((item: any) => promoIdSet.has(item.promo))
      .map((item: any) => ({ id: item.id, name: item.name, comment: item.comment, url: item.url ?? '', created: item.created ?? '' }));
  } catch {
    return [];
  }
}

/** Creates a feedback record. */
export async function createFeedback(payload: {
  promo: string;
  name: string;
  email: string;
  comment: string;
  url?: string;
  user_agent: string;
  ip: string;
}): Promise<{ id: string }> {
  const res = await fetch(`${PB_URL}/api/collections/feedback/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase feedback create failed: ${res.status} ${err}`);
  }
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Newsletter
// ─────────────────────────────────────────────────────────────────────────────

export interface NewsletterSubscriber {
  id: string;
  email: string;
  name?: string;
  confirmed: boolean;
  confirmation_token: string;
  confirmation_token_expires_at: string;
  unsubscribe_token: string;
  confirmed_at?: string;
}

/** Finds a subscriber by email. Returns null if not found. */
export async function getSubscriberByEmail(email: string): Promise<NewsletterSubscriber | null> {
  const filter = encodeURIComponent(`email='${email}'`);
  try {
    const res = await fetch(
      `${PB_URL}/api/collections/newsletter_subscribers/records?filter=${filter}&perPage=1`,
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (!res.ok) return null;
    const data = await res.json();
    return (data.items?.[0] as NewsletterSubscriber) ?? null;
  } catch {
    return null;
  }
}

/** Creates a new unconfirmed subscriber with fresh tokens. */
export async function createSubscriber(email: string, name: string): Promise<NewsletterSubscriber> {
  const { randomBytes } = await import('crypto');
  const confirmationToken = randomBytes(32).toString('hex');
  const unsubscribeToken = randomBytes(32).toString('hex');
  const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().replace('T', ' ');

  const res = await fetch(`${PB_URL}/api/collections/newsletter_subscribers/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      name,
      confirmed: false,
      confirmation_token: confirmationToken,
      confirmation_token_expires_at: expires,
      unsubscribe_token: unsubscribeToken,
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase newsletter create failed: ${res.status} ${err}`);
  }
  return res.json();
}

/** Refreshes the confirmation token for an existing unconfirmed subscriber. */
export async function refreshConfirmationToken(id: string): Promise<NewsletterSubscriber> {
  const { randomBytes } = await import('crypto');
  const confirmationToken = randomBytes(32).toString('hex');
  const expires = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().replace('T', ' ');

  const res = await fetch(`${PB_URL}/api/collections/newsletter_subscribers/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      confirmation_token: confirmationToken,
      confirmation_token_expires_at: expires,
    }),
  });
  if (!res.ok) throw new Error('Failed to refresh confirmation token');
  return res.json();
}

/** Confirms a subscriber by their confirmation token. Returns null if token invalid or expired. */
export async function confirmSubscriber(token: string): Promise<NewsletterSubscriber | null> {
  const filter = encodeURIComponent(`confirmation_token='${token}'`);
  try {
    const listRes = await fetch(
      `${PB_URL}/api/collections/newsletter_subscribers/records?filter=${filter}&perPage=1`,
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (!listRes.ok) return null;
    const data = await listRes.json();
    const subscriber = data.items?.[0] as NewsletterSubscriber | undefined;
    if (!subscriber) return null;
    if (new Date(subscriber.confirmation_token_expires_at) < new Date()) return null;

    const updateRes = await fetch(
      `${PB_URL}/api/collections/newsletter_subscribers/records/${subscriber.id}`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confirmed: true,
          confirmed_at: new Date().toISOString().replace('T', ' '),
          confirmation_token: '',
        }),
      }
    );
    if (!updateRes.ok) return null;
    return { ...(await updateRes.json()), unsubscribe_token: subscriber.unsubscribe_token };
  } catch {
    return null;
  }
}

/** Deletes a subscriber by their unsubscribe token. Returns true on success. */
export async function unsubscribeByToken(token: string): Promise<boolean> {
  const filter = encodeURIComponent(`unsubscribe_token='${token}'`);
  try {
    const listRes = await fetch(
      `${PB_URL}/api/collections/newsletter_subscribers/records?filter=${filter}&perPage=1`,
      { headers: { 'Content-Type': 'application/json' } }
    );
    if (!listRes.ok) return false;
    const data = await listRes.json();
    const subscriber = data.items?.[0] as NewsletterSubscriber | undefined;
    if (!subscriber) return false;

    const deleteRes = await fetch(
      `${PB_URL}/api/collections/newsletter_subscribers/records/${subscriber.id}`,
      { method: 'DELETE' }
    );
    return deleteRes.ok;
  } catch {
    return false;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Campaigns
// ─────────────────────────────────────────────────────────────────────────────

export interface Campaign {
  id: string;
  subject: string;
  body_html: string;
  body_md?: string;
  body_text?: string;
  status: 'draft' | 'sending' | 'sent';
  sent_at?: string;
  sent_count?: number;
  failed_count?: number;
  created: string;
  updated: string;
}

export async function getCampaigns(): Promise<Campaign[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/campaigns/records?perPage=100`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.items ?? []) as Campaign[];
  } catch { return []; }
}

export async function getCampaign(id: string): Promise<Campaign | null> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/campaigns/records/${id}`);
    if (!res.ok) return null;
    return await res.json() as Campaign;
  } catch { return null; }
}

export async function createCampaign(subject: string, bodyHtml: string, bodyText: string, bodyMd?: string): Promise<Campaign> {
  const res = await fetch(`${PB_URL}/api/collections/campaigns/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ subject, body_html: bodyHtml || ' ', body_md: bodyMd ?? bodyText, body_text: bodyText, status: 'draft', sent_count: 0, failed_count: 0 }),
  });
  if (!res.ok) throw new Error(`Failed to create campaign: ${res.status}`);
  return res.json();
}

export async function updateCampaign(id: string, fields: Partial<Campaign>): Promise<Campaign> {
  const res = await fetch(`${PB_URL}/api/collections/campaigns/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
  if (!res.ok) throw new Error(`Failed to update campaign: ${res.status}`);
  return res.json();
}

export async function deleteCampaign(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/campaigns/records/${id}`, { method: 'DELETE' });
}

export async function getConfirmedSubscribers(): Promise<NewsletterSubscriber[]> {
  try {
    const filter = encodeURIComponent(`confirmed=true`);
    const res = await fetch(`${PB_URL}/api/collections/newsletter_subscribers/records?filter=${filter}&perPage=1000`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.items ?? []) as NewsletterSubscriber[];
  } catch { return []; }
}

export async function deleteNewsletterSubscriber(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/newsletter_subscribers/records/${id}`, { method: 'DELETE' });
}

// ── Promo Subscribers ─────────────────────────────────────────────────────

export interface PromoSubscriber {
  id: string;
  email: string;
  name?: string;
  unsubscribe_token: string;
  created: string;
}

export async function getPromoSubscribers(): Promise<PromoSubscriber[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/promo_subscribers/records?perPage=1000&fields=id,email,name,unsubscribe_token,created`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.items ?? []) as PromoSubscriber[];
  } catch { return []; }
}

export async function getPromoSubscriberByEmail(email: string): Promise<PromoSubscriber | null> {
  try {
    const filter = encodeURIComponent(`email="${email}"`);
    const res = await fetch(`${PB_URL}/api/collections/promo_subscribers/records?filter=${filter}&perPage=1`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.items?.[0] ?? null;
  } catch { return null; }
}

export async function getPromoSubscriberByToken(token: string): Promise<PromoSubscriber | null> {
  try {
    const filter = encodeURIComponent(`unsubscribe_token="${token}"`);
    const res = await fetch(`${PB_URL}/api/collections/promo_subscribers/records?filter=${filter}&perPage=1`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.items?.[0] ?? null;
  } catch { return null; }
}

export async function createPromoSubscriber(email: string, name: string, token: string): Promise<PromoSubscriber> {
  const res = await fetch(`${PB_URL}/api/collections/promo_subscribers/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, name, unsubscribe_token: token }),
  });
  if (!res.ok) throw new Error(`Failed to create promo subscriber: ${res.status}`);
  return res.json();
}

export async function deletePromoSubscriber(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/promo_subscribers/records/${id}`, { method: 'DELETE' });
}

/** Creates a promo record for a specific recipient. Returns the new record. */
export async function createPromoRecord(payload: {
  token: string;
  release_slug: string;
  recipient_name: string;
  recipient_email: string;
  expires_at?: string;
}): Promise<PromoRecord> {
  const res = await fetch(`${PB_URL}/api/collections/promos/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase promo create failed: ${res.status} ${err}`);
  }
  return res.json();
}

// ── Download Events ────────────────────────────────────────────────────────

/** Returns all promo records, optionally filtered by release_slug */
export async function getPromoRecords(release_slug?: string): Promise<PromoRecord[]> {
  const filter = release_slug
    ? `?filter=${encodeURIComponent(`release_slug='${release_slug.toLowerCase()}'`)}&perPage=500`
    : '?perPage=500'
  const res = await fetch(`${PB_URL}/api/collections/promos/records${filter}`)
  if (!res.ok) return []
  const data = await res.json()
  return data.items ?? []
}

// ── Split Sheets ─────────────────────────────────────────────────────────────

export interface SplitSheetRelease {
  id: string;
  catalog: string;
  label_project: string;
  distribution_platform?: string;
  public_slug: string;
  status?: string; // "draft" | "fully_signed"
}

export interface Split {
  id: string;
  release: string; // relation id
  artist_name: string;
  artist_email?: string;
  percentage: number;
  role?: string;
  signing_token: string;
  signed_name?: string;
  signed_at?: string;
  ip_address?: string;
  document_hash?: string;
  token_expires_at?: string;
}

/** Split fields safe to expose on the public read-only page — never the token or id. */
export interface PublicSplit {
  artist_name: string;
  percentage: number;
  role?: string;
  signed_at?: string;
}

export async function getSplitSheetReleases(): Promise<SplitSheetRelease[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/split_sheet_releases/records?perPage=500`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.items ?? [];
  } catch { return []; }
}

export async function getSplit(id: string): Promise<Split | null> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/splits/records/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function getSplitSheetRelease(id: string): Promise<SplitSheetRelease | null> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/split_sheet_releases/records/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function getSplitsForRelease(releaseId: string): Promise<Split[]> {
  try {
    const filter = encodeURIComponent(`release='${releaseId}'`);
    const res = await fetch(`${PB_URL}/api/collections/splits/records?filter=${filter}&perPage=500`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.items ?? [];
  } catch { return []; }
}

export async function createSplitSheetRelease(payload: {
  catalog: string;
  label_project: string;
  distribution_platform?: string;
  public_slug: string;
}): Promise<SplitSheetRelease> {
  const res = await fetch(`${PB_URL}/api/collections/split_sheet_releases/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, status: 'draft' }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase split_sheet_releases create failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function createSplit(payload: {
  release: string;
  artist_name: string;
  artist_email?: string;
  percentage: number;
  role?: string;
  signing_token: string;
}): Promise<Split> {
  const res = await fetch(`${PB_URL}/api/collections/splits/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase splits create failed: ${res.status} ${err}`);
  }
  return res.json();
}

/** Public, read-only lookup by slug. Splits are stripped down to safe fields — never signing_token or id. */
export async function getSplitSheetBySlug(slug: string): Promise<{ release: SplitSheetRelease; splits: PublicSplit[] } | null> {
  try {
    const filter = encodeURIComponent(`public_slug='${slug}'`);
    const res = await fetch(`${PB_URL}/api/collections/split_sheet_releases/records?filter=${filter}&perPage=1`);
    if (!res.ok) return null;
    const data = await res.json();
    const release = data.items?.[0] as SplitSheetRelease | undefined;
    if (!release) return null;

    const splits = await getSplitsForRelease(release.id);
    return {
      release,
      splits: splits.map((s) => ({
        artist_name: s.artist_name,
        percentage: s.percentage,
        role: s.role,
        signed_at: s.signed_at,
      })),
    };
  } catch { return null; }
}

/** Sign-page lookup. Possessing the exact token is the authorization for this one record. */
export async function getSplitByToken(token: string): Promise<{ split: Split; release: SplitSheetRelease } | null> {
  try {
    const filter = encodeURIComponent(`signing_token='${token}'`);
    const res = await fetch(`${PB_URL}/api/collections/splits/records?filter=${filter}&perPage=1`);
    if (!res.ok) return null;
    const data = await res.json();
    const split = data.items?.[0] as Split | undefined;
    if (!split) return null;

    const relRes = await fetch(`${PB_URL}/api/collections/split_sheet_releases/records/${split.release}`);
    if (!relRes.ok) return null;
    const release = await relRes.json();
    return { split, release };
  } catch { return null; }
}

/** Writes the signature onto a split. Caller must already have verified it isn't signed yet. */
export async function signSplit(splitId: string, payload: {
  signed_name: string;
  ip_address: string;
  document_hash: string;
}): Promise<Split> {
  const res = await fetch(`${PB_URL}/api/collections/splits/records/${splitId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, signed_at: new Date().toISOString() }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase split sign failed: ${res.status} ${err}`);
  }
  return res.json();
}

/** After a signature, checks whether every split of the release is now signed and flips its status. */
export async function checkAndMarkFullySigned(releaseId: string): Promise<void> {
  const splits = await getSplitsForRelease(releaseId);
  if (splits.length === 0 || !splits.every((s) => s.signed_at)) return;
  await fetch(`${PB_URL}/api/collections/split_sheet_releases/records/${releaseId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'fully_signed' }),
  });
}

/** Deletes an unsigned split. Caller must check signed_at first — this never touches a signed record. */
export async function deleteSplit(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/splits/records/${id}`, { method: 'DELETE' });
}

/** Deletes a release and cascades its splits (cascadeDelete: true on the relation). */
export async function deleteSplitSheetRelease(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/split_sheet_releases/records/${id}`, { method: 'DELETE' });
}

// ── Contracts ────────────────────────────────────────────────────────────────

export interface ContractTemplate {
  id: string;
  name: string;
  body_md: string;
  is_active?: boolean;
}

export interface Contract {
  id: string;
  template: string; // relation id
  catalog: string;
  artist_name: string;
  artist_email?: string;
  rendered_body: string;
  signing_token: string;
  signed_name?: string;
  signed_at?: string;
  ip_address?: string;
  document_hash?: string;
  token_expires_at?: string;
}

export async function getContractTemplates(): Promise<ContractTemplate[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/contract_templates/records?perPage=500`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.items ?? [];
  } catch { return []; }
}

export async function getContractTemplate(id: string): Promise<ContractTemplate | null> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/contract_templates/records/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function createContractTemplate(payload: { name: string; body_md: string; is_active?: boolean }): Promise<ContractTemplate> {
  const res = await fetch(`${PB_URL}/api/collections/contract_templates/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase contract_templates create failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function updateContractTemplate(id: string, payload: { name: string; body_md: string; is_active?: boolean }): Promise<ContractTemplate> {
  const res = await fetch(`${PB_URL}/api/collections/contract_templates/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase contract_templates update failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function deleteContractTemplate(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/contract_templates/records/${id}`, { method: 'DELETE' });
}

export async function getContractsByTemplate(templateId: string): Promise<Contract[]> {
  try {
    const filter = encodeURIComponent(`template='${templateId}'`);
    const res = await fetch(`${PB_URL}/api/collections/contracts/records?filter=${filter}&perPage=1`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.items ?? [];
  } catch { return []; }
}

export async function getContracts(): Promise<Contract[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/contracts/records?perPage=500`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.items ?? [];
  } catch { return []; }
}

export async function getContract(id: string): Promise<Contract | null> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/contracts/records/${id}`);
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export async function createContract(payload: {
  template: string;
  catalog: string;
  artist_name: string;
  artist_email?: string;
  rendered_body: string;
  signing_token: string;
}): Promise<Contract> {
  const res = await fetch(`${PB_URL}/api/collections/contracts/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase contracts create failed: ${res.status} ${err}`);
  }
  return res.json();
}

/** Sign-page lookup. Possessing the exact token is the authorization for this one record. */
export async function getContractByToken(token: string): Promise<Contract | null> {
  try {
    const filter = encodeURIComponent(`signing_token='${token}'`);
    const res = await fetch(`${PB_URL}/api/collections/contracts/records?filter=${filter}&perPage=1`);
    if (!res.ok) return null;
    const data = await res.json();
    return data.items?.[0] ?? null;
  } catch { return null; }
}

/** Writes the signature onto a contract. Caller must already have verified it isn't signed yet. */
export async function signContract(id: string, payload: {
  signed_name: string;
  ip_address: string;
  document_hash: string;
}): Promise<Contract> {
  const res = await fetch(`${PB_URL}/api/collections/contracts/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...payload, signed_at: new Date().toISOString() }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase contract sign failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function deleteContract(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/contracts/records/${id}`, { method: 'DELETE' });
}

/** Deletes a promo record by id */
export async function deletePromoRecord(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/promos/records/${id}`, { method: 'DELETE' })
}

/** Logs a download event. Fire-and-forget — swallows errors. */
export async function logDownload(payload: {
  promo: string;
  quality: '128' | '320';
  user_agent: string;
  ip: string;
}): Promise<void> {
  await fetch(`${PB_URL}/api/collections/download_events/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  }).catch(() => {});
}

// ── Linktree ─────────────────────────────────────────────────────────────────

export interface LinktreeItem {
  id: string;
  type: 'release' | 'link';
  position: number;
  release_catalog?: string;
  label?: string;
  url?: string;
  created?: string;
}

/** All linktree items, sorted by position ascending — the display order. */
export async function getLinktreeItems(): Promise<LinktreeItem[]> {
  try {
    const res = await fetch(`${PB_URL}/api/collections/linktree_items/records?sort=position&perPage=200`);
    if (!res.ok) return [];
    const data = await res.json();
    return (data.items ?? []) as LinktreeItem[];
  } catch { return []; }
}

export async function createLinktreeItem(payload: {
  type: 'release' | 'link';
  position: number;
  release_catalog?: string;
  label?: string;
  url?: string;
}): Promise<LinktreeItem> {
  const res = await fetch(`${PB_URL}/api/collections/linktree_items/records`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase linktree_items create failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function updateLinktreeItem(id: string, fields: Partial<{
  type: 'release' | 'link';
  position: number;
  release_catalog: string;
  label: string;
  url: string;
}>): Promise<LinktreeItem> {
  const res = await fetch(`${PB_URL}/api/collections/linktree_items/records/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(fields),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`PocketBase linktree_items update failed: ${res.status} ${err}`);
  }
  return res.json();
}

export async function deleteLinktreeItem(id: string): Promise<void> {
  await fetch(`${PB_URL}/api/collections/linktree_items/records/${id}`, { method: 'DELETE' });
}
