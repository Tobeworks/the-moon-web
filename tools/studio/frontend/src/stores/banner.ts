import { defineStore } from 'pinia';
import { ref } from 'vue';
import { messageOf } from '@/api';

export interface Banner {
  id: number;
  text: string;
  error: boolean;
}

export const useBanner = defineStore('banner', () => {
  const items = ref<Banner[]>([]);
  let seq = 0;

  function show(text: string, error = true) {
    const id = ++seq;
    items.value.push({ id, text, error });
    setTimeout(() => dismiss(id), 8000);
  }
  const dismiss = (id: number) => { items.value = items.value.filter((b) => b.id !== id); };

  /** Runs an async action; any error becomes a banner instead of an unhandled rejection. */
  async function guard<T>(fn: () => Promise<T>): Promise<T | undefined> {
    try {
      return await fn();
    } catch (e) {
      show(messageOf(e));
    }
  }

  return { items, show, dismiss, guard };
});
