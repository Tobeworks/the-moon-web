<template>
  <div class="pipe">
    <span v-for="k in STEPS" :key="k" :class="['step', k === row.next ? 'next' : row.status[k]]" :title="`${STEP_NAMES[k]}: ${row.status[k]}`">{{ k }}{{ GLYPH[row.status[k]] }}</span>
  </div>
</template>

<script setup lang="ts">
import type { ReleaseRow } from '@/api/types';
import { GLYPH, STEP_NAMES, STEPS } from '@/lib/format';

defineProps<{ row: ReleaseRow }>();
</script>
