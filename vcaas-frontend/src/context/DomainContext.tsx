import React, { createContext, useContext, useState, useEffect } from 'react';

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

    const saved = localStorage.getItem('vcaas_active_domain');
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
    localStorage.setItem('vcaas_active_domain', newDomain);
  };

  const isSubdomain = domain === 'app';

  const navigateToSubdomain = (path: string = '/dashboard') => {
    const hostname = window.location.hostname;
    const port = window.location.port ? `:${window.location.port}` : '';
    const protocol = window.location.protocol;

    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      // Local development with app.localhost
      // We can directly navigate to app.localhost:5173
      window.location.href = `${protocol}//app.localhost${port}${path}`;
    } else if (hostname.includes('.') && !hostname.startsWith('app.')) {
      // Production e.g. vcaas.com -> app.vcaas.com
      window.location.href = `${protocol}//app.${hostname}${port}${path}`;
    } else {
      // Internal state toggle fallback
      setDomain('app');
      window.location.pathname = path;
    }
  };

  const navigateToMainDomain = (path: string = '/') => {
    const hostname = window.location.hostname;
    const port = window.location.port ? `:${window.location.port}` : '';
    const protocol = window.location.protocol;

    if (hostname.startsWith('app.localhost')) {
      window.location.href = `${protocol}//localhost${port}${path}`;
    } else if (hostname.startsWith('app.')) {
      const rootDomain = hostname.replace(/^app\./, '');
      window.location.href = `${protocol}//${rootDomain}${port}${path}`;
    } else {
      setDomain('main');
      window.location.pathname = path;
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

