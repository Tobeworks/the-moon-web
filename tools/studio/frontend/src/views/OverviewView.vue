<template>
  <CommitBar />
  <template v-if="s">
    <div class="row">
      <div><div class="label">Katalog</div><h1>Releases</h1></div>
      <div class="spacer" />
      <RouterLink class="btn fill linkbtn" to="/new">+ Neues Release</RouterLink>
    </div>
    <div v-if="!s.cdn_configured" class="banner gap">Push gesperrt: in .env fehlt {{ s.cdn_missing.join(', ') }}.</div>
    <div class="stats">
      <div class="stat"><span class="label">Gesamt</span><b>{{ s.releases.length }}</b></div>
      <div class="stat"><span class="label">Demnächst</span><b>{{ s.releases.filter((r) => r.upcoming).length }}</b></div>
      <div :class="['stat', open && 'warn']"><span class="label">Offene Schritte</span><b>{{ open }}</b></div>
      <div :class="['stat', noDsp && 'warn']"><span class="label">Ohne DSP-Links</span><b>{{ noDsp }}</b></div>
    </div>
    <table>
      <thead><tr class="label"><th>Katalog</th><th>Titel</th><th>Release</th><th>Ablauf</th><th>Nächster Schritt</th></tr></thead>
      <tbody>
        <tr v-for="r in s.releases" :key="r.catalog" class="click" @click="router.push(`/r/${r.catalog}`)">
          <td class="mono">{{ r.catalog }}</td>
          <td>{{ r.title || '—' }}<br /><span class="label">{{ r.artist }}</span></td>
          <td><WhenTag :row="r" /><br /><span class="mono note">{{ fmtDate(r.release_date) }}</span></td>
          <td><PipeSteps :row="r" /></td>
          <td>
            <RouterLink v-if="r.next" class="btn linkbtn" :to="`/r/${r.catalog}/${r.next}`" @click.stop>{{ NEXT_LABEL[r.next] }}</RouterLink>
            <span v-else class="label">fertig</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div class="legend">
      <span v-for="k in STEPS" :key="k">{{ k }} {{ STEP_NAMES[k] }}</span>
      <span>✓ erledigt · ! prüfen · ↻ veraltet · – nicht anwendbar</span>
    </div>
    <p class="note">Alle Werte werden bei jedem Laden aus data/releases.json, den Asset-Ordnern und git berechnet.</p>
  </template>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import CommitBar from '@/components/CommitBar.vue';
import PipeSteps from '@/components/PipeSteps.vue';
import WhenTag from '@/components/WhenTag.vue';
import { fmtDate, NEXT_LABEL, STEP_NAMES, STEPS } from '@/lib/format';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';
import { useStudio } from '@/stores/studio';

const router = useRouter();
const studio = useStudio();
const job = useJob();
const banner = useBanner();
const s = computed(() => studio.state);
const open = computed(() => s.value?.releases.filter((r) => r.next && r.next !== 'D').length ?? 0);
const noDsp = computed(() => s.value?.releases.filter((r) => r.status.D === 'open' && r.status.P === 'ok').length ?? 0);

onMounted(() => banner.guard(studio.refresh));
watch(() => job.finished, () => banner.guard(studio.refresh));
</script>
