<template>
  <div id="panel-D" class="panel">
    <h2>5 · DSP-Links</h2>
    <p class="note">Sucht über die Bandcamp-URL. Übernommen werden nur Treffer ab Confidence 85 mit passendem Künstler.</p>
    <div class="row gap">
      <button class="btn" :disabled="detail.summary.status.P !== 'ok' || scanning" @click="scan">Links suchen</button>
    </div>
    <p v-if="detail.summary.status.P !== 'ok'" class="note">Erst nach dem Push möglich.</p>
    <p v-if="scanning" class="note">Suche läuft … (dauert etwa 2 Minuten)</p>
    <p v-else-if="found && !found.length" class="note">Keine neuen Treffer.</p>
    <div v-if="found?.length">
      <div class="gap">
        <div v-for="(x, i) in found" :key="x.name" class="dsp">
          <input v-model="picked[i]" type="checkbox" />
          <span class="mono">{{ x.name }}</span>
          <a class="mono ext" :href="x.url" target="_blank" rel="noopener noreferrer">{{ x.url }}</a>
          <span :style="x.accepted ? '' : 'color:var(--warn)'">{{ x.accepted ? `✓ ${x.confidence}` : `! ${x.reason}` }}</span>
        </div>
      </div>
      <div class="row gap"><button class="btn fill" @click="apply">Ausgewählte übernehmen</button></div>
    </div>
    <div v-if="detail.entry?.platforms?.length" class="files mono">
      <div v-for="p in detail.entry.platforms" :key="p.name">
        <span>{{ p.name }}</span><a class="ext" :href="p.url" target="_blank" rel="noopener noreferrer">{{ p.url }}</a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { api } from '@/api';
import type { DspCandidate, ReleaseDetail } from '@/api/types';
import { useBanner } from '@/stores/banner';

const props = defineProps<{ catalog: string; detail: ReleaseDetail }>();
const emit = defineEmits<{ changed: [] }>();
const banner = useBanner();
const scanning = ref(false);
const found = ref<DspCandidate[] | null>(null);
const picked = ref<boolean[]>([]);

async function scan() {
  scanning.value = true;
  found.value = null;
  await banner.guard(async () => {
    const r = await api.post<{ candidates: DspCandidate[]; errors: string[] }>(`/api/releases/${props.catalog}/dsp/scan`);
    if (r.errors.length) banner.show(`Scraper-Fehler: ${r.errors.join(' | ')}`);
    found.value = r.candidates;
    picked.value = r.candidates.map((c) => c.accepted);
  });
  scanning.value = false;
}

const apply = () => banner.guard(async () => {
  const links = (found.value ?? []).filter((_, i) => picked.value[i]).map((x) => ({ name: x.name, url: x.url }));
  await api.post(`/api/releases/${props.catalog}/dsp/apply`, { links });
  banner.show('Links übernommen', false);
  found.value = null;
  emit('changed');
});
</script>
