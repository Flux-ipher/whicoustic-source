import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import {
  Mic,
  ShieldCheck,
  Coins,
  ArrowRight,
  Lock,
  Play,
  CheckCircle2,
  Sparkles,
  Zap,
} from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-24 pb-16">
      {/* 1. HERO SECTION */}
      <section className="relative pt-12 md:pt-20 px-6 max-w-container mx-auto">
        <div className="text-center space-y-6 max-w-3xl mx-auto">
          {/* Top Intelligence Pill */}
          <div className="inline-flex items-center gap-2">
            <Badge variant="amber" size="md" pulse icon={<Sparkles className="w-3.5 h-3.5 text-primary-container" />}>
              Next-Gen Voice IP Infrastructure
            </Badge>
          </div>

          {/* Main Headline (Recoleta) */}
          <h1 className="font-recoletta text-5xl sm:text-6xl md:text-7xl font-bold tracking-tight text-on-surface leading-[1.08]">
            The Biometric Voice Protocol for{' '}
            <span className="text-primary-container relative inline-block">
              Global Media
              <svg
                className="absolute -bottom-2 left-0 w-full h-3 text-primary-container/30"
                viewBox="0 0 100 12"
                preserveAspectRatio="none"
              >
                <path d="M0,8 Q50,0 100,8" stroke="currentColor" strokeWidth="3" fill="none" />
              </svg>
            </span>
          </h1>

          {/* Subtitle (Lora Italic) */}
          <p className="font-lora italic text-lg sm:text-xl text-secondary leading-relaxed max-w-2xl mx-auto">
            Forensic-grade voice synthesis anchored with SHA-256 cryptographic watermarks. Protect your vocal identity, license your AI personas, and automate recurring royalties.
          </p>

          {/* Action CTAs */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup">
              <Button
                variant="primary"
                size="lg"
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Start Onboarding Free
              </Button>
            </Link>
            <Link to="/demo">
              <Button variant="secondary" size="lg" icon={<Play className="w-4 h-4 text-primary-container" />}>
                Test Live Authentication
              </Button>
            </Link>
          </div>

          {/* Trust Highlights */}
          <div className="pt-6 flex items-center justify-center gap-6 text-xs font-berthold text-secondary">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Zero-Deepfake Guarantee</span>
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Automated Smart Contracts</span>
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>24-bit / 96kHz Fidelity</span>
            </span>
          </div>
        </div>

        {/* Hero Acoustic Visualizer Module */}
        <div className="mt-14 max-w-4xl mx-auto">
          <Card elevation="amber-border" padding="lg" className="backdrop-blur-md relative overflow-hidden">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary-container/10 flex items-center justify-center text-primary-container">
                  <Mic className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-recoletta text-base font-bold text-on-surface">
                    Acoustic Biometric Spectrum
                  </h4>
                  <p className="font-code text-xs text-secondary">
                    SHA256: 4080c0aea1ea4cc3a63a13901af1baaa • 42ms TTFT
                  </p>
                </div>
              </div>
              <Badge variant="amber" size="sm" pulse>
                Forensic Watermark Embedded
              </Badge>
            </div>

            {/* Dynamic Waveform Display */}
            <div className="py-6">
              <WaveformVisualizer height={72} barCount={48} />
            </div>

            {/* Telemetry Footer */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 border-t border-outline-subtle text-xs font-berthold">
              <div>
                <span className="text-secondary block">Sampling Frequency</span>
                <span className="font-bold text-on-surface font-code">96,000 Hz</span>
              </div>
              <div>
                <span className="text-secondary block">Phoneme Match</span>
                <span className="font-bold text-emerald-600 font-code">99.84% Precision</span>
              </div>
              <div>
                <span className="text-secondary block">Watermark Strength</span>
                <span className="font-bold text-primary-container font-code">Forensic L3</span>
              </div>
              <div>
                <span className="text-secondary block">Protocol Version</span>
                <span className="font-bold text-on-surface font-code">v2.4-Synthesized</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* 2. THREE PILLARS SECTION */}
      <section className="max-w-container mx-auto px-6">
        <div className="text-center max-w-2xl mx-auto mb-14 space-y-3">
          <h2 className="font-recoletta text-3xl sm:text-4xl font-bold text-on-surface">
            Architected for Artists. Engineered for Studios.
          </h2>
          <p className="font-lora italic text-secondary text-base">
            A comprehensive infrastructure built to bridge the gap between autonomous AI synthesis and authentic voice rights ownership.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Pillar 1 */}
          <Card elevation="elevated" padding="lg" hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-primary-container">
              <Mic className="w-6 h-6" />
            </div>
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Neural Synthesis Studio
            </h3>
            <p className="font-berthold text-sm text-secondary leading-relaxed">
              Clone voice personas with under 5 minutes of clean audio. Train multilingual models that retain vocal timber, emotional inflection, and natural breath cadence.
            </p>
            <ul className="space-y-2 text-xs font-berthold text-on-surface pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>Zero-shot cross-lingual adaptation</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>Instant emotion and pacing sliders</span>
              </li>
            </ul>
          </Card>

          {/* Pillar 2 */}
          <Card elevation="elevated" padding="lg" hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-on-surface">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Cryptographic Watermarking
            </h3>
            <p className="font-berthold text-sm text-secondary leading-relaxed">
              Imperceptible ultrasonic steganography binds every rendered second to a cryptographic hash. Deepfakes without your SHA-256 seal are flagged automatically.
            </p>
            <ul className="space-y-2 text-xs font-berthold text-on-surface pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>Lossless compression survivability</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>Automated real-time broadcast sniffing</span>
              </li>
            </ul>
          </Card>

          {/* Pillar 3 */}
          <Card elevation="elevated" padding="lg" hoverEffect className="space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-primary-container">
              <Coins className="w-6 h-6" />
            </div>
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Automated Royalty Escrow
            </h3>
            <p className="font-berthold text-sm text-secondary leading-relaxed">
              Programmatic smart licensing contracts ensure you get paid per second of game play, film dialogue, or commercial broadcast without chasing accounts receivable.
            </p>
            <ul className="space-y-2 text-xs font-berthold text-on-surface pt-2">
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>USDC or direct Fedwire ACH payouts</span>
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-primary-container" />
                <span>Customizable royalty splits & territory rules</span>
              </li>
            </ul>
          </Card>
        </div>
      </section>

      {/* 3. HOW IT WORKS FLOW */}
      <section className="bg-white border-y border-outline-subtle py-20">
        <div className="max-w-container mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16 space-y-3">
            <Badge variant="neutral" size="sm">
              Operational Workflow
            </Badge>
            <h2 className="font-recoletta text-3xl sm:text-4xl font-bold text-on-surface">
              From Microphone to Global Royalties in 3 Steps
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="space-y-4 p-6 rounded-card bg-surface-container/60 border border-outline-subtle">
              <span className="font-recoletta text-4xl font-bold text-primary-container">
                01
              </span>
              <h3 className="font-recoletta text-xl font-bold text-on-surface">
                Calibrate Your Acoustic Anchor
              </h3>
              <p className="font-berthold text-sm text-secondary leading-relaxed">
                Complete the browser-based acoustic onboarding. Read three phonetic balance sentences to generate your permanent SHA-256 voice passport.
              </p>
            </div>

            {/* Step 2 */}
            <div className="space-y-4 p-6 rounded-card bg-surface-container/60 border border-outline-subtle">
              <span className="font-recoletta text-4xl font-bold text-primary-container">
                02
              </span>
              <h3 className="font-recoletta text-xl font-bold text-on-surface">
                Set Pricing & Licensing Boundaries
              </h3>
              <p className="font-berthold text-sm text-secondary leading-relaxed">
                Determine your base hourly rate and royalty split. Restrict sensitive categories (e.g., political ads, adult content) with automated contract gates.
              </p>
            </div>

            {/* Step 3 */}
            <div className="space-y-4 p-6 rounded-card bg-surface-container/60 border border-outline-subtle">
              <span className="font-recoletta text-4xl font-bold text-primary-container">
                03
              </span>
              <h3 className="font-recoletta text-xl font-bold text-on-surface">
                Receive Automated Disbursements
              </h3>
              <p className="font-berthold text-sm text-secondary leading-relaxed">
                Track real-time synthesis consumption on your sub-domain dashboard. Withdraw monthly earnings via automated direct deposit or crypto vault.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. FINAL CTA BANNER */}
      <section className="max-w-container mx-auto px-6">
        <div className="bg-[#0B1C30] rounded-card-lg p-10 md:p-16 text-center text-white relative overflow-hidden shadow-2xl">
          <div className="absolute top-0 right-0 w-80 h-80 bg-primary-container/20 rounded-full blur-3xl pointer-events-none" />
          <div className="relative z-10 max-w-2xl mx-auto space-y-6">
            <h2 className="font-recoletta text-4xl md:text-5xl font-bold tracking-tight text-white">
              Ready to safeguard and monetize your voice?
            </h2>
            <p className="font-lora italic text-secondary-fixed-dim text-base md:text-lg">
              Join leading voice talent, Hollywood studios, and AI developers building on the verified voice protocol.
            </p>
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup">
                <Button variant="primary" size="lg" icon={<Zap className="w-4 h-4" />}>
                  Create Biometric Vault
                </Button>
              </Link>
              <Link to="/contact">
                <Button variant="secondary" size="lg">
                  Schedule Studio Consultation
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
