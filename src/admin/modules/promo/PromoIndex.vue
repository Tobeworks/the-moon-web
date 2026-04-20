<template>
  <div class="flex flex-col gap-6">

    <!-- Header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div class="flex flex-col gap-1">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// PROMO_LIST</span>
        <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Promo List</h1>
        <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">
          {{ subscribers.length }} subscriber{{ subscribers.length !== 1 ? 's' : '' }}
        </p>
      </div>
      <div class="flex gap-2 flex-wrap">
        <button @click="showSend = !showSend" class="btn btn--primary">Send Promo</button>
        <button @click="showAdd = !showAdd" class="btn btn--muted">Add Contact</button>
      </div>
    </div>

    <!-- Send Promo Panel -->
    <div v-if="showSend" class="border border-border p-5 flex flex-col gap-4">
      <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// SEND_PROMO</span>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Release *</label>
          <select v-model="selectedRelease" class="tmr-input w-full">
            <option value="">— select release —</option>
            <option v-for="r in releases" :key="r.slug" :value="r">
              {{ r.catalog }} — {{ r.title }} ({{ r.artist }})
            </option>
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Expires at (optional)</label>
          <input v-model="expiresAt" type="date" class="tmr-input w-full" />
        </div>
      </div>

      <!-- Test row -->
      <div class="flex flex-col gap-1.5">
        <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Test email</label>
        <div class="flex gap-2">
          <input v-model="testEmail" type="email" class="tmr-input flex-1" placeholder="your@email.com" />
          <button
            @click="sendTest"
            :disabled="!selectedRelease || !testEmail || testing"
            class="btn btn--muted flex-shrink-0"
          >{{ testing ? 'Sending…' : 'Send Test' }}</button>
        </div>
        <p v-if="testResult" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase"
          :class="testResult.ok ? 'text-green-400' : 'text-red-400'">
          {{ testResult.ok ? `✓ Test sent — ${testResult.promoUrl}` : `✗ ${testResult.error}` }}
        </p>
      </div>

      <!-- Send to all -->
      <div class="border-t border-border pt-4 flex items-center gap-3 flex-wrap">
        <button
          @click="sendToAll"
          :disabled="!selectedRelease || sending"
          class="btn btn--primary"
        >{{ sending ? `Sending… (${sendProgress})` : `Send to all ${subscribers.length} subscribers` }}</button>
        <button @click="showSend = false; sendResult = null; testResult = null" class="btn btn--muted">Cancel</button>
        <p v-if="sendResult" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase"
          :class="sendResult.failed > 0 ? 'text-yellow-400' : 'text-green-400'">
          {{ sendResult.failed > 0
            ? `✓ ${sendResult.sent} sent, ✗ ${sendResult.failed} failed`
            : `✓ ${sendResult.sent} sent successfully` }}
        </p>
      </div>
    </div>

    <!-- Add Contact form -->
    <div v-if="showAdd" class="border border-border p-5 flex flex-col gap-4">
      <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// ADD_CONTACT</span>
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Email *</label>
          <input v-model="newEmail" type="email" class="tmr-input w-full" placeholder="email@example.com" @keyup.enter="add" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Name</label>
          <input v-model="newName" type="text" class="tmr-input w-full" placeholder="Optional" @keyup.enter="add" />
        </div>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <button @click="add" :disabled="adding || !newEmail.trim()" class="btn btn--primary">
          {{ adding ? 'Adding…' : 'Add' }}
        </button>
        <button @click="showAdd = false; newEmail = ''; newName = ''" class="btn btn--muted">Cancel</button>
        <span v-if="addError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ addError }}</span>
      </div>
    </div>

    <!-- Error / Loading / Empty -->
    <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>
    <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">Loading…</p>
    <p v-else-if="subscribers.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">No contacts yet.</p>

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
          @click="remove(s.id)"
          :disabled="deletingId === s.id"
          class="btn btn--muted flex-shrink-0"
          style="font-size:0.6rem;padding:0.3rem 0.75rem;color:var(--color-fg-muted);"
        >
          {{ deletingId === s.id ? '…' : 'Remove' }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { promoApi, type PromoSubscriber } from '../../../lib/admin-api';

// ── Releases (embedded from build-time import) ──────────────────────────────
import releasesJson from '../../../../the-moon-os/data/releases.json';

interface Release { slug: string; catalog: string; title: string; artist: string; }
const releases: Release[] = (releasesJson as any).releases.map((r: any) => ({
  slug: r.catalog,
  catalog: r.catalog,
  title: r.title,
  artist: r.artist,
}));

// ── State ────────────────────────────────────────────────────────────────────
const subscribers = ref<PromoSubscriber[]>([]);
const loading     = ref(true);
const loadError   = ref('');

const showAdd    = ref(false);
const newEmail   = ref('');
const newName    = ref('');
const adding     = ref(false);
const addError   = ref('');
const deletingId = ref('');

const showSend       = ref(false);
const selectedRelease = ref<Release | ''>('');
const expiresAt      = ref('');
const testEmail      = ref('');
const testing        = ref(false);
const testResult     = ref<{ ok: boolean; promoUrl?: string; error?: string } | null>(null);
const sending        = ref(false);
const sendProgress   = ref('');
const sendResult     = ref<{ sent: number; failed: number } | null>(null);

// ── Load ─────────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    subscribers.value = await promoApi.getSubscribers();
  } catch {
    loadError.value = 'Failed to load subscribers.';
  } finally {
    loading.value = false;
  }
});

// ── Add ──────────────────────────────────────────────────────────────────────
async function add() {
  if (!newEmail.value.trim()) return;
  adding.value = true;
  addError.value = '';
  try {
    const s = await promoApi.addSubscriber(newEmail.value.trim(), newName.value.trim());
    subscribers.value.unshift(s);
    showAdd.value = false;
    newEmail.value = '';
    newName.value  = '';
  } catch (e: any) {
    addError.value = e.message ?? 'Error adding contact.';
  } finally {
    adding.value = false;
  }
}

// ── Remove ───────────────────────────────────────────────────────────────────
async function remove(id: string) {
  if (!confirm('Remove this contact from the promo list?')) return;
  deletingId.value = id;
  try {
    await promoApi.deleteSubscriber(id);
    subscribers.value = subscribers.value.filter(s => s.id !== id);
  } finally {
    deletingId.value = '';
  }
}

// ── Test ─────────────────────────────────────────────────────────────────────
async function sendTest() {
  if (!selectedRelease.value || !testEmail.value) return;
  testing.value = true;
  testResult.value = null;
  const r = selectedRelease.value as Release;
  try {
    testResult.value = await promoApi.testPromo({
      releaseSlug: r.slug,
      releaseTitle: r.title,
      releaseArtist: r.artist,
      testEmail: testEmail.value,
    });
  } finally {
    testing.value = false;
  }
}

// ── Send to all ───────────────────────────────────────────────────────────────
async function sendToAll() {
  if (!selectedRelease.value) return;
  const r = selectedRelease.value as Release;
  if (!confirm(`Send promo for "${r.title}" to all ${subscribers.value.length} subscribers?`)) return;
  sending.value = true;
  sendResult.value = null;
  sendProgress.value = '0/' + subscribers.value.length;
  try {
    const result = await promoApi.sendPromo({
      releaseSlug: r.slug,
      releaseTitle: r.title,
      releaseArtist: r.artist,
      ...(expiresAt.value ? { expiresAt: expiresAt.value } : {}),
    });
    sendResult.value = result;
  } finally {
    sending.value = false;
  }
}
</script>
