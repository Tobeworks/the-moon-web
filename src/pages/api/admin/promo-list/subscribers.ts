export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoSubscribers, getPromoSubscriberByEmail, createPromoSubscriber } from '../../../../lib/pocketbase';
import { randomBytes } from 'node:crypto';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async () => {
  const subscribers = await getPromoSubscribers();
  return json(subscribers);
};

export const POST = async ({ request }: APIContext) => {
  let body: Record<string, string> = {};
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Invalid body' }, 400);
  }

  const email = (body.email ?? '').trim().toLowerCase();
  const name  = (body.name  ?? '').trim();

  if (!email) return json({ error: 'Email required' }, 422);

  const existing = await getPromoSubscriberByEmail(email);
  if (existing) return json({ error: 'Already subscribed' }, 409);

  const token = randomBytes(32).toString('hex');
  const subscriber = await createPromoSubscriber(email, name, token);
  return json(subscriber, 201);
};
