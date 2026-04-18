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
