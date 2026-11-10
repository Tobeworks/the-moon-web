<template>
  <div v-if="studio.state?.releases_dirty" class="panel">
    <h2>releases.json committen</h2>
    <p class="note">Committet nur data/releases.json, lokal. Pushen machst du selbst im Terminal (git push).</p>
    <div class="row gap">
      <div style="flex:1;min-width:280px"><input v-model="message" class="mono" /></div>
      <button class="btn fill" :disabled="busy" @click="commit">Committen</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { api } from '@/api';
import { useBanner } from '@/stores/banner';
import { useStudio } from '@/stores/studio';

const studio = useStudio();
const banner = useBanner();
const message = ref('');
const busy = ref(false);

watch(() => studio.state?.releases, (rs) => {
  if (message.value || !rs) return;
  const warn = rs.filter((r) => r.status.G === 'warn').map((r) => r.catalog.toLowerCase());
  message.value = `feat: ${warn.join(', ') || 'releases'} release`;
}, { immediate: true });

async function commit() {
  busy.value = true;
  await banner.guard(async () => {
    const r = await api.post<{ commit: string }>('/api/git/commit', { message: message.value });
    banner.show(`Committet (${r.commit}). Jetzt im Terminal: git push`, false);
    message.value = '';
    await studio.refresh();
  });
  busy.value = false;
}
</script>
