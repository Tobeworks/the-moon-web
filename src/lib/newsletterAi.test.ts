// Run: node --test src/lib/newsletterAi.test.ts
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildMessages, generate, spliceSelection } from './newsletterAi.ts';

const reply = (text: string, status = 200, stop_reason = 'end_turn') =>
  new Response(JSON.stringify({ stop_reason, content: [{ type: 'text', text }] }), { status });

function fake(res: Response | Error) {
  const calls: { url: string; init: RequestInit }[] = [];
  const impl = (async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    if (res instanceof Error) throw res;
    return res;
  }) as unknown as typeof fetch;
  return { impl, calls };
}

const input = { mode: 'text' as const, instruction: 'kürzer', body: 'Langer Text.' };

test('no api key → error, no request', async () => {
  const f = fake(reply('x'));
  const r = await generate(input, undefined, undefined, f.impl);
  assert.equal(r.ok, false);
  assert.match((r as { error: string }).error, /ANTHROPIC_API_KEY/);
  assert.equal(f.calls.length, 0);
});

test('empty instruction and empty body → error, no request', async () => {
  const f = fake(reply('x'));
  const r = await generate({ mode: 'text', instruction: ' ', body: '' }, 'k', undefined, f.impl);
  assert.equal(r.ok, false);
  assert.equal(f.calls.length, 0);
});

test('trims the reply', async () => {
  const r = await generate(input, 'k', undefined, fake(reply('  Hallo  ')).impl);
  assert.deepEqual(r, { ok: true, text: 'Hallo' });
});

test('strips an outer code fence', async () => {
  const r = await generate(input, 'k', undefined, fake(reply('```markdown\n## A\n```')).impl);
  assert.deepEqual(r, { ok: true, text: '## A' });
});

test('subject: one line, no quotes', async () => {
  const r = await generate({ ...input, mode: 'subject' }, 'k', undefined, fake(reply('"Neu: Spelrum"\nzweite Zeile')).impl);
  assert.deepEqual(r, { ok: true, text: 'Neu: Spelrum' });
});

test('error mapping', async () => {
  const e = async (res: Response | Error) =>
    ((await generate(input, 'k', undefined, fake(res).impl)) as { error: string }).error;
  assert.match(await e(reply('', 401)), /ANTHROPIC_API_KEY/);
  assert.match(await e(reply('', 429)), /überlastet/);
  assert.match(await e(new Error('boom')), /Verbindung/);
  assert.match(await e(reply('', 500)), /500/);
});

test('refusal and empty text are errors', async () => {
  assert.equal((await generate(input, 'k', undefined, fake(reply('x', 200, 'refusal')).impl)).ok, false);
  assert.equal((await generate(input, 'k', undefined, fake(reply('  ')).impl)).ok, false);
});

test('request: default model, override, key header', async () => {
  const a = fake(reply('x'));
  await generate(input, 'secret', undefined, a.impl);
  assert.equal(JSON.parse(a.calls[0].init.body as string).model, 'claude-sonnet-5-5');
  assert.equal((a.calls[0].init.headers as Record<string, string>)['x-api-key'], 'secret');
  const b = fake(reply('x'));
  await generate(input, 'k', 'x', b.impl);
  assert.equal(JSON.parse(b.calls[0].init.body as string).model, 'x');
});

test('buildMessages with selection', () => {
  const { system, user } = buildMessages({ ...input, selection: 'Langer' });
  assert.match(user, /kürzer/);
  assert.match(user, /Langer Text\./);
  assert.match(user, /Langer/);
  assert.match(system, /replacement for the selected passage/);
});

test('spliceSelection keeps whitespace edges', () => {
  assert.equal(spliceSelection('ab \nXY\n cd', 3, 8, 'Z'), 'ab \nZ\n cd');
  assert.equal(spliceSelection('abXYcd', 2, 4, 'Z'), 'abZcd');
});
