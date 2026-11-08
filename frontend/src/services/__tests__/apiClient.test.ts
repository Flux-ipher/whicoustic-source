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
  ApiError,
  getApiBaseUrl,
} from '../apiClient';
import { auth } from '../../config/firebase';

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
        const originalUser = (auth as any)?.currentUser;
        let getIdTokenCalled = false;
        (auth as any).currentUser = {
          getIdToken: async (forceRefresh?: boolean) => {
            if (forceRefresh) getIdTokenCalled = true;
            return 'freshly-refreshed-firebase-token-999';
          },
        };

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
          if (auth) {
            (auth as any).currentUser = originalUser;
          }
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
