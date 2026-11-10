import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { api } from '@/api';
import type { AppState } from '@/api/types';

export const useStudio = defineStore('studio', () => {
  const state = ref<AppState | null>(null);

  async function refresh() {
    state.value = await api.get<AppState>('/api/state');
  }

  const dirtyCount = computed(() => state.value?.releases.filter((r) => r.status.G === 'warn').length ?? 0);

  return { state, refresh, dirtyCount };
});
