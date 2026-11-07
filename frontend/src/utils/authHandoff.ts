/**
 * Cross-Subdomain URL Hash Session Handoff Utility
 *
 * Implements Tier 1 ephemeral session transfer between Whicoustic apex domain
 * (whicoustic.xyz / localhost:5173) and console subdomain (app.whicoustic.xyz / app.localhost:5173).
 *
 * Architecture & Security Guarantees:
 * 1. Client-Side Only (RFC 3986 §3.5): Transferred purely in URL hash fragment
 *    (#session_handoff=<base64url_json>). URL hash fragments are never sent over HTTP/HTTPS
 *    to origin or proxy servers, guaranteeing zero server log / referrer leakage.
 * 2. Ephemeral TTL: Maximum validity of 60 seconds (Date.now() - timestamp < 60000)
 *    to prevent token replay attacks or stale transfers.
 * 3. Instant URL Sanitization: Immediately stripped from the browser address bar via
 *    window.history.replaceState upon extraction.
 * 4. Safe Encoding: URL-safe Base64 encoding compatible with UTF-8 characters and
 *    both Browser and Node.js environments.
 */

export interface SessionUser {
  id: string;
  name: string;
  email: string;
  role: 'TALENT' | 'STUDIO' | 'ENTERPRISE';
  avatar?: string;
  vaultKey?: string;
  isOnboarded: boolean;
  dob?: string;
  token?: string;
}

export interface SessionHandoffPayload {
  token: string;
  user: SessionUser;
  timestamp: number;
}

export const SESSION_HANDOFF_TTL_MS = 60_000; // 60 seconds
export const SESSION_HANDOFF_PARAM = 'session_handoff';
export const LEGACY_AUTH_SESSION_PARAM = 'auth_session';

/**
 * Universal Base64URL encoder supporting full UTF-8 Unicode.
 */
export function toBase64Url(str: string): string {
  const buf = typeof globalThis !== 'undefined' && 'Buffer' in globalThis
    ? (globalThis as Record<string, any>).Buffer
    : undefined;

  if (buf && typeof buf.from === 'function') {
    return buf.from(str, 'utf-8')
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');
  }

  const utf8Bytes = new TextEncoder().encode(str);
  let binary = '';
  for (let i = 0; i < utf8Bytes.length; i++) {
    binary += String.fromCharCode(utf8Bytes[i]);
  }
  return btoa(binary)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

/**
 * Universal Base64URL decoder supporting full UTF-8 Unicode.
 */
export function fromBase64Url(base64Url: string): string {
  let base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4 !== 0) {
    base64 += '=';
  }

  const buf = typeof globalThis !== 'undefined' && 'Buffer' in globalThis
    ? (globalThis as Record<string, any>).Buffer
    : undefined;

  if (buf && typeof buf.from === 'function') {
    return buf.from(base64, 'base64').toString('utf-8');
  }

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new TextDecoder().decode(bytes);
}

/**
 * Encodes a user and auth token into a Base64URL-encoded session handoff string.
 */
export function encodeSessionHandoff(
  user: SessionUser,
  token: string,
  timestamp: number = Date.now()
): string {
  const payload: SessionHandoffPayload = {
    token,
    user,
    timestamp,
  };
  return toBase64Url(JSON.stringify(payload));
}

/**
 * Builds the URL hash fragment for cross-subdomain navigation.
 * E.g., `#session_handoff=<base64url_json>`
 */
export function buildSessionHandoffFragment(
  user: SessionUser,
  token: string,
  timestamp: number = Date.now()
): string {
  const encoded = encodeSessionHandoff(user, token, timestamp);
  return `#${SESSION_HANDOFF_PARAM}=${encoded}`;
}

/**
 * Parses, validates, and expires a raw session handoff string.
 * Returns { user, token } on success, or null if invalid or expired.
 */
export function parseSessionHandoff(
  rawHandoff: string,
  maxAgeMs: number = SESSION_HANDOFF_TTL_MS,
  referenceTime: number = Date.now()
): { user: SessionUser; token: string } | null {
  if (!rawHandoff || typeof rawHandoff !== 'string') {
    return null;
  }

  try {
    const jsonStr = fromBase64Url(rawHandoff);
    const payload = JSON.parse(jsonStr) as SessionHandoffPayload;

    if (!payload || typeof payload !== 'object') {
      return null;
    }

    const { token, user, timestamp } = payload;

    // Validate token
    if (!token || typeof token !== 'string') {
      return null;
    }

    // Validate timestamp and TTL
    if (typeof timestamp !== 'number' || !Number.isFinite(timestamp)) {
      return null;
    }

    const age = referenceTime - timestamp;
    // Allow up to 5 seconds of positive clock skew between systems
    if (age > maxAgeMs || age < -5_000) {
      return null;
    }

    // Validate user object essentials
    if (!user || typeof user !== 'object') {
      return null;
    }

    if (!user.id || typeof user.id !== 'string') {
      return null;
    }

    if (!user.email || typeof user.email !== 'string') {
      return null;
    }

    if (typeof user.isOnboarded !== 'boolean') {
      return null;
    }

    return {
      user: {
        ...user,
        token: user.token || token,
      },
      token,
    };
  } catch {
    return null;
  }
}

/**
 * Extracts session handoff from a hash string (e.g. window.location.hash).
 * Returns the raw handoff token if found.
 */
export function getHandoffFromHashString(hash: string): string | null {
  if (!hash) return null;
  const cleanHash = hash.startsWith('#') ? hash.slice(1) : hash;
  if (!cleanHash) return null;

  // Check query-style hash params
  const params = new URLSearchParams(cleanHash);
  const handoff = params.get(SESSION_HANDOFF_PARAM) || params.get(LEGACY_AUTH_SESSION_PARAM);
  if (handoff) return handoff;

  // Direct regex fallback in case URLSearchParams encoded special chars
  const regex = new RegExp(`(?:^|&)(?:${SESSION_HANDOFF_PARAM}|${LEGACY_AUTH_SESSION_PARAM})=([^&]+)`);
  const match = cleanHash.match(regex);
  if (match && match[1]) {
    try {
      return decodeURIComponent(match[1]);
    } catch {
      return match[1];
    }
  }

  return null;
}

/**
 * Client-side browser function:
 * Extracts session handoff from window.location.hash, validates TTL,
 * immediately cleans the browser address bar via window.history.replaceState,
 * and returns the hydrated session credentials.
 */
export function extractAndCleanSessionHandoff(
  maxAgeMs: number = SESSION_HANDOFF_TTL_MS
): { user: SessionUser; token: string } | null {
  if (typeof window === 'undefined' || !window.location) {
    return null;
  }

  const hash = window.location.hash;
  if (!hash) {
    return null;
  }

  const rawHandoff = getHandoffFromHashString(hash);
  if (!rawHandoff) {
    return null;
  }

  const result = parseSessionHandoff(rawHandoff, maxAgeMs);

  // Instantly clean the hash from the browser address bar
  try {
    if (window.history && window.history.replaceState) {
      // Retain search params if any, remove hash
      const cleanUrl = window.location.pathname + window.location.search;
      window.history.replaceState(window.history.state, '', cleanUrl);
    }
  } catch (err) {
    console.warn('Failed to sanitize URL hash:', err);
  }

  return result;
}
