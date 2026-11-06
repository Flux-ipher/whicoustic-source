import React from 'react';
import { useDomain } from '../../context/DomainContext';
import { Globe, LayoutDashboard, ArrowRightLeft } from 'lucide-react';

export const DomainSwitcherBar: React.FC = () => {
  const { domain, setDomain, navigateToSubdomain, navigateToMainDomain } = useDomain();

  return (
    <div className="bg-[#0B1C30] text-white border-b border-white/10 px-4 py-1.5 text-xs font-berthold flex items-center justify-between z-50 sticky top-0 shadow-sm">
      <div className="flex items-center gap-2">
        <span className="flex h-2 w-2 relative">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-container" />
        </span>
        <span className="text-secondary font-medium">Domain Routing Environment:</span>
        <span className="font-bold text-white tracking-wide">
          {domain === 'main' ? 'whicoustic.xyz (Marketing & Onboarding)' : 'app.whicoustic.xyz (Platform Sub-domain)'}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-secondary text-[11px] hidden sm:inline">
          Current Host: <code className="text-primary-container font-code">{window.location.host}</code>
        </span>

        <button
          onClick={() => {
            if (domain === 'main') {
              navigateToSubdomain('/dashboard');
            } else {
              navigateToMainDomain('/');
            }
          }}
          className="inline-flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-2.5 py-1 rounded-pill transition-colors text-[11px] font-semibold text-white border border-white/10"
        >
          <ArrowRightLeft className="w-3 h-3 text-primary-container" />
          <span>Switch to {domain === 'main' ? 'App Sub-domain' : 'Main Domain'}</span>
        </button>

        {/* Quick state toggle for offline / localhost environments */}
        <div className="flex items-center bg-black/40 rounded-pill p-0.5 border border-white/10">
          <button
            onClick={() => setDomain('main')}
            className={`px-2 py-0.5 rounded-pill text-[10px] font-semibold transition-all ${
              domain === 'main'
                ? 'bg-primary-container text-[#0B1C30] shadow-sm'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <Globe className="w-2.5 h-2.5 inline mr-1" />
            Main
          </button>
          <button
            onClick={() => setDomain('app')}
            className={`px-2 py-0.5 rounded-pill text-[10px] font-semibold transition-all ${
              domain === 'app'
                ? 'bg-primary-container text-[#0B1C30] shadow-sm'
                : 'text-white/60 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-2.5 h-2.5 inline mr-1" />
            App
          </button>
        </div>
      </div>
    </div>
  );
};

