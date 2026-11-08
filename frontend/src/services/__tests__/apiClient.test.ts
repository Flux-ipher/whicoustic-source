/**
 * Automated Unit & Integration Tests for apiClient.ts
 * Milestone 7: Production 401 Auth Chain Alignment & Fix
 *
 * Validates:
 * 1. Token retrieval from localStorage ('whicoustic_token' and 'whicoustic_user').
 * 2. Header construction for JSON and multipart form-data requests.
 * 3. Base URL formatting and absolute URL preservation.
 * 4. Response handling for 200, 204, and error statuses.
 * 5. Automatic 401 token refresh via Firebase auth.currentUser.getIdToken(true) and retry.
 */

import {
  apiClient,
  getAuthToken,
  buildHeaders,
  handleResponse,
  requestWithRetry,
  persistFreshToken,
  isTokenExpired,
  decodeJwtPayload,
  ApiError,
  getApiBaseUrl,
} from '../apiClient.ts';
import { auth, setAuthForTesting } from '../../config/firebase.ts';
import {
  getCookieDomain,
  buildSessionCookieString,
  buildClearCookieStrings,
  getSessionCookie,
  setSessionCookie,
} from '../../utils/cookies.ts';

// In-memory mock for environments without a fully featured document.cookie
if (typeof (globalThis as any).document === 'undefined') {
  let cookieStore = '';
  (globalThis as any).document = {
    get cookie() {
      return cookieStore;
    },
    set cookie(val: string) {
      const [pair] = val.split(';');
      if (!pair) return;
      const [name] = pair.split('=');
      if (val.includes('max-age=0') || val.includes('expires=Thu, 01 Jan 1970')) {
        cookieStore = cookieStore
          .split('; ')
          .filter((c) => !c.startsWith(`${name}=`))
          .join('; ');
      } else {
        const existing = cookieStore.split('; ').filter((c) => c && !c.startsWith(`${name}=`));
        existing.push(pair.trim());
        cookieStore = existing.join('; ');
      }
    },
  };
}

// In-memory mock for environments without a fully featured localStorage (e.g. Node 22+)
if (!globalThis.localStorage || typeof (globalThis.localStorage as any).clear !== 'function') {
  const store = new Map<string, string>();
  (globalThis as any).localStorage = {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => { store.set(key, String(value)); },
    removeItem: (key: string) => { store.delete(key); },
    clear: () => { store.clear(); },
  };
}

function assert(condition: boolean, message: string): void {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertEqual<T>(actual: T, expected: T, message: string): void {
  if (actual !== expected) {
    throw new Error(`Assertion failed: ${message}. Expected: ${String(expected)}, Got: ${String(actual)}`);
  }
}

export async function runApiClientTests(): Promise<{ passed: number; failed: number }> {
  let passed = 0;
  let failed = 0;

  const testCases: Array<{ name: string; fn: () => void | Promise<void> }> = [
    {
      name: 'getAuthToken returns explicit whicoustic_token from localStorage',
      fn: () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_token', 'explicit-token-xyz');
        const token = getAuthToken();
        assertEqual(token, 'explicit-token-xyz', 'Token should match explicit whicoustic_token');
      },
    },
    {
      name: 'getAuthToken falls back to whicoustic_user token if explicit token is missing',
      fn: () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_user', JSON.stringify({ id: 'u1', email: 'test@whicoustic.xyz', token: 'user-token-abc' }));
        const token = getAuthToken();
        assertEqual(token, 'user-token-abc', 'Token should match user json token');
      },
    },
    {
      name: 'getAuthToken ignores corrupt whicoustic_user JSON gracefully',
      fn: () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_user', '{corrupted_json');
        const token = getAuthToken();
        // In dev it might return mock-token-123, in prod null. It should not throw!
        assert(token === null || token === 'mock-token-123', 'Corrupt JSON should not throw');
      },
    },
    {
      name: 'buildHeaders injects Content-Type: application/json for standard requests',
      fn: () => {
        localStorage.clear();
        const headers = buildHeaders();
        assertEqual(headers.get('Content-Type'), 'application/json', 'Content-Type should be application/json');
      },
    },
    {
      name: 'buildHeaders omits Content-Type for FormData uploads',
      fn: () => {
        localStorage.clear();
        const headers = buildHeaders(undefined, true);
        assertEqual(headers.get('Content-Type'), null, 'Content-Type must be omitted for multipart FormData');
      },
    },
    {
      name: 'buildHeaders injects Bearer token into Authorization header',
      fn: () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_token', 'jwt-bearer-test-123');
        const headers = buildHeaders();
        assertEqual(headers.get('Authorization'), 'Bearer jwt-bearer-test-123', 'Bearer token must be attached');
      },
    },
    {
      name: 'buildHeaders preserves custom Authorization header if already present',
      fn: () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_token', 'ignored-token');
        const custom = { Authorization: 'Bearer custom-explicit-override' };
        const headers = buildHeaders(custom);
        assertEqual(headers.get('Authorization'), 'Bearer custom-explicit-override', 'Custom Authorization must be preserved');
      },
    },
    {
      name: 'apiClient.buildUrl respects absolute URLs and relative paths',
      fn: () => {
        const baseUrl = getApiBaseUrl();
        assert(typeof baseUrl === 'string', 'getApiBaseUrl should return a string');

        const abs = apiClient.buildUrl('https://api.whicoustic.xyz/api/v1/voices');
        assertEqual(abs, 'https://api.whicoustic.xyz/api/v1/voices', 'Absolute URL should remain intact');

        const rel = apiClient.buildUrl('/api/v1/voices');
        assert(rel.endsWith('/api/v1/voices'), 'Relative URL should end with path');
      },
    },
    {
      name: 'handleResponse returns parsed JSON on 200 OK',
      fn: async () => {
        const mockResponse = new Response(JSON.stringify({ id: 'v1', status: 'ready' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
        const data = await handleResponse<{ id: string; status: string }>(mockResponse);
        assertEqual(data.id, 'v1', 'Parsed id should match');
        assertEqual(data.status, 'ready', 'Parsed status should match');
      },
    },
    {
      name: 'handleResponse returns empty object on 204 No Content',
      fn: async () => {
        const mockResponse = new Response(null, { status: 204 });
        const data = await handleResponse<Record<string, unknown>>(mockResponse);
        assertEqual(typeof data, 'object', '204 response should return object');
      },
    },
    {
      name: 'handleResponse throws ApiError on 401 Unauthorized with detail string',
      fn: async () => {
        const mockResponse = new Response(JSON.stringify({ detail: 'Invalid or expired token' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        });
        let caught: ApiError | null = null;
        try {
          await handleResponse(mockResponse);
        } catch (err) {
          caught = err as ApiError;
        }
        assert(caught !== null, 'handleResponse should throw ApiError');
        assertEqual(caught?.status, 401, 'Error status should be 401');
        assertEqual(caught?.message, 'Invalid or expired token', 'Error message should match detail');
      },
    },
    {
      name: 'requestWithRetry automatically refreshes token and retries on 401 when currentUser is present',
      fn: async () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_token', 'stale-token-111');

        let fetchCallCount = 0;
        let lastAuthHeader: string | null = null;
        const originalFetch = globalThis.fetch;

        // Mock fetch that fails with 401 on first call, succeeds on retry
        globalThis.fetch = (async (input: RequestInfo | URL, init?: RequestInit) => {
          fetchCallCount++;
          const headers = new Headers(init?.headers);
          lastAuthHeader = headers.get('Authorization');

          if (fetchCallCount === 1) {
            return new Response(JSON.stringify({ detail: 'Token expired' }), {
              status: 401,
              headers: { 'Content-Type': 'application/json' },
            });
          }

          return new Response(JSON.stringify({ success: true, count: 42 }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }) as typeof fetch;

        // Mock Firebase auth currentUser
        const originalAuth = auth;
        let getIdTokenCalled = false;
        setAuthForTesting({
          authStateReady: async () => {},
          currentUser: {
            getIdToken: async (forceRefresh?: boolean) => {
              if (forceRefresh) getIdTokenCalled = true;
              return 'freshly-refreshed-firebase-token-999';
            },
          },
        });

        try {
          const result = await requestWithRetry<{ success: boolean; count: number }>(
            'https://api.whicoustic.xyz/api/v1/voices',
            { method: 'GET' }
          );

          assertEqual(fetchCallCount, 2, 'Request should have been retried once');
          assert(getIdTokenCalled, 'getIdToken(true) must be called on 401');
          assertEqual(
            localStorage.getItem('whicoustic_token'),
            'freshly-refreshed-firebase-token-999',
            'Fresh token must be persisted in localStorage'
          );
          assertEqual(
            lastAuthHeader,
            'Bearer freshly-refreshed-firebase-token-999',
            'Retried request must include fresh Bearer token'
          );
          assertEqual(result.success, true, 'Result from retried request should be returned');
        } finally {
          globalThis.fetch = originalFetch;
          setAuthForTesting(originalAuth);
        }
      },
    },
    {
      name: 'requestWithRetry proactively acquires token from auth.currentUser when storage is empty',
      fn: async () => {
        localStorage.clear();

        let initialAuthHeader: string | null = null;
        let fetchCallCount = 0;
        const originalFetch = globalThis.fetch;

        globalThis.fetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
          fetchCallCount++;
          const headers = new Headers(init?.headers);
          initialAuthHeader = headers.get('Authorization');
          return new Response(JSON.stringify([{ id: 'voice_1', name: 'Test Voice' }]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }) as typeof fetch;

        const originalAuth = auth;
        setAuthForTesting({
          authStateReady: async () => {},
          currentUser: {
            getIdToken: async () => 'proactively-acquired-fb-token-888',
          },
        });

        try {
          const data = await requestWithRetry<Array<{ id: string }>>(
            'https://api.whicoustic.xyz/api/v1/voices/',
            { method: 'GET' }
          );

          assertEqual(fetchCallCount, 1, 'Proactive acquisition should succeed on first call without 401');
          assertEqual(
            initialAuthHeader,
            'Bearer proactively-acquired-fb-token-888',
            'Initial request must include proactively acquired Bearer token'
          );
          assertEqual(
            localStorage.getItem('whicoustic_token'),
            'proactively-acquired-fb-token-888',
            'Token should be cached in localStorage'
          );
          assertEqual(data.length, 1, 'Returned voices array should match');
        } finally {
          globalThis.fetch = originalFetch;
          setAuthForTesting(originalAuth);
        }
      },
    },
    {
      name: 'requestWithRetry preserves multipart form-data without Content-Type override on 401 retry',
      fn: async () => {
        localStorage.clear();
        localStorage.setItem('whicoustic_token', 'stale-upload-token');

        let fetchCallCount = 0;
        let retryContentType: string | null = null;
        let retryAuthHeader: string | null = null;
        const originalFetch = globalThis.fetch;

        globalThis.fetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
          fetchCallCount++;
          const headers = new Headers(init?.headers);
          if (fetchCallCount === 1) {
            return new Response(JSON.stringify({ detail: 'Token expired' }), {
              status: 401,
              headers: { 'Content-Type': 'application/json' },
            });
          }
          retryContentType = headers.get('Content-Type');
          retryAuthHeader = headers.get('Authorization');
          return new Response(JSON.stringify({ voice_id: 'voice_uploaded_1', status: 'pending' }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }) as typeof fetch;

        const originalAuth = auth;
        setAuthForTesting({
          authStateReady: async () => {},
          currentUser: {
            getIdToken: async () => 'fresh-upload-token-777',
          },
        });

        try {
          const formData = new FormData();
          formData.append('name', 'My Voice');

          const uploadResult = await requestWithRetry<{ voice_id: string; status: string }>(
            'https://api.whicoustic.xyz/api/v1/voices/upload',
            { method: 'POST', body: formData },
            true
          );

          assertEqual(fetchCallCount, 2, 'Upload request should be retried once on 401');
          assertEqual(
            retryAuthHeader,
            'Bearer fresh-upload-token-777',
            'Retried upload request must include fresh Bearer token'
          );
          assertEqual(
            retryContentType,
            null,
            'Content-Type header must NOT be overwritten to application/json for FormData'
          );
          assertEqual(uploadResult.voice_id, 'voice_uploaded_1', 'Upload result must match');
        } finally {
          globalThis.fetch = originalFetch;
          setAuthForTesting(originalAuth);
        }
      },
    },
    {
      name: 'persistFreshToken synchronizes whicoustic_token and whicoustic_user in localStorage',
      fn: () => {
        localStorage.clear();
        const userObj = { id: 'u_sync', email: 'sync@whicoustic.xyz', token: 'old-tok' };
        localStorage.setItem('whicoustic_user', JSON.stringify(userObj));
        persistFreshToken('brand-new-synced-token');

        assertEqual(
          localStorage.getItem('whicoustic_token'),
          'brand-new-synced-token',
          'whicoustic_token must be updated'
        );
        const updatedUser = JSON.parse(localStorage.getItem('whicoustic_user') || '{}');
        assertEqual(
          updatedUser.token,
          'brand-new-synced-token',
          'whicoustic_user.token must be synchronized with fresh token'
        );
      },
    },
    {
      name: 'persistFreshToken falls back to cookie session user when whicoustic_user is missing in localStorage',
      fn: () => {
        localStorage.clear();
        const cookieUser = { id: 'u_cookie_99', email: 'cookie@whicoustic.xyz', name: 'Cookie User', role: 'TALENT' as const, isOnboarded: true };
        setSessionCookie(cookieUser, 'old-cookie-token');

        persistFreshToken('fresh-token-from-cookie-fallback');

        assertEqual(
          localStorage.getItem('whicoustic_token'),
          'fresh-token-from-cookie-fallback',
          'whicoustic_token should be set'
        );
        const savedUser = JSON.parse(localStorage.getItem('whicoustic_user') || '{}');
        assertEqual(
          savedUser.token,
          'fresh-token-from-cookie-fallback',
          'whicoustic_user token must be populated from cookie session'
        );
        const refreshedCookie = getSessionCookie();
        assert(refreshedCookie !== null, 'Cookie should be refreshed');
        assertEqual(
          refreshedCookie?.token,
          'fresh-token-from-cookie-fallback',
          'Session cookie token must be updated with fresh token'
        );
      },
    },
    {
      name: 'persistFreshToken falls back to auth.currentUser when both localStorage and cookie are empty',
      fn: () => {
        localStorage.clear();
        if (typeof document !== 'undefined') {
          document.cookie = 'whicoustic_session=; max-age=0;';
        }

        const originalAuth = auth;
        setAuthForTesting({
          currentUser: {
            uid: 'fb_user_direct_123',
            email: 'direct@whicoustic.xyz',
            displayName: 'Direct User',
          },
        });

        try {
          persistFreshToken('direct-firebase-fresh-token');

          assertEqual(
            localStorage.getItem('whicoustic_token'),
            'direct-firebase-fresh-token',
            'whicoustic_token should be set'
          );
          const savedUser = JSON.parse(localStorage.getItem('whicoustic_user') || '{}');
          assertEqual(
            savedUser.id,
            'fb_user_direct_123',
            'whicoustic_user id must be populated from auth.currentUser'
          );
          assertEqual(
            savedUser.token,
            'direct-firebase-fresh-token',
            'whicoustic_user token must be populated from fresh token'
          );
        } finally {
          setAuthForTesting(originalAuth);
        }
      },
    },
    {
      name: 'getCookieDomain and buildSessionCookieString support .whicoustic.ai apex and console subdomains',
      fn: () => {
        assertEqual(getCookieDomain('whicoustic.ai'), '.whicoustic.ai', 'whicoustic.ai domain match');
        assertEqual(getCookieDomain('app.whicoustic.ai'), '.whicoustic.ai', 'app.whicoustic.ai domain match');
        assertEqual(getCookieDomain('whicoustic.xyz'), '.whicoustic.xyz', 'whicoustic.xyz domain match');
        assertEqual(getCookieDomain('app.whicoustic.xyz'), '.whicoustic.xyz', 'app.whicoustic.xyz domain match');
        assertEqual(getCookieDomain('localhost'), '', 'localhost domain must be empty');

        const testUser = { id: 'u1', email: 'test@whicoustic.ai', name: 'User 1', role: 'TALENT' as const, isOnboarded: true };
        const cookieStr = buildSessionCookieString(testUser, 'test-tok-ai', { hostname: 'app.whicoustic.ai' });
        assert(cookieStr.includes('domain=.whicoustic.ai'), 'Cookie string must include domain=.whicoustic.ai');
        assert(cookieStr.includes('Secure'), 'Cookie string must include Secure attribute for production domains');
      },
    },
    {
      name: 'isTokenExpired accurately detects expired, fresh, and mock tokens',
      fn: () => {
        const now = Math.floor(Date.now() / 1000);
        const toB64Url = (obj: any) => {
          const str = JSON.stringify(obj);
          const raw = typeof btoa !== 'undefined'
            ? btoa(str)
            : (globalThis as any).Buffer.from(str).toString('base64');
          return raw.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
        };

        const expiredB64 = toB64Url({ sub: 'user1', exp: now - 60 });
        const expiredToken = `eyJhbGciOiJSUzI1NiJ9.${expiredB64}.fakesig`;
        assertEqual(isTokenExpired(expiredToken), true, 'Expired JWT must return true');

        const freshB64 = toB64Url({ sub: 'user2', exp: now + 3600 });
        const freshToken = `eyJhbGciOiJSUzI1NiJ9.${freshB64}.fakesig`;
        assertEqual(isTokenExpired(freshToken), false, 'Fresh JWT must return false');

        assertEqual(isTokenExpired('mock-token-123'), false, 'Non-JWT mock tokens should not be expired');
      },
    },
    {
      name: 'requestWithRetry proactively refreshes and transmits fresh token when stored token is expired',
      fn: async () => {
        localStorage.clear();
        const now = Math.floor(Date.now() / 1000);
        const toB64Url = (obj: any) => {
          const str = JSON.stringify(obj);
          const raw = typeof btoa !== 'undefined'
            ? btoa(str)
            : (globalThis as any).Buffer.from(str).toString('base64');
          return raw.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
        };
        const expiredB64 = toB64Url({ sub: 'u-exp', exp: now - 120 });
        const expiredToken = `header.${expiredB64}.sig`;
        localStorage.setItem('whicoustic_token', expiredToken);

        let initialAuthHeader: string | null = null;
        let fetchCallCount = 0;
        const originalFetch = globalThis.fetch;

        globalThis.fetch = (async (_input: RequestInfo | URL, init?: RequestInit) => {
          fetchCallCount++;
          const headers = new Headers(init?.headers);
          initialAuthHeader = headers.get('Authorization');
          return new Response(JSON.stringify({ success: true }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          });
        }) as typeof fetch;

        const originalAuth = auth;
        let forceRefreshPassed = false;
        setAuthForTesting({
          authStateReady: async () => {},
          currentUser: {
            getIdToken: async (force?: boolean) => {
              if (force) forceRefreshPassed = true;
              return 'newly-minted-fresh-token-777';
            },
          },
        });

        try {
          const res = await requestWithRetry<{ success: boolean }>(
            'https://api.whicoustic.xyz/api/v1/voices/',
            { method: 'GET' }
          );

          assertEqual(fetchCallCount, 1, 'Only 1 fetch call needed when proactive refresh catches expired token');
          assertEqual(forceRefreshPassed, true, 'forceRefresh=true must be passed to getIdToken on expired token');
          assertEqual(initialAuthHeader, 'Bearer newly-minted-fresh-token-777', 'Fresh token must be sent on initial fetch');
          assertEqual(localStorage.getItem('whicoustic_token'), 'newly-minted-fresh-token-777', 'Fresh token must be persisted');
          assertEqual(res.success, true, 'Response must be successful');
        } finally {
          globalThis.fetch = originalFetch;
          setAuthForTesting(originalAuth);
        }
      },
    },
    {
      name: 'buildClearCookieStrings attaches Secure attribute for HTTPS and production domains',
      fn: () => {
        const prodStrings = buildClearCookieStrings('app.whicoustic.xyz');
        assert(prodStrings.length >= 2, 'Should return root and host-only clear strings');
        for (const str of prodStrings) {
          assert(str.includes('; Secure'), `Clear string must include ; Secure for production: ${str}`);
        }

        const aiStrings = buildClearCookieStrings('whicoustic.ai');
        for (const str of aiStrings) {
          assert(str.includes('; Secure'), `Clear string must include ; Secure for whicoustic.ai: ${str}`);
        }
      },
    },
  ];

  console.log('======================================================================');
  console.log('WHICOUSTIC FRONTEND AUTH & API CLIENT TEST SUITE');
  console.log('======================================================================');

  for (const tc of testCases) {
    try {
      await tc.fn();
      console.log(`  [PASS] ${tc.name}`);
      passed++;
    } catch (err: any) {
      console.error(`  [FAIL] ${tc.name}:`, err.message || err);
      failed++;
    }
  }

  console.log('======================================================================');
  console.log(`TOTAL: ${passed + failed} | PASSED: ${passed} | FAILED: ${failed}`);
  console.log('======================================================================');

  return { passed, failed };
}

// Auto-run if executed in a standalone test runner environment
const proc = (globalThis as any).process;
if (proc && proc.argv && proc.argv.includes('--run')) {
  runApiClientTests().then(({ failed }: { failed: number }) => {
    if (failed > 0) proc.exit(1);
  });
}
