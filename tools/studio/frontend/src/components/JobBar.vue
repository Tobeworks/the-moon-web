<template>
  <div v-if="store.job" class="jobbar" aria-live="polite">
    <div class="jobbar-in">
      <span class="mono">{{ GLYPH[j.status] }}</span>
      <span>{{ j.label }} · {{ STATE[j.status] }}</span>
      <progress max="100" :value="j.status === 'running' ? (j.progress ? j.progress.pct : undefined) : 100" :aria-label="`Fortschritt ${j.label}`" />
      <span class="mono">{{ j.progress ? `${j.progress.done}/${j.progress.total} · ${j.progress.pct} %` : '' }}</span>
      <button v-if="j.status === 'running'" class="btn ghost" @click="banner.guard(store.cancel)">Abbrechen</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { JobStatus } from '@/api/types';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';

const store = useJob();
const banner = useBanner();
const j = computed(() => store.job!);
const STATE: Record<JobStatus, string> = { running: 'läuft', ok: 'fertig', failed: 'fehlgeschlagen', cancelled: 'abgebrochen' };
const GLYPH: Record<JobStatus, string> = { running: '⟳', ok: '✓', failed: '✗', cancelled: '■' };
</script>
