import React, { createContext, useContext, useState } from 'react';
import { useDomain } from './DomainContext';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'TALENT' | 'STUDIO' | 'ENTERPRISE';
  avatar?: string;
  vaultKey?: string;
  isOnboarded: boolean;
  dob?: string;
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

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { navigateToSubdomain, navigateToMainDomain } = useDomain();

  const [user, setUser] = useState<User | null>(() => {
    // If explicitly logged out, do not revive demo user
    if (localStorage.getItem('whicoustic_logged_out') === 'true') {
      return null;
    }

    const saved = localStorage.getItem('whicoustic_user');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return null;
      }
    }
    // Default demo authenticated state for direct sub-domain testing
    return {
      id: 'usr_forensic_9921',
      name: 'Elena Rostova',
      email: 'elena@acoustic-lab.io',
      role: 'TALENT',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      vaultKey: 'SHA256:9f8e7d...01bc',
      isOnboarded: true,
    };
  });

  const [onboardingData, setOnboardingData] = useState<OnboardingData>(() => {
    const saved = localStorage.getItem('whicoustic_onboarding');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        return defaultOnboarding;
      }
    }
    return defaultOnboarding;
  });

  const updateOnboardingData = (data: Partial<OnboardingData>) => {
    setOnboardingData((prev) => {
      const updated = { ...prev, ...data };
      localStorage.setItem('whicoustic_onboarding', JSON.stringify(updated));
      return updated;
    });
  };

  const signup = async (email: string, password?: string, name?: string, dob?: string) => {
    localStorage.removeItem('whicoustic_logged_out');

    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: email.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '_') || 'user',
          email,
          password: password || 'DefaultPassword123!',
          full_name: name || email.split('@')[0],
          dob,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 422 || response.status === 400) {
          const detail = errorData.detail;
          if (Array.isArray(detail)) {
            const msgs = detail.map((d: { msg?: string }) => d.msg || '').join(', ');
            throw new Error(msgs || 'Registration compliance validation failed.');
          } else if (typeof detail === 'string') {
            throw new Error(detail);
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('17 years old')) {
        throw err;
      }
      console.warn('Backend registration API note:', err);
    }

    const newUser: User = {
      id: `usr_${Math.random().toString(36).substring(2, 9)}`,
      name: name || email.split('@')[0],
      email,
      role: 'TALENT',
      isOnboarded: false,
      dob,
    };
    setUser(newUser);
    localStorage.setItem('whicoustic_user', JSON.stringify(newUser));
  };

  const login = async (email: string, _password?: string) => {
    localStorage.removeItem('whicoustic_logged_out');
    const loggedInUser: User = {
      id: 'usr_forensic_9921',
      name: email.split('@')[0],
      email,
      role: 'TALENT',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      vaultKey: 'SHA256:9f8e7d...01bc',
      isOnboarded: true,
    };
    setUser(loggedInUser);
    localStorage.setItem('whicoustic_user', JSON.stringify(loggedInUser));
    navigateToSubdomain('/dashboard');
  };

  const loginWithOAuth = async (provider: 'google' | 'github') => {
    localStorage.removeItem('whicoustic_logged_out');
    const oauthUser: User = {
      id: `usr_oauth_${provider}_${Date.now()}`,
      name: provider === 'google' ? 'Alex Rivera (Google)' : 'Dev Architect (GitHub)',
      email: provider === 'google' ? 'alex.rivera@gmail.com' : 'dev@github.com',
      role: 'STUDIO',
      isOnboarded: false,
    };
    setUser(oauthUser);
    localStorage.setItem('whicoustic_user', JSON.stringify(oauthUser));
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
    // Redirect to Dashboard on the sub-domain!
    navigateToSubdomain('/dashboard');
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('whicoustic_user');
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

