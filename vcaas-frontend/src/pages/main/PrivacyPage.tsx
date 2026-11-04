import React from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ShieldCheck, EyeOff } from 'lucide-react';

export const PrivacyPage: React.FC = () => {
  return (
    <div className="max-w-container mx-auto px-6 py-12 space-y-10">
      <div className="max-w-3xl space-y-3">
        <Badge variant="amber" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5 text-primary-container" />}>
          Biometric Protection Charter
        </Badge>
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Privacy Policy & Biometric Governance
        </h1>
        <p className="font-lora italic text-secondary text-base">
          How we safeguard raw vocal recordings, isolate neural model weights, and enforce zero-retention raw audio policies.
        </p>
      </div>

      <div className="max-w-4xl space-y-6">
        <Card elevation="elevated" padding="lg" className="space-y-6 text-sm font-berthold leading-relaxed text-secondary">
          <section className="space-y-3">
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Biometric Data Processing & Isolation
            </h3>
            <p>
              Your raw voice recordings are used strictly to generate acoustic embedding matrices and train your private neural weights. Raw WAV audio files are immediately purged from active cache once biometric anchor calibration is complete, unless you explicitly choose to maintain them in encrypted cold storage.
            </p>
          </section>

          <section className="space-y-3 pt-6 border-t border-outline-subtle">
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Zero Model Leakage Guarantee
            </h3>
            <p>
              Your voice model weights are isolated in private tenant partitions. They are never pooled, merged, or used to fine-tune foundational models without prior written mutual consent and explicit multi-signature validation.
            </p>
          </section>

          <section className="space-y-3 pt-6 border-t border-outline-subtle">
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              The Right to Acoustic Erasure
            </h3>
            <p>
              Under California Consumer Privacy Act (CCPA) and EU GDPR Section 17, you hold the perpetual right to trigger immediate neural model deletion and revoke downstream API synthesis endpoints within 24 hours of notification.
            </p>
          </section>
        </Card>
      </div>
    </div>
  );
};
