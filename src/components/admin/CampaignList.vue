<template>
  <div class="flex flex-col gap-6">

    <!-- Header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div class="flex flex-col gap-1">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// NEWSLETTER_ADMIN</span>
        <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Campaigns</h1>
        <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">
          {{ subscriberCount }} confirmed subscriber{{ subscriberCount !== 1 ? 's' : '' }}
        </p>
      </div>
      <div class="flex gap-3">
        <button @click="showNew = true" class="btn btn--primary">New Campaign</button>
        <form method="POST" action="/api/admin/logout">
          <button type="submit" class="btn btn--muted">Logout</button>
        </form>
      </div>
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

    <!-- Error -->
    <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>

    <!-- Loading -->
    <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">Loading…</p>

    <!-- Empty -->
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
              <template v-if="c.sent_at"> · {{ formatDate(c.sent_at) }}</template>
            </template>
            <template v-else>{{ c.status.toUpperCase() }}</template>
          </span>
        </div>
        <div class="flex gap-2 flex-shrink-0">
          <a :href="`/admin/newsletter/${c.id}`" class="btn btn--muted" style="font-size:0.6rem;padding:0.3rem 0.75rem;">
            {{ c.status === 'sent' ? 'View' : 'Edit' }}
          </a>
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

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { adminApi, type Campaign } from '../../lib/admin-api';

const props = defineProps<{ subscriberCount: number }>();

const campaigns   = ref<Campaign[]>([]);
const loading     = ref(true);
const loadError   = ref('');
const showNew     = ref(false);
const newSubject  = ref('');
const creating    = ref(false);
const createError = ref('');
const sendingId   = ref('');

onMounted(async () => {
  try {
    campaigns.value = await adminApi.getCampaigns();
  } catch (e) {
    loadError.value = 'Failed to load campaigns.';
  } finally {
    loading.value = false;
  }
});

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
  if (!confirm(`Send "${c.subject}" to ${props.subscriberCount} subscriber(s)?`)) return;
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

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('de-DE');
}
</script>
