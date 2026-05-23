<template>
  <div class="flex flex-col gap-6">

    <!-- Tab switcher -->
    <div class="flex gap-0 border border-border">
      <button
        @click="tab = 'campaigns'"
        :class="tab === 'campaigns' ? 'bg-surface text-fg' : 'text-fg-muted hover:text-fg'"
        class="flex-1 px-5 py-3 font-mono text-[0.6rem] tracking-[0.3em] uppercase transition-colors"
      >Campaigns</button>
      <button
        @click="tab = 'subscribers'; loadSubscribers()"
        :class="tab === 'subscribers' ? 'bg-surface text-fg' : 'text-fg-muted hover:text-fg'"
        class="flex-1 px-5 py-3 font-mono text-[0.6rem] tracking-[0.3em] uppercase border-l border-border transition-colors"
      >Subscribers</button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Campaigns                                                         -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="tab === 'campaigns'">

      <!-- Header -->
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="flex flex-col gap-1">
          <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// NEWSLETTER</span>
          <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Campaigns</h1>
          <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">
            {{ subscriberCount }} confirmed subscriber{{ subscriberCount !== 1 ? 's' : '' }}
          </p>
        </div>
        <button @click="showNew = true" class="btn btn--primary">New Campaign</button>
      </div>

      <!-- New campaign form -->
      <div v-if="showNew" class="border border-border p-5 flex flex-col gap-4">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// NEW_CAMPAIGN</span>
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Subject</label>
          <input v-model="newSubject" type="text" class="tmr-input w-full" placeholder="Subject line" @keyup.enter="create" />
        </div>
        <div class="flex gap-3">
          <button @click="create" :disabled="creating || !newSubject.trim()" class="btn btn--primary">
            {{ creating ? 'Creating…' : 'Create Draft' }}
          </button>
          <button @click="showNew = false; newSubject = ''" class="btn btn--muted">Cancel</button>
        </div>
        <p v-if="createError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ createError }}</p>
      </div>

      <!-- Error / Loading / Empty -->
      <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>
      <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">Loading…</p>
      <p v-else-if="campaigns.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">No campaigns yet.</p>

      <!-- List -->
      <div v-else class="flex flex-col border border-border">
        <div
          v-for="c in campaigns"
          :key="c.id"
          class="flex items-center gap-4 px-5 py-4 border-b border-border last:border-b-0 flex-wrap"
        >
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <span class="font-label font-semibold text-[0.85rem] tracking-[0.08em] text-fg truncate">{{ c.subject }}</span>
            <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-muted">
              <template v-if="c.status === 'sent'">
                Sent {{ c.sent_count ?? 0 }} · Failed {{ c.failed_count ?? 0 }}
                <template v-if="c.sent_at"> · {{ new Date(c.sent_at).toLocaleDateString('de-DE') }}</template>
              </template>
              <template v-else>{{ c.status.toUpperCase() }}</template>
            </span>
          </div>
          <div class="flex gap-2 flex-shrink-0">
            <RouterLink
              :to="`/newsletter/${c.id}`"
              class="btn btn--muted"
              style="font-size:0.6rem;padding:0.3rem 0.75rem;"
            >
              {{ c.status === 'sent' ? 'View' : 'Edit' }}
            </RouterLink>
            <button
              v-if="c.status === 'draft'"
              @click="send(c)"
              :disabled="sendingId === c.id"
              class="btn btn--primary"
              style="font-size:0.6rem;padding:0.3rem 0.75rem;"
            >
              {{ sendingId === c.id ? 'Sending…' : 'Send' }}
            </button>
            <button
              v-if="c.status !== 'sent'"
              @click="remove(c.id)"
              class="btn btn--muted"
              style="font-size:0.6rem;padding:0.3rem 0.75rem;color:var(--color-fg-muted);"
            >Delete</button>
          </div>
        </div>
      </div>

    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Subscribers                                                        -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="tab === 'subscribers'">

      <!-- Header -->
      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="flex flex-col gap-1">
          <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// SUBSCRIBERS</span>
          <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Newsletter Subscribers</h1>
          <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">
            {{ subscribers.length }} confirmed subscriber{{ subscribers.length !== 1 ? 's' : '' }}
          </p>
        </div>
      </div>

      <!-- Loading / Error / Empty -->
      <p v-if="subsLoading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">Loading…</p>
      <p v-else-if="subsError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ subsError }}</p>
      <p v-else-if="subscribers.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">No subscribers yet.</p>

      <!-- List -->
      <div v-else class="flex flex-col border border-border">
        <div
          v-for="s in subscribers"
          :key="s.id"
          class="flex items-center gap-4 px-5 py-4 border-b border-border last:border-b-0 flex-wrap"
        >
          <div class="flex-1 min-w-0 flex flex-col gap-1">
            <span class="font-label font-semibold text-[0.85rem] tracking-[0.08em] text-fg">{{ s.email }}</span>
            <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
              {{ s.name || '—' }} · {{ s.created ? new Date(s.created.replace(' ', 'T')).toLocaleDateString('de-DE') : '—' }}
            </span>
          </div>
          <button
            @click="deleteSub(s.id)"
            :disabled="deletingSubId === s.id"
            class="btn btn--muted flex-shrink-0"
            style="font-size:0.6rem;padding:0.3rem 0.75rem;color:var(--color-fg-muted);"
          >
            {{ deletingSubId === s.id ? '…' : 'Remove' }}
          </button>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { adminApi, newsletterSubscribersApi, type Campaign, type NewsletterSubscriber } from '../../../lib/admin-api';

const tab = ref<'campaigns' | 'subscribers'>('campaigns');

// ── Campaigns ────────────────────────────────────────────────────────────────
const subscriberCount = ref(0);
const campaigns   = ref<Campaign[]>([]);
const loading     = ref(true);
const loadError   = ref('');
const showNew     = ref(false);
const newSubject  = ref('');
const creating    = ref(false);
const createError = ref('');
const sendingId   = ref('');

// ── Subscribers ───────────────────────────────────────────────────────────────
const subscribers   = ref<NewsletterSubscriber[]>([]);
const subsLoading   = ref(false);
const subsError     = ref('');
const deletingSubId = ref('');
let subsLoaded = false;

onMounted(async () => {
  try {
    const [camps, subsRes] = await Promise.all([
      adminApi.getCampaigns(),
      fetch('/api/admin/newsletter/subscribers/count'),
    ]);
    campaigns.value = camps;
    if (subsRes.ok) {
      const d = await subsRes.json();
      subscriberCount.value = d.count ?? 0;
    }
  } catch {
    loadError.value = 'Failed to load campaigns.';
  } finally {
    loading.value = false;
  }
});

async function loadSubscribers() {
  if (subsLoaded) return;
  subsLoading.value = true;
  subsError.value = '';
  try {
    subscribers.value = await newsletterSubscribersApi.getAll();
    subsLoaded = true;
  } catch {
    subsError.value = 'Failed to load subscribers.';
  } finally {
    subsLoading.value = false;
  }
}

async function deleteSub(id: string) {
  if (!confirm('Remove this subscriber?')) return;
  deletingSubId.value = id;
  try {
    await newsletterSubscribersApi.delete(id);
    subscribers.value = subscribers.value.filter(s => s.id !== id);
    subscriberCount.value = Math.max(0, subscriberCount.value - 1);
  } catch {
    subsError.value = 'Failed to remove subscriber.';
  } finally {
    deletingSubId.value = '';
  }
}

async function create() {
  if (!newSubject.value.trim()) return;
  creating.value = true;
  createError.value = '';
  try {
    const c = await adminApi.createCampaign(newSubject.value.trim(), '', '');
    window.location.href = `/admin/newsletter/${c.id}`;
  } catch {
    createError.value = 'Failed to create campaign.';
    creating.value = false;
  }
}

async function send(c: Campaign) {
  if (!confirm(`Send "${c.subject}" to ${subscriberCount.value} subscriber(s)?`)) return;
  sendingId.value = c.id;
  const result = await adminApi.sendCampaign(c.id);
  sendingId.value = '';
  if (result.ok) {
    alert(`Done — Sent: ${result.sent} · Failed: ${result.failed}`);
    campaigns.value = await adminApi.getCampaigns();
  } else {
    alert('Error: ' + (result.error ?? 'unknown'));
  }
}

async function remove(id: string) {
  if (!confirm('Delete this campaign?')) return;
  await adminApi.deleteCampaign(id);
  campaigns.value = campaigns.value.filter(c => c.id !== id);
}
</script>
