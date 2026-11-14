/**
 * AI help for the newsletter editor: write or rewrite the Markdown body, or suggest a subject.
 * One call to the Anthropic Messages API via fetch — no SDK. Voice mirrors tools/studio/ai.py.
 * Pure of Astro/Vue imports so node --test can run it and the editor can import spliceSelection.
 */

export type AiMode = 'text' | 'subject';
export interface AiInput { mode: AiMode; instruction: string; body: string; selection?: string }
export type AiResult = { ok: true; text: string } | { ok: false; error: string };

const MODEL = 'claude-sonnet-5-5';

const VOICE = `You write for The Moon Records, an independent ambient label.
Voice: calm, concrete, atmospheric, a little literary. Never hype.
Use only the facts you are given. Do not invent collaborators, instruments, places, earlier releases or release details.
No emojis, no hashtags, no clichés such as "sonic journey", "tapestry" or "immersive soundscape".
Write in the language of the existing text or of the instruction.`;

const SYSTEM_TEXT = `${VOICE}
You help edit a newsletter. The body is Markdown; the header and footer are added automatically, so do not write them.
Output only the Markdown text itself, with no comment before or after it and no code fence.`;

const SYSTEM_SELECTION = `${SYSTEM_TEXT}
You are given the whole text and one selected passage. Return only the replacement for the selected passage, not the whole text.`;

const SYSTEM_SUBJECT = `${VOICE}
Write one subject line for the newsletter. Output exactly one line, at most 70 characters, no Markdown, no quotation marks.`;

export function buildMessages({ mode, instruction, body, selection }: AiInput): { system: string; user: string } {
  const task = instruction.trim() || (mode === 'subject' ? 'Suggest a subject.' : 'Write the newsletter.');
  const parts = [`Instruction: ${task}`];
  if (body.trim()) parts.push(`Current text:\n${body}`);
  if (mode === 'text' && selection) parts.push(`Selected passage (rewrite only this):\n${selection}`);
  const system = mode === 'subject' ? SYSTEM_SUBJECT : selection ? SYSTEM_SELECTION : SYSTEM_TEXT;
  return { system, user: parts.join('\n\n') };
}

function clean(text: string, mode: AiMode): string {
  let t = text.trim().replace(/^```[a-z]*\n([\s\S]*?)\n?```$/i, '$1').trim();
  if (mode === 'subject') t = (t.split('\n')[0] ?? '').trim().replace(/^["'„“”‚‘]+|["'“”‘’]+$/g, '').trim();
  return t;
}

function failure(status: number, message: string): string {
  if (status === 401 || status === 403) return 'Die KI hat den Zugang abgelehnt. ANTHROPIC_API_KEY prüfen.';
  if (status === 429) return 'Die KI ist gerade überlastet. Gleich noch einmal versuchen.';
  return `Die KI meldet einen Fehler (${status})${message ? `: ${message}` : ''}`;
}

export async function generate(
  input: AiInput,
  apiKey: string | undefined,
  model?: string,
  fetchImpl: typeof fetch = fetch,
): Promise<AiResult> {
  if (!apiKey) return { ok: false, error: 'ANTHROPIC_API_KEY fehlt auf dem Server.' };
  if (!input.instruction.trim() && !input.body.trim()) {
    return { ok: false, error: 'Anweisung oder Text nötig.' };
  }

  const { system, user } = buildMessages(input);
  let res: Response;
  try {
    res = await fetchImpl('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'content-type': 'application/json', 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
      body: JSON.stringify({ model: model || MODEL, max_tokens: 1500, system, messages: [{ role: 'user', content: user }] }),
    });
  } catch {
    return { ok: false, error: 'Keine Verbindung zur KI.' };
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) return { ok: false, error: failure(res.status, data?.error?.message ?? '') };
  if (data.stop_reason === 'refusal') return { ok: false, error: 'Die KI hat die Anfrage abgelehnt. Anders formulieren.' };

  const raw = (data.content ?? []).filter((b: { type: string }) => b.type === 'text').map((b: { text: string }) => b.text).join('');
  const text = clean(raw, input.mode);
  return text ? { ok: true, text } : { ok: false, error: 'Die KI hat keinen Text geliefert. Bitte noch einmal versuchen.' };
}

/** Replaces body[start,end) with replacement, keeping the selection's leading/trailing whitespace. */
export function spliceSelection(body: string, start: number, end: number, replacement: string): string {
  const sel = body.slice(start, end);
  const lead = sel.match(/^\s*/)![0];
  const trail = sel.slice(lead.length).match(/\s*$/)![0];
  return body.slice(0, start) + lead + replacement.trim() + trail + body.slice(end);
}
