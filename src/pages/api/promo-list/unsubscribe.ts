export const prerender = false;

import type { APIContext } from 'astro';
import { getPromoSubscriberByToken, deletePromoSubscriber } from '../../../lib/pocketbase';

export const GET = async ({ url, redirect }: APIContext) => {
  const token = url.searchParams.get('token') ?? '';

  if (!/^[0-9a-f]{64}$/.test(token)) {
    return redirect('/promo-list/unsubscribed?error=1');
  }

  const subscriber = await getPromoSubscriberByToken(token);
  if (!subscriber) return redirect('/promo-list/unsubscribed?error=1');

  await deletePromoSubscriber(subscriber.id);
  return redirect('/promo-list/unsubscribed');
};
