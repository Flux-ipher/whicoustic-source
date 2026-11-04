import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useAuth } from '../../context/AuthContext';
import { PageTransition } from '../../components/ui/PageTransition';
import { Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';

export const SignupPage: React.FC = () => {
  const navigate = useNavigate();
  const { signup, loginWithOAuth } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await signup(email, password, name);
      // Immediately direct the user to the Onboarding Stepper screen as requested!
      navigate('/onboarding');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuth = async (provider: 'google' | 'github') => {
    setIsLoading(true);
    try {
      await loginWithOAuth(provider);
      navigate('/onboarding');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <PageTransition className="bg-white p-8 sm:p-10 rounded-card-lg border border-outline-subtle shadow-elevated space-y-6">
      <div className="space-y-2">
        <h2 className="font-recoletta text-3xl font-bold text-on-surface">
          Create Voice Vault
        </h2>
        <p className="font-berthold text-xs text-slate-600">
          Register with your email or federated identity to begin biometric anchor calibration.
        </p>
      </div>

      {/* OAuth Buttons */}
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
          <span>Continue with Google</span>
        </button>

        <button
          type="button"
          onClick={() => handleOAuth('github')}
          className="w-full h-11 px-4 bg-white hover:bg-surface-container border border-outline-border rounded-pill flex items-center justify-center gap-3 text-xs font-berthold font-semibold text-on-surface transition-colors shadow-sm"
        >
          <svg className="w-4 h-4 fill-current text-on-surface" viewBox="0 0 24 24">
            <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
          </svg>
          <span>Continue with GitHub</span>
        </button>
      </div>

      <div className="relative flex items-center justify-center">
        <div className="border-t border-outline-subtle w-full" />
        <span className="bg-white px-3 text-[11px] font-berthold uppercase tracking-wider text-secondary">
          Or with email
        </span>
      </div>

      {/* Email Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Your Full Name"
          required
          placeholder="Elena Rostova"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <Input
          label="Email Address"
          type="email"
          required
          placeholder="elena@studio.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <Input
          label="Vault Password"
          type="password"
          required
          placeholder="••••••••••••"
          helperText="Minimum 8 characters with biometric entropy"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

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
            Create Vault & Continue to Onboarding
          </Button>
        </div>
      </form>

      <div className="pt-2 text-center text-xs font-berthold text-secondary space-y-2">
        <p>
          Already hold a cryptographic voice passport?{' '}
          <Link to="/login" className="text-primary-container font-semibold hover:underline">
            Console Sign In
          </Link>
        </p>
        <p className="text-[11px] font-berthold text-slate-500 flex items-center justify-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          Zero raw vocal storage without encryption.
        </p>
      </div>
    </PageTransition>
  );
};

