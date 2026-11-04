import React from 'react';
import { useLocation } from 'react-router-dom';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Bell, Search, ShieldCheck, Zap } from 'lucide-react';

export const SubdomainHeader: React.FC = () => {
  const location = useLocation();

  const getPageTitle = (pathname: string) => {
    switch (pathname) {
      case '/dashboard':
        return 'Enterprise Operations Dashboard';
      case '/studio':
        return 'Neural Voice Cloning Studio';
      case '/talent':
        return 'Voice Persona & Talent Hub';
      case '/licensing':
        return 'Studio Licensing Inbound Requests';
      case '/earnings':
        return 'Earnings & Royalty Disbursements';
      case '/royalties':
        return 'Licensing & Royalties Portal';
      case '/settings':
        return 'Cryptographic Security & API Keys';
      default:
        return 'Whicoustic Console';
    }
  };

  return (
    <header className="h-20 bg-white/90 backdrop-blur-md border-b border-outline-subtle px-8 flex items-center justify-between sticky top-0 z-20">
      {/* Title & Path */}
      <div>
        <h1 className="font-recoletta text-2xl font-bold text-on-surface tracking-tight">
          {getPageTitle(location.pathname)}
        </h1>
        <p className="font-lora italic text-xs text-secondary">
          Sub-domain Workspace • app.whicoustic.ai
        </p>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-4">
        {/* Forensic Status Badge */}
        <Badge variant="amber" size="sm" pulse icon={<ShieldCheck className="w-3.5 h-3.5 text-primary-container" />}>
          Watermark Active: SHA-256
        </Badge>

        {/* Quick Search */}
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-secondary absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search clones, licenses..."
            className="w-56 h-9 pl-9 pr-3 text-xs font-berthold bg-surface-container rounded-pill border border-outline-subtle focus:outline-none focus:border-primary-container focus:ring-1 focus:ring-primary-container"
          />
        </div>

        {/* Notifications */}
        <button className="relative w-9 h-9 rounded-full bg-surface-container hover:bg-surface-container-high flex items-center justify-center text-secondary hover:text-on-surface transition-colors border border-outline-subtle">
          <Bell className="w-4 h-4" />
          <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary-container ring-2 ring-white" />
        </button>

        {/* Deploy New Voice CTA */}
        <Button variant="primary" size="sm" icon={<Zap className="w-3.5 h-3.5" />}>
          Deploy Voice Model
        </Button>
      </div>
    </header>
  );
};

