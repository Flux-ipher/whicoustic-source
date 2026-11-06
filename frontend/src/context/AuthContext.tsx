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
      } catch {
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
      } catch {
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
      let msg = 'Registration compliance validation failed.';
      const detail = errorData.detail;
      if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string }) => d.msg || '').join(', ');
      } else if (typeof detail === 'string') {
        msg = detail;
      }
      throw new Error(msg);
    }

    const regUser = await response.json().catch(() => ({}));

    const newUser: User = {
      id: regUser.id ? String(regUser.id) : `usr_${Math.random().toString(36).substring(2, 9)}`,
      name: regUser.full_name || name || email.split('@')[0],
      email: regUser.email || email,
      role: 'TALENT',
      isOnboarded: false,
      dob: regUser.dob || dob,
    };
    setUser(newUser);
    localStorage.setItem('whicoustic_user', JSON.stringify(newUser));
  };

  const login = async (email: string, password?: string) => {
    localStorage.removeItem('whicoustic_logged_out');
    const pwd = password || 'DefaultPassword123!';

    const response = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password: pwd,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      let msg = 'Authentication failed. Please verify your email and password.';
      const detail = errorData.detail;
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail)) {
        msg = detail.map((d: { msg?: string }) => d.msg || '').join(', ');
      }
      throw new Error(msg);
    }

    const tokenData = await response.json().catch(() => ({}));
    if (tokenData.access_token) {
      localStorage.setItem('whicoustic_token', tokenData.access_token);
    }

    let profile: Partial<User> = {};
    if (tokenData.access_token) {
      try {
        const profRes = await fetch('/api/v1/auth/profile', {
          headers: {
            Authorization: `Bearer ${tokenData.access_token}`,
          },
        });
        if (profRes.ok) {
          const profData = await profRes.json();
          profile = {
            id: String(profData.id),
            name: profData.full_name || profData.username,
            email: profData.email,
            dob: profData.dob,
          };
        }
      } catch {
        // Fallback to minimal profile if network glitch
      }
    }

    const loggedInUser: User = {
      id: profile.id || 'usr_forensic_9921',
      name: profile.name || email.split('@')[0],
      email: profile.email || email,
      role: 'TALENT',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
      vaultKey: 'SHA256:9f8e7d...01bc',
      isOnboarded: true,
      dob: profile.dob,
      token: tokenData.access_token,
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

