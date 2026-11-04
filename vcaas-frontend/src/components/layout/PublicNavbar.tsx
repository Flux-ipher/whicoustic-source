import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '../ui/Button';
import { BrandLogo } from '../ui/BrandLogo';
import { useDomain } from '../../context/DomainContext';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck } from 'lucide-react';

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
    <header className="sticky top-0 z-40 w-full bg-white/90 backdrop-blur-md border-b border-outline-subtle transition-all">
      <div className="max-w-container mx-auto px-6 h-20 flex items-center justify-between">
        {/* Brand & Wordmark */}
        <Link to="/" className="flex items-center gap-3 group">
          <BrandLogo variant="dark" type="wordmark" className="h-7 w-auto transition-transform group-hover:scale-[1.02]" alt="Whicoustic" />
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
              Open Console
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
                >
                  Get started free
                </Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
};

