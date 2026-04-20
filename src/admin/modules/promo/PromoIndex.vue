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
      <button @click="showAdd = true" class="btn btn--primary">Add Contact</button>
    </div>

    <!-- Add form -->
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

const subscribers = ref<PromoSubscriber[]>([]);
const loading     = ref(true);
const loadError   = ref('');
const showAdd     = ref(false);
const newEmail    = ref('');
const newName     = ref('');
const adding      = ref(false);
const addError    = ref('');
const deletingId  = ref('');

onMounted(async () => {
  try {
    subscribers.value = await promoApi.getSubscribers();
  } catch {
    loadError.value = 'Failed to load subscribers.';
  } finally {
    loading.value = false;
  }
});

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
</script>
