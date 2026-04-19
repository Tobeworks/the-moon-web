export const prerender = false;

import type { APIContext } from 'astro';

const PB_URL = process.env.POCKETBASE_URL ?? import.meta.env.POCKETBASE_URL ?? 'http://pocketbase:8090';

export const POST = async ({ request, cookies }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ ok: false, error: 'Invalid request' }, 400);
  }

  const { email, password } = body;
  if (!email || !password) return json({ ok: false, error: 'Email and password required' }, 422);

  // Authenticate against PocketBase users
  const pbRes = await fetch(`${PB_URL}/api/collections/users/auth-with-password`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ identity: email, password }),
  }).catch(() => null);

  if (!pbRes || !pbRes.ok) {
    return json({ ok: false, error: 'Invalid credentials' }, 401);
  }

  const data = await pbRes.json();
  const token = data.token as string;

  cookies.set('admin_token', token, {
    httpOnly: true,
    sameSite: 'strict',
    path: '/',
    maxAge: 60 * 60 * 8,
  });

  return json({ ok: true });
};

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });
