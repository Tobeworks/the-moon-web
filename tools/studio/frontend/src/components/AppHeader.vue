<template>
  <header class="top">
    <div class="logo">The Moon <span>/ Studio</span></div>
    <nav class="main">
      <RouterLink to="/" active-class="" exact-active-class="on">Übersicht</RouterLink>
      <RouterLink to="/new" exact-active-class="on">Neu anlegen</RouterLink>
    </nav>
    <div class="spacer" />
    <template v-if="studio.state">
      <div :class="['chip mono', studio.dirtyCount ? 'warn' : 'ok']">
        {{ studio.dirtyCount ? `! ${studio.dirtyCount} Release(s) nicht committet` : '✓ releases.json committet' }}
      </div>
      <div :class="['chip mono', studio.state.cdn_configured ? 'ok' : 'warn']">
        {{ studio.state.cdn_configured ? '✓ CDN konfiguriert' : '! CDN: .env unvollständig' }}
      </div>
    </template>
  </header>
</template>

<script setup lang="ts">
import { useStudio } from '@/stores/studio';

const studio = useStudio();
</script>
