import React, { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { Mic, ShieldCheck, Sparkles, AlertCircle, RefreshCw, Volume2 } from 'lucide-react';

export const DemoPage: React.FC = () => {
  const [inputText, setInputText] = useState(
    'In a world where digital presence precedes physical reality, your acoustic signature is your ultimate biometric sovereign asset.'
  );
  const [selectedVoice, setSelectedVoice] = useState('Elena Rostova (Cinematic)');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [hasSynthesized, setHasSynthesized] = useState(true);
  const [playbackActive, setPlaybackActive] = useState(false);

  const handleSynthesize = () => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
      setHasSynthesized(true);
      setPlaybackActive(true);
    }, 1200);
  };

  return (
    <div className="max-w-container mx-auto px-6 py-12 space-y-12">
      <div className="max-w-3xl mx-auto text-center space-y-3">
        <Badge variant="amber" size="sm" pulse icon={<Sparkles className="w-3 h-3 text-primary-container" />}>
          Interactive Biometric Sandbox
        </Badge>
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Real-Time Voice Authentication
        </h1>
        <p className="font-lora italic text-secondary text-base">
          Experience zero-latency neural synthesis paired with forensic SHA-256 watermark stamping. Test synthetic phonemes and verify cryptographic authenticity.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 max-w-5xl mx-auto">
        {/* Left: Input & Synthesis Control */}
        <div className="lg:col-span-7 space-y-6">
          <Card elevation="elevated" padding="lg" className="space-y-5">
            <div>
              <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-2">
                1. Select Verified Voice Persona
              </label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
                className="w-full h-11 px-3.5 bg-surface-container font-berthold text-sm text-on-surface rounded-input border border-outline-subtle focus:outline-none focus:border-primary-container"
              >
                <option>Elena Rostova (Cinematic Warmth)</option>
                <option>Marcus Vance (Iron Vanguard Baritone)</option>
                <option>Aoi Tanaka (Conversational AI)</option>
                <option>Julian Sterling (Royal Chronicler)</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary">
                  2. Enter Script for Neural Rendering
                </label>
                <span className="text-[11px] font-code text-secondary">
                  {inputText.length} / 300 chars
                </span>
              </div>
              <textarea
                rows={4}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                className="w-full p-3.5 bg-white font-berthold text-sm text-on-surface rounded-input border border-outline-border focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20"
                placeholder="Type any phrase to render in authentic biometric voice..."
              />
            </div>

            <Button
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={isSynthesizing}
              onClick={handleSynthesize}
              icon={<Mic className="w-4 h-4" />}
            >
              Synthesize & Watermark Audio
            </Button>
          </Card>
        </div>

        {/* Right: Forensic Verification Output */}
        <div className="lg:col-span-5 space-y-6">
          <Card elevation="amber-border" padding="lg" className="space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
              <span className="text-xs font-berthold uppercase font-semibold text-secondary">
                Forensic Verification
              </span>
              <Badge variant="amber" size="sm" pulse>
                SHA-256 Validated
              </Badge>
            </div>

            {/* Audio Waveform */}
            <div className="bg-surface-container p-4 rounded-card border border-outline-subtle space-y-3">
              <div className="flex items-center justify-between text-xs font-berthold">
                <span className="flex items-center gap-1.5 font-semibold text-on-surface">
                  <Volume2 className="w-4 h-4 text-primary-container" />
                  Rendered Stream
                </span>
                <button
                  onClick={() => setPlaybackActive(!playbackActive)}
                  className="text-primary-container hover:underline font-semibold"
                >
                  {playbackActive ? 'Pause Stream' : 'Replay Audio'}
                </button>
              </div>
              <WaveformVisualizer isPlaying={playbackActive} height={46} barCount={30} />
            </div>

            {/* Cryptographic Proof Details */}
            <div className="space-y-3 text-xs font-berthold">
              <div className="flex justify-between py-1.5 border-b border-outline-subtle">
                <span className="text-secondary">Watermark Hash</span>
                <span className="font-code text-on-surface font-semibold">
                  4080c0aea1ea...baaa
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-outline-subtle">
                <span className="text-secondary">Biometric Persona ID</span>
                <span className="font-code text-on-surface font-semibold">
                  PRJ_269326659273
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-outline-subtle">
                <span className="text-secondary">Inference Latency</span>
                <span className="font-code text-emerald-600 font-semibold">
                  38.4 ms (Edge TPU)
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-outline-subtle">
                <span className="text-secondary">Consent Certificate</span>
                <span className="text-emerald-700 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Legally Bound
                </span>
              </div>
            </div>

            <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs font-berthold text-[#92400E] flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                Ultrasonic biometric payload embedded into output PCM without audible degradation.
              </span>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

