import { defineMiddleware } from 'astro:middleware';

const PB_URL = process.env.POCKETBASE_URL ?? import.meta.env.POCKETBASE_URL ?? 'http://pocketbase:8090';

export const onRequest = defineMiddleware(async ({ url, cookies, redirect }, next) => {
  const isAdminPage = url.pathname.startsWith('/admin');
  const isAdminApi  = url.pathname.startsWith('/api/admin');
  const isLoginPage = url.pathname === '/admin/login';
  const isLoginApi  = url.pathname === '/api/admin/login';

  if ((isAdminPage || isAdminApi) && !isLoginPage && !isLoginApi) {
    const token = cookies.get('admin_token')?.value;
    // A page visit belongs at the login screen; a fetch() caller needs JSON it can read.
    const unauthorized = () => isAdminApi
      ? new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401, headers: { 'content-type': 'application/json' } })
      : redirect('/admin/login');

    if (!token) return unauthorized();

    // Verify token against PocketBase
    const res = await fetch(`${PB_URL}/api/collections/users/auth-refresh`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => null);

    if (!res || !res.ok) {
      cookies.delete('admin_token', { path: '/' });
      return unauthorized();
    }
  }

  return next();
});
