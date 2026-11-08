import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onIdTokenChanged,
  updateProfile,
} from 'firebase/auth';
import { auth, googleProvider, githubProvider } from '../config/firebase';
import { useDomain } from './DomainContext';
import { getApiBaseUrl } from '../services/apiClient';
import {
  extractAndCleanSessionHandoff,
  type SessionUser,
} from '../utils/authHandoff';
import {
  getSessionCookie,
  setSessionCookie,
  clearSessionCookie,
} from '../utils/cookies';

export type User = SessionUser;

export interface OnboardingData {
  role: string;
  primaryCategory: string;
  voiceGender: string;
  language: string;
  acousticAnchorRecorded: boolean;
  watermarkSha256: string;
  royaltyFloorPct: number;
}

export interface OnboardingPreferences {
  royalty_floor_pct?: number;
  voice_category?: string;
  vault_key?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  onboardingData: OnboardingData;
  updateOnboardingData: (data: Partial<OnboardingData>) => void;
  signup: (email: string, password?: string, name?: string, dob?: string) => Promise<void>;
  login: (email: string, password?: string) => Promise<void>;
  loginWithOAuth: (provider: 'google' | 'github') => Promise<void>;
  completeOnboarding: (data?: OnboardingPreferences) => Promise<void>;
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

const initializeAuthSession = (): User | null => {
  if (typeof window === 'undefined') return null;

  // Check URL query parameters for explicit cross-origin logout signal (?logged_out=true)
  try {
    const search = window.location.search;
    if (search && search.includes('logged_out=true')) {
      localStorage.setItem('whicoustic_logged_out', 'true');
      localStorage.removeItem('whicoustic_user');
      localStorage.removeItem('whicoustic_token');
      clearSessionCookie();
      return null;
    }
  } catch {
    // Ignore query param error
  }

  // Tier 1: Check URL hash handoff fragment FIRST!
  // A fresh URL hash handoff represents an active cross-origin authentication
  // event and MUST take precedence over any stale origin-partitioned logout flag.
  try {
    const handoff = extractAndCleanSessionHandoff();
    if (handoff && handoff.user && handoff.token) {
      localStorage.setItem('whicoustic_user', JSON.stringify(handoff.user));
      localStorage.setItem('whicoustic_token', handoff.token);
      localStorage.removeItem('whicoustic_logged_out');
      setSessionCookie(handoff.user, handoff.token);
      return handoff.user;
    }
  } catch (err) {
    console.warn('Tier 1 hash handoff initialization error:', err);
  }

  // If user explicitly logged out in this browser AND no fresh incoming handoff exists,
  // prevent auto-resurrection from stale cookies or stale storage.
  if (localStorage.getItem('whicoustic_logged_out') === 'true') {
    return null;
  }

  // Tier 2: Check Domain-Scoped Cookie
  try {
    const cookieSession = getSessionCookie();
    if (cookieSession && cookieSession.user && cookieSession.token) {
      localStorage.setItem('whicoustic_user', JSON.stringify(cookieSession.user));
      localStorage.setItem('whicoustic_token', cookieSession.token);
      localStorage.removeItem('whicoustic_logged_out');
      return cookieSession.user;
    }
  } catch (err) {
    console.warn('Tier 2 cookie initialization error:', err);
  }

  // Tier 3: Check Local Storage
  try {
    const saved = localStorage.getItem('whicoustic_user');
    if (saved) {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.id && parsed.email) {
        return parsed;
      }
    }
  } catch {
    return null;
  }

  return null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { navigateToSubdomain, navigateToMainDomain } = useDomain();

  const [user, setUser] = useState<User | null>(() => initializeAuthSession());
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      if (localStorage.getItem('whicoustic_user') || localStorage.getItem('whicoustic_token')) {
        return false;
      }
    }
    return true;
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

  // Multi-tier session hydration on mount:
  // Tier 1: URL Hash Fragment (#session_handoff=<base64url>) [Highest Priority - overrides stale logout]
  // Query Param: ?logged_out=true [Cross-origin logout synchronization]
  // Stored Flag: whicoustic_logged_out === 'true' [Blocks auto-resurrection from stale cookie/storage]
  // Tier 2: Domain-Scoped Cookie (whicoustic_session)
  // Tier 3: Origin Local Storage (whicoustic_user)
  useEffect(() => {
    const hydrateSession = () => {
      // Tier 1: Check URL hash handoff fragment FIRST!
      // A cryptographically fresh URL hash handoff represents an active cross-origin authentication
      // event and MUST take precedence over any stale origin-partitioned logout flag.
      try {
        const handoff = extractAndCleanSessionHandoff();
        if (handoff && handoff.user && handoff.token) {
          localStorage.setItem('whicoustic_user', JSON.stringify(handoff.user));
          localStorage.setItem('whicoustic_token', handoff.token);
          localStorage.removeItem('whicoustic_logged_out');
          setSessionCookie(handoff.user, handoff.token);
          setUser(handoff.user);
          setIsLoading(false);
          return;
        }
      } catch (err) {
        console.warn('Tier 1 hash handoff hydration error:', err);
      }

      // Check URL query parameters for explicit cross-origin logout signal (?logged_out=true)
      if (typeof window !== 'undefined' && window.location) {
        try {
          const search = window.location.search;
          if (search && search.includes('logged_out=true')) {
            localStorage.setItem('whicoustic_logged_out', 'true');
            localStorage.removeItem('whicoustic_user');
            localStorage.removeItem('whicoustic_token');
            clearSessionCookie();
            const params = new URLSearchParams(search);
            params.delete('logged_out');
            const newSearch = params.toString() ? `?${params.toString()}` : '';
            const cleanUrl = window.location.pathname + newSearch + window.location.hash;
            if (window.history && window.history.replaceState) {
              window.history.replaceState(window.history.state, '', cleanUrl);
            }
            setUser(null);
            setIsLoading(false);
            return;
          }
        } catch (err) {
          console.warn('URL logout parameter extraction error:', err);
        }
      }

      // If user explicitly logged out in this browser AND no fresh incoming handoff exists,
      // prevent auto-resurrection from stale cookies or stale storage.
      if (localStorage.getItem('whicoustic_logged_out') === 'true') {
        setUser(null);
        setIsLoading(false);
        return;
      }

      // Tier 2: Check Domain-Scoped Cookie
      try {
        const cookieSession = getSessionCookie();
        if (cookieSession && cookieSession.user && cookieSession.token) {
          localStorage.setItem('whicoustic_user', JSON.stringify(cookieSession.user));
          localStorage.setItem('whicoustic_token', cookieSession.token);
          localStorage.removeItem('whicoustic_logged_out');
          setUser(cookieSession.user);
          setIsLoading(false);
          return;
        }
      } catch (err) {
        console.warn('Tier 2 cookie hydration error:', err);
      }

      // Tier 3: Check Local Storage
      try {
        const saved = localStorage.getItem('whicoustic_user');
        const token = localStorage.getItem('whicoustic_token');
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed && parsed.id && parsed.email) {
            setUser(parsed);
            if (token) {
              setSessionCookie(parsed, token);
            }
            setIsLoading(false);
            return;
          }
        }
      } catch (err) {
        console.warn('Tier 3 localStorage hydration error:', err);
      }

      // Unauthenticated state
      setUser(null);
      setIsLoading(false);
    };

    hydrateSession();
  }, []);

  interface BackendSyncExtraData {
    is_onboarded?: boolean;
    royalty_floor_pct?: number;
    voice_category?: string;
    vault_key?: string;
    provider_id?: string;
  }

  const syncWithBackend = async (
    token: string,
    fbUser: { uid: string; email: string | null; displayName: string | null; photoURL: string | null },
    name?: string,
    extraData?: BackendSyncExtraData
  ) => {
    const apiBase = getApiBaseUrl();
    try {
      const syncPayload: Record<string, any> = {
        uid: fbUser.uid || undefined,
        email: fbUser.email || undefined,
        name: name || fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'User'),
        photo_url: fbUser.photoURL || undefined,
      };

      if (extraData?.provider_id) {
        syncPayload.provider_id = extraData.provider_id;
      }
      if (extraData?.is_onboarded !== undefined) {
        syncPayload.is_onboarded = extraData.is_onboarded;
      }
      if (extraData?.royalty_floor_pct !== undefined) {
        syncPayload.royalty_floor_pct = extraData.royalty_floor_pct;
      }
      if (extraData?.voice_category !== undefined) {
        syncPayload.voice_category = extraData.voice_category;
      }
      if (extraData?.vault_key !== undefined) {
        syncPayload.vault_key = extraData.vault_key;
      }

      const syncRes = await fetch(`${apiBase}/api/v1/users/sync`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(syncPayload),
      });

      if (syncRes.ok) {
        return await syncRes.json();
      }
    } catch (err) {
      console.warn('Backend user synchronization deferred:', err);
    }
    return null;
  };

  // Sync session state with Firebase Auth
  useEffect(() => {
    if (!auth) {
      return;
    }

    const unsubscribe = onIdTokenChanged(auth, async (fbUser) => {
      if (localStorage.getItem('whicoustic_logged_out') === 'true') {
        return;
      }

      if (fbUser) {
        try {
          const token = await fbUser.getIdToken();
          localStorage.setItem('whicoustic_token', token);

          const synced = await syncWithBackend(token, fbUser);

          setUser((prev) => {
            const isOnboarded = synced?.is_onboarded !== undefined
              ? Boolean(synced.is_onboarded)
              : (prev?.isOnboarded ?? false);

            if (!prev) {
              const restored: User = {
                id: synced?.id ? String(synced.id) : fbUser.uid,
                name: synced?.name || fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
                email: fbUser.email || '',
                role: (synced?.role === 'STUDIO' || synced?.role === 'ENTERPRISE') ? synced.role : 'TALENT',
                avatar: fbUser.photoURL || undefined,
                vaultKey: synced?.vault_key || undefined,
                isOnboarded,
                token,
              };
              localStorage.setItem('whicoustic_user', JSON.stringify(restored));
              setSessionCookie(restored, token);
              return restored;
            }
            const updated = {
              ...prev,
              isOnboarded,
              token,
              ...(synced?.vault_key ? { vaultKey: synced.vault_key } : {}),
            };
            localStorage.setItem('whicoustic_user', JSON.stringify(updated));
            setSessionCookie(updated, token);
            return updated;
          });
        } catch (tokenErr) {
          console.warn('Failed to retrieve Firebase ID token or sync profile:', tokenErr);
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
      setSessionCookie(newUser, token);
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

      const isOnboarded = synced?.is_onboarded !== undefined
        ? Boolean(synced.is_onboarded)
        : true;

      const loggedInUser: User = {
        id: synced?.id ? String(synced.id) : fbUser.uid,
        name: synced?.name || fbUser.displayName || email.split('@')[0],
        email: fbUser.email || email,
        role: (synced?.role === 'STUDIO' || synced?.role === 'ENTERPRISE') ? synced.role : 'TALENT',
        avatar: fbUser.photoURL || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
        vaultKey: synced?.vault_key || 'SHA256:9f8e7d...01bc',
        isOnboarded,
        token,
      };

      setUser(loggedInUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(loggedInUser));
      setSessionCookie(loggedInUser, token);
      if (isOnboarded) {
        navigateToSubdomain('/dashboard');
      } else {
        navigateToMainDomain('/onboarding');
      }
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

      const providerId = provider === 'github' ? 'github.com' : 'google.com';
      const synced = await syncWithBackend(token, fbUser, undefined, { provider_id: providerId });

      const isOnboarded = Boolean(synced?.is_onboarded);

      const oauthUser: User = {
        id: synced?.id ? String(synced.id) : fbUser.uid,
        name: synced?.name || fbUser.displayName || fbUser.email?.split('@')[0] || 'User',
        email: fbUser.email || `${fbUser.uid}@firebase.oauth`,
        role: (synced?.role === 'STUDIO' || synced?.role === 'ENTERPRISE') ? synced.role : 'TALENT',
        avatar: fbUser.photoURL || undefined,
        vaultKey: synced?.vault_key || undefined,
        isOnboarded,
        token,
      };

      setUser(oauthUser);
      localStorage.setItem('whicoustic_user', JSON.stringify(oauthUser));
      setSessionCookie(oauthUser, token);

      if (isOnboarded) {
        navigateToSubdomain('/dashboard');
      } else {
        navigateToMainDomain('/onboarding');
      }
    } catch (err: any) {
      throw new Error(formatFirebaseError(err));
    }
  };

  const completeOnboarding = async (preferences?: OnboardingPreferences) => {
    const token = localStorage.getItem('whicoustic_token') || user?.token;

    const royaltyFloor = preferences?.royalty_floor_pct !== undefined
      ? preferences.royalty_floor_pct
      : onboardingData.royaltyFloorPct;

    const voiceCategory = preferences?.voice_category || onboardingData.primaryCategory;

    const rawVaultKey = preferences?.vault_key || `SHA256:${onboardingData.watermarkSha256}`;

    if (token) {
      try {
        const synced = await syncWithBackend(
          token,
          {
            uid: auth?.currentUser?.uid || user?.id || '',
            email: user?.email || null,
            displayName: user?.name || null,
            photoURL: user?.avatar || null,
          },
          user?.name,
          {
            is_onboarded: true,
            royalty_floor_pct: royaltyFloor,
            voice_category: voiceCategory,
            vault_key: rawVaultKey,
          }
        );
        if (synced) {
          console.log('Onboarding state successfully persisted to backend:', synced);
        }
      } catch (syncErr) {
        console.warn('Backend sync during onboarding completion deferred:', syncErr);
      }
    }

    // Resolve current base user object from state, local storage, or current auth token
    let baseUser: User | null = user;
    if (!baseUser) {
      try {
        const stored = localStorage.getItem('whicoustic_user');
        if (stored) {
          baseUser = JSON.parse(stored) as User;
        }
      } catch {
        // Ignore JSON error
      }
    }

    if (!baseUser && auth?.currentUser) {
      baseUser = {
        id: auth.currentUser.uid,
        name: auth.currentUser.displayName || auth.currentUser.email?.split('@')[0] || 'User',
        email: auth.currentUser.email || '',
        role: 'TALENT',
        avatar: auth.currentUser.photoURL || undefined,
        isOnboarded: false,
        token: token || undefined,
      };
    }

    const shortVault = rawVaultKey.startsWith('SHA256:')
      ? `${rawVaultKey.substring(0, 19)}...`
      : `SHA256:${rawVaultKey.substring(0, 12)}...`;

    const updatedUser: User = baseUser ? {
      ...baseUser,
      isOnboarded: true,
      vaultKey: shortVault,
      token: token || baseUser.token,
    } : {
      id: auth?.currentUser?.uid || 'usr_onboarded',
      name: auth?.currentUser?.displayName || 'User',
      email: auth?.currentUser?.email || '',
      role: 'TALENT',
      isOnboarded: true,
      vaultKey: shortVault,
      token: token || undefined,
    };

    setUser(updatedUser);
    localStorage.setItem('whicoustic_user', JSON.stringify(updatedUser));
    if (token) {
      setSessionCookie(updatedUser, token);
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
    clearSessionCookie();
    localStorage.removeItem('whicoustic_user');
    localStorage.removeItem('whicoustic_token');
    localStorage.setItem('whicoustic_logged_out', 'true');
    navigateToMainDomain('/?logged_out=true');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
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
