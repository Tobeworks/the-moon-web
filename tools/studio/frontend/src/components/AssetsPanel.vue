<template>
  <div id="panel-A" class="panel">
    <h2>1 · Assets</h2>
    <div :class="['drop', over && 'over']" @dragover="onFileOver" @dragleave="over = false" @drop="onFileDrop">
      <b>WAVs und Cover hierher ziehen</b><br />
      oder mit den Knöpfen wählen. Dateien landen im Asset-Ordner des Releases.
      <div class="row">
        <button class="btn" @click="pick('files')">Dateien wählen …</button>
        <button class="btn" @click="pick('folder')">Ordner wählen …</button>
        <button class="btn ghost" @click="pick('cover')">Cover wählen …</button>
      </div>
    </div>

    <p v-if="sortable" class="note">Reihenfolge der Tracks: Zeile mit dem Griff ⠿ ziehen, oder Alt + Pfeil hoch/runter.</p>
    <div class="files mono">
      <div
        v-for="r in rows" :key="r.kind + r.name"
        :class="['asset', r.i >= 0 && 'drag', from === r.i && r.i >= 0 && 'from', over2 === r.i && r.i >= 0 && from !== null && from > r.i && 'before', over2 === r.i && r.i >= 0 && from !== null && from < r.i && 'after']"
        :draggable="r.i >= 0" :tabindex="r.i >= 0 ? 0 : undefined" :data-row="r.i"
        @dragstart="onDragStart($event, r.i)" @dragover="onRowOver($event, r.i)" @dragleave="over2 = null"
        @drop="onRowDrop($event, r.i)" @dragend="from = over2 = null"
        @keydown.alt.up.prevent="r.i >= 0 && moveKey(r.i, r.i - 1)" @keydown.alt.down.prevent="r.i >= 0 && moveKey(r.i, r.i + 1)"
      >
        <span v-if="r.i >= 0" class="grip" aria-hidden="true">⠿</span>
        <span v-if="r.i >= 0" class="no">{{ r.i + 1 }}</span>
        <span class="name">{{ r.name }}</span>
        <button class="btn ghost" title="In den Papierkorb" :aria-label="`${r.name} entfernen`" @click="remove(r)">×</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue';
import { api, ApiError } from '@/api';
import type { FileResult, ReleaseDetail } from '@/api/types';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';

interface Row { kind: 'audio' | 'artwork'; name: string; i: number }

const props = defineProps<{ catalog: string; detail: ReleaseDetail }>();
const emit = defineEmits<{ reorder: [from: number, to: number]; changed: [] }>();
const banner = useBanner();
const job = useJob();

const over = ref(false); // OS files over the drop zone
const from = ref<number | null>(null); // internal drag: track index
const over2 = ref<number | null>(null);

// the order of the asset folder's tracklist (may hold tracks that are not pushed yet)
const local = computed(() => (props.detail.local_tracks.length ? props.detail.local_tracks : props.detail.tracks));
const rows = computed<Row[]>(() => {
  const idx = (n: string) => local.value.findIndex((t) => t.file === n);
  const audio = props.detail.files.audio.map((name) => ({ kind: 'audio' as const, name, i: idx(name) }))
    .sort((a, b) => Number(a.i < 0) - Number(b.i < 0) || a.i - b.i);
  return [...audio, ...props.detail.files.artwork.map((name) => ({ kind: 'artwork' as const, name, i: -1 }))];
});
const sortable = computed(() => rows.value.filter((r) => r.i >= 0).length > 1);

// ── add files ───────────────────────────────────────────────────────────────
async function done(r: { job_id: string | null }) {
  if (r.job_id) job.follow(r.job_id, 0);
  else emit('changed');
}

async function sendPaths(paths: string[], overwrite: string[] = []): Promise<void> {
  const r = await api.post<FileResult>(`/api/releases/${props.catalog}/files`, { paths, overwrite });
  if (r.conflicts.length && confirm(`Überschreiben?\n${r.conflicts.join('\n')}`)) return sendPaths(paths, r.conflicts);
  await done(r);
}

const pick = (kind: string) => banner.guard(async () => {
  const r = await api.post<{ paths: string[] }>('/api/pick', { kind });
  if (r.paths.length) await sendPaths(r.paths);
});

async function upload(files: File[], overwrite = false): Promise<void> {
  const form = new FormData();
  files.forEach((f) => form.append('files', f));
  if (overwrite) form.append('overwrite', 'true');
  try {
    await done(await api.form<FileResult>(`/api/releases/${props.catalog}/upload`, form));
  } catch (e) {
    const conflicts = e instanceof ApiError && e.status === 409 ? (e.detail as { conflicts?: string[] })?.conflicts ?? [] : null;
    if (conflicts && !overwrite && confirm(`Überschreiben?\n${conflicts.join('\n')}`)) return upload(files, true);
    throw e;
  }
}

const isFiles = (e: DragEvent) => e.dataTransfer?.types.includes('Files') ?? false;
function onFileOver(e: DragEvent) { if (isFiles(e)) { e.preventDefault(); over.value = true; } }
function onFileDrop(e: DragEvent) {
  over.value = false;
  if (!isFiles(e)) return;
  e.preventDefault();
  void banner.guard(() => upload([...(e.dataTransfer?.files ?? [])]));
}

// ── remove ──────────────────────────────────────────────────────────────────
const remove = (r: Row) => banner.guard(async () => {
  if (!confirm(`„${r.name}“ aus den Assets entfernen?\nDie Datei landet im Papierkorb.`)) return;
  await done(await api.del<{ job_id: string | null }>(`/api/releases/${props.catalog}/files/${r.kind}/${encodeURIComponent(r.name)}`));
});

// ── sort by drag and drop (or Alt + arrow keys) ─────────────────────────────
function onDragStart(e: DragEvent, i: number) {
  if (i < 0) return;
  from.value = i;
  if (e.dataTransfer) { e.dataTransfer.effectAllowed = 'move'; e.dataTransfer.setData('text/plain', String(i)); }
}
function onRowOver(e: DragEvent, i: number) {
  if (from.value === null || i < 0) return; // not an internal drag: leave it to the drop zone
  e.preventDefault();
  over2.value = i;
}
function onRowDrop(e: DragEvent, to: number) {
  if (from.value === null || to < 0) return;
  e.preventDefault();
  const a = from.value;
  from.value = over2.value = null;
  if (a !== to) emit('reorder', a, to);
}
async function moveKey(a: number, b: number) {
  if (b < 0 || b >= local.value.length) return;
  emit('reorder', a, b);
  await nextTick();
  document.querySelector<HTMLElement>(`[data-row="${b}"]`)?.focus(); // focus follows the moved row
}
</script>
