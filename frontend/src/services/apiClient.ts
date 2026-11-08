/**
 * Whicoustic API Client
 * Centralized fetch wrapper enforcing Strict Real-Data Policy.
 * Zero silent mock fallbacks: network or HTTP failures throw typed ApiError instances.
 */

import { auth } from '../config/firebase.ts';
import { getSessionCookie, setSessionCookie } from '../utils/cookies.ts';

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export const getApiBaseUrl = (): string => {
  const env = typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined;
  const envUrl = (env?.VITE_API_URL || env?.VITE_API_BASE_URL) as string | undefined;
  if (envUrl) {
    return envUrl.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
  }
  // In production on whicoustic.xyz or whicoustic.ai, automatically route to production API backend
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname.includes('whicoustic.xyz') ||
     window.location.hostname.includes('whicoustic.ai'))
  ) {
    return 'https://api.whicoustic.xyz';
  }
  // In development, Vite proxies '/api' to backend http://localhost:8000
  return '';
};

export const getAuthToken = (): string | null => {
  const explicitToken = localStorage.getItem('whicoustic_token');
  if (explicitToken) return explicitToken;

  const cookieSession = getSessionCookie();
  if (cookieSession?.token) {
    localStorage.setItem('whicoustic_token', cookieSession.token);
    return cookieSession.token;
  }

  const savedUser = localStorage.getItem('whicoustic_user');
  if (savedUser) {
    try {
      const parsed = JSON.parse(savedUser);
      if (parsed.token) {
        localStorage.setItem('whicoustic_token', parsed.token);
        return parsed.token;
      }
    } catch {
      // Ignore parse failure
    }
  }

  // Development convenience token accepted by FastAPI Mock Auth
  const env = typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined;
  if (env?.DEV) {
    return 'mock-token-123';
  }

  return null;
};

export const buildHeaders = (customHeaders?: HeadersInit, isFormData = false): Headers => {
  const headers = new Headers(customHeaders);

  if (!isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getAuthToken();
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  return headers;
};

export const handleResponse = async <T>(response: Response): Promise<T> => {
  if (response.ok) {
    // 204 No Content
    if (response.status === 204) {
      return {} as T;
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return (await response.json()) as T;
    }
    return (await response.text()) as unknown as T;
  }

  let errorMessage = `API Request failed with status ${response.status}`;
  let errorDetails: unknown = null;

  try {
    const errorJson = await response.json();
    errorDetails = errorJson;
    if (errorJson.detail) {
      if (Array.isArray(errorJson.detail)) {
        errorMessage = errorJson.detail
          .map((item: { msg?: string; loc?: string[] }) => item.msg || JSON.stringify(item))
          .join(', ');
      } else if (typeof errorJson.detail === 'string') {
        errorMessage = errorJson.detail;
      }
    } else if (errorJson.message && typeof errorJson.message === 'string') {
      errorMessage = errorJson.message;
    }
  } catch {
    // Response was not JSON
    errorMessage = `${response.status} ${response.statusText || 'Server Error'}`;
  }

  throw new ApiError(errorMessage, response.status, errorDetails);
};

async function ensureAuthReady(): Promise<void> {
  if (auth && typeof (auth as any).authStateReady === 'function') {
    try {
      await (auth as any).authStateReady();
    } catch {
      // Ignore auth ready error
    }
  }
}

export function persistFreshToken(token: string): void {
  try {
    localStorage.setItem('whicoustic_token', token);
    const savedUser = localStorage.getItem('whicoustic_user');
    if (savedUser) {
      try {
        const user = JSON.parse(savedUser);
        if (user && typeof user === 'object') {
          user.token = token;
          localStorage.setItem('whicoustic_user', JSON.stringify(user));
          setSessionCookie(user, token);
        }
      } catch {
        // Ignore user json parse error
      }
    }
  } catch (err) {
    console.warn('Failed to persist fresh token across storage and cookies:', err);
  }
}

export async function requestWithRetry<T>(
  url: string,
  options: RequestInit,
  isFormData = false
): Promise<T> {
  // 1. Proactive auth initialization check if no token found in storage
  let token = getAuthToken();
  if (!token && auth) {
    await ensureAuthReady();
    if (auth.currentUser) {
      try {
        token = await auth.currentUser.getIdToken();
        if (token) {
          persistFreshToken(token);
        }
      } catch (tokenErr) {
        console.warn('Initial token acquisition deferred:', tokenErr);
      }
    }
  }

  let headers = buildHeaders(options.headers, isFormData);
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response = await fetch(url, { ...options, headers });

  // 2. 401 Token Refresh & Single Retry
  if (response.status === 401) {
    try {
      await ensureAuthReady();
      if (auth?.currentUser) {
        const freshToken = await auth.currentUser.getIdToken(true);
        if (freshToken) {
          persistFreshToken(freshToken);
          const retryHeaders = new Headers(headers);
          retryHeaders.set('Authorization', `Bearer ${freshToken}`);
          response = await fetch(url, { ...options, headers: retryHeaders });
        }
      }
    } catch (refreshErr) {
      console.warn('Firebase token refresh on 401 failed:', refreshErr);
    }
  }

  return await handleResponse<T>(response);
}

export const apiClient = {
  baseUrl: getApiBaseUrl(),

  buildUrl(path: string): string {
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    const base = getApiBaseUrl();
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    return `${base}${cleanPath}`;
  },

  async get<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = this.buildUrl(path);
    try {
      return await requestWithRetry<T>(url, { ...options, method: 'GET' }, false);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to connect to Whicoustic API server. Please check your network connection or verify that the backend is running.',
        0,
        err
      );
    }
  },

  async post<T>(path: string, body?: unknown, options: RequestInit = {}): Promise<T> {
    const url = this.buildUrl(path);
    try {
      return await requestWithRetry<T>(
        url,
        {
          ...options,
          method: 'POST',
          body: body !== undefined ? JSON.stringify(body) : undefined,
        },
        false
      );
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to connect to Whicoustic API server. Please check your network connection or verify that the backend is running.',
        0,
        err
      );
    }
  },

  async put<T>(path: string, body?: unknown, options: RequestInit = {}): Promise<T> {
    const url = this.buildUrl(path);
    try {
      return await requestWithRetry<T>(
        url,
        {
          ...options,
          method: 'PUT',
          body: body !== undefined ? JSON.stringify(body) : undefined,
        },
        false
      );
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to connect to Whicoustic API server. Please check your network connection or verify that the backend is running.',
        0,
        err
      );
    }
  },

  async delete<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = this.buildUrl(path);
    try {
      return await requestWithRetry<T>(url, { ...options, method: 'DELETE' }, false);
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to connect to Whicoustic API server. Please check your network connection or verify that the backend is running.',
        0,
        err
      );
    }
  },

  async upload<T>(path: string, formData: FormData, options: RequestInit = {}): Promise<T> {
    const url = this.buildUrl(path);
    try {
      return await requestWithRetry<T>(
        url,
        {
          ...options,
          method: 'POST',
          body: formData,
        },
        true
      );
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to connect to Whicoustic API server. Please check your network connection or verify that the backend is running.',
        0,
        err
      );
    }
  },
};
