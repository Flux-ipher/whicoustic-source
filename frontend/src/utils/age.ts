/**
 * Age calculation and compliance utilities for Whicoustic registration.
 */

export const COMPLIANCE_AGE_ERROR =
  'Users must be at least 17 years old to register on Whicoustic in compliance with digital biometric licensing regulations.';

export const MINIMUM_REGISTRATION_AGE = 17;

/**
 * Calculates exact age in years from a date of birth string (YYYY-MM-DD).
 * Timezone-safe calendar parsing avoiding UTC midnight rollback in negative timezones.
 * Accurately takes leap years, months, and days into account.
 */
export const calculateAge = (dobString: string, referenceDate: Date = new Date()): number => {
  if (!dobString) return 0;
  const parts = dobString.split('-').map(Number);
  if (parts.length !== 3 || parts.some(isNaN)) return 0;
  const [birthYear, birthMonth, birthDay] = parts;
  if (birthYear <= 0 || birthMonth < 1 || birthMonth > 12 || birthDay < 1 || birthDay > 31) return 0;

  const currentYear = referenceDate.getFullYear();
  const currentMonth = referenceDate.getMonth() + 1; // 1-indexed to match birthMonth
  const currentDay = referenceDate.getDate();

  let age = currentYear - birthYear;
  if (currentMonth < birthMonth || (currentMonth === birthMonth && currentDay < birthDay)) {
    age--;
  }
  return Math.max(0, age);
};

/**
 * Validates whether the given DOB meets the minimum age requirement (>= 17).
 */
export const isAgeCompliant = (dobString: string, referenceDate: Date = new Date()): boolean => {
  return calculateAge(dobString, referenceDate) >= MINIMUM_REGISTRATION_AGE;
};

