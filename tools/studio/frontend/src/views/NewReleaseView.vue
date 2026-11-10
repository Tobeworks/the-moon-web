<template>
  <div class="crumb"><RouterLink to="/">Releases</RouterLink> / Neu anlegen</div>
  <h1>Neues Release</h1>
  <div class="panel gap" style="max-width:760px">
    <div class="form">
      <label><span class="label">Katalognummer</span><input v-model="f.catalog" class="mono" /></label>
      <label><span class="label">Release-Datum</span><input v-model="f.release_date" type="date" /></label>
      <label><span class="label">Artist</span><input v-model="f.artist" placeholder="Logic Moon" /></label>
      <label><span class="label">Titel</span><input v-model="f.title" /></label>
    </div>
    <p class="note">Legt den Ordner tmr-NNN-artist-title in the-moon-assets mit audio/ und artwork/ an. Danach Dateien hinzufügen.</p>
    <div class="row gap">
      <button class="btn fill" :disabled="busy" @click="create">Anlegen</button>
      <RouterLink class="btn ghost linkbtn" to="/">Abbrechen</RouterLink>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watchEffect } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '@/api';
import { useBanner } from '@/stores/banner';
import { useStudio } from '@/stores/studio';

const router = useRouter();
const studio = useStudio();
const banner = useBanner();
const f = reactive({ catalog: '', release_date: '', artist: '', title: '' });
const busy = ref(false);

void banner.guard(studio.refresh);
watchEffect(() => { if (!f.catalog && studio.state) f.catalog = studio.state.next_catalog; });

async function create() {
  busy.value = true;
  const r = await banner.guard(() => api.post<{ catalog: string }>('/api/releases', { ...f }));
  busy.value = false;
  if (r) await router.push(`/r/${r.catalog}/A`);
}
</script>
