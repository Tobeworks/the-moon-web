<template>
  <div id="panel-K" class="panel">
    <h2>3 · Konvertieren</h2>
    <div class="row">
      <button class="btn fill" @click="banner.guard(() => job.run(catalog, 'convert', { force }))">Konvertieren</button>
      <label class="note">
        <input v-model="force" type="checkbox" />Überschreiben (--force){{ detail.summary.status.K === 'stale' ? ' — Cover ist neuer als die MP3s' : '' }}
      </label>
    </div>
    <div v-if="detail.files.mp3.length" class="files mono">
      <div v-for="n in detail.files.mp3" :key="n">{{ n }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import type { ReleaseDetail } from '@/api/types';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';

const props = defineProps<{ catalog: string; detail: ReleaseDetail }>();
const banner = useBanner();
const job = useJob();
const force = ref(props.detail.summary.status.K === 'stale');
watch(() => props.detail.summary.status.K, (k) => { if (k === 'stale') force.value = true; });
</script>
