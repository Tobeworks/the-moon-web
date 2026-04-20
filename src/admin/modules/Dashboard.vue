<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-col gap-1">
      <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// SYSTEM_STATUS</span>
      <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Dashboard</h1>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <RouterLink to="/newsletter" class="border border-border p-5 flex flex-col gap-1 hover:border-accent transition-colors">
        <span class="font-mono text-[0.5rem] tracking-[0.2em] uppercase text-accent">// MODULE</span>
        <span class="font-label font-bold uppercase tracking-[0.08em] text-fg">Newsletter</span>
        <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-muted">Campaigns &amp; Subscribers</span>
      </RouterLink>
      <RouterLink to="/promo" class="border border-border p-5 flex flex-col gap-1 hover:border-accent transition-colors">
        <span class="font-mono text-[0.5rem] tracking-[0.2em] uppercase text-accent">// MODULE</span>
        <span class="font-label font-bold uppercase tracking-[0.08em] text-fg">Promo</span>
        <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-muted">Promo Links &amp; Feedback</span>
      </RouterLink>
    </div>
  </div>
</template>
