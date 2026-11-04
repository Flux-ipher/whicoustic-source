import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { ShieldCheck, Key, Copy, Check, RefreshCw, Lock, AlertTriangle } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedSha, setCopiedSha] = useState(false);
  const [twoFactorActive, setTwoFactorActive] = useState(true);

  const apiKey = 'vcaas_live_891f7a02c99b24e6371da05178419';
  const sha256Key = '4080c0aea1ea4cc3a63a13901af1baaa76da6e81e2804561b6fff5d5f6d917c0';

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleCopySha = () => {
    navigator.clipboard.writeText(sha256Key);
    setCopiedSha(true);
    setTimeout(() => setCopiedSha(false), 2000);
  };

  return (
    <div className="space-y-8 max-w-4xl pb-10">
      <div className="pb-6 border-b border-outline-subtle space-y-1">
        <Badge variant="amber" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
          Cryptographic Provenance Controls
        </Badge>
        <h2 className="font-recoletta text-3xl font-bold text-on-surface">
          Security & API Key Provisioning
        </h2>
        <p className="font-lora italic text-xs text-secondary">
          Manage your biometric root certificate, rotate ultrasonic watermarking seeds, and provision production API credentials.
        </p>
      </div>

      {/* 1. Biometric Root Vault Hash */}
      <Card elevation="amber-border" padding="lg" className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
          <div className="flex items-center gap-2">
            <Lock className="w-5 h-5 text-primary-container" />
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              Biometric Root SHA-256 Vault Hash
            </h3>
          </div>
          <Badge variant="amber" size="sm">
            Active Forensic Anchor
          </Badge>
        </div>

        <p className="text-xs font-berthold text-secondary leading-relaxed">
          This 256-bit hash is irreversibly computed from your acoustic voice anchor. It is embedded into every synthesized PCM sample via ultrasonic psychoacoustic steganography.
        </p>

        <div className="flex items-center gap-3 p-3 bg-surface-container rounded-card border border-outline-subtle">
          <code className="text-xs font-code text-on-surface break-all flex-1">
            {sha256Key}
          </code>
          <Button variant="secondary" size="sm" onClick={handleCopySha} icon={copiedSha ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}>
            {copiedSha ? 'Copied' : 'Copy'}
          </Button>
        </div>
      </Card>

      {/* 2. Production API Key */}
      <Card elevation="elevated" padding="lg" className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-primary-container" />
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              Synthesis API Secret Key
            </h3>
          </div>
          <Badge variant="neutral" size="sm">
            Live Production Key
          </Badge>
        </div>

        <p className="text-xs font-berthold text-secondary leading-relaxed">
          Use this secret key in enterprise backend pipelines to request real-time speech synthesis at <code className="font-code text-primary-container">https://api.vcaas.ai/v1/synthesize</code>.
        </p>

        <div className="flex items-center gap-3 p-3 bg-surface-container rounded-card border border-outline-subtle">
          <code className="text-xs font-code text-on-surface flex-1">
            {apiKey}
          </code>
          <Button variant="secondary" size="sm" onClick={handleCopyKey} icon={copiedKey ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}>
            {copiedKey ? 'Copied' : 'Copy Key'}
          </Button>
        </div>

        <div className="pt-2 flex items-center justify-between">
          <span className="text-xs font-berthold text-secondary">
            Last rotated 14 days ago
          </span>
          <Button variant="dark" size="sm" icon={<RefreshCw className="w-3.5 h-3.5" />}>
            Rotate API Key
          </Button>
        </div>
      </Card>

      {/* 3. Multi-Factor Authentication */}
      <Card elevation="elevated" padding="lg" className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              Hardware & Biometric 2FA
            </h3>
            <p className="font-berthold text-xs text-secondary mt-1">
              Require FIDO2 WebAuthn or authenticator app confirmation before modifying royalty floors or licensing boundaries.
            </p>
          </div>
          <button
            onClick={() => setTwoFactorActive(!twoFactorActive)}
            className={`w-12 h-6 rounded-full transition-colors relative p-0.5 ${
              twoFactorActive ? 'bg-primary-container' : 'bg-outline-border'
            }`}
          >
            <div
              className={`w-5 h-5 rounded-full bg-white transition-transform ${
                twoFactorActive ? 'translate-x-6' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </Card>
    </div>
  );
};
