<template>
  <div class="flex flex-col gap-6">

    <!-- Header -->
    <div class="flex items-start justify-between gap-4 flex-wrap">
      <div class="flex flex-col gap-1">
        <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// SPLIT_SHEETS</span>
        <h1 class="font-label font-bold uppercase tracking-[0.08em] text-xl text-fg">Split Sheets</h1>
        <p class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
          {{ sheets.length }} release{{ sheets.length !== 1 ? 's' : '' }}
        </p>
      </div>
      <button @click="showNew = !showNew" class="btn btn--primary">New Split Sheet</button>
    </div>

    <!-- New split sheet form -->
    <div v-if="showNew" class="border border-border p-5 flex flex-col gap-4">
      <span class="font-mono text-[0.6rem] tracking-[0.3em] uppercase text-accent">// NEW_SPLIT_SHEET</span>

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
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">
            Label Project *
            <span class="text-fg-dim normal-case tracking-normal" style="font-size:0.6rem;">(the artist/imprint this is filed under — filled in from the release, edit if it differs)</span>
          </label>
          <input v-model="form.label_project" type="text" class="tmr-input w-full" placeholder="Logic Moon" />
        </div>
        <div class="flex flex-col gap-1.5 sm:col-span-2">
          <label class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Distribution Platform (optional)</label>
          <input v-model="form.distribution_platform" type="text" class="tmr-input w-full" placeholder="DistroKid" />
        </div>
      </div>

      <!-- Splits -->
      <div class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <span class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Splits</span>
          <span
            class="font-mono text-[0.5rem] tracking-[0.15em] uppercase"
            :class="percentageTotal === 100 ? 'text-fg-dim' : 'text-red-400'"
          >Total: {{ percentageTotal }}%</span>
        </div>
        <p v-if="form.splits.some((s) => s.artist_name.trim()) && percentageTotal !== 100" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">
          Splits must add up to 100% — currently {{ percentageTotal }}%.
        </p>

        <!-- Column labels — placeholders alone vanish once a value is typed in, so the
             percentage field in particular would read as a bare, unlabeled number. -->
        <div class="hidden sm:grid grid-cols-[1.4fr_1.4fr_0.75fr_0.9fr_auto] gap-2 px-3">
          <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">Artist Name *</span>
          <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">Email</span>
          <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">Split *</span>
          <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">Role</span>
          <span></span>
        </div>

        <div v-for="(s, i) in form.splits" :key="i" class="grid grid-cols-1 gap-2 sm:grid-cols-[1.4fr_1.4fr_0.75fr_0.9fr_auto] items-center border border-border p-3">
          <input v-model="s.artist_name" type="text" class="tmr-input w-full" placeholder="Artist name *" />
          <input v-model="s.artist_email" type="email" class="tmr-input w-full" placeholder="Email (optional)" />
          <div class="relative">
            <input
              v-model.number="s.percentage"
              type="number"
              min="0"
              max="100"
              step="0.1"
              class="tmr-input w-full pr-5 font-mono text-accent"
              placeholder="0"
            />
            <span class="absolute right-0 bottom-[0.6rem] font-mono text-accent pointer-events-none">%</span>
          </div>
          <input v-model="s.role" type="text" class="tmr-input w-full" placeholder="Role (optional)" />
          <button
            @click="removeSplit(i)"
            :disabled="form.splits.length <= 1"
            class="bg-transparent border-0 text-fg-dim cursor-pointer text-lg px-1.5 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-fg-dim"
          >×</button>
        </div>

        <button @click="addSplit" class="btn btn--muted self-start" style="font-size:0.6rem;padding:0.3rem 0.75rem;">+ Add Split</button>
      </div>

      <div class="flex items-center gap-4 flex-wrap">
        <button @click="create" :disabled="creating || !canCreate" class="btn btn--primary">
          {{ creating ? 'Creating…' : 'Create & Send' }}
        </button>
        <button @click="cancelNew" class="btn btn--muted">Cancel</button>
        <span v-if="createError" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-red-400">{{ createError }}</span>
      </div>

      <div v-if="lastResult" class="border-t border-border pt-4 flex flex-col gap-1">
        <p v-if="lastResult.mailed.length" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
          ✉ Sent to {{ lastResult.mailed.join(', ') }}
        </p>
        <p v-if="lastResult.skipped.length" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-accent">
          No email on file for {{ lastResult.skipped.join(', ') }} — copy their link below.
        </p>
      </div>
    </div>

    <!-- Error / Loading / Empty -->
    <p v-if="loadError" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-red-400">{{ loadError }}</p>
    <p v-else-if="loading" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">Loading…</p>
    <p v-else-if="sheets.length === 0" class="font-mono text-[0.55rem] tracking-[0.2em] uppercase text-fg-dim">No split sheets yet.</p>

    <!-- List -->
    <div v-else class="flex flex-col gap-4">
      <div v-for="sheet in sheets" :key="sheet.release.id" class="border border-border">

        <div class="flex items-center justify-between gap-4 px-5 py-4 border-b border-border flex-wrap">
          <div class="flex flex-col gap-1">
            <span class="font-label font-semibold text-[0.85rem] tracking-[0.06em] text-fg">
              {{ sheet.release.catalog }} — {{ sheet.release.label_project }}
            </span>
            <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
              {{ sheet.release.distribution_platform || '—' }}
            </span>
          </div>
          <div class="flex items-center gap-3">
            <span
              class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border"
              :class="sheet.release.status === 'fully_signed' ? 'text-accent border-accent-border' : 'text-fg-dim border-border'"
            >{{ sheet.release.status === 'fully_signed' ? 'Fully Signed' : 'Draft' }}</span>
            <a
              :href="`/split-sheet/${sheet.release.public_slug}`"
              target="_blank"
              class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim hover:text-fg transition-colors"
            >View public →</a>
            <button
              v-if="!sheet.splits.some((s) => s.signed_at)"
              @click="deleteReleaseEntry(sheet.release)"
              :disabled="deletingReleaseId === sheet.release.id"
              class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-red-400 hover:border-red-400/40 transition-colors disabled:cursor-not-allowed"
            >{{ deletingReleaseId === sheet.release.id ? '…' : 'Delete' }}</button>
          </div>
        </div>

        <div class="flex flex-col">
          <div
            v-for="split in sheet.splits"
            :key="split.id"
            class="flex items-center justify-between gap-4 px-5 py-3 border-b border-border last:border-b-0 flex-wrap"
          >
            <div class="flex flex-col gap-1 min-w-0">
              <span class="font-label text-[0.8rem] text-fg">{{ split.artist_name }}</span>
              <span class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
                {{ split.percentage }}%{{ split.role ? ` · ${split.role}` : '' }}{{ split.artist_email ? ` · ${split.artist_email}` : '' }}
              </span>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span v-if="split.signed_at" class="font-mono text-[0.5rem] tracking-[0.15em] uppercase text-fg-dim">
                Signed {{ new Date(split.signed_at).toLocaleDateString('en-GB') }}
              </span>
              <template v-else>
                <button
                  @click="resend(split)"
                  :disabled="resendingId === split.id"
                  class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors disabled:cursor-not-allowed"
                >{{ resendingId === split.id ? '…' : (split.artist_email ? 'Resend' : 'Get Link') }}</button>
                <button
                  v-if="linkFor[split.id]"
                  @click="copyLink(split.id)"
                  class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-fg transition-colors"
                >{{ copiedIds.has(split.id) ? '✓' : 'Copy' }}</button>
                <button
                  @click="deleteSplitEntry(split)"
                  :disabled="deletingSplitId === split.id"
                  class="font-mono text-[0.5rem] tracking-[0.15em] uppercase px-2 py-0.5 border border-border text-fg-dim cursor-pointer hover:text-red-400 hover:border-red-400/40 transition-colors disabled:cursor-not-allowed"
                >{{ deletingSplitId === split.id ? '…' : 'Delete' }}</button>
              </template>
            </div>
          </div>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { splitSheetsApi, type SplitSheetWithSplits, type Split, type SplitSheetRelease } from '../../../lib/admin-api';
import releasesJson from '../../../../the-moon-os/data/releases.json';

interface Release { catalog: string; artist: string; title: string; }
const releases: Release[] = (releasesJson as any).releases.map((r: any) => ({
  catalog: r.catalog,
  artist: r.artist,
  title: r.title,
}));

const sheets     = ref<SplitSheetWithSplits[]>([]);
const loading    = ref(true);
const loadError  = ref('');
const showNew    = ref(false);
const creating   = ref(false);
const createError = ref('');
const lastResult = ref<{ mailed: string[]; skipped: string[] } | null>(null);

const resendingId = ref('');
const linkFor      = ref<Record<string, string>>({});
const copiedIds    = ref(new Set<string>());

const deletingSplitId   = ref('');
const deletingReleaseId = ref('');

const emptySplit = () => ({ artist_name: '', artist_email: '', percentage: 0, role: '' });
const form = ref({
  catalog: '',
  label_project: '',
  distribution_platform: '',
  splits: [emptySplit(), emptySplit()],
});

const percentageTotal = computed(() =>
  Math.round(form.value.splits.reduce((sum, s) => sum + (Number(s.percentage) || 0), 0) * 10) / 10,
);

const canCreate = computed(() =>
  form.value.catalog.trim() &&
  form.value.label_project.trim() &&
  form.value.splits.some((s) => s.artist_name.trim() && s.percentage > 0) &&
  percentageTotal.value === 100,
);

async function load() {
  loading.value = true;
  loadError.value = '';
  try {
    sheets.value = await splitSheetsApi.getAll();
  } catch {
    loadError.value = 'Failed to load split sheets.';
  } finally {
    loading.value = false;
  }
}

function addSplit() {
  form.value.splits.push(emptySplit());
}

function removeSplit(i: number) {
  if (form.value.splits.length <= 1) return;
  form.value.splits.splice(i, 1);
}

function cancelNew() {
  showNew.value = false;
  createError.value = '';
  lastResult.value = null;
  form.value = { catalog: '', label_project: '', distribution_platform: '', splits: [emptySplit(), emptySplit()] };
}

// Label Project defaults to the release's own artist — usually correct as-is,
// but stays editable for collaborations or compilations filed under a different name.
function applyReleaseDefaults() {
  const release = releases.find((r) => r.catalog === form.value.catalog);
  if (release) form.value.label_project = release.artist;
}

async function create() {
  if (!canCreate.value) return;
  creating.value = true;
  createError.value = '';
  lastResult.value = null;
  try {
    const validSplits = form.value.splits
      .filter((s) => s.artist_name.trim() && s.percentage > 0)
      .map((s) => ({
        artist_name: s.artist_name.trim(),
        artist_email: s.artist_email.trim() || undefined,
        percentage: Number(s.percentage),
        role: s.role.trim() || undefined,
      }));

    const result = await splitSheetsApi.create({
      catalog: form.value.catalog,
      label_project: form.value.label_project.trim(),
      distribution_platform: form.value.distribution_platform.trim() || undefined,
      splits: validSplits,
    });
    lastResult.value = { mailed: result.mailed, skipped: result.skipped };
    await load();
  } catch (e: any) {
    createError.value = e.message ?? 'Failed to create split sheet.';
  } finally {
    creating.value = false;
  }
}

async function resend(split: Split) {
  resendingId.value = split.id;
  try {
    const result = await splitSheetsApi.resend(split.id);
    linkFor.value = { ...linkFor.value, [split.id]: result.signing_url };
  } catch {
    // surfaced implicitly — no link/mailed state changes
  } finally {
    resendingId.value = '';
  }
}

async function deleteSplitEntry(split: Split) {
  if (!confirm(`Remove "${split.artist_name}" from this split sheet?`)) return;
  deletingSplitId.value = split.id;
  try {
    await splitSheetsApi.deleteSplit(split.id);
    await load();
  } catch (e: any) {
    alert(e.message ?? 'Failed to delete split.');
  } finally {
    deletingSplitId.value = '';
  }
}

async function deleteReleaseEntry(release: SplitSheetRelease) {
  if (!confirm(`Delete the split sheet for ${release.catalog}? This removes all of its splits too.`)) return;
  deletingReleaseId.value = release.id;
  try {
    await splitSheetsApi.deleteRelease(release.id);
    await load();
  } catch (e: any) {
    alert(e.message ?? 'Failed to delete release.');
  } finally {
    deletingReleaseId.value = '';
  }
}

async function copyLink(splitId: string) {
  const url = linkFor.value[splitId];
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    copiedIds.value = new Set(copiedIds.value).add(splitId);
    setTimeout(() => {
      const next = new Set(copiedIds.value);
      next.delete(splitId);
      copiedIds.value = next;
    }, 1500);
  } catch {
    // clipboard not available
  }
}

onMounted(load);
</script>
