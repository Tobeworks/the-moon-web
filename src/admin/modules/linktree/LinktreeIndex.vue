<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div class="flex flex-col gap-1">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// LINKTREE</span>
        <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Linktree</h1>
        <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
          {{ items.length }} entr{{ items.length !== 1 ? 'ies' : 'y' }} — <a href="/links" target="_blank" class="text-accent hover:underline">/links ↗</a>
        </p>
      </div>
      <button @click="startNew" class="btn btn--primary">New Entry</button>
    </div>

    <!-- New / edit entry form -->
    <div v-if="showNew" class="border border-border p-5 flex flex-col gap-4">
      <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// {{ editingId ? 'EDIT_ENTRY' : 'NEW_ENTRY' }}</span>

      <div class="flex gap-0 border border-border w-fit">
        <button
          @click="form.type = 'release'"
          :class="form.type === 'release' ? 'bg-surface text-fg' : 'text-fg-dim hover:text-fg'"
          class="px-4 py-2 font-mono text-[0.55rem] tracking-[0.2em] uppercase transition-colors cursor-pointer"
        >Release</button>
        <button
          @click="form.type = 'link'"
          :class="form.type === 'link' ? 'bg-surface text-fg' : 'text-fg-dim hover:text-fg'"
          class="px-4 py-2 font-mono text-[0.55rem] tracking-[0.2em] uppercase border-l border-border transition-colors cursor-pointer"
        >Custom Link</button>
      </div>

      <div v-if="form.type === 'release'" class="flex flex-col gap-1.5">
        <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Release *</label>
        <select v-model="form.release_catalog" class="tmr-input w-full">
          <option value="">— select release —</option>
          <option v-for="r in releases" :key="r.catalog" :value="r.catalog">
            {{ r.catalog }} — {{ r.artist }} — {{ r.title }}
          </option>
        </select>
      </div>

      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Label *</label>
          <input v-model="form.label" type="text" class="tmr-input w-full" placeholder="Newsletter" />
        </div>
        <div class="flex flex-col gap-1.5">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">URL *</label>
          <input v-model="form.url" type="url" class="tmr-input w-full" placeholder="https://..." />
        </div>
      </div>

      <div class="flex items-center gap-4 flex-wrap">
        <button @click="create" :disabled="creating || !canCreate" class="btn btn--primary">
          {{ creating ? 'Saving…' : (editingId ? 'Save' : 'Create') }}
        </button>
        <button @click="cancelNew" class="btn btn--muted">Cancel</button>
        <span v-if="createError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ createError }}</span>
      </div>
    </div>

    <!-- Error / Loading / Empty -->
    <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>
    <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Loading…</p>
    <p v-else-if="items.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">No entries yet.</p>

    <!-- List -->
    <div v-else class="flex flex-col border border-border">
      <div
        v-for="(item, idx) in items"
        :key="item.id"
        @click="startEdit(item)"
        class="flex items-center justify-between gap-4 px-5 py-4 border-b border-border last:border-b-0 flex-wrap cursor-pointer transition-colors"
        :class="editingId === item.id ? 'bg-surface' : 'hover:bg-surface'"
      >
        <div class="flex flex-col gap-1 min-w-0">
          <span class="font-label font-semibold text-[0.85rem] tracking-[0.06em] text-fg">
            {{ item.type === 'release' ? releaseLabel(item.release_catalog) : item.label }}
          </span>
          <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
            {{ item.type === 'release' ? item.release_catalog : item.url }}
          </span>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <button
            @click.stop="move(item, 'up')"
            :disabled="idx === 0 || movingId === item.id"
            class="font-mono text-[0.6rem] px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >▲</button>
          <button
            @click.stop="move(item, 'down')"
            :disabled="idx === items.length - 1 || movingId === item.id"
            class="font-mono text-[0.6rem] px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >▼</button>
          <button
            @click.stop="removeItem(item)"
            :disabled="deletingId === item.id"
            class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-red-400 hover:border-red-400/40 transition-colors disabled:cursor-not-allowed"
          >{{ deletingId === item.id ? '…' : 'Delete' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { linktreeApi, type LinktreeItem } from '../../../lib/admin-api';
import releasesJson from '../../../../the-moon-os/data/releases.json';

interface Release { catalog: string; artist: string; title: string; }
const releases: Release[] = (releasesJson as any).releases.map((r: any) => ({
  catalog: r.catalog,
  artist: r.artist,
  title: r.title,
}));

const releaseLabel = (catalog?: string) => {
  const r = releases.find((x) => x.catalog === catalog);
  return r ? `${r.catalog} — ${r.artist} — ${r.title}` : catalog ?? '(unknown release)';
};

const items      = ref<LinktreeItem[]>([]);
const loading    = ref(true);
const loadError  = ref('');
const showNew    = ref(false);
const creating   = ref(false);
const createError = ref('');
const movingId   = ref('');
const deletingId = ref('');
const editingId  = ref('');

const emptyForm = () => ({ type: 'release' as 'release' | 'link', release_catalog: '', label: '', url: '' });
const form = ref(emptyForm());

const canCreate = computed(() =>
  form.value.type === 'release'
    ? form.value.release_catalog.trim().length > 0
    : form.value.label.trim().length > 0 && form.value.url.trim().length > 0,
);

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    items.value = await linktreeApi.getAll();
  } catch {
    loadError.value = 'Failed to load linktree items.';
  } finally {
    loading.value = false;
  }
}

function cancelNew() {
  showNew.value = false;
  editingId.value = '';
  createError.value = '';
  form.value = emptyForm();
}

function startNew() {
  if (showNew.value && !editingId.value) return cancelNew();
  cancelNew();
  showNew.value = true;
}

function startEdit(item: LinktreeItem) {
  editingId.value = item.id;
  createError.value = '';
  form.value = {
    type: item.type,
    release_catalog: item.release_catalog ?? '',
    label: item.label ?? '',
    url: item.url ?? '',
  };
  showNew.value = true;
}

async function create() {
  if (!canCreate.value) return;
  creating.value = true;
  createError.value = '';
  const payload = {
    type: form.value.type,
    release_catalog: form.value.type === 'release' ? form.value.release_catalog : undefined,
    label: form.value.type === 'link' ? form.value.label.trim() : undefined,
    url: form.value.type === 'link' ? form.value.url.trim() : undefined,
  };
  try {
    if (editingId.value) await linktreeApi.update(editingId.value, payload);
    else await linktreeApi.create(payload);
    cancelNew();
    await load();
  } catch (e: any) {
    createError.value = e.message ?? 'Failed to save entry.';
  } finally {
    creating.value = false;
  }
}

async function move(item: LinktreeItem, direction: 'up' | 'down') {
  movingId.value = item.id;
  try {
    items.value = await linktreeApi.move(item.id, direction);
  } catch (e: any) {
    alert(e.message ?? 'Failed to reorder.');
  } finally {
    movingId.value = '';
  }
}

async function removeItem(item: LinktreeItem) {
  const label = item.type === 'release' ? releaseLabel(item.release_catalog) : item.label;
  if (!confirm(`Delete "${label}"?`)) return;
  deletingId.value = item.id;
  try {
    await linktreeApi.delete(item.id);
    await load();
  } catch (e: any) {
    alert(e.message ?? 'Failed to delete entry.');
  } finally {
    deletingId.value = '';
  }
}

onMounted(load);
</script>
