import { initializeApp, getApps, getApp, type FirebaseApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  GithubAuthProvider,
  type Auth,
  browserLocalPersistence,
  setPersistence,
} from 'firebase/auth';

const env = (typeof import.meta !== 'undefined' ? (import.meta as any).env : undefined) || {};
const apiKey = (env.VITE_FIREBASE_API_KEY as string) || '';

const firebaseConfig = {
  apiKey,
  authDomain: (env.VITE_FIREBASE_AUTH_DOMAIN as string) || '',
  projectId: (env.VITE_FIREBASE_PROJECT_ID as string) || '',
  storageBucket: (env.VITE_FIREBASE_STORAGE_BUCKET as string) || '',
  messagingSenderId: (env.VITE_FIREBASE_MESSAGING_SENDER_ID as string) || '',
  appId: (env.VITE_FIREBASE_APP_ID as string) || '',
  measurementId: (env.VITE_FIREBASE_MEASUREMENT_ID as string) || '',
};

export const isFirebaseConfigured = Boolean(
  apiKey && apiKey.length > 5 && apiKey !== 'your-firebase-api-key'
);

let appInstance: FirebaseApp | null = null;
let authInstance: Auth | null = null;

if (isFirebaseConfigured) {
  try {
    appInstance = !getApps().length ? initializeApp(firebaseConfig) : getApp();
    authInstance = getAuth(appInstance);
    // Explicitly enforce browserLocalPersistence across full page refreshes and tab reloads
    setPersistence(authInstance, browserLocalPersistence).catch((err) => {
      console.warn('Firebase persistence initialization note:', err);
    });
  } catch (err) {
    console.warn('Firebase initialization error:', err);
  }
} else {
  console.warn(
    'Firebase Auth credentials not detected in environment. Please set VITE_FIREBASE_API_KEY and VITE_FIREBASE_AUTH_DOMAIN in Vercel settings.'
  );
}

export const app = appInstance;
export let auth = authInstance;
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();

export function setAuthForTesting(mockAuth: any): void {
  auth = mockAuth;
}
