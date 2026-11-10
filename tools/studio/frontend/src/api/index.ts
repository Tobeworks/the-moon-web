export class ApiError extends Error {
  constructor(message: string, public status: number, public detail?: unknown) {
    super(message);
  }
}

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const form = body instanceof FormData;
  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers: body !== undefined && !form ? { 'Content-Type': 'application/json' } : undefined,
      body: body === undefined ? undefined : form ? body : JSON.stringify(body),
    });
  } catch {
    throw new ApiError('Der Server ist nicht erreichbar.', 0);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    throw new ApiError(typeof d === 'string' ? d : d?.conflicts ? 'Dateien existieren schon' : res.statusText, res.status, d);
  }
  return data as T;
}

export const api = {
  get: <T>(url: string) => request<T>('GET', url),
  post: <T>(url: string, body?: unknown) => request<T>('POST', url, body ?? {}),
  put: <T>(url: string, body: unknown) => request<T>('PUT', url, body),
  del: <T>(url: string) => request<T>('DELETE', url),
  form: <T>(url: string, form: FormData) => request<T>('POST', url, form),
};

export const messageOf = (e: unknown) => (e instanceof Error ? e.message : String(e));
