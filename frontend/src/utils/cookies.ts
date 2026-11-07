/**
 * Domain-Scoped Cookie Helpers for Cross-Subdomain Session Persistence
 *
 * Implements Tier 2 fallback session persistence between apex domain
 * (whicoustic.xyz) and console subdomain (app.whicoustic.xyz).
 *
 * Architecture & Constraints:
 * 1. Production Scope: Sets Domain=.whicoustic.xyz so cookies are automatically
 *    accessible to all subdomains (*.whicoustic.xyz) under RFC 6265.
 * 2. Localhost Compatibility: Browsers reject cookies with Domain=.localhost.
 *    For localhost/127.0.0.1 environments, Domain is omitted (host-only)
 *    while Tier 1 URL hash handoff handles cross-origin transfer.
 * 3. Security: SameSite=Lax and Secure flags enforced in production/HTTPS.
 */

import type { SessionUser } from './authHandoff';

export const SESSION_COOKIE_NAME = 'whicoustic_session';
export const DEFAULT_COOKIE_MAX_AGE_SECONDS = 604800; // 7 days
export const PRODUCTION_ROOT_DOMAIN = '.whicoustic.xyz';

export interface CookieOptions {
  hostname?: string;
  isHttps?: boolean;
  maxAgeSeconds?: number;
}

/**
 * Determines appropriate cookie domain attribute.
 * Returns '.whicoustic.xyz' for production Whicoustic domains.
 * Returns empty string for localhost / local IP addresses.
 */
export function getCookieDomain(hostname?: string): string {
  const rawHost = hostname ||
    (typeof window !== 'undefined' && window.location && typeof window.location.hostname === 'string'
      ? window.location.hostname
      : '');

  const host = (rawHost || '').toLowerCase();

  if (!host) {
    return '';
  }

  // Local development: no domain attribute (host-only cookie)
  if (host === 'localhost' || host === '127.0.0.1' || host.endsWith('.localhost')) {
    return '';
  }

  // Whicoustic production apex or subdomains
  if (host === 'whicoustic.xyz' || host.endsWith('.whicoustic.xyz')) {
    return PRODUCTION_ROOT_DOMAIN;
  }

  // Generic two-part domain fallback (e.g. custom staging domains)
  const parts = host.split('.');
  if (parts.length >= 2) {
    return `.${parts.slice(-2).join('.')}`;
  }

  return '';
}

/**
 * Pure builder function to construct the Set-Cookie string.
 */
export function buildSessionCookieString(
  user: SessionUser,
  token: string,
  options?: CookieOptions
): string {
  const hostname = options?.hostname ||
    (typeof window !== 'undefined' && window.location && typeof window.location.hostname === 'string'
      ? window.location.hostname
      : '');
  const isHttps = options?.isHttps !== undefined
    ? options.isHttps
    : (typeof window !== 'undefined' && window.location ? window.location.protocol === 'https:' : false);
  const maxAge = options?.maxAgeSeconds ?? DEFAULT_COOKIE_MAX_AGE_SECONDS;

  const cookieDomain = getCookieDomain(hostname);
  const isProd = hostname.endsWith('whicoustic.xyz') || isHttps;

  const payload = encodeURIComponent(
    JSON.stringify({
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        role: user.role,
        avatar: user.avatar,
        vaultKey: user.vaultKey,
        isOnboarded: user.isOnboarded,
        dob: user.dob,
        token: user.token || token,
      },
      token,
      timestamp: Date.now(),
    })
  );

  let cookieStr = `${SESSION_COOKIE_NAME}=${payload}; path=/; max-age=${maxAge}; SameSite=Lax`;

  if (cookieDomain) {
    cookieStr += `; domain=${cookieDomain}`;
  }

  if (isProd) {
    cookieStr += '; Secure';
  }

  return cookieStr;
}

/**
 * Pure parser function to extract user and token from a raw cookie string.
 */
export function parseSessionCookieString(
  cookieHeader: string
): { user: SessionUser; token: string } | null {
  if (!cookieHeader || typeof cookieHeader !== 'string') {
    return null;
  }

  const cookies = cookieHeader.split(';');
  for (const cookie of cookies) {
    const trimmed = cookie.trim();
    if (trimmed.startsWith(`${SESSION_COOKIE_NAME}=`)) {
      const rawVal = trimmed.substring(`${SESSION_COOKIE_NAME}=`.length);
      if (!rawVal) return null;

      try {
        const decoded = decodeURIComponent(rawVal);
        const parsed = JSON.parse(decoded);

        if (!parsed || typeof parsed !== 'object') {
          return null;
        }

        const { user, token } = parsed;
        if (!user || !token || typeof token !== 'string') {
          return null;
        }

        if (!user.id || !user.email || typeof user.isOnboarded !== 'boolean') {
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
  }

  return null;
}

/**
 * Pure builder function to generate cookie removal strings for both root domain and host-only.
 */
export function buildClearCookieStrings(hostname?: string): string[] {
  const cookieDomain = getCookieDomain(hostname);
  const clearStrings = [
    `${SESSION_COOKIE_NAME}=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`,
  ];

  if (cookieDomain) {
    clearStrings.push(
      `${SESSION_COOKIE_NAME}=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 GMT; domain=${cookieDomain}; SameSite=Lax`
    );
  }

  return clearStrings;
}

/**
 * Sets domain-scoped session cookie in the browser.
 */
export function setSessionCookie(
  user: SessionUser,
  token: string,
  options?: CookieOptions
): void {
  if (typeof document === 'undefined') {
    return;
  }

  try {
    const cookieStr = buildSessionCookieString(user, token, options);
    document.cookie = cookieStr;
  } catch (err) {
    console.warn('Failed to set session cookie:', err);
  }
}

/**
 * Retrieves and deserializes the session from document.cookie.
 */
export function getSessionCookie(): { user: SessionUser; token: string } | null {
  if (typeof document === 'undefined') {
    return null;
  }

  try {
    return parseSessionCookieString(document.cookie);
  } catch (err) {
    console.warn('Failed to read session cookie:', err);
    return null;
  }
}

/**
 * Clears the session cookie across both domain-scoped and host-only scopes.
 */
export function clearSessionCookie(hostname?: string): void {
  if (typeof document === 'undefined') {
    return;
  }

  try {
    const clearStrings = buildClearCookieStrings(hostname);
    for (const str of clearStrings) {
      document.cookie = str;
    }
  } catch (err) {
    console.warn('Failed to clear session cookie:', err);
  }
}
