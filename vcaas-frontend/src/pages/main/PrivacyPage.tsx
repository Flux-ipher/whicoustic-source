import React from 'react';
import { Card } from '../../components/ui/Card';
import { PageTransition } from '../../components/ui/PageTransition';
import { BiometricShieldIllustration } from '../../components/ui/Illustrations';

export const PrivacyPage: React.FC = () => {
  return (
    <PageTransition className="max-w-container mx-auto px-6 py-12 space-y-10">
      <div className="max-w-3xl space-y-3">
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Privacy Policy & Biometric Governance
        </h1>
        <p className="font-berthold text-slate-600 text-sm sm:text-base leading-relaxed">
          How we safeguard raw vocal recordings, isolate neural model weights, and enforce zero-retention raw audio policies.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Table of Contents & Biometric Vault Sidebar */}
        <div className="lg:col-span-4 hidden lg:block space-y-6">
          <div className="space-y-2 p-5 bg-white rounded-card border border-outline-subtle text-xs font-berthold shadow-sm">
            <span className="text-secondary uppercase tracking-wider font-bold block mb-2">
              Governance Sections
            </span>
            <a href="#section-1" className="block text-on-surface hover:text-primary-container py-1 transition-colors">
              1. Biometric Data Processing & Isolation
            </a>
            <a href="#section-2" className="block text-on-surface hover:text-primary-container py-1 transition-colors">
              2. Zero Model Leakage Guarantee
            </a>
            <a href="#section-3" className="block text-on-surface hover:text-primary-container py-1 transition-colors">
              3. The Right to Acoustic Erasure
            </a>
            <a href="#section-4" className="block text-on-surface hover:text-primary-container py-1 transition-colors">
              4. Data Residency & Cryptographic Vaults
            </a>
          </div>

          <div className="p-5 bg-surface-container/60 rounded-card border border-outline-subtle text-center space-y-2">
            <BiometricShieldIllustration size={130} className="mx-auto" />
            <h4 className="font-recoletta text-sm font-bold text-on-surface">Zero-Knowledge Biometric Vault</h4>
            <p className="text-[11px] font-berthold text-slate-600">
              CCPA & EU GDPR Art. 17 compliant. Raw audio purged immediately post-calibration; weights strictly tenant-isolated.
            </p>
          </div>
        </div>

        {/* Policy Text */}
        <div className="lg:col-span-8 space-y-8">
          <Card elevation="elevated" padding="lg" className="space-y-6 text-sm font-berthold leading-relaxed text-secondary">
            <section id="section-1" className="space-y-3">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                1. Biometric Data Processing & Isolation
              </h3>
              <p>
                Your raw voice recordings are used strictly to generate acoustic embedding matrices and train your private neural weights. Raw WAV audio files are immediately purged from active cache once biometric anchor calibration is complete, unless you explicitly choose to maintain them in encrypted cold storage.
              </p>
            </section>

            <section id="section-2" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                2. Zero Model Leakage Guarantee
              </h3>
              <p>
                Your voice model weights are isolated in private tenant partitions. They are never pooled, merged, or used to fine-tune foundational models without prior written mutual consent and explicit multi-signature validation.
              </p>
            </section>

            <section id="section-3" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                3. The Right to Acoustic Erasure
              </h3>
              <p>
                Under California Consumer Privacy Act (CCPA) and EU GDPR Article 17, you hold the perpetual right to trigger immediate neural model deletion and revoke downstream API synthesis endpoints within 24 hours of notification.
              </p>
            </section>

            <section id="section-4" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                4. Data Residency & Cryptographic Vaults
              </h3>
              <p>
                All biometric representations and watermarked acoustic fingerprints are encrypted in transit via TLS 1.3 and at rest with AES-256 encryption. Hardware security modules (HSMs) enforce cryptographic boundaries, ensuring no unauthenticated entity can extract or decompile your biometric voice signatures.
              </p>
            </section>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
};


