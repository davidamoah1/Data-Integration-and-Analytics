// NEXT_PUBLIC_API_URL is the backend origin ONLY (e.g. http://localhost:8000).
// Every service call already includes the leading /api/... segment, so this
// must NOT also be "/api" or requests will double up as /api/api/....
// An explicitly empty string (same-origin deployments behind a rewrite, e.g.
// Vercel) is intentional and must not fall back to the localhost default.
//
// In development (NODE_ENV !== 'production'), defaults to localhost:8000
// which is the port the FastAPI backend runs on.
// In production, NEXT_PUBLIC_API_URL MUST be set — an empty-string value
// means same-origin, which is valid; an *undefined* value means
// misconfiguration.
const API_URL = (() => {
  if (process.env.NEXT_PUBLIC_API_URL !== undefined) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '');
  }
  if (process.env.NODE_ENV === 'production') {
    // Same-origin fallback — works behind reverse proxy / Vercel rewrite.
    return '';
  }
  return 'http://localhost:8000';
})();
const REQUEST_TIMEOUT = 30000;
const MAX_RETRIES = 2;

// ─── Token Management ────────────────────────────────────────

const TOKEN_KEY = 'dataflow_access_token';
const REFRESH_TOKEN_KEY = 'dataflow_refresh_token';

export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// ─── API Error ───────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ─── Core Request Function ───────────────────────────────────

type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  headers?: Record<string, string>;
  skipAuth?: boolean;
  isFormData?: boolean;
  timeout?: number;
  retries?: number;
  params?: Record<string, string | number | boolean | undefined | null>;
};

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const json = await res.json();
    if (json.success && json.data) {
      setTokens(json.data.access_token, json.data.refresh_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = 'GET',
    body,
    headers = {},
    skipAuth = false,
    isFormData = false,
    timeout = REQUEST_TIMEOUT,
    retries = MAX_RETRIES,
    params,
  } = options;

  // Always prefix non-/api/ paths with /api to avoid conflicts with
  // Next.js page routes (e.g. /datasets page vs /datasets API).
  let normalizedPath = path;
  if (!normalizedPath.startsWith('/api/') && !normalizedPath.startsWith('/api?')) {
    normalizedPath = '/api' + (normalizedPath.startsWith('/') ? '' : '/') + normalizedPath;
  }

  let url = normalizedPath;
  if (params) {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        query.append(key, String(value));
      }
    }
    const queryString = query.toString();
    if (queryString) {
      url += (normalizedPath.includes('?') ? '&' : '?') + queryString;
    }
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const requestHeaders: Record<string, string> = {
    ...headers,
  };

  if (!isFormData) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  if (!skipAuth) {
    const token = getAccessToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${url}`, {
      method,
      headers: requestHeaders,
      body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(408, 'Request timed out. The server took too long to respond.');
    }
    if (retries > 0) {
      return request<T>(path, { ...options, retries: retries - 1 });
    }
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('Network request failed')) {
      throw new ApiError(0, `Unable to connect to the server at ${API_URL}. Make sure the backend is running.`);
    }
    throw new ApiError(0, `Network error: ${msg}`);
  }

  clearTimeout(timeoutId);

  // Handle 401 — try refresh
  if (response.status === 401 && !skipAuth) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return request<T>(path, { ...options, retries: 0 });
    }
    clearTokens();
    if (typeof window !== 'undefined') {
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- plain service module (no router access); hard navigation intentionally resets all in-memory state on session expiry
      window.location.href = '/login';
    }
    throw new ApiError(401, 'Session expired');
  }

  if (!response.ok) {
    let errorData: unknown;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        errorData = await response.json();
      } catch {
        // non-JSON error
      }
    } else {
      // Response is HTML or other non-JSON content
      try {
        await response.text();
      } catch {
        // ignore
      }
    }
    const serverMessage =
      (errorData as { message?: string })?.message ||
      (errorData as { detail?: string })?.detail;
    
    const statusMessages: Record<number, string> = {
      401: 'Your session has expired. Please sign in again.',
      403: 'You do not have permission to perform this action.',
      404: 'The requested resource was not found.',
      413: 'This file is too large. Maximum allowed size is 50 MB.',
      415: 'This file type is not supported.',
      422: 'The file could not be processed because some information is invalid.',
      500: 'The server encountered an error while processing your request.',
      502: 'The server received an invalid response from an upstream service.',
      503: 'The service is temporarily unavailable. Please try again later.',
      504: 'The server took too long to respond. Please try again.',
    };
    const message = serverMessage || statusMessages[response.status] || `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, errorData);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  let responseText: string;
  try {
    responseText = await response.text();
  } catch {
    throw new ApiError(response.status, `The server returned an empty response (HTTP ${response.status}).`);
  }

  // Handle empty response body (e.g. 200 with no content)
  if (!responseText || responseText.trim() === '') {
    if (response.status === 200) {
      return null as T;
    }
    throw new ApiError(response.status, `The server returned an empty response (HTTP ${response.status}).`);
  }

  let json: unknown;
  try {
    json = JSON.parse(responseText);
  } catch {
    // Response is not JSON (e.g. HTML error page from proxy/CDN)
    if (responseText.includes('<!DOCTYPE') || responseText.includes('<html')) {
      throw new ApiError(
        response.status,
        response.status === 200
          ? 'The server returned an HTML page instead of JSON. The API endpoint may be misconfigured or the backend is down.'
          : `Server returned HTML instead of JSON (HTTP ${response.status}). The backend may be restarting or unavailable.`,
      );
    }
    throw new ApiError(
      response.status,
      `The server returned a non-JSON response (HTTP ${response.status}). Response: ${responseText.slice(0, 200)}`,
    );
  }

  // Backend wraps responses in { success, data, message }
  if (json && typeof json === 'object' && 'success' in json) {
    if (!(json as { success: boolean }).success) {
      throw new ApiError(response.status, (json as { message?: string }).message || 'Request failed', json);
    }
    return (json as unknown as { data: T }).data;
  }
  return json as T;
}

// ─── Exported API Methods ────────────────────────────────────

export const apiClient = {
  get: <T = unknown>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'GET' }),

  post: <T = unknown>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ) => request<T>(path, { ...options, method: 'POST', body }),

  put: <T = unknown>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ) => request<T>(path, { ...options, method: 'PUT', body }),

  patch: <T = unknown>(
    path: string,
    body?: unknown,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ) => request<T>(path, { ...options, method: 'PATCH', body }),

  delete: <T = unknown>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'DELETE' }),

  upload: <T = unknown>(path: string, formData: FormData, options?: Omit<RequestOptions, 'method' | 'body'>) =>
    request<T>(path, { ...options, method: 'POST', body: formData, isFormData: true }),

  uploadWithProgress: <T = unknown>(
    path: string,
    formData: FormData,
    onProgress?: (percent: number) => void,
    options?: Omit<RequestOptions, 'method' | 'body'>,
  ): Promise<T> => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      let normalizedPath = path;
      if (!normalizedPath.startsWith('/api/') && !normalizedPath.startsWith('/api?')) {
        normalizedPath = '/api' + (normalizedPath.startsWith('/') ? '' : '/') + normalizedPath;
      }
      const url = `${API_URL}${normalizedPath}`;
      xhr.open('POST', url);

      // Auth header
      if (!options?.skipAuth) {
        const token = getAccessToken();
        if (token) {
          xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        }
      }

      // Upload progress
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };

      xhr.onload = () => {
        try {
          const json = JSON.parse(xhr.responseText);
          if (json && typeof json === 'object' && 'success' in json) {
            if (!json.success) {
              reject(new ApiError(xhr.status, json.message || 'Upload failed', json));
              return;
            }
            resolve(json.data as T);
            return;
          }
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(json as T);
          } else {
            const msg = (json && typeof json === 'object' && 'detail' in json) ? json.detail : `Upload failed with status ${xhr.status}`;
            reject(new ApiError(xhr.status, msg, json));
          }
        } catch {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(null as T);
          } else {
            reject(new ApiError(xhr.status, `Upload failed with status ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => {
        reject(new ApiError(0, `Unable to connect to the server at ${API_URL}. Make sure the backend is running.`));
      };

      xhr.ontimeout = () => {
        reject(new ApiError(408, 'Upload timed out. The server took too long to respond.'));
      };

      xhr.timeout = options?.timeout ?? REQUEST_TIMEOUT;
      xhr.send(formData);
    });
  },

  getApiUrl: () => API_URL,
};
