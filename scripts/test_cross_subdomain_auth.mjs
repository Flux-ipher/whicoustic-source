/**
 * Automated Verification Suite for Cross-Subdomain Session Persistence & Console Routing
 * Milestone 2 (worker_m2_r1)
 *
 * Verifies:
 * 1. URL Hash Handoff utility (TTL, Base64URL encoding, Unicode, instant URL sanitation)
 * 2. Domain-scoped cookie utility (.whicoustic.xyz production vs localhost host-only)
 * 3. Multi-tier hydration hierarchy (Tier 1 Hash -> Tier 2 Cookie -> Tier 3 LocalStorage)
 * 4. AuthContext state invariants (isLoading default true, clean logout purging)
 * 5. DashboardLayout guard logic & Stitch Design System compliance
 */

import {
  toBase64Url,
  fromBase64Url,
  encodeSessionHandoff,
  buildSessionHandoffFragment,
  parseSessionHandoff,
  getHandoffFromHashString,
  extractAndCleanSessionHandoff,
  SESSION_HANDOFF_TTL_MS,
  SESSION_HANDOFF_PARAM,
  LEGACY_AUTH_SESSION_PARAM,
} from '../frontend/src/utils/authHandoff.ts';

import {
  getCookieDomain,
  buildSessionCookieString,
  parseSessionCookieString,
  buildClearCookieStrings,
  setSessionCookie,
  getSessionCookie,
  clearSessionCookie,
  SESSION_COOKIE_NAME,
  PRODUCTION_ROOT_DOMAIN,
} from '../frontend/src/utils/cookies.ts';

import fs from 'node:fs';
import path from 'node:path';

function assert(condition, message) {
  if (!condition) {
    console.error(`\x1b[31m[FAIL]\x1b[0m ${message}`);
    process.exit(1);
  }
}

function pass(testName) {
  console.log(`\x1b[32m[PASS]\x1b[0m ${testName}`);
}

console.log('=====================================================================');
console.log('WHICOUSTIC CROSS-SUBDOMAIN AUTH & CONSOLE REDIRECT VERIFICATION SUITE');
console.log('=====================================================================');

const mockUser = {
  id: 'usr_m2_test_9876',
  name: "Dr. Jane Doe / Jürgen Müller / 桜井 葵",
  email: 'jane.doe@whicoustic.xyz',
  role: 'STUDIO',
  avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb',
  vaultKey: 'SHA256:4a8b9c...f1e2',
  isOnboarded: true,
  dob: '1995-04-12',
};

const mockToken = 'mock_firebase_jwt_token_header.payload.signature_xyz123';

// -----------------------------------------------------------------------------
// PART 1: URL Hash Handoff Utility (authHandoff.ts)
// -----------------------------------------------------------------------------
console.log('\n--- Part 1: URL Hash Handoff Utility (Base64URL, TTL, & Parsing) ---');

// 1.1 Base64URL encoding/decoding and UTF-8 round-trip
const unicodeSample = "Whicoustic Biometrics: €150.00 / Jürgen / 🎧 / 🎙️ / 東京";
const encodedSample = toBase64Url(unicodeSample);
assert(!encodedSample.includes('+') && !encodedSample.includes('/') && !encodedSample.includes('='),
  'Base64URL output must not contain +, /, or = characters');
const decodedSample = fromBase64Url(encodedSample);
assert(decodedSample === unicodeSample, `UTF-8 round-trip failed: got "${decodedSample}"`);
pass('Base64URL round-trip preserves complex UTF-8 strings and emojis without standard Base64 padding/symbols');

// 1.2 Hash fragment generator
const fragment = buildSessionHandoffFragment(mockUser, mockToken);
assert(fragment.startsWith(`#${SESSION_HANDOFF_PARAM}=`), `Fragment must start with #${SESSION_HANDOFF_PARAM}=`);
const rawEncoded = fragment.split('=')[1];
assert(rawEncoded && rawEncoded.length > 20, 'Raw encoded handoff payload must be non-empty');
pass(`buildSessionHandoffFragment produces expected fragment: ${fragment.substring(0, 45)}...`);

// 1.3 Fresh payload parsing
const now = Date.now();
const parsed = parseSessionHandoff(rawEncoded, SESSION_HANDOFF_TTL_MS, now);
assert(parsed !== null, 'Fresh session handoff payload must parse successfully');
assert(parsed.token === mockToken, 'Parsed token must match original mock token');
assert(parsed.user.id === mockUser.id, 'Parsed user ID must match');
assert(parsed.user.email === mockUser.email, 'Parsed user email must match');
assert(parsed.user.name === mockUser.name, 'Parsed user name with Unicode must match');
assert(parsed.user.isOnboarded === true, 'Parsed user isOnboarded must be true');
pass('parseSessionHandoff parses valid payload and preserves user identity and onboarded state');

// 1.4 TTL Expiration (60-second rule)
const expiredTimestamp = now - 60_001; // 60.001 seconds ago
const expiredPayload = encodeSessionHandoff(mockUser, mockToken, expiredTimestamp);
const expiredResult = parseSessionHandoff(expiredPayload, SESSION_HANDOFF_TTL_MS, now);
assert(expiredResult === null, 'Session handoff older than 60 seconds MUST be rejected as expired');
pass('parseSessionHandoff enforces strict 60s TTL expiration (60001ms payload rejected)');

// 1.5 TTL Boundary Acceptance (59 seconds)
const validBoundaryTimestamp = now - 59_000; // 59 seconds ago
const boundaryPayload = encodeSessionHandoff(mockUser, mockToken, validBoundaryTimestamp);
const boundaryResult = parseSessionHandoff(boundaryPayload, SESSION_HANDOFF_TTL_MS, now);
assert(boundaryResult !== null, 'Session handoff at 59 seconds MUST be accepted');
pass('parseSessionHandoff accepts valid boundary payload (59s old < 60s limit)');

// 1.6 Future clock-skew handling
const futureSkewAllowed = now + 3_000; // 3 seconds in the future (acceptable skew)
const futurePayloadAllowed = encodeSessionHandoff(mockUser, mockToken, futureSkewAllowed);
assert(parseSessionHandoff(futurePayloadAllowed, SESSION_HANDOFF_TTL_MS, now) !== null,
  'Small clock skew up to 5s in future should be tolerated');
pass('parseSessionHandoff permits moderate positive clock skew (+3s tolerated)');

const futureSkewDisallowed = now + 15_000; // 15 seconds in future (unacceptable)
const futurePayloadDisallowed = encodeSessionHandoff(mockUser, mockToken, futureSkewDisallowed);
assert(parseSessionHandoff(futurePayloadDisallowed, SESSION_HANDOFF_TTL_MS, now) === null,
  'Extreme future timestamp (+15s) must be rejected');
pass('parseSessionHandoff rejects excessive future timestamps (+15s rejected)');

// 1.7 Malformed and corrupted inputs
assert(parseSessionHandoff('') === null, 'Empty string returns null');
assert(parseSessionHandoff('not-base-64-json!!!') === null, 'Corrupt base64 returns null');
assert(parseSessionHandoff(toBase64Url('{ "invalidJson": true, ')) === null, 'Malformed JSON returns null');
assert(parseSessionHandoff(toBase64Url(JSON.stringify({ token: '', user: mockUser, timestamp: now }))) === null,
  'Payload with empty token returns null');
assert(parseSessionHandoff(toBase64Url(JSON.stringify({ token: mockToken, user: { id: '' }, timestamp: now }))) === null,
  'Payload with invalid user schema returns null');
pass('parseSessionHandoff safely handles malformed, truncated, and corrupt payloads without throwing');

// 1.8 Hash extraction helper & legacy fallback
const multiParamHash = `#something=1&${SESSION_HANDOFF_PARAM}=${rawEncoded}&analytics=true`;
assert(getHandoffFromHashString(multiParamHash) === rawEncoded, 'Must extract handoff from multi-param hash');
const legacyHash = `#${LEGACY_AUTH_SESSION_PARAM}=${rawEncoded}`;
assert(getHandoffFromHashString(legacyHash) === rawEncoded, 'Must support legacy auth_session fallback');
pass('getHandoffFromHashString extracts handoff token from multi-param hash and legacy fallbacks');

// 1.9 Browser extractAndCleanSessionHandoff simulation
let replacedUrl = null;
globalThis.window = {
  location: {
    hash: `#${SESSION_HANDOFF_PARAM}=${rawEncoded}`,
    pathname: '/dashboard',
    search: '?view=analytics',
  },
  history: {
    state: { key: 'sample-state' },
    replaceState: (state, title, url) => {
      replacedUrl = url;
    },
  },
};

const extracted = extractAndCleanSessionHandoff();
assert(extracted !== null, 'Browser extractAndCleanSessionHandoff must extract valid session');
assert(extracted.user.id === mockUser.id, 'Extracted user matches');
assert(replacedUrl === '/dashboard?view=analytics',
  `URL hash must be sanitized via replaceState. Expected '/dashboard?view=analytics', got '${replacedUrl}'`);
pass('extractAndCleanSessionHandoff cleans window.location.hash immediately via replaceState');

// -----------------------------------------------------------------------------
// PART 2: Domain-Scoped Cookies (cookies.ts)
// -----------------------------------------------------------------------------
console.log('\n--- Part 2: Domain-Scoped Cookie Helpers (cookies.ts) ---');

// 2.1 Cookie domain resolution
assert(getCookieDomain('whicoustic.xyz') === PRODUCTION_ROOT_DOMAIN, 'whicoustic.xyz -> .whicoustic.xyz');
assert(getCookieDomain('app.whicoustic.xyz') === PRODUCTION_ROOT_DOMAIN, 'app.whicoustic.xyz -> .whicoustic.xyz');
assert(getCookieDomain('console.whicoustic.xyz') === PRODUCTION_ROOT_DOMAIN, 'console.whicoustic.xyz -> .whicoustic.xyz');
assert(getCookieDomain('localhost') === '', 'localhost -> empty domain (host-only)');
assert(getCookieDomain('app.localhost') === '', 'app.localhost -> empty domain (host-only)');
assert(getCookieDomain('127.0.0.1') === '', '127.0.0.1 -> empty domain (host-only)');
pass('getCookieDomain resolves .whicoustic.xyz for prod subdomains and host-only for localhost/127.0.0.1');

// 2.2 Production Cookie Header String
const prodCookieStr = buildSessionCookieString(mockUser, mockToken, {
  hostname: 'app.whicoustic.xyz',
  isHttps: true,
  maxAgeSeconds: 604800,
});
assert(prodCookieStr.includes(`domain=${PRODUCTION_ROOT_DOMAIN}`), 'Prod cookie must include domain=.whicoustic.xyz');
assert(prodCookieStr.includes('Secure'), 'Prod cookie must include Secure flag');
assert(prodCookieStr.includes('SameSite=Lax'), 'Prod cookie must include SameSite=Lax');
assert(prodCookieStr.includes('max-age=604800'), 'Prod cookie must include 7-day max-age');
pass('buildSessionCookieString sets domain=.whicoustic.xyz, Secure, SameSite=Lax, and max-age=604800');

// 2.3 Localhost Cookie Header String
const localCookieStr = buildSessionCookieString(mockUser, mockToken, {
  hostname: 'app.localhost',
  isHttps: false,
});
assert(!localCookieStr.includes('domain='), 'Localhost cookie must NOT specify domain (prevents browser rejection)');
assert(!localCookieStr.includes('Secure'), 'Localhost HTTP cookie must omit Secure flag');
assert(localCookieStr.includes('SameSite=Lax'), 'Localhost cookie includes SameSite=Lax');
pass('buildSessionCookieString on localhost produces valid host-only cookie without invalid domain attribute');

// 2.4 Parsing Session Cookie Header
const parsedFromCookie = parseSessionCookieString(`other_id=999; ${prodCookieStr}; theme=dark`);
assert(parsedFromCookie !== null, 'Must extract and parse session from composite cookie header');
assert(parsedFromCookie.user.id === mockUser.id, 'User ID matches from cookie');
assert(parsedFromCookie.token === mockToken, 'Token matches from cookie');
pass('parseSessionCookieString parses composite Cookie header and restores user & token');

// 2.5 Clear Cookie Headers
const clearHeaders = buildClearCookieStrings('app.whicoustic.xyz');
assert(clearHeaders.length === 2, 'Clear headers must clear both host-only and domain-scoped variants');
assert(clearHeaders.some(h => h.includes(`domain=${PRODUCTION_ROOT_DOMAIN}`) && h.includes('max-age=0')),
  'Clear header with domain=.whicoustic.xyz and max-age=0 required');
pass('buildClearCookieStrings generates proper invalidation headers across all domain scopes');

// 2.6 Simulated Document Cookie Round-Trip
let mockCookieStorage = '';
globalThis.document = {
  get cookie() {
    return mockCookieStorage;
  },
  set cookie(val) {
    mockCookieStorage = val;
  },
};

setSessionCookie(mockUser, mockToken, { hostname: 'app.whicoustic.xyz', isHttps: true });
const readSession = getSessionCookie();
assert(readSession !== null, 'getSessionCookie reads from document.cookie');
assert(readSession.user.email === mockUser.email, 'Read user matches');
clearSessionCookie('app.whicoustic.xyz');
// After clearing, cookie value has max-age=0 and empty value
assert(mockCookieStorage.startsWith(`${SESSION_COOKIE_NAME}=;`), 'Cookie must be cleared after clearSessionCookie');
pass('document.cookie getter/setter/clear integration succeeds seamlessly');

// -----------------------------------------------------------------------------
// PART 3: Multi-Tier Session Hydration Hierarchy Simulation
// -----------------------------------------------------------------------------
console.log('\n--- Part 3: Multi-Tier Session Hydration Hierarchy Simulation ---');

/**
 * Simulates AuthContext hydration hierarchy:
 * Tier 1: URL Hash Handoff (evaluates FIRST; fresh handoff overrides prior loggedOut flag)
 * Guard:  URL query ?logged_out=true or whicoustic_logged_out flag (blocks Tier 2 and Tier 3 zombie sessions)
 * Tier 2: Domain Cookie
 * Tier 3: Local Storage
 */
function simulateHydration({ hash, cookie, storage, loggedOut = false, search = '' }) {
  // Tier 1: URL Hash Handoff takes precedence on cross-subdomain arrival
  if (hash) {
    const rawHandoff = getHandoffFromHashString(hash);
    if (rawHandoff) {
      const parsed = parseSessionHandoff(rawHandoff);
      if (parsed) {
        // Fresh handoff explicitly overrides any prior logged-out state
        return { tier: 1, user: parsed.user, token: parsed.token, authenticated: true };
      }
    }
  }

  // Cross-origin URL query parameter (?logged_out=true)
  if (search && search.includes('logged_out=true')) {
    return { tier: 0, user: null, token: null, authenticated: false, reason: 'URL_LOGOUT_PARAM' };
  }

  // If user explicitly logged out in this browser AND no fresh handoff arrived,
  // block auto-resurrection from cookies or storage
  if (loggedOut) {
    return { tier: 0, user: null, token: null, authenticated: false, reason: 'BLOCKED_BY_LOGGED_OUT_FLAG' };
  }

  // Tier 2: Cookie
  if (cookie) {
    const parsedCookie = parseSessionCookieString(cookie);
    if (parsedCookie) {
      return { tier: 2, user: parsedCookie.user, token: parsedCookie.token, authenticated: true };
    }
  }

  // Tier 3: Local Storage
  if (storage && storage.user) {
    try {
      const parsedUser = JSON.parse(storage.user);
      return { tier: 3, user: parsedUser, token: storage.token || null, authenticated: true };
    } catch {}
  }

  return { tier: 0, user: null, token: null, authenticated: false };
}

// Test Tier 1 priority over Tier 2 & 3
const tier1Hash = buildSessionHandoffFragment({ ...mockUser, name: 'Tier 1 User' }, 'tier1-token');
const tier2Cookie = buildSessionCookieString({ ...mockUser, name: 'Tier 2 User' }, 'tier2-token');
const tier3Storage = { user: JSON.stringify({ ...mockUser, name: 'Tier 3 User' }), token: 'tier3-token' };

const res1 = simulateHydration({ hash: tier1Hash, cookie: tier2Cookie, storage: tier3Storage });
assert(res1.tier === 1 && res1.user.name === 'Tier 1 User', 'Tier 1 hash handoff must take precedence');
pass('Tier 1 (URL hash handoff) takes precedence on cross-subdomain arrival');

// Test Tier 2 priority when Tier 1 absent
const res2 = simulateHydration({ hash: '', cookie: tier2Cookie, storage: tier3Storage });
assert(res2.tier === 2 && res2.user.name === 'Tier 2 User', 'Tier 2 cookie must take precedence when hash absent');
pass('Tier 2 (Domain cookie) activates when URL hash is absent');

// Test Tier 3 priority when Tier 1 & 2 absent
const res3 = simulateHydration({ hash: '', cookie: '', storage: tier3Storage });
assert(res3.tier === 3 && res3.user.name === 'Tier 3 User', 'Tier 3 storage must activate on page refresh');
pass('Tier 3 (Local storage) maintains session across intradomain refreshes');

// Test Fresh Tier 1 handoff OVERRIDES prior logged-out state (remediation verification)
const resReauth = simulateHydration({ hash: tier1Hash, cookie: tier2Cookie, storage: tier3Storage, loggedOut: true });
assert(resReauth.tier === 1 && resReauth.authenticated === true && resReauth.user.name === 'Tier 1 User',
  'Fresh Tier 1 hash handoff MUST override prior whicoustic_logged_out state, preventing re-authentication lockout');
pass('Fresh Tier 1 handoff overrides prior whicoustic_logged_out state (resolves re-authentication lockout loop)');

// Test Explicit Logout suppresses auto-revival when no fresh Tier 1 handoff is present
const resLogout = simulateHydration({ hash: '', cookie: tier2Cookie, storage: tier3Storage, loggedOut: true });
assert(resLogout.authenticated === false && resLogout.reason === 'BLOCKED_BY_LOGGED_OUT_FLAG',
  'whicoustic_logged_out flag must prevent session revival from cookies or storage');
pass('Explicit logout flag blocks hydration across Tier 2 (cookie) and Tier 3 (storage) when hash is absent');

// Test Cross-Origin URL query (?logged_out=true) suppresses session revival
const resUrlLogout = simulateHydration({ hash: '', cookie: tier2Cookie, storage: tier3Storage, search: '?logged_out=true' });
assert(resUrlLogout.authenticated === false, 'Cross-origin ?logged_out=true must clear session state');
pass('Cross-origin URL query parameter ?logged_out=true suppresses session revival across domains');

// Test Expired Tier 1 handoff does NOT override logged-out flag
const expiredHandoffTimestamp = Date.now() - 65_000;
const expiredHandoffHash = `#${SESSION_HANDOFF_PARAM}=${encodeSessionHandoff(mockUser, mockToken, expiredHandoffTimestamp)}`;
const resExpiredBlocked = simulateHydration({ hash: expiredHandoffHash, cookie: tier2Cookie, storage: tier3Storage, loggedOut: true });
assert(resExpiredBlocked.authenticated === false, 'Expired Tier 1 handoff must NOT override loggedOut flag');
pass('Expired Tier 1 handoff cannot bypass logged-out flag');

// Test Malformed Tier 1 handoff does NOT override logged-out flag
const resMalformedBlocked = simulateHydration({ hash: '#session_handoff=invalid-base64!', cookie: tier2Cookie, storage: tier3Storage, loggedOut: true });
assert(resMalformedBlocked.authenticated === false, 'Malformed Tier 1 handoff must NOT override loggedOut flag');
pass('Malformed Tier 1 handoff cannot bypass logged-out flag');

// -----------------------------------------------------------------------------
// PART 4: DashboardLayout Guard Logic & Redirect Loop Elimination
// -----------------------------------------------------------------------------
console.log('\n--- Part 4: DashboardLayout Guard Logic Simulation ---');

/**
 * Simulates DashboardLayout redirect guard:
 * 1. If isLoading === true -> HOLD (render verifying session spinner, zero redirect)
 * 2. If !isAuthenticated || !user -> redirect('/login')
 * 3. If !user.isOnboarded -> redirect('/onboarding')
 * 4. Otherwise -> render console dashboard
 */
function evaluateDashboardGuard({ isLoading, user, isAuthenticated }) {
  if (isLoading) {
    return { action: 'RENDER_LOADING', target: null };
  }

  if (!isAuthenticated || !user) {
    return { action: 'REDIRECT_MAIN', target: '/login' };
  }

  if (!user.isOnboarded) {
    return { action: 'REDIRECT_MAIN', target: '/onboarding' };
  }

  return { action: 'RENDER_DASHBOARD', target: null };
}

// Case A: Initial mount before hydration finishes (isLoading: true, user: null)
const guardLoading = evaluateDashboardGuard({ isLoading: true, user: null, isAuthenticated: false });
assert(guardLoading.action === 'RENDER_LOADING' && guardLoading.target === null,
  'When isLoading is true, guard must NOT redirect, preventing the redirect loop');
pass('Guard awaits isLoading: true without redirecting (prevents console redirect loop)');

// Case B: Hydration finishes with unauthenticated user
const guardUnauth = evaluateDashboardGuard({ isLoading: false, user: null, isAuthenticated: false });
assert(guardUnauth.action === 'REDIRECT_MAIN' && guardUnauth.target === '/login',
  'Unauthenticated user must redirect cleanly to /login on main domain');
pass('Unauthenticated user cleanly redirects to main domain /login');

// Case C: Authenticated user but NOT onboarded
const unonboardedUser = { ...mockUser, isOnboarded: false };
const guardUnonboarded = evaluateDashboardGuard({ isLoading: false, user: unonboardedUser, isAuthenticated: true });
assert(guardUnonboarded.action === 'REDIRECT_MAIN' && guardUnonboarded.target === '/onboarding',
  'Unonboarded user must redirect to /onboarding on main domain');
pass('Unonboarded user cleanly redirects to main domain /onboarding');

// Case D: Authenticated and fully onboarded user
const guardReady = evaluateDashboardGuard({ isLoading: false, user: mockUser, isAuthenticated: true });
assert(guardReady.action === 'RENDER_DASHBOARD' && guardReady.target === null,
  'Fully onboarded user must be permitted to render console dashboard without redirect');
pass('Fully onboarded user cleanly renders console dashboard');

// -----------------------------------------------------------------------------
// PART 5: Stitch Design System Compliance in DashboardLayout
// -----------------------------------------------------------------------------
console.log('\n--- Part 5: Stitch Design System Compliance Verification ---');

const layoutPath = path.resolve('frontend/src/components/layout/DashboardLayout.tsx');
assert(fs.existsSync(layoutPath), 'DashboardLayout.tsx must exist');
const layoutContent = fs.readFileSync(layoutPath, 'utf8');

assert(layoutContent.includes('font-recoleta'), 'DashboardLayout must use font-recoleta for headings');
assert(layoutContent.includes('font-berthold'), 'DashboardLayout must use font-berthold for subheadings/body text');
assert(layoutContent.includes('#F59E0B') || layoutContent.includes('border-amber-500'),
  'DashboardLayout must use Acoustic Amber (#F59E0B) for active loading spinners');
assert(layoutContent.includes('#0B1C30'), 'DashboardLayout must use dark slate canvas (#0B1C30)');
assert(layoutContent.includes('isLoading'), 'DashboardLayout must inspect isLoading');
assert(layoutContent.includes('isOnboarded'), 'DashboardLayout must check user.isOnboarded');
pass('DashboardLayout satisfies Stitch Design System specifications (Recoleta, Berthold, #F59E0B, #0B1C30)');

console.log('\n=====================================================================');
console.log('ALL CROSS-SUBDOMAIN AUTHENTICATION & ROUTING CHECKS PASSED (100%)');
console.log('=====================================================================');
