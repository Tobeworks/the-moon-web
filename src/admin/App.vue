<template>
  <div class="min-h-screen bg-base text-fg flex">

    <!-- Sidebar -->
    <aside class="w-52 flex-shrink-0 border-r border-border flex flex-col">
      <div class="px-5 py-6 border-b border-border">
        <span class="font-mono text-[0.5rem] tracking-[0.3em] uppercase text-accent">// ADMIN</span>
        <div class="font-label font-bold uppercase tracking-[0.1em] text-fg text-sm mt-0.5">The Moon</div>
      </div>

      <nav class="flex-1 py-4 flex flex-col gap-1 px-3">
        <RouterLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-2.5 px-3 py-2 font-mono text-[0.55rem] tracking-[0.2em] uppercase transition-colors rounded-sm"
          :class="isActive(item.to)
            ? 'text-accent bg-accent-dim'
            : 'text-fg-muted hover:text-fg hover:bg-surface'"
        >
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="px-3 py-4 border-t border-border">
        <button
          @click="auth.logout()"
          class="w-full px-3 py-2 font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted hover:text-fg transition-colors text-left"
        >
          Logout
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 min-w-0 p-8 overflow-auto">
      <RouterView />
    </main>

  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router';
import { useAuthStore } from './store/auth';

const auth = useAuthStore();
const route = useRoute();

const nav = [
  { to: '/',           label: 'Dashboard' },
  { to: '/newsletter', label: 'Newsletter' },
  { to: '/promo',      label: 'Promo' },
];

function isActive(to: string) {
  if (to === '/') return route.path === '/';
  return route.path.startsWith(to);
}
</script>
