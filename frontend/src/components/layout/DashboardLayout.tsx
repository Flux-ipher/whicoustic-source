import React from 'react';
import { Outlet } from 'react-router-dom';
import { SubdomainSidebar } from './SubdomainSidebar';
import { SubdomainHeader } from './SubdomainHeader';

export const DashboardLayout: React.FC = () => {
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

