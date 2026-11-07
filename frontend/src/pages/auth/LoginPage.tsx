import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../context/AuthContext';
import { ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';
import { PageTransition } from '../../components/ui/PageTransition';

export const LoginPage: React.FC = () => {
  const { login, loginWithOAuth } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await login(email, password);
      // login automatically redirects to Sub-domain Dashboard (app.whicoustic.xyz/dashboard)
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Authentication failed. Please verify your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    setError(null);
    setIsLoading(true);
    try {
      await loginWithOAuth(provider);
      // loginWithOAuth in AuthContext is single source of truth for conditional routing
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Federated sign-in failed. Please try again.');
      }
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
          Enter your credentials to access the platform console (app.whicoustic.xyz).
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs font-berthold text-red-700 flex items-start gap-2"
        >
          <AlertCircle className="w-4 h-4 text-red-600 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Federated Identity Buttons */}
      <div className="space-y-2.5">
        <button
          type="button"
          onClick={() => handleOAuth('google')}
          className="w-full h-11 px-4 bg-white hover:bg-surface-container border border-outline-border rounded-pill flex items-center justify-center gap-3 text-xs font-berthold font-semibold text-on-surface transition-colors shadow-sm"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Sign In with Google</span>
        </button>
      </div>

      <div className="relative flex items-center justify-center">
        <div className="border-t border-outline-subtle w-full" />
        <span className="bg-white px-3 text-[11px] font-berthold uppercase tracking-wider text-secondary">
          Or with email
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email Address"
          type="email"
          required
          placeholder="your.email@organization.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <div>
          <Input
            label="Password"
            type="password"
            required
            placeholder="••••••••••••"
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
            Access Platform Console
          </Button>
        </div>
      </form>

      <div className="pt-2 text-center text-xs font-berthold text-secondary space-y-2">
        <p>
          New voice rights holder?{' '}
          <Link to="/signup" className="text-primary-container font-semibold hover:underline">
            Register & Calibrate Anchor
          </Link>
        </p>
        <p className="text-[11px] font-berthold text-slate-500 flex items-center justify-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          End-to-end cryptographic authentication enforced.
        </p>
      </div>
    </PageTransition>
  );
};
