import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile,
} from 'firebase/auth';
import { auth, googleProvider, githubProvider } from '../config/firebase';
import { useDomain } from './DomainContext';
import { getApiBaseUrl } from '../services/apiClient';

export interface User {
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

export interface OnboardingData {
  role: string;
  primaryCategory: string;
  voiceGender: string;
  language: string;
  acousticAnchorRecorded: boolean;
  watermarkSha256: string;
  royaltyFloorPct: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  onboardingData: OnboardingData;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  signup: (email: string, password?: string, name?: string, dob?: string) => Promise<void>;
  login: (email: string, password?: string) => Promise<void>;
  loginWithOAuth: (provider: 'google' | 'github') => Promise<void>;
  completeOnboarding: () => void;
  logout: () => void;
}

const defaultOnboarding: OnboardingData = {
  role: 'TALENT',
  primaryCategory: 'Cinematic Narration',
  voiceGender: 'Neutral / Dynamic',
  language: 'English (US / Neutral)',
  acousticAnchorRecorded: false,
  watermarkSha256: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  royaltyFloorPct: 18.5,
};

const formatFirebaseError = (err: any): string => {
  if (!err || typeof err !== 'object') return 'Authentication failed. Please try again.';
  const code = err.code;
  switch (code) {
    case 'auth/email-already-in-use':
      return 'This email address is already in use. Please log in instead.';
    case 'auth/invalid-email':
      return 'Invalid email address format.';
    case 'auth/weak-password':
      return 'Password should be at least 6 characters.';
    case 'auth/user-not-found':
      return 'No account found with this email. Please register.';
    case 'auth/wrong-password':
    case 'auth/invalid-credential':
      return 'Incorrect email or password. Please verify your credentials.';
    case 'auth/popup-closed-by-user':
      return 'Authentication popup was closed before completing.';
    case 'auth/unauthorized-domain':
      return 'Domain not authorized in Firebase. Please add this domain to Firebase Console > Authentication > Authorized domains.';
    default:
      return err.message || 'Authentication failed. Please check your credentials and try again.';
  }
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { navigateToSubdomain, navigateToMainDomain } = useDomain();

  const [user, setUser] = useState<User | null>(() => {
    // If explicitly logged out, do not revive session
    if (localStorage.getItem('whicoustic_logged_out') === 'true') {
      return null;
    }

    const saved = localStorage.getItem('whicoustic_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return null;
      }
    }
    return null;
  });

  const [onboardingData, setOnboardingData] = useState<OnboardingData>(() => {
    const saved = localStorage.getItem('whicoustic_onboarding');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return defaultOnboarding;
      }
    }
    return defaultOnboarding;
  });

  // Sync session state with Firebase Auth
  useEffect(() => {
    if (!auth) {
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      if (localStorage.getItem('whicoustic_logged_out') === 'true') {
        return;
      }

      if (fbUser) {
        try {
          const token = await fbUser.getIdToken();
          localStorage.setItem('whicoustic_token', token);

          setUser((prev) => {
            if (!prev) {
              const restored: User = {
                id: fbUser.uid,
                name: fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
                email: fbUser.email || '',
                role: 'TALENT',
                avatar: fbUser.photoURL || undefined,
                isOnboarded: true,
                token,
              };
              localStorage.setItem('whicoustic_user', JSON.stringify(restored));
              return restored;
            }
            const updated = { ...prev, token };
            localStorage.setItem('whicoustic_user', JSON.stringify(updated));
            return updated;
          });
        } catch (tokenErr) {
          console.warn('Failed to retrieve Firebase ID token:', tokenErr);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  const updateOnboardingData = (data: Partial<OnboardingData>) => {
    setOnboardingData((prev) => {
      const updated = { ...prev, ...data };
      localStorage.setItem('whicoustic_onboarding', JSON.stringify(updated));
      return updated;
    });
  };

  const syncWithBackend = async (token: string, fbUser: { uid: string; email: string | null; displayName: string | null; photoURL: string | null }, name?: string) => {
    const apiBase = getApiBaseUrl();
    try {
      const syncRes = await fetch(`${apiBase}/api/v1/users/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          uid: fbUser.uid,
          email: fbUser.email,
          name: name || fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
          photo_url: fbUser.photoURL,
        }),
      });

      if (syncRes.ok) {
        return await syncRes.json();
      }
    } catch (err) {
      console.warn('Backend user synchronization deferred:', err);
    }
    return null;
  };

  const signup = async (email: string, password?: string, name?: string, dob?: string) => {
    localStorage.removeItem('whicoustic_logged_out');

    if (!auth) {
      throw new Error(
        'Authentication service not configured. Please add VITE_FIREBASE_API_KEY to your Vercel Environment Variables.'
      );
    }

    try {
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password || 'DefaultPassword123!'
      );
      const fbUser = userCredential.user;

      if (name) {
        await updateProfile(fbUser, { displayName: name }).catch(() => {});
      }

      const token = await fbUser.getIdToken();
      localStorage.setItem('whicoustic_token', token);

      const synced = await syncWithBackend(token, fbUser, name);

      const newUser: User = {
        id: synced?.id ? String(synced.id) : fbUser.uid,
        name: synced?.name || name || fbUser.displayName || email.split('@')[0],
        email: fbUser.email || email,
        role: 'TALENT',
        isOnboarded: false,
        dob,
        token,
      };

      setUser(newUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(newUser));
    } catch (err: any) {
      throw new Error(formatFirebaseError(err));
    }
  };

  const login = async (email: string, password?: string) => {
    localStorage.removeItem('whicoustic_logged_out');

    if (!auth) {
      throw new Error(
        'Authentication service not configured. Please add VITE_FIREBASE_API_KEY to your Vercel Environment Variables.'
      );
    }

    try {
      const userCredential = await signInWithEmailAndPassword(
        auth,
        email,
        password || 'DefaultPassword123!'
      );
      const fbUser = userCredential.user;
      const token = await fbUser.getIdToken();
      localStorage.setItem('whicoustic_token', token);

      const synced = await syncWithBackend(token, fbUser);

      const loggedInUser: User = {
        id: synced?.id ? String(synced.id) : fbUser.uid,
        name: synced?.name || fbUser.displayName || email.split('@')[0],
        email: fbUser.email || email,
        role: 'TALENT',
        avatar: fbUser.photoURL || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
        vaultKey: 'SHA256:9f8e7d...01bc',
        isOnboarded: true,
        token,
      };

      setUser(loggedInUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(loggedInUser));
      navigateToSubdomain('/dashboard');
    } catch (err: any) {
      throw new Error(formatFirebaseError(err));
    }
  };

  const loginWithOAuth = async (provider: 'google' | 'github') => {
    localStorage.removeItem('whicoustic_logged_out');

    if (!auth) {
      throw new Error(
        'Authentication service not configured. Please add VITE_FIREBASE_API_KEY to your Vercel Environment Variables.'
      );
    }

    try {
      const authProvider = provider === 'github' ? githubProvider : googleProvider;
      const userCredential = await signInWithPopup(auth, authProvider);
      const fbUser = userCredential.user;
      const token = await fbUser.getIdToken();
      localStorage.setItem('whicoustic_token', token);

      const synced = await syncWithBackend(token, fbUser);

      const oauthUser: User = {
        id: synced?.id ? String(synced.id) : fbUser.uid,
        name: synced?.name || fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
        email: fbUser.email || `${fbUser.uid}@firebase.oauth`,
        role: 'STUDIO',
        avatar: fbUser.photoURL || undefined,
        isOnboarded: true,
        token,
      };

      setUser(oauthUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(oauthUser));
      navigateToSubdomain('/dashboard');
    } catch (err: any) {
      throw new Error(formatFirebaseError(err));
    }
  };

  const completeOnboarding = () => {
    if (user) {
      const updatedUser = {
        ...user,
        isOnboarded: true,
        vaultKey: `SHA256:${onboardingData.watermarkSha256.substring(0, 12)}...`,
      };
      setUser(updatedUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(updatedUser));
    }
    navigateToSubdomain('/dashboard');
  };

  const logout = async () => {
    try {
      if (auth) {
        await signOut(auth);
      }
    } catch (err) {
      console.warn('Firebase signOut error:', err);
    }
    setUser(null);
    localStorage.removeItem('whicoustic_user');
    localStorage.removeItem('whicoustic_token');
    localStorage.setItem('whicoustic_logged_out', 'true');
    navigateToMainDomain('/');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        onboardingData,
        updateOnboardingData,
        signup,
        login,
        loginWithOAuth,
        completeOnboarding,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
