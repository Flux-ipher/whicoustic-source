import React from 'react';
import { Card } from '../../components/ui/Card';
import { ShieldCheck, Lock, FileText } from 'lucide-react';

export const TermsPage: React.FC = () => {
  return (
    <div className="max-w-container mx-auto px-6 py-12 space-y-10">
      <div className="max-w-3xl space-y-3">
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Terms of Service & Licensing Protocol
        </h1>
        <p className="font-berthold text-slate-600 text-sm">
          Last revised: November 2026 • Governed by SAG-AFTRA Digital Persona Framework & NIST Acoustic Steganography Standards.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Table of Contents */}
        <div className="lg:col-span-4 hidden lg:block">
          <div className="sticky top-28 space-y-2 p-5 bg-white rounded-card border border-outline-subtle text-xs font-berthold">
            <span className="text-secondary uppercase tracking-wider font-bold block mb-2">
              Protocol Sections
            </span>
            <a href="#section-1" className="block text-on-surface hover:text-primary-container py-1">
              1. Sovereign Voice Ownership
            </a>
            <a href="#section-2" className="block text-on-surface hover:text-primary-container py-1">
              2. Cryptographic Watermark Mandate
            </a>
            <a href="#section-3" className="block text-on-surface hover:text-primary-container py-1">
              3. Smart Contract Royalty Escrow
            </a>
            <a href="#section-4" className="block text-on-surface hover:text-primary-container py-1">
              4. Commercial Exclusions & Defamation
            </a>
            <a href="#section-5" className="block text-on-surface hover:text-primary-container py-1">
              5. Dispute Resolution & Forensics
            </a>
          </div>
        </div>

        {/* Legal Text */}
        <div className="lg:col-span-8 space-y-8">
          <Card elevation="elevated" padding="lg" className="space-y-6 text-sm font-berthold leading-relaxed text-secondary">
            <section id="section-1" className="space-y-3">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                1. Sovereign Voice Ownership
              </h3>
              <p>
                By enrolling in the Whicoustic Platform, the Voice Artist or verified rights holder retains 100% indisputable biometric intellectual property ownership over their acoustic timbre, resonance patterns, and phonemic models. Whicoustic acts solely as a non-exclusive cryptographic licensing facilitator and custodian of synthetic neural weights.
              </p>
            </section>

            <section id="section-2" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                2. Cryptographic Watermark Mandate
              </h3>
              <p>
                Every audio stream synthesized via the platform MUST be stamped with the Artist's unique SHA-256 ultrasonic watermark. Any studio, licensee, or downstream platform that intentionally strips, bandpass-filters, or obfuscates this watermark will incur immediate license revocation and liquidated damages.
              </p>
            </section>

            <section id="section-3" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                3. Smart Contract Royalty Escrow
              </h3>
              <p>
                All licensing revenues, whether fixed upfront fees or streaming per-second royalties, are held in an automated cryptographic escrow contract. Funds are automatically cleared on a 30-day settlement cycle and disbursed directly to the Artist’s designated banking or cryptocurrency vault.
              </p>
            </section>

            <section id="section-4" className="space-y-3 pt-6 border-t border-outline-subtle">
              <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                4. Commercial Exclusions & Defamation
              </h3>
              <p>
                Voice personas may never be used for deceptive election interference, unconsented adult content, harassment, or defamatory broadcasts. Violating entities face permanent network banning and referral to federal copyright and identity theft enforcement authorities.
              </p>
            </section>
          </Card>
        </div>
      </div>
    </div>
  );
};

