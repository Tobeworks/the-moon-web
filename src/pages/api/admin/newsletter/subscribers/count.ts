export const prerender = false;
import { getConfirmedSubscribers } from '../../../../../lib/pocketbase';

export const GET = async () => {
  const subs = await getConfirmedSubscribers();
  return new Response(JSON.stringify({ count: subs.length }), {
    headers: { 'content-type': 'application/json' },
  });
};
