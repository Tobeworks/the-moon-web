export const prerender = false;

import type { APIContext } from 'astro';
import { generate, type AiInput } from '../../../../lib/newsletterAi';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const POST = async ({ request }: APIContext) => {
  let b: Partial<AiInput>;
  try {
    b = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid body' }, 400);
  }
  if (b.mode !== 'text' && b.mode !== 'subject') return json({ ok: false, error: 'mode must be text or subject' }, 422);

  const result = await generate(
    {
      mode: b.mode,
      instruction: String(b.instruction ?? ''),
      body: String(b.body ?? ''),
      selection: b.selection ? String(b.selection) : undefined,
    },
    process.env.ANTHROPIC_API_KEY ?? import.meta.env.ANTHROPIC_API_KEY,
    process.env.ANTHROPIC_MODEL ?? import.meta.env.ANTHROPIC_MODEL,
  );
  return json(result);
};
