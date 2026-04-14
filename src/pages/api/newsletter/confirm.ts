export const prerender = false;

import type { APIContext } from 'astro';
import { confirmSubscriber } from '../../../lib/pocketbase';
import { sendWelcomeEmail } from '../../../lib/mailer';

export const GET = async ({ request, redirect, url: reqUrl }: APIContext) => {
  const url    = new URL(request.url);
  const token  = url.searchParams.get('token') ?? '';
  const siteUrl = reqUrl.origin;

  if (!token || !/^[0-9a-f]{64}$/.test(token)) {
    return redirect('/newsletter?error=invalid', 302);
  }

  const subscriber = await confirmSubscriber(token);

  if (!subscriber) {
    return redirect('/newsletter?error=expired', 302);
  }

  await sendWelcomeEmail(subscriber.email, subscriber.name ?? '', subscriber.unsubscribe_token, siteUrl).catch(() => {});

  return redirect('/newsletter/confirmed', 302);
};
