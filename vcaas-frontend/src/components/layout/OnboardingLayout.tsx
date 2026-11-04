import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { DomainSwitcherBar } from './DomainSwitcherBar';
import { Activity, ShieldCheck, ArrowLeft } from 'lucide-react';

export const OnboardingLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F8F9FF] text-on-surface flex flex-col">
      <DomainSwitcherBar />

      {/* Top Header */}
      <header className="h-16 px-8 flex items-center justify-between border-b border-outline-subtle bg-white">
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#0B1C30] flex items-center justify-center text-primary-container">
            <Activity className="w-4 h-4 text-primary-container" />
          </div>
          <span className="font-recoletta text-xl font-bold text-on-surface">
            VCaaS
          </span>
        </Link>

        <div className="flex items-center gap-3 text-xs font-berthold text-secondary">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Cryptographic Vault Onboarding</span>
        </div>

        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-berthold font-medium text-secondary hover:text-on-surface transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Exit to Homepage</span>
        </Link>
      </header>

      {/* Main Stepper Body */}
      <main className="flex-1 flex flex-col justify-center items-center p-6 md:p-12">
        <div className="w-full max-w-4xl">
          <Outlet />
        </div>
      </main>

      {/* Footer Note */}
      <footer className="py-4 text-center text-xs font-lora italic text-secondary border-t border-outline-subtle bg-white">
        Forensic audio biometric encryption applied in real time. ISO/IEC 27001 compliant.
      </footer>
    </div>
  );
};
