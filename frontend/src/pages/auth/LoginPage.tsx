import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../context/AuthContext';
import { Lock, ArrowRight, ShieldCheck } from 'lucide-react';
import { PageTransition } from '../../components/ui/PageTransition';

export const LoginPage: React.FC = () => {
  const { login, loginWithOAuth } = useAuth();
  const [email, setEmail] = useState('elena@acoustic-lab.io');
  const [password, setPassword] = useState('password123');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);
      // login automatically redirects to Sub-domain Dashboard (app.whicoustic.ai/dashboard)
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageTransition className="bg-white p-8 sm:p-10 rounded-card-lg border border-outline-subtle shadow-elevated space-y-6">
      <div className="space-y-2">
        <h2 className="font-recoleta text-3xl font-bold text-on-surface">
          Console Login
        </h2>
        <p className="font-berthold text-xs text-slate-600">
          Enter your credentials to access the platform console (app.whicoustic.ai).
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email Address"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <div>
          <div className="flex justify-between items-center mb-1">
            <span />
            <a href="#forgot" className="text-xs font-berthold text-primary-container hover:underline">
              Forgot Vault Key?
            </a>
          </div>
          <Input
            label="Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <div className="pt-2">
          <Button
            variant="primary"
            size="lg"
            type="submit"
            className="w-full"
            isLoading={isLoading}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Access Sub-domain Console
          </Button>
        </div>
      </form>

      <div className="relative flex items-center justify-center">
        <div className="border-t border-outline-subtle w-full" />
        <span className="bg-white px-3 text-[11px] font-berthold uppercase tracking-wider text-secondary">
          Or enterprise SSO
        </span>
      </div>

      <div className="space-y-2">
        <button
          type="button"
          onClick={() => loginWithOAuth('google')}
          className="w-full h-11 px-4 bg-white hover:bg-surface-container border border-outline-border rounded-pill flex items-center justify-center gap-3 text-xs font-berthold font-semibold text-on-surface transition-colors shadow-sm"
        >
          <span>Sign In with Google Workspace</span>
        </button>
      </div>

      <div className="pt-2 text-center text-xs font-berthold text-secondary space-y-2">
        <p>
          New voice rights holder?{' '}
          <Link to="/signup" className="text-primary-container font-semibold hover:underline">
            Register & Calibrate Anchor
          </Link>
        </p>
        <p className="text-[11px] font-berthold text-slate-500 flex items-center justify-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Multi-factor cryptographic authentication enforced.
        </p>
      </div>
    </PageTransition>
  );
};

