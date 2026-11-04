import React, { createContext, useContext, useState, useEffect } from 'react';
import { useDomain } from './DomainContext';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'TALENT' | 'STUDIO' | 'ENTERPRISE';
  avatar?: string;
  vaultKey?: string;
  isOnboarded: boolean;
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
  signup: (email: string, password?: string, name?: string) => Promise<void>;
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
    if (localStorage.getItem('vcaas_logged_out') === 'true') {
      return null;
    }

    const saved = localStorage.getItem('vcaas_user');
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
    const saved = localStorage.getItem('vcaas_onboarding');
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
      localStorage.setItem('vcaas_onboarding', JSON.stringify(updated));
      return updated;
    });
  };

  const signup = async (email: string, _password?: string, name?: string) => {
    localStorage.removeItem('vcaas_logged_out');
    const newUser: User = {
      id: `usr_${Math.random().toString(36).substring(2, 9)}`,
      name: name || email.split('@')[0],
      email,
      role: 'TALENT',
      isOnboarded: false,
    };
    setUser(newUser);
    localStorage.setItem('vcaas_user', JSON.stringify(newUser));
  };

  const login = async (email: string, _password?: string) => {
    localStorage.removeItem('vcaas_logged_out');
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
    localStorage.setItem('vcaas_user', JSON.stringify(loggedInUser));
    navigateToSubdomain('/dashboard');
  };

  const loginWithOAuth = async (provider: 'google' | 'github') => {
    localStorage.removeItem('vcaas_logged_out');
    const oauthUser: User = {
      id: `usr_oauth_${provider}_${Date.now()}`,
      name: provider === 'google' ? 'Alex Rivera (Google)' : 'Dev Architect (GitHub)',
      email: provider === 'google' ? 'alex.rivera@gmail.com' : 'dev@github.com',
      role: 'STUDIO',
      isOnboarded: false,
    };
    setUser(oauthUser);
    localStorage.setItem('vcaas_user', JSON.stringify(oauthUser));
  };

  const completeOnboarding = () => {
    if (user) {
      const updatedUser = {
        ...user,
        isOnboarded: true,
        vaultKey: `SHA256:${onboardingData.watermarkSha256.substring(0, 12)}...`,
      };
      setUser(updatedUser);
      localStorage.setItem('vcaas_user', JSON.stringify(updatedUser));
    }
    // Redirect to Dashboard on the sub-domain!
    navigateToSubdomain('/dashboard');
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('vcaas_user');
    localStorage.setItem('vcaas_logged_out', 'true');
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

