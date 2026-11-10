<template>
  <div v-if="rows.length" class="panel">
    <h2>Anhören</h2>
    <p class="note">Spielt die WAV-Originale, sonst die 320k-MP3s. Klick auf den Balken springt an die Stelle.</p>
    <div v-for="r in rows" :key="r.t.number" class="track">
      <button class="btn ghost" :disabled="!r.src" :aria-label="`Abspielen: ${r.t.title}`" @click="toggle(r)">{{ playing === r.t.number ? '❚❚' : '▶' }}</button>
      <div>
        {{ r.t.number }}. {{ r.t.title || '—' }}<span class="label" style="margin-left:12px">{{ r.quality }}</span>
        <progress max="100" :value="cur === r.t.number ? pct : 0" :aria-label="`Position: ${r.t.title}`" @click="seek($event, r)" />
      </div>
      <span class="mono note">{{ cur === r.t.number && elapsed ? elapsed : r.t.duration }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import type { ReleaseDetail, Track } from '@/api/types';
import { mmss } from '@/lib/format';

const props = defineProps<{ catalog: string; detail: ReleaseDetail }>();

interface Row { t: Track; src: string | null; quality: string }
const rows = computed<Row[]>(() => (props.detail.release.tracks ?? []).map((t) => {
  const pad = String(t.number).padStart(2, '0');
  const mp3 = props.detail.files.mp3.find((n) => n.startsWith(`320/${pad}_`));
  const wav = !!t.file && props.detail.files.audio.includes(t.file);
  // best quality first: the WAV original, else the 320k MP3
  const src = wav ? `/api/releases/${props.catalog}/media/audio/${encodeURIComponent(t.file)}`
    : mp3 ? `/api/releases/${props.catalog}/media/mp3-320/${encodeURIComponent(mp3.slice(4))}` : null;
  return { t, src, quality: wav ? 'WAV Original' : mp3 ? 'MP3 320k' : 'keine Datei' };
}));

const audio = new Audio();
audio.preload = 'none';
const cur = ref<number | null>(null);
const playing = ref<number | null>(null);
const pct = ref(0);
const elapsed = ref('');

audio.addEventListener('timeupdate', () => {
  if (!audio.duration) return;
  pct.value = (audio.currentTime / audio.duration) * 100;
  elapsed.value = `${mmss(audio.currentTime)} / ${mmss(audio.duration)}`;
});
audio.addEventListener('ended', () => { cur.value = playing.value = null; pct.value = 0; elapsed.value = ''; });

function toggle(r: Row) {
  if (!r.src) return;
  if (cur.value === r.t.number && !audio.paused) { audio.pause(); playing.value = null; return; }
  if (cur.value !== r.t.number) { cur.value = r.t.number; pct.value = 0; elapsed.value = ''; audio.src = r.src; }
  void audio.play();
  playing.value = r.t.number;
}
function seek(e: MouseEvent, r: Row) {
  const bar = e.currentTarget as HTMLElement;
  if (cur.value === r.t.number && audio.duration) audio.currentTime = (e.offsetX / bar.clientWidth) * audio.duration;
}
onBeforeUnmount(() => { audio.pause(); audio.src = ''; });
</script>
