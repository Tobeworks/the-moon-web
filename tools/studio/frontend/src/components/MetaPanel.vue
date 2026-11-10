<template>
  <div id="panel-V" class="panel">
    <h2>2 · Metadaten</h2>
    <div class="form">
      <label><span class="label">Artist</span><input v-model="form.artist" /></label>
      <label><span class="label">Titel</span><input v-model="form.title" /></label>
      <label><span class="label">Release-Datum</span><input v-model="form.release_date" type="date" /></label>
      <label>
        <span class="label">Genre</span>
        <select v-model="form.genre">
          <option v-for="g in genres" :key="g" :value="g">{{ g || '—' }}</option>
        </select>
      </label>
      <label class="wide"><span class="label">Bandcamp-URL</span><input v-model="form.bandcamp" /></label>

      <div v-if="detail.tracks.length" class="wide">
        <span class="label">Tracktitel (bestimmen den Namen der MP3: NN_titel.mp3). Reihenfolge ändern: unter 1 · Assets.</span>
        <div v-for="t in detail.tracks" :key="t.number" class="gap">
          <label>
            <span class="note" style="margin:0">Track {{ t.number }} · Original: {{ t.file }}</span>
            <input v-model="form.titles[t.number]" />
          </label>
          <span class="note mono">→ {{ t.mp3 }}</span>
        </div>
      </div>

      <label class="wide">
        <span class="label">about.md (Releasetext, landet auf der Website)</span>
        <textarea v-model="form.about" />
      </label>
      <div class="wide">
        <input v-model="notes" placeholder="Stichworte für die KI: Stimmung, Idee hinter dem Titel … (optional)" />
        <div class="row gap">
          <button class="btn" :disabled="!ai || writing" @click="write">{{ writing ? 'KI schreibt …' : 'Text mit KI schreiben' }}</button>
          <span class="note" style="margin:0">{{ ai
            ? 'Sendet Titel, Tracknamen, Stichworte, den aktuellen Text und drei ältere Releasetexte an die Anthropic-API. Der Entwurf wird nicht gespeichert.'
            : 'ANTHROPIC_API_KEY fehlt in der .env im Repo-Root.' }}</span>
        </div>
      </div>
    </div>

    <div class="row gap">
      <button class="btn fill" :disabled="saving" @click="emit('save')">Speichern</button>
      <button class="btn" @click="run('generate')">Tracks einlesen</button>
      <button class="btn ghost" @click="run('validate')">Validieren</button>
    </div>
    <p v-for="p in problems" :key="p" class="note" style="color:var(--warn)">! {{ p }}</p>
    <p v-for="w in detail.warnings" :key="w" class="note">Hinweis: {{ w }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { api } from '@/api';
import type { ReleaseDetail } from '@/api/types';
import type { MetaForm } from '@/lib/form';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';
import { useStudio } from '@/stores/studio';

const props = defineProps<{ catalog: string; detail: ReleaseDetail; form: MetaForm; saving: boolean }>();
const emit = defineEmits<{ save: [] }>();
const studio = useStudio();
const banner = useBanner();
const job = useJob();

const notes = ref('');
const writing = ref(false);
const ai = computed(() => studio.state?.ai_configured ?? false);
const genres = computed(() => ['', ...new Set([...(studio.state?.genres ?? []), props.form.genre])].filter((g, i, a) => a.indexOf(g) === i));
const problems = computed(() => (props.detail.summary.status.V === 'open' ? props.detail.problems.validation : []));

const run = (step: string) => banner.guard(() => job.run(props.catalog, step));

async function write() {
  writing.value = true;
  await banner.guard(async () => {
    const r = await api.post<{ text: string }>(`/api/releases/${props.catalog}/about/generate`, { notes: notes.value, draft: props.form.about });
    props.form.about = `# ${props.form.title || props.detail.release.title || ''}\n\n${r.text}`;
    banner.show('Entwurf eingefügt. Prüfen, anpassen und speichern.', false);
  });
  writing.value = false;
}
</script>
