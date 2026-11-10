<template>
  <dialog ref="dlg" class="lightbox" @close="src = null" @click="onClick">
    <template v-if="src">
      <button class="x" aria-label="Schließen" @click="dlg?.close()">×</button>
      <img :src="src" alt="Cover" @click="dlg?.close()" />
    </template>
  </dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const src = defineModel<string | null>({ default: null });
const dlg = ref<HTMLDialogElement>();

watch(src, (v) => {
  if (v && !dlg.value?.open) dlg.value?.showModal();
  else if (!v && dlg.value?.open) dlg.value.close();
});
const onClick = (e: MouseEvent) => { if (e.target === dlg.value) dlg.value?.close(); };
</script>
