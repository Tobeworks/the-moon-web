export const prerender = false;

import type { APIContext } from 'astro';
import { unsubscribeByToken } from '../../../lib/pocketbase';

export const GET = async ({ request, redirect }: APIContext) => {
  const url   = new URL(request.url);
  const token = url.searchParams.get('token') ?? '';

  if (!token || !/^[0-9a-f]{64}$/.test(token)) {
    return redirect('/newsletter/unsubscribed', 302);
  }

  await unsubscribeByToken(token);

  return redirect('/newsletter/unsubscribed', 302);
};
