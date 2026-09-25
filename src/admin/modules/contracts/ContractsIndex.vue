<template>
  <div class="flex flex-col gap-6">

    <!-- Tab switcher -->
    <div class="flex gap-0 border border-border">
      <button
        @click="tab = 'contracts'"
        :class="tab === 'contracts' ? 'bg-surface text-fg' : 'text-fg-dim hover:text-fg'"
        class="flex-1 px-5 py-3 font-mono text-[0.6rem] tracking-[0.3em] uppercase transition-colors cursor-pointer"
      >Contracts</button>
      <button
        @click="tab = 'templates'; loadTemplates()"
        :class="tab === 'templates' ? 'bg-surface text-fg' : 'text-fg-dim hover:text-fg'"
        class="flex-1 px-5 py-3 font-mono text-[0.6rem] tracking-[0.3em] uppercase border-l border-border transition-colors cursor-pointer"
      >Templates</button>
    </div>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Contracts                                                         -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="tab === 'contracts'">

      <div class="flex items-start justify-between gap-4 flex-wrap">
        <div class="flex flex-col gap-1">
          <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// CONTRACTS</span>
          <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Contracts</h1>
          <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
            {{ contracts.length }} contract{{ contracts.length !== 1 ? 's' : '' }}
          </p>
        </div>
        <button @click="showNew = !showNew" class="btn btn--primary">New Contract</button>
      </div>

      <!-- New contract form -->
      <div v-if="showNew" class="border border-border p-5 flex flex-col gap-4">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// NEW_CONTRACT</span>

        <div v-if="templates.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
          No templates yet — create one under the Templates tab first.
        </div>

        <template v-else>
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Release *</label>
              <select v-model="form.catalog" @change="applyReleaseDefaults" class="tmr-input w-full">
                <option value="">— select release —</option>
                <option v-for="r in releases" :key="r.catalog" :value="r.catalog">
                  {{ r.catalog }} — {{ r.artist }} — {{ r.title }}
                </option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Template *</label>
              <select v-model="form.template" class="tmr-input w-full">
                <option value="">— select template —</option>
                <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
                Artist Name *
                <span class="text-fg-dim normal-case tracking-normal" style="font-size:0.6rem;">(filled in from the release, edit if it differs)</span>
              </label>
              <input v-model="form.artist_name" type="text" class="tmr-input w-full" placeholder="Logic Moon" />
            </div>
            <div class="flex flex-col gap-1.5">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Artist Email (optional)</label>
              <input v-model="form.artist_email" type="email" class="tmr-input w-full" placeholder="artist@example.com" />
            </div>
            <div class="flex flex-col gap-1.5 sm:col-span-2">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Artist Address (optional)</label>
              <textarea v-model="form.artist_address" rows="2" class="tmr-input w-full resize-y" placeholder="Musterstraße 1&#10;12345 Berlin, Germany"></textarea>
            </div>
          </div>

          <!-- Extra placeholders from the chosen template — artist_name/release_title/
               catalog/release_date are already covered above, only custom ones show here. -->
          <div v-if="customPlaceholders.length" class="flex flex-col gap-3">
            <span class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Template Fields</span>
            <div v-for="key in customPlaceholders" :key="key" class="flex flex-col gap-1.5">
              <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">{{ key }} *</label>
              <input v-model="form.values[key]" type="text" class="tmr-input w-full" />
            </div>
          </div>

          <div class="flex items-center gap-4 flex-wrap">
            <button @click="create" :disabled="creating || !canCreate" class="btn btn--primary">
              {{ creating ? 'Creating…' : 'Create & Send' }}
            </button>
            <button @click="cancelNew" class="btn btn--muted">Cancel</button>
            <span v-if="createError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ createError }}</span>
          </div>

          <p v-if="lastResult" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim border-t border-border pt-4">
            {{ lastResult.mailed ? '✉ Signing link sent by email.' : 'No email on file — copy the link below.' }}
          </p>
        </template>
      </div>

      <!-- Error / Loading / Empty -->
      <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>
      <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Loading…</p>
      <p v-else-if="contracts.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">No contracts yet.</p>

      <!-- List -->
      <div v-else class="flex flex-col border border-border">
        <div
          v-for="c in contracts"
          :key="c.id"
          class="flex items-center justify-between gap-4 px-5 py-4 border-b border-border last:border-b-0 flex-wrap"
        >
          <div class="flex flex-col gap-1 min-w-0">
            <span class="font-label font-semibold text-[0.85rem] tracking-[0.06em] text-fg">{{ c.artist_name }}</span>
            <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
              {{ c.catalog }}{{ c.artist_email ? ` · ${c.artist_email}` : '' }}
            </span>
          </div>
          <div class="flex items-center gap-2 flex-shrink-0">
            <span v-if="c.signed_at" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
              Signed {{ new Date(c.signed_at).toLocaleDateString('en-GB') }}
            </span>
            <template v-else>
              <button
                @click="resend(c)"
                :disabled="resendingId === c.id"
                class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors disabled:cursor-not-allowed"
              >{{ resendingId === c.id ? '…' : (c.artist_email ? 'Resend' : 'Get Link') }}</button>
              <button
                v-if="linkFor[c.id]"
                @click="copyLink(c.id)"
                class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors"
              >{{ copiedIds.has(c.id) ? '✓' : 'Copy' }}</button>
              <button
                @click="deleteContractEntry(c)"
                :disabled="deletingId === c.id"
                class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-red-400 hover:border-red-400/40 transition-colors disabled:cursor-not-allowed"
              >{{ deletingId === c.id ? '…' : 'Delete' }}</button>
            </template>
          </div>
        </div>
      </div>

    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- TAB: Templates                                                         -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <template v-if="tab === 'templates'">

      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div class="flex flex-col gap-1">
          <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// TEMPLATES</span>
          <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Contract Templates</h1>
        </div>
        <button @click="startNewTemplate" class="btn btn--primary">New Template</button>
      </div>

      <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
        Placeholders: <code class="text-accent">{{ braced('artist_name') }}</code>
        <code class="text-accent">{{ braced('release_title') }}</code>
        <code class="text-accent">{{ braced('catalog') }}</code>
        <code class="text-accent">{{ braced('release_date') }}</code>
        are filled in automatically. Any other <code class="text-accent">{{ braced('name') }}</code>
        becomes a field in the contract form.
      </p>

      <div v-if="templatesLoading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Loading…</div>

      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-[220px_1fr]">
        <!-- List -->
        <div class="flex flex-col gap-1">
          <button
            v-for="t in templates"
            :key="t.id"
            @click="selectTemplate(t)"
            class="text-left px-3 py-2 font-mono text-[0.6rem] tracking-[0.1em] border cursor-pointer transition-colors"
            :class="editingTemplate?.id === t.id ? 'border-accent text-accent' : 'border-border text-fg-dim hover:text-fg'"
          >{{ t.name }}</button>
          <p v-if="templates.length === 0" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">No templates yet.</p>
        </div>

        <!-- Editor -->
        <div v-if="editingTemplate" class="flex flex-col gap-4">
          <div class="flex flex-col gap-1.5">
            <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Name</label>
            <input v-model="editingTemplate.name" type="text" class="tmr-input w-full" placeholder="Standard Release Agreement" />
          </div>

          <div class="flex flex-col gap-1.5">
            <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Content (Markdown)</label>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <textarea
                v-model="editingTemplate.body_md"
                rows="18"
                class="tmr-input w-full font-mono text-[0.75rem] resize-y"
                placeholder="# Release Agreement&#10;&#10;Between The Moon Records and {{artist_name}}..."
              ></textarea>
              <div class="border border-border p-4 bg-surface text-fg-dim text-[0.8rem] leading-relaxed overflow-auto preview-content" v-html="templatePreview"></div>
            </div>
          </div>

          <div class="flex items-center gap-4 flex-wrap">
            <button @click="saveTemplate" :disabled="savingTemplate || !editingTemplate.name.trim() || !editingTemplate.body_md.trim()" class="btn btn--primary">
              {{ savingTemplate ? 'Saving…' : 'Save' }}
            </button>
            <button v-if="editingTemplate.id" @click="deleteTemplateEntry" class="btn btn--muted">Delete</button>
            <span v-if="templateError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ templateError }}</span>
          </div>
        </div>
      </div>

    </template>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { marked } from 'marked';
import {
  contractsApi, contractTemplatesApi,
  type Contract, type ContractTemplate,
} from '../../../lib/admin-api';
import { findPlaceholders } from '../../../lib/contractTemplate';
import releasesJson from '../../../../the-moon-os/data/releases.json';

interface Release { catalog: string; artist: string; title: string; }
const releases: Release[] = (releasesJson as any).releases.map((r: any) => ({
  catalog: r.catalog,
  artist: r.artist,
  title: r.title,
}));

const FIXED_PLACEHOLDERS = ['artist_name', 'artist_address', 'release_title', 'catalog', 'release_date'];

// Vue's template tokenizer reads the first `}}` it finds as the interpolation's own
// closer — a literal '{{name}}' string inline in the template breaks on itself.
// Building the braces here sidesteps that.
const braced = (name: string) => `{{${name}}}`;

const tab = ref<'contracts' | 'templates'>('contracts');

// ── Contracts ────────────────────────────────────────────────────────────────
const contracts   = ref<Contract[]>([]);
const templates   = ref<ContractTemplate[]>([]);
const loading     = ref(true);
const loadError   = ref('');
const showNew     = ref(false);
const creating    = ref(false);
const createError = ref('');
const lastResult  = ref<{ mailed: boolean } | null>(null);

const resendingId = ref('');
const deletingId  = ref('');
const linkFor      = ref<Record<string, string>>({});
const copiedIds    = ref(new Set<string>());

const emptyForm = () => ({ catalog: '', template: '', artist_name: '', artist_email: '', artist_address: '', values: {} as Record<string, string> });
const form = ref(emptyForm());

const customPlaceholders = computed(() => {
  const t = templates.value.find((x) => x.id === form.value.template);
  if (!t) return [];
  return findPlaceholders(t.body_md).filter((k) => !FIXED_PLACEHOLDERS.includes(k));
});

const canCreate = computed(() =>
  form.value.catalog.trim() &&
  form.value.template.trim() &&
  form.value.artist_name.trim() &&
  customPlaceholders.value.every((k) => form.value.values[k]?.trim()),
);

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    [contracts.value, templates.value] = await Promise.all([
      contractsApi.getAll(),
      contractTemplatesApi.getAll(),
    ]);
  } catch {
    loadError.value = 'Failed to load contracts.';
  } finally {
    loading.value = false;
  }
}

function cancelNew() {
  showNew.value = false;
  createError.value = '';
  lastResult.value = null;
  form.value = emptyForm();
}

// Artist Name defaults to the release's own artist — usually correct as-is,
// but stays editable for collaborations filed under a different name.
function applyReleaseDefaults() {
  const release = releases.find((r) => r.catalog === form.value.catalog);
  if (release) form.value.artist_name = release.artist;
}

async function create() {
  if (!canCreate.value) return;
  creating.value = true;
  createError.value = '';
  lastResult.value = null;
  try {
    const result = await contractsApi.create({
      template: form.value.template,
      catalog: form.value.catalog,
      artist_name: form.value.artist_name.trim(),
      artist_email: form.value.artist_email.trim() || undefined,
      artist_address: form.value.artist_address.trim() || undefined,
      values: form.value.values,
    });
    lastResult.value = { mailed: result.mailed };
    await load();
  } catch (e: any) {
    createError.value = e.message ?? 'Failed to create contract.';
  } finally {
    creating.value = false;
  }
}

async function resend(contract: Contract) {
  resendingId.value = contract.id;
  try {
    const result = await contractsApi.resend(contract.id);
    linkFor.value = { ...linkFor.value, [contract.id]: result.signing_url };
  } catch {
    // surfaced implicitly — no link/mailed state changes
  } finally {
    resendingId.value = '';
  }
}

async function deleteContractEntry(contract: Contract) {
  if (!confirm(`Delete the contract for "${contract.artist_name}"?`)) return;
  deletingId.value = contract.id;
  try {
    await contractsApi.delete(contract.id);
    await load();
  } catch (e: any) {
    alert(e.message ?? 'Failed to delete contract.');
  } finally {
    deletingId.value = '';
  }
}

async function copyLink(id: string) {
  const url = linkFor.value[id];
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    copiedIds.value = new Set(copiedIds.value).add(id);
    setTimeout(() => {
      const next = new Set(copiedIds.value);
      next.delete(id);
      copiedIds.value = next;
    }, 1500);
  } catch {
    // clipboard not available
  }
}

// ── Templates ─────────────────────────────────────────────────────────────────
const templatesLoading = ref(false);
const editingTemplate  = ref<{ id?: string; name: string; body_md: string } | null>(null);
const savingTemplate   = ref(false);
const templateError    = ref('');
let templatesLoaded = false;

async function loadTemplates() {
  if (templatesLoaded) return;
  templatesLoading.value = true;
  try {
    templates.value = await contractTemplatesApi.getAll();
    templatesLoaded = true;
  } finally {
    templatesLoading.value = false;
  }
}

function selectTemplate(t: ContractTemplate) {
  editingTemplate.value = { id: t.id, name: t.name, body_md: t.body_md };
  templateError.value = '';
}

function startNewTemplate() {
  tab.value = 'templates';
  editingTemplate.value = { name: '', body_md: '' };
  templateError.value = '';
}

const templatePreview = computed(() =>
  editingTemplate.value ? marked.parse(editingTemplate.value.body_md) as string : '',
);

async function saveTemplate() {
  if (!editingTemplate.value) return;
  savingTemplate.value = true;
  templateError.value = '';
  try {
    const { id, name, body_md } = editingTemplate.value;
    if (id) {
      await contractTemplatesApi.update(id, { name, body_md });
    } else {
      await contractTemplatesApi.create({ name, body_md });
    }
    templatesLoaded = false;
    await loadTemplates();
    const saved = templates.value.find((t) => t.name === name);
    if (saved) selectTemplate(saved);
  } catch (e: any) {
    templateError.value = e.message ?? 'Failed to save template.';
  } finally {
    savingTemplate.value = false;
  }
}

async function deleteTemplateEntry() {
  if (!editingTemplate.value?.id) return;
  if (!confirm(`Delete template "${editingTemplate.value.name}"?`)) return;
  try {
    await contractTemplatesApi.delete(editingTemplate.value.id);
    editingTemplate.value = null;
    templatesLoaded = false;
    await loadTemplates();
  } catch (e: any) {
    templateError.value = e.message ?? 'Failed to delete template.';
  }
}

onMounted(load);
</script>

<style>
.preview-content h1 { font-size: 1.2rem; font-weight: 700; margin: 0 0 1rem; color: #E8E4D8; letter-spacing: 0.04em; }
.preview-content h2 { font-size: 1rem; font-weight: 700; margin: 1.5rem 0 0.75rem; color: #E8E4D8; }
.preview-content h3 { font-size: 0.9rem; font-weight: 600; margin: 1.25rem 0 0.5rem; color: rgba(232,228,216,0.7); }
.preview-content p  { margin: 0 0 1rem; }
.preview-content strong { color: #E8E4D8; font-weight: 700; }
.preview-content ul, .preview-content ol { padding-left: 1.5rem; margin: 0 0 1rem; list-style: revert; }
.preview-content li { margin-bottom: 0.25rem; display: list-item; }
.preview-content hr { border: none; border-top: 1px solid rgba(196,185,138,0.12); margin: 1.5rem 0; }
</style>
