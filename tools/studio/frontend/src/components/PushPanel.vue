<template>
  <div id="panel-P" class="panel">
    <h2>4 · Push ans CDN</h2>
    <p class="note">{{ st.P === 'ok'
      ? 'Bereits gepusht. Ein erneuter Push behält DSP-Links und manuelle Felder.'
      : 'Lädt MP3s und Artwork hoch und schreibt den Eintrag in data/releases.json (mit Backup).' }}</p>
    <div class="row gap">
      <button class="btn danger" :disabled="detail.problems.push.length > 0 || !studio.state?.cdn_configured" @click="banner.guard(async () => { await dialog?.open(); })">Freigeben und hochladen …</button>
    </div>
    <p v-for="p in detail.problems.push" :key="p" class="note" style="color:var(--warn)">! {{ p }}</p>
    <p v-if="studio.state && !studio.state.cdn_configured" class="note">In .env fehlt: {{ studio.state.cdn_missing.join(', ') }}</p>
    <p v-if="st.G === 'warn'" class="note" style="color:var(--warn)">! releases.json nicht committet — Commit-Feld oben auf der Seite.</p>
    <PushDialog ref="dialog" :catalog="catalog" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ReleaseDetail } from '@/api/types';
import PushDialog from '@/components/PushDialog.vue';
import { useBanner } from '@/stores/banner';
import { useStudio } from '@/stores/studio';

const props = defineProps<{ catalog: string; detail: ReleaseDetail }>();
const studio = useStudio();
const banner = useBanner();
const dialog = ref<InstanceType<typeof PushDialog>>();
const st = computed(() => props.detail.summary.status);
</script>
