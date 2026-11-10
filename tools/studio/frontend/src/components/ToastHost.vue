<template>
  <div class="toast" aria-live="polite">
    <div v-for="b in banner.items" :key="b.id" :class="['banner', b.error ? 'err' : 'ok']" role="status" @click="banner.dismiss(b.id)">{{ b.text }}</div>
  </div>
</template>

<script setup lang="ts">
import { useBanner } from '@/stores/banner';

const banner = useBanner();
</script>
