import React from 'react';
import { Outlet } from 'react-router-dom';
import { DomainSwitcherBar } from './DomainSwitcherBar';
import { PublicNavbar } from './PublicNavbar';
import { PublicFooter } from './PublicFooter';

export const PublicLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-background text-on-surface">
      <DomainSwitcherBar />
      <PublicNavbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
};

