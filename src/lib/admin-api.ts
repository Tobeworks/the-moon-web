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
}

export interface Subscriber {
  id: string;
  email: string;
  name?: string;
  confirmed: boolean;
}

export interface SendResult {
  ok: boolean;
  sent: number;
  failed: number;
  error?: string;
}

const base = '/api/admin/newsletter';

export const adminApi = {
  async getCampaigns(): Promise<Campaign[]> {
    const res = await fetch(`${base}/campaigns`);
    if (!res.ok) throw new Error('Failed to load campaigns');
    return res.json();
  },

  async getCampaign(id: string): Promise<Campaign> {
    const res = await fetch(`${base}/campaigns/${id}`);
    if (!res.ok) throw new Error('Failed to load campaign');
    return res.json();
  },

  async createCampaign(subject: string, bodyHtml: string, bodyMd: string): Promise<Campaign> {
    const res = await fetch(`${base}/campaigns`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ subject, body_html: bodyHtml, body_md: bodyMd, body_text: bodyMd }),
    });
    if (!res.ok) throw new Error('Failed to create campaign');
    return res.json();
  },

  async updateCampaign(id: string, fields: Partial<Campaign>): Promise<Campaign> {
    const res = await fetch(`${base}/campaigns/${id}`, {
      method: 'PATCH',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(fields),
    });
    if (!res.ok) throw new Error('Failed to update campaign');
    return res.json();
  },

  async deleteCampaign(id: string): Promise<void> {
    const res = await fetch(`${base}/campaigns/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete campaign');
  },

  async sendCampaign(id: string): Promise<SendResult> {
    const res = await fetch(`${base}/send`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    return res.json();
  },

  async testCampaign(id: string, email: string): Promise<SendResult> {
    const res = await fetch(`${base}/test`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ id, email }),
    });
    return res.json();
  },
};

export interface PromoSubscriber {
  id: string;
  email: string;
  name?: string;
  unsubscribe_token: string;
  created: string;
}

export const promoApi = {
  async getSubscribers(): Promise<PromoSubscriber[]> {
    const res = await fetch('/api/admin/promo-list/subscribers');
    if (!res.ok) throw new Error('Failed to load promo subscribers');
    return res.json();
  },

  async addSubscriber(email: string, name: string): Promise<PromoSubscriber> {
    const res = await fetch('/api/admin/promo-list/subscribers', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email, name }),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.error ?? 'Failed to add subscriber');
    }
    return res.json();
  },

  async deleteSubscriber(id: string): Promise<void> {
    const res = await fetch(`/api/admin/promo-list/subscribers/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to delete subscriber');
  },

  async sendPromo(payload: {
    releaseSlug: string;
    releaseTitle: string;
    releaseArtist: string;
    expiresAt?: string;
  }): Promise<{ ok: boolean; sent: number; failed: number; errors: string[] }> {
    const res = await fetch('/api/admin/promo-list/send', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to send promo');
    return res.json();
  },

  async testPromo(payload: {
    releaseSlug: string;
    releaseTitle: string;
    releaseArtist: string;
    testEmail: string;
  }): Promise<{ ok: boolean; promoUrl?: string; error?: string }> {
    const res = await fetch('/api/admin/promo-list/test', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  },
};
