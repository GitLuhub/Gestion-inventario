const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface RequestOptions extends RequestInit {
  token?: string
  /** Interno — evita loops infinitos en el retry post-refresh */
  _isRetry?: boolean
}

// ---------------------------------------------------------------------------
// G3: Auto-refresh interceptor
// authStore registra este callback después de inicializarse, de modo que
// api.ts no tiene dependencia directa del store (evita circular imports).
// ---------------------------------------------------------------------------
type RefreshCallback = () => Promise<string | null>
let _refreshCallback: RefreshCallback | null = null

/** Llamar desde authStore durante la inicialización. */
export function setRefreshCallback(fn: RefreshCallback): void {
  _refreshCallback = fn
}

/** Clears the refresh callback on logout. */
export function clearRefreshCallback(): void {
  _refreshCallback = null
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------
async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { token, _isRetry, ...fetchOptions } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(fetchOptions.headers as Record<string, string>),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
    // Needed for httpOnly cookie to be sent on same-origin refresh calls
    credentials: 'include',
  })

  // G3: On 401, try to silently refresh the access token once.
  if (response.status === 401 && !_isRetry && _refreshCallback) {
    const newToken = await _refreshCallback()
    if (newToken) {
      return request<T>(endpoint, { ...options, token: newToken, _isRetry: true })
    }
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Error desconocido' }))
    throw new Error(error.detail || `HTTP error ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json()
}

export function getToken(): string | undefined {
  if (typeof document === 'undefined') return undefined
  const cookies = document.cookie.split(';')
  for (const cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'access_token') {
      return decodeURIComponent(value)
    }
  }
  return undefined
}

export const apiClient = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),
}

export { request }
