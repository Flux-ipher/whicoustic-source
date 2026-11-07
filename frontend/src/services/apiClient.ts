/**
 * Whicoustic API Client
 * Centralized fetch wrapper enforcing Strict Real-Data Policy.
 * Zero silent mock fallbacks: network or HTTP failures throw typed ApiError instances.
 */

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
  const envUrl = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL) as string | undefined;
  if (envUrl) {
    return envUrl.replace(/\/api\/v1\/?$/, '').replace(/\/+$/, '');
  }
  // In production on whicoustic.xyz, automatically route to production API backend
  if (typeof window !== 'undefined' && window.location.hostname.includes('whicoustic.xyz')) {
    return 'https://api.whicoustic.xyz';
  }
  // In development, Vite proxies '/api' to backend http://localhost:8000
  return '';
};

export const getAuthToken = (): string | null => {
  const explicitToken = localStorage.getItem('whicoustic_token');
  if (explicitToken) return explicitToken;

  const savedUser = localStorage.getItem('whicoustic_user');
  if (savedUser) {
    try {
      const parsed = JSON.parse(savedUser);
      if (parsed.token) return parsed.token;
    } catch {
      // Ignore parse failure
    }
  }

  // Development convenience token accepted by FastAPI Mock Auth
  if (import.meta.env.DEV) {
    return 'mock-token-123';
  }

  return null;
};

const buildHeaders = (customHeaders?: HeadersInit, isFormData = false): Headers => {
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

const handleResponse = async <T>(response: Response): Promise<T> => {
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
      const response = await fetch(url, {
        ...options,
        method: 'GET',
        headers: buildHeaders(options.headers),
      });
      return await handleResponse<T>(response);
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
      const response = await fetch(url, {
        ...options,
        method: 'POST',
        headers: buildHeaders(options.headers),
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
      return await handleResponse<T>(response);
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
      const response = await fetch(url, {
        ...options,
        method: 'PUT',
        headers: buildHeaders(options.headers),
        body: body !== undefined ? JSON.stringify(body) : undefined,
      });
      return await handleResponse<T>(response);
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
      const response = await fetch(url, {
        ...options,
        method: 'DELETE',
        headers: buildHeaders(options.headers),
      });
      return await handleResponse<T>(response);
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
      const response = await fetch(url, {
        ...options,
        method: 'POST',
        headers: buildHeaders(options.headers, true),
        body: formData,
      });
      return await handleResponse<T>(response);
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
