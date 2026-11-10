<template>
  <dialog ref="dlg">
    <template v-if="p">
      <h2>{{ catalog }} ans CDN senden</h2>
      <p class="note">Ziel: {{ p.target }}</p>
      <p class="mono">{{ p.files.length }} Dateien · {{ fmtMB(p.total_bytes) }}</p>
      <div class="files mono" style="max-height:220px;overflow:auto">
        <div v-for="f in p.files" :key="f.name"><span>{{ f.name }}</span><span>{{ fmtMB(f.size) }}</span></div>
      </div>
      <p v-for="x in p.problems" :key="x" class="problem">! {{ x }}</p>
      <p v-for="x in p.warnings" :key="x" class="note">Hinweis: {{ x }}</p>
      <label class="gap" style="display:block">
        <span class="label">Zur Bestätigung {{ catalog }} eintippen</span>
        <input v-model="typed" class="mono" :placeholder="catalog" />
      </label>
      <div class="row gap">
        <button class="btn danger" :disabled="!allowed || busy" @click="go">Jetzt hochladen</button>
        <button class="btn ghost" @click="dlg?.close()">Abbrechen</button>
      </div>
    </template>
  </dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { api } from '@/api';
import type { PushPreview } from '@/api/types';
import { fmtMB } from '@/lib/format';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';

const props = defineProps<{ catalog: string }>();
const dlg = ref<HTMLDialogElement>();
const p = ref<PushPreview | null>(null);
const typed = ref('');
const busy = ref(false);
const job = useJob();
const banner = useBanner();

const allowed = computed(() => !!p.value && p.value.problems.length === 0 && typed.value.trim().toUpperCase() === props.catalog);

async function open() {
  typed.value = '';
  p.value = await api.get<PushPreview>(`/api/releases/${props.catalog}/push-preview`);
  dlg.value?.showModal();
}

async function go() {
  busy.value = true;
  await banner.guard(async () => {
    const r = await api.post<{ job_id: string }>(`/api/releases/${props.catalog}/push`, { confirm: typed.value });
    dlg.value?.close();
    job.follow(r.job_id, 0);
  });
  busy.value = false;
}

defineExpose({ open });
</script>
