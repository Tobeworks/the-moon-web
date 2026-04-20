<template>
  <div class="flex flex-col gap-6">

    <!-- Back -->
    <RouterLink to="/newsletter" class="font-mono text-[0.5rem] tracking-[0.2em] uppercase text-fg-muted hover:text-fg transition-colors">
      ← All Campaigns
    </RouterLink>

    <div v-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-muted">Loading…</div>
    <div v-else-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</div>

    <template v-else>
      <!-- Subject -->
      <div class="flex flex-col gap-1.5">
        <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Subject</label>
        <input v-model="subject" type="text" class="tmr-input w-full" :disabled="status === 'sent'" />
      </div>

      <!-- Editor + Preview -->
      <div class="flex flex-col gap-1.5">
        <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
          Content
          <span class="text-fg-muted normal-case tracking-normal" style="font-size:0.6rem;">
            (Markdown — header &amp; footer added automatically)
          </span>
        </label>
        <div class="grid grid-cols-2 gap-4">
          <textarea
            v-model="bodyMd"
            rows="20"
            class="tmr-input w-full font-mono text-[0.75rem] resize-y"
            placeholder="## Hello&#10;&#10;New release out now."
            :disabled="status === 'sent'"
          ></textarea>
          <div class="border border-border p-4 bg-surface text-fg-dim text-[0.8rem] leading-relaxed overflow-auto preview-content" v-html="renderedHtml"></div>
        </div>
      </div>

      <!-- Sent info -->
      <div v-if="status === 'sent'" class="border border-border p-4 flex flex-col gap-1">
        <span class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-accent">// SENT</span>
        <p class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-muted">
          {{ sentCount }} sent · {{ failedCount }} failed
          <template v-if="sentAt"> · {{ new Date(sentAt).toLocaleString('de-DE') }}</template>
        </p>
      </div>

      <!-- Actions -->
      <div v-if="status !== 'sent'" class="flex items-center gap-4 flex-wrap">
        <button @click="save" :disabled="saving" class="btn btn--muted">
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <button @click="sendTest" :disabled="testing" class="btn btn--muted">
          {{ testing ? 'Sending…' : 'Send test' }}
        </button>
        <button @click="send" :disabled="sending" class="btn btn--primary">
          {{ sending ? 'Sending…' : `Send to ${subscriberCount} subscriber${subscriberCount !== 1 ? 's' : ''}` }}
        </button>
        <span class="font-mono text-[0.55rem] tracking-[0.2em] uppercase" :class="msgColor">{{ msg }}</span>
      </div>
    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { marked } from 'marked';
import { adminApi } from '../../../lib/admin-api';

const route = useRoute();
const id    = route.params.id as string;

const loading      = ref(true);
const loadError    = ref('');
const subscriberCount = ref(0);
const subject      = ref('');
const bodyMd       = ref('');
const status       = ref('draft');
const sentCount    = ref(0);
const failedCount  = ref(0);
const sentAt       = ref('');
const saving       = ref(false);
const sending      = ref(false);
const testing      = ref(false);
const msg          = ref('');
const msgColor     = ref('text-fg-muted');

const renderedHtml = computed(() => marked.parse(bodyMd.value) as string);

onMounted(async () => {
  try {
    const [campaign, campaigns] = await Promise.all([
      adminApi.getCampaign(id),
      fetch('/api/admin/newsletter/campaigns').then(r => r.json()),
    ]);
    subject.value      = campaign.subject;
    bodyMd.value       = campaign.body_md ?? campaign.body_text ?? '';
    status.value       = campaign.status;
    sentCount.value    = campaign.sent_count ?? 0;
    failedCount.value  = campaign.failed_count ?? 0;
    sentAt.value       = campaign.sent_at ?? '';

    // Get subscriber count from index page data
    const res = await fetch('/api/admin/newsletter/campaigns');
    const data = await res.json();
    subscriberCount.value = data.subscriberCount ?? 0;
  } catch (e) {
    loadError.value = 'Failed to load campaign.';
  } finally {
    loading.value = false;
  }
});

async function save() {
  saving.value = true;
  msg.value = '';
  try {
    const html = await marked.parse(bodyMd.value);
    await adminApi.updateCampaign(id, {
      subject: subject.value,
      body_html: html,
      body_md: bodyMd.value,
      body_text: bodyMd.value,
    });
    msg.value = 'Saved.';
    msgColor.value = 'text-fg-muted';
  } catch {
    msg.value = 'Error saving.';
    msgColor.value = 'text-red-400';
  } finally {
    saving.value = false;
    setTimeout(() => { msg.value = ''; }, 2000);
  }
}

async function sendTest() {
  const email = prompt('Send test to:', 'hallo@tobeworks.de');
  if (!email) return;
  testing.value = true;
  msg.value = '';
  try {
    await save();
    const result = await adminApi.testCampaign(id, email);
    msg.value = result.ok ? `Test sent to ${email}` : 'Error: ' + (result.error ?? 'unknown');
    msgColor.value = result.ok ? 'text-fg-muted' : 'text-red-400';
  } finally {
    testing.value = false;
  }
}

async function send() {
  if (!confirm(`Send to ${subscriberCount.value} subscriber(s)? This cannot be undone.`)) return;
  sending.value = true;
  try {
    const result = await adminApi.sendCampaign(id);
    if (result.ok) {
      status.value      = 'sent';
      sentCount.value   = result.sent;
      failedCount.value = result.failed;
      sentAt.value      = new Date().toISOString();
      msg.value         = `Done — ${result.sent} sent, ${result.failed} failed`;
      msgColor.value    = 'text-accent';
    } else {
      msg.value      = 'Error: ' + (result.error ?? 'unknown');
      msgColor.value = 'text-red-400';
    }
  } finally {
    sending.value = false;
  }
}
</script>

<style>
.preview-content h1 { font-size: 1.3rem; font-weight: 700; margin: 0 0 1rem; color: #E8E4D8; letter-spacing: 0.06em; }
.preview-content h2 { font-size: 1rem; font-weight: 700; margin: 1.5rem 0 0.75rem; color: #E8E4D8; }
.preview-content h3 { font-size: 0.85rem; font-weight: 600; margin: 1.25rem 0 0.5rem; color: rgba(232,228,216,0.7); }
.preview-content p  { margin: 0 0 1rem; }
.preview-content a  { color: #C4B98A; text-decoration: underline; }
.preview-content strong { color: #E8E4D8; font-weight: 700; }
.preview-content ul, .preview-content ol { padding-left: 1.5rem; margin: 0 0 1rem; list-style: revert; }
.preview-content li { margin-bottom: 0.25rem; display: list-item; }
.preview-content hr { border: none; border-top: 1px solid rgba(196,185,138,0.12); margin: 1.5rem 0; }
</style>
