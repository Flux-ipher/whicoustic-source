import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { NotFoundIllustration } from '../../components/ui/Illustrations';
import { Home, Mic, Radio, Search } from 'lucide-react';
import { PageTransition } from '../../components/ui/PageTransition';

export const NotFoundPage: React.FC = () => {
  return (
    <PageTransition className="min-h-[70vh] flex items-center justify-center px-6 py-16">
      <div className="max-w-xl mx-auto text-center space-y-6">
        <NotFoundIllustration size={220} className="mx-auto" />

        <div className="space-y-2">
          <h1 className="font-recoleta text-3xl sm:text-4xl font-bold text-on-surface tracking-tight">
            Acoustic Signal Lost (404)
          </h1>
          <p className="font-berthold text-slate-600 text-sm sm:text-base leading-relaxed max-w-md mx-auto">
            The frequency or page you requested does not exist on the Whicoustic protocol network. It may have moved or been decommissioned.
          </p>
        </div>

        {/* Suggested Next Steps */}
        <div className="bg-white rounded-card border border-outline-subtle p-5 max-w-md mx-auto text-left shadow-sm space-y-3">
          <span className="text-xs font-berthold font-bold uppercase tracking-wider text-slate-500">
            Suggested Destinations:
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-berthold">
            <Link
              to="/"
              className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors"
            >
              <Home className="w-4 h-4 text-primary-container" />
              <span>Whicoustic Home</span>
            </Link>
            <Link
              to="/demo"
              className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors"
            >
              <Radio className="w-4 h-4 text-primary-container" />
              <span>Live Biometric Demo</span>
            </Link>
            <Link
              to="/marketplace"
              className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors"
            >
              <Search className="w-4 h-4 text-primary-container" />
              <span>Voice Marketplace</span>
            </Link>
            <Link
              to="/help"
              className="flex items-center gap-2 p-2.5 rounded-lg hover:bg-surface-container text-on-surface transition-colors"
            >
              <Mic className="w-4 h-4 text-primary-container" />
              <span>Help Center & FAQ</span>
            </Link>
          </div>
        </div>

        <div>
          <Link to="/">
            <Button variant="primary" size="md" icon={<Home className="w-4 h-4" />}>
              Return to Safe Frequency
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
};

