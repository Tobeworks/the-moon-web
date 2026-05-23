export const prerender = false;
import { getConfirmedSubscribers } from '../../../../../lib/pocketbase';

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json' } });

export const GET = async () => {
  const subscribers = await getConfirmedSubscribers();
  return json(subscribers);
};
