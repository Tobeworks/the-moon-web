<template>
  <AppHeader />
  <JobBar />
  <main><RouterView /></main>
  <ToastHost />
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import AppHeader from '@/components/AppHeader.vue';
import JobBar from '@/components/JobBar.vue';
import ToastHost from '@/components/ToastHost.vue';
import { useBanner } from '@/stores/banner';
import { useJob } from '@/stores/job';
import { useStudio } from '@/stores/studio';

const studio = useStudio();
const job = useJob();
const banner = useBanner();

onMounted(() => banner.guard(async () => {
  await studio.refresh();
  job.resume(studio.state?.job ?? null);
}));
</script>
