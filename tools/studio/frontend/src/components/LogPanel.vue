<template>
  <div class="panel">
    <h2>Protokoll</h2>
    <div ref="box" :class="['log mono', job.failed && 'fail']">{{ job.log }}</div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from 'vue';
import { useJob } from '@/stores/job';

const job = useJob();
const box = ref<HTMLElement>();
const toEnd = async () => { await nextTick(); if (box.value) box.value.scrollTop = box.value.scrollHeight; };
watch(() => job.log, toEnd);
onMounted(toEnd);
</script>
