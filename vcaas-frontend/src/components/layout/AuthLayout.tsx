import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { WaveformVisualizer } from '../ui/WaveformVisualizer';
import { Activity, ShieldCheck, Lock, Sparkles } from 'lucide-react';

export const AuthLayout: React.FC = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <div className="flex-1 flex flex-col md:flex-row">
        {/* Left Branding / Acoustic Visualizer Panel */}
        <div className="w-full md:w-5/12 bg-[#0B1C30] text-white p-8 md:p-14 flex flex-col justify-between relative overflow-hidden">
          {/* Subtle amber gradient aura in background */}
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary-container/15 rounded-full blur-3xl pointer-events-none" />

          {/* Top Logo */}
          <div className="relative z-10">
            <Link to="/" className="inline-flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-primary-container border border-white/10 group-hover:scale-105 transition-transform">
                <Activity className="w-5 h-5 text-primary-container" />
              </div>
              <span className="font-recoletta text-2xl font-bold tracking-tight text-white">
                VCaaS
              </span>
            </Link>
          </div>

          {/* Center Pitch & Waveform */}
          <div className="relative z-10 my-12 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-pill bg-white/10 border border-white/15 text-xs font-berthold text-primary-container">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Forensic Neural Synthesis</span>
            </div>

            <h2 className="font-recoletta text-3xl md:text-4xl font-bold leading-tight tracking-tight text-white">
              Own your voice IP. License at global scale.
            </h2>

            <p className="font-lora italic text-secondary-fixed-dim text-sm md:text-base leading-relaxed">
              Every synthesized phoneme is cryptographically stamped with your SHA-256 biometric anchor, preventing deepfake exploitation and automating royalty attribution.
            </p>

            <div className="bg-white/5 p-4 rounded-card border border-white/10 backdrop-blur-sm">
              <div className="flex items-center justify-between text-xs font-code text-white/70 mb-2">
                <span>Active Anchor Frequency</span>
                <span className="text-primary-container">24-Bit / 96kHz</span>
              </div>
              <WaveformVisualizer height={48} barCount={32} />
            </div>
          </div>

          {/* Bottom Security Seals */}
          <div className="relative z-10 flex items-center gap-6 text-xs font-berthold text-white/60 pt-6 border-t border-white/10">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-primary-container" />
              <span>Biometric Proof-of-Consent</span>
            </span>
            <span className="flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-primary-container" />
              <span>Zero-Knowledge Vault</span>
            </span>
          </div>
        </div>

        {/* Right Form Container */}
        <div className="flex-1 flex items-center justify-center p-6 md:p-14 bg-background">
          <div className="w-full max-w-md">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
};

