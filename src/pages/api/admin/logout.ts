export const prerender = false;

import type { APIContext } from 'astro';

export const POST = async ({ cookies }: APIContext) => {
  cookies.delete('admin_session', { path: '/' });
  return new Response(null, {
    status: 302,
    headers: { Location: '/admin/login' },
  });
};
