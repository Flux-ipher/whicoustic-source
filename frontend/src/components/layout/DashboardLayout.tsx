import React, { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useDomain } from '../../context/DomainContext';
import { SubdomainSidebar } from './SubdomainSidebar';
import { SubdomainHeader } from './SubdomainHeader';

export const DashboardLayout: React.FC = () => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const { navigateToMainDomain } = useDomain();

  useEffect(() => {
    // Await isLoading before evaluating redirect guards
    if (isLoading) {
      return;
    }

    if (!isAuthenticated || !user) {
      // Unauthenticated access strictly prohibited: route to login on main domain
      navigateToMainDomain('/login');
      return;
    }

    if (!user.isOnboarded) {
      // Unonboarded access prohibited on console: route to calibration on main domain
      navigateToMainDomain('/onboarding');
      return;
    }
  }, [isLoading, isAuthenticated, user, navigateToMainDomain]);

  // Loading state: Verifying session hydration (Tier 1 hash, Tier 2 cookie, or Tier 3 storage)
  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B1C30] flex flex-col items-center justify-center text-white p-6">
        <div className="w-10 h-10 border-3 border-[#F59E0B] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-bold font-recoleta text-white tracking-tight">Verifying Biometric Session</h2>
        <p className="text-xs text-slate-400 mt-2 font-berthold">
          Synchronizing credentials with Whicoustic Console...
        </p>
      </div>
    );
  }

  // Unauthenticated fallback: Redirecting cleanly to login gateway
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-[#0B1C30] flex flex-col items-center justify-center text-white p-6">
        <div className="w-10 h-10 border-3 border-[#F59E0B] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-bold font-recoleta text-white tracking-tight">Authentication Required</h2>
        <p className="text-xs text-slate-400 mt-2 font-berthold">
          Redirecting to secure login gateway on whicoustic.xyz...
        </p>
      </div>
    );
  }

  // Unonboarded guard: Redirecting cleanly to biometric onboarding flow
  if (!user.isOnboarded) {
    return (
      <div className="min-h-screen bg-[#0B1C30] flex flex-col items-center justify-center text-white p-6">
        <div className="w-10 h-10 border-3 border-[#F59E0B] border-t-transparent rounded-full animate-spin mb-4" />
        <h2 className="text-xl font-bold font-recoleta text-white tracking-tight">Biometric Onboarding Required</h2>
        <p className="text-xs text-slate-400 mt-2 font-berthold">
          Redirecting to acoustic anchor calibration on whicoustic.xyz...
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
