import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, GithubAuthProvider, Auth } from 'firebase/auth';

const apiKey = (import.meta.env.VITE_FIREBASE_API_KEY as string) || '';

const firebaseConfig = {
  apiKey,
  authDomain: (import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string) || '',
  projectId: (import.meta.env.VITE_FIREBASE_PROJECT_ID as string) || '',
  storageBucket: (import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string) || '',
  messagingSenderId: (import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string) || '',
  appId: (import.meta.env.VITE_FIREBASE_APP_ID as string) || '',
  measurementId: (import.meta.env.VITE_FIREBASE_MEASUREMENT_ID as string) || '',
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
  } catch (err) {
    console.warn('Firebase initialization error:', err);
  }
} else {
  console.warn(
    'Firebase Auth credentials not detected in environment. Please set VITE_FIREBASE_API_KEY and VITE_FIREBASE_AUTH_DOMAIN in Vercel settings.'
  );
}

export const app = appInstance;
export const auth = authInstance;
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();
