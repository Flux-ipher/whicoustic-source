/**
 * Automated Verification Script for Client-Side Age Gate (Milestone 2)
 * Tests `calculateAge`, `isAgeCompliant`, and compliance message assertions
 * on real TypeScript modules directly using Node.js runtime.
 * Includes exhaustive timezone boundary and leap-year tests.
 */

import { execSync } from 'child_process';
import { calculateAge, isAgeCompliant, COMPLIANCE_AGE_ERROR, MINIMUM_REGISTRATION_AGE } from '../frontend/src/utils/age.ts';

function assert(condition, message) {
  if (!condition) {
    console.error(`FAILED: ${message}`);
    process.exit(1);
  }
}

console.log('=====================================================================');
console.log('RUNNING WHICOUSTIC CLIENT-SIDE AGE GATE VERIFICATION');
console.log('=====================================================================');

const today = new Date();
const currentYear = today.getFullYear();
const currentMonth = today.getMonth() + 1; // 1-indexed
const currentDay = today.getDate();

const pad = (n) => String(n).padStart(2, '0');

// Format dates
const formatDate = (y, m, d) => `${y}-${pad(m)}-${pad(d)}`;

console.log('\n--- Part 1: Standard Age Calculation & Compliance Checks ---');

// 1. Underage: 15 years old
const dob15 = formatDate(currentYear - 15, currentMonth, currentDay);
assert(calculateAge(dob15) === 15, `Age 15 should calculate as 15, got ${calculateAge(dob15)}`);
assert(isAgeCompliant(dob15) === false, `Age 15 should NOT be compliant`);
console.log(`PASS: Underage (15 years, DOB: ${dob15}) blocked -> compliant: false`);

// 2. Underage: 10 years old
const dob10 = formatDate(currentYear - 10, currentMonth, currentDay);
assert(calculateAge(dob10) === 10, `Age 10 should calculate as 10, got ${calculateAge(dob10)}`);
assert(isAgeCompliant(dob10) === false, `Age 10 should NOT be compliant`);
console.log(`PASS: Underage (10 years, DOB: ${dob10}) blocked -> compliant: false`);

// 3. Boundary: Exactly 1 day before 17th birthday (16 years 364 days)
const tomorrow = new Date(today);
tomorrow.setDate(today.getDate() + 1);
const dobAlmost17 = formatDate(currentYear - 17, tomorrow.getMonth() + 1, tomorrow.getDate());
assert(calculateAge(dobAlmost17) === 16, `1 day before 17th birthday should calculate as 16, got ${calculateAge(dobAlmost17)}`);
assert(isAgeCompliant(dobAlmost17) === false, `1 day before 17th birthday should NOT be compliant`);
console.log(`PASS: Boundary (1 day before 17th birthday, DOB: ${dobAlmost17}) blocked -> age: 16, compliant: false`);

// 4. Boundary: Exact 17th birthday today
const dobExact17 = formatDate(currentYear - 17, currentMonth, currentDay);
assert(calculateAge(dobExact17) === 17, `Exact 17th birthday should calculate as 17, got ${calculateAge(dobExact17)}`);
assert(isAgeCompliant(dobExact17) === true, `Exact 17th birthday should be compliant`);
console.log(`PASS: Boundary (Exact 17th birthday, DOB: ${dobExact17}) allowed -> age: 17, compliant: true`);

// 5. Adult: 25 years old
const dob25 = formatDate(currentYear - 25, currentMonth, currentDay);
assert(calculateAge(dob25) === 25, `Age 25 should calculate as 25, got ${calculateAge(dob25)}`);
assert(isAgeCompliant(dob25) === true, `Age 25 should be compliant`);
console.log(`PASS: Adult (25 years, DOB: ${dob25}) allowed -> age: 25, compliant: true`);

// 6. Verify exact compliance error message string
const expectedMessage = 'Users must be at least 17 years old to register on Whicoustic in compliance with digital biometric licensing regulations.';
assert(COMPLIANCE_AGE_ERROR === expectedMessage, `Compliance error message mismatch: ${COMPLIANCE_AGE_ERROR}`);
console.log(`PASS: Compliance error string verified: "${COMPLIANCE_AGE_ERROR}"`);

// 7. Verify empty/invalid input handling
assert(calculateAge('') === 0, 'Empty DOB should return 0');
assert(isAgeCompliant('') === false, 'Empty DOB should not be compliant');
assert(calculateAge('invalid-date') === 0, 'Invalid DOB should return 0');
assert(isAgeCompliant('invalid-date') === false, 'Invalid DOB should not be compliant');
assert(calculateAge('2000-13-01') === 0, 'Invalid month (>12) should return 0');
assert(calculateAge('2000-01-32') === 0, 'Invalid day (>31) should return 0');
console.log(`PASS: Empty and invalid DOB safely rejected`);

console.log('\n--- Part 2: Calendar Edge Cases & Leap-Year Logic ---');

// 8. Leap Year & Boundary Scenarios with explicit reference dates
// Born 2008-02-29 evaluated on 2025-02-28 (16 years 365 days, not 17 yet)
const feb28_2025 = new Date(2025, 1, 28);
assert(calculateAge('2008-02-29', feb28_2025) === 16, 'Leap year birthday on Feb 28 should calculate as 16');
assert(isAgeCompliant('2008-02-29', feb28_2025) === false, 'Leap year birthday on Feb 28 should NOT be compliant');
console.log('PASS: Leap year Feb 29 birthday on Feb 28 of non-leap year -> age: 16 (blocked)');

// Born 2008-02-29 evaluated on 2025-03-01 (exact 17th birthday reached)
const mar01_2025 = new Date(2025, 2, 1);
assert(calculateAge('2008-02-29', mar01_2025) === 17, 'Leap year birthday on March 1 should calculate as 17');
assert(isAgeCompliant('2008-02-29', mar01_2025) === true, 'Leap year birthday on March 1 should be compliant');
console.log('PASS: Leap year Feb 29 birthday on March 1 of non-leap year -> age: 17 (allowed)');

// Year-end boundary: Born 2009-01-01 evaluated on 2025-12-31 (1 day before 17th)
const dec31_2025 = new Date(2025, 11, 31);
assert(calculateAge('2009-01-01', dec31_2025) === 16, 'Jan 1 birthday evaluated on Dec 31 should calculate as 16');
assert(isAgeCompliant('2009-01-01', dec31_2025) === false, 'Jan 1 birthday evaluated on Dec 31 should NOT be compliant');
console.log('PASS: Jan 1 birthday evaluated on Dec 31 -> age: 16 (blocked)');

// Year-end boundary: Born 2009-01-01 evaluated on 2026-01-01 (17th birthday)
const jan01_2026 = new Date(2026, 0, 1);
assert(calculateAge('2009-01-01', jan01_2026) === 17, 'Jan 1 birthday evaluated on Jan 1 should calculate as 17');
assert(isAgeCompliant('2009-01-01', jan01_2026) === true, 'Jan 1 birthday evaluated on Jan 1 should be compliant');
console.log('PASS: Jan 1 birthday evaluated on Jan 1 -> age: 17 (allowed)');

console.log('\n--- Part 3: Cross-Timezone Invariance Verification ---');

const testTimezones = [
  'America/New_York',       // UTC-5 (Eastern)
  'America/Chicago',        // UTC-6 (Central)
  'America/Los_Angeles',    // UTC-8 (Pacific)
  'Pacific/Honolulu',       // UTC-10 (Hawaii)
  'UTC',                    // UTC+0
  'Europe/London',          // UTC+0 / GMT
  'Europe/Berlin',          // UTC+1
  'Asia/Kolkata',           // UTC+5:30
  'Asia/Tokyo',             // UTC+9
  'Pacific/Auckland'        // UTC+12/13
];

for (const tz of testTimezones) {
  const runnerScript = `
    const { calculateAge, isAgeCompliant } = await import('./frontend/src/utils/age.ts');
    const localNow = new Date();
    const y = localNow.getFullYear();
    const m = localNow.getMonth() + 1;
    const d = localNow.getDate();
    const pad = (n) => String(n).padStart(2, '0');
    
    // Exact 17th birthday in this timezone
    const dobExact17 = \`\${y - 17}-\${pad(m)}-\${pad(d)}\`;
    if (calculateAge(dobExact17) !== 17 || !isAgeCompliant(dobExact17)) {
      console.error(\`Failed exact 17 in \${process.env.TZ}: got \${calculateAge(dobExact17)}\`);
      process.exit(1);
    }
    
    // Tomorrow (1 day before 17th birthday) in this timezone
    const nextDay = new Date(localNow);
    nextDay.setDate(localNow.getDate() + 1);
    const dobTomorrow = \`\${y - 17}-\${pad(nextDay.getMonth() + 1)}-\${pad(nextDay.getDate())}\`;
    if (calculateAge(dobTomorrow) !== 16 || isAgeCompliant(dobTomorrow)) {
      console.error(\`Failed 1 day before in \${process.env.TZ}: got \${calculateAge(dobTomorrow)}\`);
      process.exit(1);
    }
  `;

  try {
    execSync(`node --experimental-strip-types --input-type=module -e "${runnerScript.replace(/\n/g, ' ')}"`, {
      env: { ...process.env, TZ: tz },
      encoding: 'utf-8',
      stdio: 'pipe'
    });
    console.log(`PASS: Timezone ${tz.padEnd(22)} verified: exact 17 -> allowed, day-before -> blocked`);
  } catch (err) {
    console.error(`FAIL: Timezone check failed for ${tz}:`, err.message);
    process.exit(1);
  }
}

console.log('\n--- Part 4: Specific Reviewer M2-2 Adversarial Cases ---');

// Adversarial case: In America/New_York on 2026-11-05:
// DOB 2009-11-06 (16 years, 364 days old) MUST be blocked
const advScriptNY = `
  const { calculateAge, isAgeCompliant } = await import('./frontend/src/utils/age.ts');
  const nov05_2026 = new Date('2026-11-05T12:00:00');
  const age1 = calculateAge('2009-11-06', nov05_2026);
  const comp1 = isAgeCompliant('2009-11-06', nov05_2026);
  if (age1 !== 16 || comp1 !== false) {
    console.error('Adversarial 2009-11-06 failed: age=' + age1 + ' comp=' + comp1);
    process.exit(1);
  }
  const age2 = calculateAge('2009-01-01', new Date('2025-12-31T12:00:00'));
  const comp2 = isAgeCompliant('2009-01-01', new Date('2025-12-31T12:00:00'));
  if (age2 !== 16 || comp2 !== false) {
    console.error('Adversarial 2009-01-01 failed: age=' + age2 + ' comp=' + comp2);
    process.exit(1);
  }
`;

execSync(`node --experimental-strip-types --input-type=module -e "${advScriptNY.replace(/\n/g, ' ')}"`, {
  env: { ...process.env, TZ: 'America/New_York' },
  encoding: 'utf-8',
  stdio: 'pipe'
});
console.log('PASS: Reviewer M2-2 America/New_York adversarial tests (2009-11-06 & 2009-01-01) passed perfectly!');

console.log('\n=====================================================================');
console.log('ALL CLIENT-SIDE AGE GATE & TIMEZONE INVARIANCE CHECKS PASSED (100%)!');
console.log('=====================================================================');
