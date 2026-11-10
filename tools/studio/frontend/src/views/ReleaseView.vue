<template>
  <template v-if="detail">
    <div class="crumb"><RouterLink to="/">Releases</RouterLink> / {{ catalog }}</div>
    <div class="row">
      <img
        v-if="detail.files.cover" class="cover" alt="Cover" title="Vergrößern"
        :src="`/api/releases/${catalog}/media/cover/${detail.files.cover}`"
        @click="lightbox = `/api/releases/${catalog}/media/cover/${detail.files.cover_large || detail.files.cover}`"
      />
      <div><div class="label">{{ detail.summary.artist }}</div><h1>{{ detail.summary.title || catalog }}</h1></div>
      <div class="spacer" />
      <WhenTag :row="detail.summary" />
      <span class="mono">{{ fmtDate(detail.summary.release_date) }}</span>
    </div>
    <div class="gap"><PipeSteps :row="detail.summary" /></div>

    <div class="gap">
      <CommitBar />
      <AssetsPanel :catalog="catalog" :detail="detail" @reorder="reorder" @changed="load" />
      <MetaPanel :catalog="catalog" :detail="detail" :form="form" :saving="saving" @save="save()" />
      <ConvertPanel :catalog="catalog" :detail="detail" />
      <PlayerPanel :catalog="catalog" :detail="detail" />
      <PushPanel :catalog="catalog" :detail="detail" />
      <DspPanel :catalog="catalog" :detail="detail" @changed="load" />
      <LogPanel />
    </div>
    <CoverLightbox v-model="lightbox" />
  </template>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref, watch } from 'vue';
import { api } from '@/api';
import type { ReleaseDetail } from '@/api/types';
import AssetsPanel from '@/components/AssetsPanel.vue';
import CommitBar from '@/components/CommitBar.vue';
import ConvertPanel from '@/components/ConvertPanel.vue';
import CoverLightbox from '@/components/CoverLightbox.vue';
import DspPanel from '@/components/DspPanel.vue';
import LogPanel from '@/components/LogPanel.vue';
import MetaPanel from '@/components/MetaPanel.vue';
import PipeSteps from '@/components/PipeSteps.vue';
import PlayerPanel from '@/components/PlayerPanel.vue';
import PushPanel from '@/components/PushPanel.vue';
import WhenTag from '@/components/WhenTag.vue';
import { fieldsOf, formFrom, type MetaForm } from '@/lib/form';
import { fmtDate } from '@/lib/format';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';
import { useStudio } from '@/stores/studio';

const props = defineProps<{ catalog: string; focus?: string }>();
const banner = useBanner();
const job = useJob();
const studio = useStudio();

const detail = ref<ReleaseDetail | null>(null);
const lightbox = ref<string | null>(null);
const saving = ref(false);
const form = reactive<MetaForm>({ artist: '', title: '', release_date: '', genre: '', bandcamp: '', about: '', titles: {} });
let base = '';
const dirty = () => JSON.stringify(form) !== base;
function resetForm(d: ReleaseDetail) {
  Object.assign(form, formFrom(d));
  base = JSON.stringify(form);
}

/** Loads in the background; keeps what is on screen, and keeps unsaved edits in the form. */
async function load(forceForm = false) {
  const d = await api.get<ReleaseDetail>(`/api/releases/${props.catalog}`);
  detail.value = d;
  if (forceForm || !dirty()) resetForm(d);
  await studio.refresh();
}
const reload = (forceForm = false) => banner.guard(() => load(forceForm));

onMounted(async () => {
  await reload(true);
  if (props.focus) {
    await nextTick();
    document.getElementById(`panel-${props.focus}`)?.scrollIntoView({ block: 'start' });
  }
});
watch(() => props.catalog, () => { detail.value = null; void reload(true); });
watch(() => job.finished, () => void reload());

/** Saves the form (plus an optional new track order) in one request. */
async function save(extra: { track_order?: number[] } = {}) {
  saving.value = true;
  const ok = await banner.guard(async () => {
    const saved = await api.put<{ published: string[] }>(`/api/releases/${props.catalog}/meta`, {
      fields: { ...fieldsOf(form), ...extra }, about: form.about,
    });
    if (extra.track_order) {
      banner.show(detail.value?.entry
        ? 'Reihenfolge gespeichert. Zum Veröffentlichen committen; für saubere Dateinamen auf dem CDN neu konvertieren (Überschreiben) und pushen.'
        : 'Reihenfolge gespeichert. MP3s neu konvertieren (Überschreiben).', false);
    } else {
      banner.show(saved.published.length
        ? `Gespeichert. Auch in releases.json aktualisiert: ${saved.published.join(', ')}. Zum Veröffentlichen committen und pushen.`
        : 'Gespeichert', false);
    }
    await load(true);
    return true;
  });
  saving.value = false;
  return ok === true;
}

/** Drag and drop: the list changes at once, the save runs in the background. */
async function reorder(from: number, to: number) {
  const d = detail.value;
  if (!d) return;
  const local = d.local_tracks.length ? d.local_tracks : d.tracks;
  const order = local.map((t) => t.number);
  order.splice(to, 0, ...order.splice(from, 1));
  if (d.local_tracks.length) {
    const byNumber = new Map(d.local_tracks.map((t) => [t.number, t]));
    d.local_tracks = order.map((n, i) => ({ ...byNumber.get(n)!, number: i + 1 }));
  }
  if (!(await save({ track_order: order }))) await reload(); // save failed: show the real order again
}

</script>
