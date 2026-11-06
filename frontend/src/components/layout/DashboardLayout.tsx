import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useDomain } from '../../context/DomainContext';
import { SubdomainSidebar } from './SubdomainSidebar';
import { SubdomainHeader } from './SubdomainHeader';

export const DashboardLayout: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { navigateToMainDomain } = useDomain();

  useEffect(() => {
    if (!isAuthenticated || !user) {
      // Unauthenticated access strictly prohibited: route to login on main domain
      navigateToMainDomain('/login');
    }
  }, [isAuthenticated, user, navigateToMainDomain]);

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-[#0B1C30] flex flex-col items-center justify-center text-white p-6">
        <div className="w-10 h-10 border-3 border-amber-500 border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-bold font-recoleta">Authentication Required</h2>
        <p className="text-xs text-slate-400 mt-2 font-berthold">
          Redirecting to secure login gateway on whicoustic.xyz...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col">
      <div className="flex-1 flex">
        <SubdomainSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <SubdomainHeader />
          <main className="flex-1 p-8 overflow-y-auto">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

