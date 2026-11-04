import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '../ui/Button';
import { useDomain } from '../../context/DomainContext';
import { useAuth } from '../../context/AuthContext';
import { Activity, ShieldCheck, Sparkles } from 'lucide-react';

export const PublicNavbar: React.FC = () => {
  const location = useLocation();
  const { navigateToSubdomain } = useDomain();
  const { isAuthenticated, user } = useAuth();

  const navLinks = [
    { label: 'Voice Marketplace', path: '/marketplace' },
    { label: 'Live Demo', path: '/demo' },
    { label: 'Help & FAQ', path: '/help' },
    { label: 'Consultation', path: '/contact' },
  ];

  return (
    <header className="sticky top-7 z-40 w-full bg-white/90 backdrop-blur-md border-b border-outline-subtle transition-all">
      <div className="max-w-container mx-auto px-6 h-20 flex items-center justify-between">
        {/* Brand & Wordmark */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-full bg-[#0B1C30] flex items-center justify-center text-primary-container shadow-md group-hover:scale-105 transition-transform">
            <Activity className="w-5 h-5 text-primary-container" />
          </div>
          <div className="flex flex-col">
            <span className="font-recoletta text-2xl font-bold tracking-tight text-on-surface leading-none">
              VCaaS
            </span>
            <span className="font-lora italic text-[11px] text-secondary tracking-wide">
              Voice Clone as a Service
            </span>
          </div>
        </Link>

        {/* Navigation Items */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-berthold font-medium transition-colors ${
                  isActive
                    ? 'text-primary-container font-semibold'
                    : 'text-on-surface/80 hover:text-primary-container'
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Actions / Auth CTAs */}
        <div className="flex items-center gap-3">
          {isAuthenticated && user?.isOnboarded ? (
            <Button
              variant="dark"
              size="sm"
              icon={<ShieldCheck className="w-4 h-4 text-primary-container" />}
              onClick={() => navigateToSubdomain('/dashboard')}
            >
              Open Console (Sub-domain)
            </Button>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost" size="sm">
                  Console Login
                </Button>
              </Link>
              <Link to="/signup">
                <Button
                  variant="primary"
                  size="sm"
                  icon={<Sparkles className="w-3.5 h-3.5" />}
                >
                  Start Onboarding
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

