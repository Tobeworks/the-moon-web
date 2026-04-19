import { defineMiddleware } from 'astro:middleware';

const PB_URL = process.env.POCKETBASE_URL ?? import.meta.env.POCKETBASE_URL ?? 'http://pocketbase:8090';

export const onRequest = defineMiddleware(async ({ url, cookies, redirect }, next) => {
  const isAdminRoute = url.pathname.startsWith('/admin');
  const isLoginPage  = url.pathname === '/admin/login';
  const isLoginApi   = url.pathname === '/api/admin/login';

  if (isAdminRoute && !isLoginPage && !isLoginApi) {
    const token = cookies.get('admin_token')?.value;
    if (!token) return redirect('/admin/login');

    // Verify token against PocketBase
    const res = await fetch(`${PB_URL}/api/collections/users/auth-refresh`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => null);

    if (!res || !res.ok) {
      cookies.delete('admin_token', { path: '/' });
      return redirect('/admin/login');
    }
  }

  return next();
});
