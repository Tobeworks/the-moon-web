import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api, messageOf } from '@/api';
import type { Job } from '@/api/types';
import { useBanner } from './banner';
import { useStudio } from './studio';

/** One background job at a time (the server runs them in a subprocess). Polls its log. */
export const useJob = defineStore('job', () => {
  const job = ref<Job | null>(null);
  const log = ref('Noch kein Job gestartet.');
  const failed = ref(false);
  const finished = ref(0); // counts finished jobs: views watch it and reload their data
  let timer: ReturnType<typeof setTimeout> | undefined;
  let hideTimer: ReturnType<typeof setTimeout> | undefined;

  function follow(id: string, since = 0) {
    clearTimeout(timer);
    clearTimeout(hideTimer);
    if (since === 0) { log.value = ''; failed.value = false; }

    const tick = async () => {
      try {
        const j = await api.get<Job>(`/api/jobs/${id}?since=${since}`);
        if (j.lines.length) log.value += `${j.lines.join('\n')}\n`;
        since = j.next;
        job.value = j;
        if (j.status === 'running') { timer = setTimeout(tick, 500); return; }
        log.value += j.status === 'ok' ? '\n✓ fertig' : j.status === 'cancelled' ? '\n■ abgebrochen' : `\n✗ fehlgeschlagen (Exit ${j.exit_code})`;
        failed.value = j.status === 'failed';
        hideTimer = setTimeout(() => { job.value = null; }, 6000);
        await useStudio().refresh();
        finished.value++;
      } catch (e) {
        useBanner().show(messageOf(e));
      }
    };
    void tick();
  }

  async function cancel() {
    if (!job.value || !confirm('Aufgabe abbrechen? Bereits Erledigtes bleibt erhalten.')) return;
    await api.post(`/api/jobs/${job.value.id}/cancel`);
  }

  /** Picks up a job that was already running when the page opened. */
  function resume(running: { id: string; status: string } | null) {
    if (running?.status === 'running' && job.value?.id !== running.id) follow(running.id, 0);
  }

  /** Starts a CLI step (generate, validate, convert …) for a release and follows its log. */
  async function run(catalog: string, step: string, extra: Record<string, unknown> = {}) {
    const r = await api.post<{ job_id: string }>(`/api/releases/${catalog}/run`, { step, ...extra });
    follow(r.job_id, 0);
  }

  return { job, log, failed, finished, follow, cancel, resume, run };
});
