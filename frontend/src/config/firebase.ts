import { initializeApp, getApps, getApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from 'firebase/auth';

const firebaseConfig = {
  apiKey: (import.meta.env.VITE_FIREBASE_API_KEY as string),
  authDomain: (import.meta.env.VITE_FIREBASE_AUTH_DOMAIN as string),
  projectId: (import.meta.env.VITE_FIREBASE_PROJECT_ID as string),
  storageBucket: (import.meta.env.VITE_FIREBASE_STORAGE_BUCKET as string),
  messagingSenderId: (import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID as string),
  appId: (import.meta.env.VITE_FIREBASE_APP_ID as string),
  measurementId: (import.meta.env.VITE_FIREBASE_MEASUREMENT_ID as string),
};

// Initialize Firebase App
export const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();

// Initialize Firebase Auth
export const auth = getAuth(app);

// Providers
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();
