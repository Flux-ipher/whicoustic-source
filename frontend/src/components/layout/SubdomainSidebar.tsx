import React from 'react';
import { NavLink } from 'react-router-dom';
import { BrandLogo } from '../ui/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { useDomain } from '../../context/DomainContext';
import {
  LayoutDashboard,
  Mic2,
  Users,
  FileCheck2,
  DollarSign,
  PieChart,
  ShieldAlert,
  LogOut,
  Globe,
  Sparkles,
} from 'lucide-react';

export const SubdomainSidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const { navigateToMainDomain } = useDomain();

  const navItems = [
    { label: 'Operations Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Cloning Studio', path: '/studio', icon: Mic2, badge: 'PRO' },
    { label: 'Voice Persona Hub', path: '/talent', icon: Users },
    { label: 'Licensing Requests', path: '/licensing', icon: FileCheck2 },
    { label: 'Earnings & Payouts', path: '/earnings', icon: DollarSign },
    { label: 'Royalties Portal', path: '/royalties', icon: PieChart },
    { label: 'Security & API Keys', path: '/settings', icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-white border-r border-outline-subtle flex flex-col justify-between shrink-0 h-screen sticky top-0 z-30 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-20 px-6 flex items-center justify-between border-b border-outline-subtle">
          <BrandLogo variant="dark" type="full" className="h-8 w-auto" alt="Whicoustic" />
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-berthold uppercase tracking-wider text-secondary font-semibold">
            Infrastructure Console
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-pill text-sm font-berthold transition-all duration-150 ${
                    isActive
                      ? 'bg-primary-container text-[#0B1C30] font-semibold shadow-amber-glow'
                      : 'text-on-surface/80 hover:bg-surface-container-high hover:text-on-surface'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-[#0B1C30]' : 'text-secondary'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] font-code font-bold px-1.5 py-0.5 rounded-pill ${
                          isActive
                            ? 'bg-[#0B1C30] text-white'
                            : 'bg-[#FEF3C7] text-[#92400E]'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* User profile & Domain hand-off */}
      <div className="p-4 border-t border-outline-subtle space-y-2 bg-[#F8F9FF]">
        {/* User Card */}
        <div className="flex items-center gap-3 px-2 py-1.5">
          <img
            src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80'}
            alt="Avatar"
            className="w-9 h-9 rounded-full object-cover border border-outline-subtle"
          />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-berthold font-bold text-on-surface truncate">
              {user?.name || 'Acoustic Engineer'}
            </p>
            <p className="text-[11px] font-code text-secondary truncate">
              {user?.vaultKey || 'SHA256:Active'}
            </p>
          </div>
        </div>

        {/* Quick Link back to Main Domain */}
        <button
          onClick={() => navigateToMainDomain('/')}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-pill text-xs font-berthold text-secondary hover:text-on-surface hover:bg-white border border-outline-subtle transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-primary-container" />
          <span>Exit to Main Domain (whicoustic.ai)</span>
        </button>

        {/* Logout */}
        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 px-3 py-1.5 rounded-pill text-xs font-berthold text-error hover:bg-rose-50 transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Log out</span>
        </button>
      </div>
    </aside>
  );
};

