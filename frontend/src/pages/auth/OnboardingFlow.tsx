import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { StepIndicator, Step } from '../../components/ui/StepIndicator';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { MicrophoneTroubleshooterModal } from '../../components/ui/MicrophoneTroubleshooterModal';
import { PageTransition } from '../../components/ui/PageTransition';
import { TalentVoiceIllustration, BiometricShieldIllustration } from '../../components/ui/Illustrations';
import {
  Mic,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Volume2,
  Lock,
  Layers,
  Sliders,
  Award,
  HelpCircle,
} from 'lucide-react';

export const OnboardingFlow: React.FC = () => {
  const { onboardingData, updateOnboardingData, completeOnboarding, user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingProgress, setRecordingProgress] = useState(0);
  const [showTroubleshooter, setShowTroubleshooter] = useState(false);
  const calibrationTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (calibrationTimerRef.current) {
        clearInterval(calibrationTimerRef.current);
      }
    };
  }, []);

  const steps: Step[] = [
    { id: 1, title: 'Voice Persona & Role' },
    { id: 2, title: 'Acoustic Calibration' },
    { id: 3, title: 'Vault Key & Royalty Escrow' },
  ];

  // Step 2 recording simulator
  const handleStartCalibration = () => {
    if (calibrationTimerRef.current) {
      clearInterval(calibrationTimerRef.current);
    }
    setIsRecording(true);
    setRecordingProgress(0);
    calibrationTimerRef.current = setInterval(() => {
      setRecordingProgress((prev) => {
        if (prev >= 100) {
          if (calibrationTimerRef.current) {
            clearInterval(calibrationTimerRef.current);
            calibrationTimerRef.current = null;
          }
          setIsRecording(false);
          updateOnboardingData({ acousticAnchorRecorded: true });
          return 100;
        }
        return prev + 12;
      });
    }, 400);
  };

  return (
    <PageTransition className="space-y-10">
      {/* Stepper Bar */}
      <StepIndicator
        steps={steps}
        currentStep={currentStep}
        onStepClick={(id) => id < currentStep && setCurrentStep(id)}
      />

      {/* STEP 1: Persona & Role Selection */}
      {currentStep === 1 && (
        <Card elevation="elevated" padding="lg" className="space-y-8 animate-fadeIn">
          <div className="text-center space-y-2 max-w-lg mx-auto">
            <TalentVoiceIllustration size={110} className="mx-auto pb-1" />
            <h2 className="font-recoleta text-3xl font-bold text-on-surface">
              Welcome, {user?.name || 'Artist'}. Define Your Persona.
            </h2>
            <p className="font-berthold text-xs text-slate-600">
              Configure your licensing identity and primary domain of artistic work.
            </p>
          </div>

          <div className="space-y-6 max-w-2xl mx-auto">
            {/* Role Choice */}
            <div>
              <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-3">
                1. Select Account Archetype
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { id: 'TALENT', label: 'Voice Talent / Actor', icon: Mic, desc: 'Monetize personal vocal IP' },
                  { id: 'STUDIO', label: 'Game / Film Studio', icon: Layers, desc: 'License voices for production' },
                  { id: 'ENTERPRISE', label: 'Enterprise Developer', icon: Sliders, desc: 'API synthesis at scale' },
                ].map((item) => {
                  const Icon = item.icon;
                  const isSelected = onboardingData.role === item.id;
                  return (
                    <div
                      key={item.id}
                      onClick={() => updateOnboardingData({ role: item.id })}
                      className={`p-4 rounded-card border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-primary-container bg-amber-50/50 shadow-sm'
                          : 'border-outline-subtle bg-white hover:border-secondary'
                      }`}
                    >
                      <Icon className={`w-5 h-5 mb-2 ${isSelected ? 'text-primary-container' : 'text-secondary'}`} />
                      <p className="font-recoleta text-sm font-bold text-on-surface">{item.label}</p>
                      <p className="font-berthold text-xs text-secondary mt-1">{item.desc}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Primary Category */}
            <div>
              <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-2">
                2. Primary Voice Specialization
              </label>
              <select
                value={onboardingData.primaryCategory}
                onChange={(e) => updateOnboardingData({ primaryCategory: e.target.value })}
                className="w-full h-11 px-3.5 bg-surface-container font-berthold text-sm text-on-surface rounded-input border border-outline-subtle focus:outline-none focus:border-primary-container"
              >
                <option>Cinematic Narration & Audio Drama</option>
                <option>AAA Video Game & Character Dialogue</option>
                <option>Commercial Advertising & Broadcast</option>
                <option>Audiobooks & Literary Narration</option>
                <option>Conversational AI & Automotive Keynotes</option>
              </select>
            </div>

            <div className="pt-4 flex justify-end">
              <Button
                variant="primary"
                size="md"
                onClick={() => setCurrentStep(2)}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Continue to Acoustic Calibration
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* STEP 2: Acoustic Anchor & Biometric Verification */}
      {currentStep === 2 && (
        <Card elevation="amber-border" padding="lg" className="space-y-8 animate-fadeIn">
          <div className="text-center space-y-2 max-w-lg mx-auto">
            <span className="text-xs font-berthold font-semibold tracking-wider text-primary-container uppercase">
              Step 2 of 3: Biometric Calibration
            </span>
            <h2 className="font-recoleta text-3xl font-bold text-on-surface">
              Record Acoustic Anchor
            </h2>
            <p className="font-berthold text-xs text-slate-600">
              Read the test phrase into your microphone to calibrate your ultrasonic SHA-256 watermark.
            </p>
          </div>

          <div className="space-y-6 max-w-2xl mx-auto">
            {/* Calibration Script */}
            <div className="p-5 rounded-card bg-surface-container border border-outline-subtle text-center space-y-2">
              <span className="text-[11px] font-berthold uppercase tracking-wider text-secondary font-bold">
                Phonetic Calibration Sentence
              </span>
              <p className="font-recoleta text-lg md:text-xl text-on-surface font-semibold leading-relaxed">
                "The quick bronze fox synthesized zero acoustic jitter over forty-two neural frequency gates."
              </p>
            </div>

            {/* Waveform & Recording Control */}
            <div className="p-6 rounded-card bg-white border border-outline-subtle text-center space-y-4">
              <WaveformVisualizer isPlaying={isRecording} height={56} barCount={36} />

              {isRecording ? (
                <div className="space-y-2">
                  <span className="text-xs font-code font-bold text-primary-container animate-pulse">
                    ANALYZING SPECTRAL FORMants ({recordingProgress}%)
                  </span>
                  <div className="w-full bg-surface-container h-1.5 rounded-full overflow-hidden">
                    <div
                      className="bg-primary-container h-full transition-all duration-300"
                      style={{ width: `${recordingProgress}%` }}
                    />
                  </div>
                </div>
              ) : onboardingData.acousticAnchorRecorded ? (
                <div className="flex items-center justify-center gap-2 text-xs font-berthold font-semibold text-emerald-700 bg-emerald-50 py-2 rounded-pill border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Acoustic Anchor Captured (SHA256: 4080c0aea1ea...baaa)</span>
                </div>
              ) : (
                <p className="text-xs font-berthold text-secondary">
                  Click below to capture 4 seconds of microphone calibration.
                </p>
              )}

              <div className="flex flex-col items-center gap-2">
                <Button
                  variant={isRecording ? 'dark' : 'primary'}
                  size="md"
                  onClick={handleStartCalibration}
                  disabled={isRecording}
                  icon={<Mic className="w-4 h-4" />}
                >
                  {isRecording ? 'Listening...' : 'Begin Voice Calibration'}
                </Button>

                <button
                  type="button"
                  onClick={() => setShowTroubleshooter(true)}
                  className="inline-flex items-center gap-1.5 text-xs font-berthold text-slate-500 hover:text-slate-800 transition-colors pt-1"
                >
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>Microphone not working? Open troubleshooting guide</span>
                </button>
              </div>
            </div>

            <div className="pt-4 flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={() => setCurrentStep(1)} icon={<ArrowLeft className="w-4 h-4" />}>
                Back
              </Button>
              <Button
                variant="primary"
                size="md"
                onClick={() => setCurrentStep(3)}
                disabled={!onboardingData.acousticAnchorRecorded || isRecording}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Continue to Vault Provisioning
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* STEP 3: Vault Key & Licensing Preferences */}
      {currentStep === 3 && (
        <Card elevation="elevated" padding="lg" className="space-y-8 animate-fadeIn">
          <div className="text-center space-y-2 max-w-lg mx-auto">
            <BiometricShieldIllustration size={100} className="mx-auto pb-1" />
            <span className="text-xs font-berthold font-semibold tracking-wider text-primary-container uppercase">
              Step 3 of 3: Final Activation
            </span>
            <h2 className="font-recoleta text-3xl font-bold text-on-surface">
              Vault Key & Escrow Governance
            </h2>
            <p className="font-berthold text-xs text-slate-600">
              Review your cryptographic credentials. You will be redirected to your private dashboard on the sub-domain.
            </p>
          </div>

          <div className="space-y-6 max-w-2xl mx-auto">
            {/* Vault Key Card */}
            <div className="p-5 rounded-card bg-[#0B1C30] text-white space-y-3">
              <div className="flex items-center justify-between text-xs font-berthold text-secondary-fixed-dim">
                <span className="flex items-center gap-1.5">
                  <Award className="w-4 h-4 text-primary-container" />
                  Sovereign Cryptographic Passport
                </span>
                <span className="font-code text-primary-container">ISO 27001</span>
              </div>
              <div>
                <p className="text-xs font-code text-white/50 mb-1">PROVISIONED VAULT ADDRESS</p>
                <p className="font-code text-sm text-primary-container break-all">
                  SHA256: 4080c0aea1ea4cc3a63a13901af1baaa76da6e81e2804561b6fff5d5f6d917c0
                </p>
              </div>
            </div>

            {/* Royalty Floor Preference */}
            <div className="space-y-2">
              <div className="flex justify-between items-center text-xs font-berthold font-semibold">
                <span className="text-on-surface uppercase tracking-wider">
                  Minimum Royalty Floor Share
                </span>
                <span className="text-primary-container font-code font-bold text-sm">
                  {onboardingData.royaltyFloorPct}% per Second Synthesized
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="40"
                step="0.5"
                value={onboardingData.royaltyFloorPct}
                onChange={(e) => updateOnboardingData({ royaltyFloorPct: parseFloat(e.target.value) })}
                className="w-full h-2 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary-container"
              />
              <p className="text-[11px] font-berthold text-slate-500">
                Inbound licensing requests below this percentage threshold will be filtered out automatically.
              </p>
            </div>

            {/* Launch Banner to Sub-domain */}
            <div className="p-4 rounded-card bg-amber-50 border border-amber-200 text-xs font-berthold text-[#92400E] space-y-1">
              <p className="font-bold">Next Stop: Sub-domain Console (app.whicoustic.ai)</p>
              <p className="text-[11px] text-[#92400E]/90">
                Clicking complete will finalize your identity and route you into your isolated Operations Dashboard on the platform sub-domain.
              </p>
            </div>

            <div className="pt-4 flex items-center justify-between">
              <Button variant="ghost" size="sm" onClick={() => setCurrentStep(2)} icon={<ArrowLeft className="w-4 h-4" />}>
                Back
              </Button>
              <Button
                variant="primary"
                size="lg"
                onClick={completeOnboarding}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Complete & Enter Sub-domain Dashboard
              </Button>
            </div>
          </div>
        </Card>
      )}

      <MicrophoneTroubleshooterModal
        isOpen={showTroubleshooter}
        onClose={() => setShowTroubleshooter(false)}
        onRetry={handleStartCalibration}
      />
    </PageTransition>
  );
};

