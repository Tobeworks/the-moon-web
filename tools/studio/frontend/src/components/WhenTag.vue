<template><span :class="['tag', w.up && 'up']">{{ w.text }}</span></template>

<script setup lang="ts">
import { computed } from 'vue';
import type { ReleaseRow } from '@/api/types';
import { whenOf } from '@/lib/format';

const props = defineProps<{ row: ReleaseRow }>();
const w = computed(() => whenOf(props.row));
</script>
