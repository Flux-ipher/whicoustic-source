import React, { createContext, useContext, useState, useEffect } from 'react';
import { buildSessionHandoffFragment, type SessionUser } from '../utils/authHandoff';
import { setSessionCookie } from '../utils/cookies';

export type DomainType = 'main' | 'app';

interface DomainContextType {
  domain: DomainType;
  setDomain: (domain: DomainType) => void;
  isSubdomain: boolean;
  navigateToSubdomain: (path?: string) => void;
  navigateToMainDomain: (path?: string) => void;
}

const DomainContext = createContext<DomainContextType | undefined>(undefined);

export const DomainProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const detectDomain = (): DomainType => {
    if (typeof window === 'undefined') return 'main';

    const hostname = window.location.hostname;
    // Check if hostname starts with app. or subdomain
    if (hostname.startsWith('app.') || hostname.startsWith('console.')) {
      return 'app';
    }

    // Also support search param override or localStorage for development convenience
    const urlParams = new URLSearchParams(window.location.search);
    const domainOverride = urlParams.get('domain');
    if (domainOverride === 'app' || domainOverride === 'main') {
      return domainOverride;
    }

    const saved = localStorage.getItem('whicoustic_active_domain');
    if (saved === 'app' || saved === 'main') {
      return saved;
    }

    return 'main';
  };

  const [domain, setDomainState] = useState<DomainType>(detectDomain);

  useEffect(() => {
    const handlePopState = () => {
      setDomainState(detectDomain());
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const setDomain = (newDomain: DomainType) => {
    setDomainState(newDomain);
    localStorage.setItem('whicoustic_active_domain', newDomain);
  };

  const isSubdomain = domain === 'app';

  const navigateToSubdomain = (path: string = '/dashboard') => {
    const configuredSubdomain = import.meta.env.VITE_APP_SUBDOMAIN;
    const rawProtocol = (import.meta.env.VITE_PROTOCOL as string) || window.location.protocol;
    const protocol = rawProtocol.endsWith(':') ? rawProtocol : `${rawProtocol}:`;
    const hostname = window.location.hostname;
    const port = window.location.port ? `:${window.location.port}` : '';

    // Check for active authenticated session to attach ephemeral handoff hash and domain cookie
    let hashFragment = '';
    try {
      const savedUserStr = localStorage.getItem('whicoustic_user');
      const token = localStorage.getItem('whicoustic_token');
      if (savedUserStr && token) {
        const user = JSON.parse(savedUserStr) as SessionUser;
        if (user && user.id && user.email) {
          // Set Tier 2 domain-scoped cookie
          setSessionCookie(user, token);
          // Build Tier 1 URL hash fragment
          hashFragment = buildSessionHandoffFragment(user, token);
        }
      }
    } catch (err) {
      console.warn('Session handoff preparation skipped:', err);
    }

    // Attach hash fragment to destination path if not already present
    const destinationPath = path.includes('#')
      ? path
      : `${path}${hashFragment}`;

    if (configuredSubdomain && !hostname.startsWith('app.')) {
      // Use configured environment target
      const target = configuredSubdomain.includes(':')
        ? configuredSubdomain
        : `${configuredSubdomain}${port}`;
      window.location.href = `${protocol}//${target}${destinationPath}`;
    } else if (hostname === 'localhost' || hostname === '127.0.0.1') {
      window.location.href = `${protocol}//app.localhost${port}${destinationPath}`;
    } else if (hostname.includes('.') && !hostname.startsWith('app.')) {
      window.location.href = `${protocol}//app.${hostname}${port}${destinationPath}`;
    } else {
      setDomain('app');
      window.location.href = destinationPath;
    }
  };

  const navigateToMainDomain = (path: string = '/') => {
    const configuredMain = import.meta.env.VITE_MAIN_DOMAIN;
    const rawProtocol = (import.meta.env.VITE_PROTOCOL as string) || window.location.protocol;
    const protocol = rawProtocol.endsWith(':') ? rawProtocol : `${rawProtocol}:`;
    const hostname = window.location.hostname;
    const port = window.location.port ? `:${window.location.port}` : '';

    // If active session exists, ensure cookie is synchronized
    try {
      const savedUserStr = localStorage.getItem('whicoustic_user');
      const token = localStorage.getItem('whicoustic_token');
      if (savedUserStr && token) {
        const user = JSON.parse(savedUserStr) as SessionUser;
        if (user && user.id && user.email) {
          setSessionCookie(user, token);
        }
      }
    } catch {
      // Ignore
    }

    if (configuredMain && hostname.startsWith('app.')) {
      const target = configuredMain.includes(':')
        ? configuredMain
        : `${configuredMain}${port}`;
      window.location.href = `${protocol}//${target}${path}`;
    } else if (hostname.startsWith('app.localhost')) {
      window.location.href = `${protocol}//localhost${port}${path}`;
    } else if (hostname.startsWith('app.')) {
      const rootDomain = hostname.replace(/^app\./, '');
      window.location.href = `${protocol}//${rootDomain}${port}${path}`;
    } else {
      setDomain('main');
      window.location.href = path;
    }
  };

  return (
    <DomainContext.Provider
      value={{
        domain,
        setDomain,
        isSubdomain,
        navigateToSubdomain,
        navigateToMainDomain,
      }}
    >
      {children}
    </DomainContext.Provider>
  );
};

export const useDomain = () => {
  const context = useContext(DomainContext);
  if (!context) {
    throw new Error('useDomain must be used within a DomainProvider');
  }
  return context;
};

