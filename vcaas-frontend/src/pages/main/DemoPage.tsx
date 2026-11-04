import React from 'react';
import { useMicrophoneAnalysis } from '../../hooks/useMicrophoneAnalysis';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Card } from '../../components/ui/Card';
import {
  Mic,
  MicOff,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Activity,
  Radio,
  Code2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

export const DemoPage: React.FC = () => {
  const {
    isListening,
    error,
    decibels,
    frequencyData,
    analysisResult,
    simulationMode,
    setSimulationMode,
    startListening,
    stopListening,
  } = useMicrophoneAnalysis();

  const isHuman = analysisResult.verdict === 'HUMAN';

  return (
    <div className="max-w-container mx-auto px-6 py-12 space-y-12">
      {/* 1. Header Section */}
      <div className="max-w-3xl mx-auto text-center space-y-3">
        <Badge
          variant={isListening ? 'amber' : 'neutral'}
          size="sm"
          pulse={isListening}
          icon={<ShieldCheck className="w-3.5 h-3.5 text-primary-container" />}
        >
          {isListening ? 'Live Real-Time Voice Verification Active' : '6-Layer Biometric Acoustic Defense'}
        </Badge>
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Real-Time Voice Verification
        </h1>
        <p className="font-lora italic text-secondary text-base">
          Continuously analyzes microphone input to determine whether spoken audio is authentic human speech or AI-generated synthetic deepfakes across 6 independent acoustic defense layers.
        </p>
      </div>

      {/* Permission Error Banner */}
      {error && (
        <div className="max-w-3xl mx-auto p-4 rounded-card bg-rose-50 border border-rose-200 text-xs font-berthold text-rose-800 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 2. Microphone Command & Real-Time Audio Deck */}
      <Card elevation="elevated" padding="lg" className="max-w-4xl mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-outline-subtle">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                isListening ? 'bg-primary-container text-white shadow-amber-glow' : 'bg-surface-container text-secondary'
              }`}
            >
              {isListening ? <Radio className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
            </div>
            <div>
              <h3 className="font-recoletta text-lg font-bold text-on-surface">
                Acoustic Sensor Feed
              </h3>
              <p className="text-xs font-berthold text-secondary">
                {isListening ? 'Microphone stream captured at 48.0 kHz 24-bit PCM' : 'Microphone idle • Click to activate real-time defense'}
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 text-xs font-berthold">
            <span className="text-secondary font-medium">Test Mode:</span>
            <div className="bg-surface-container p-1 rounded-pill flex items-center border border-outline-subtle">
              <button
                onClick={() => setSimulationMode('HUMAN')}
                className={`px-3 py-1 rounded-pill font-semibold transition-all ${
                  simulationMode !== 'AI_ATTACK'
                    ? 'bg-white text-on-surface shadow-sm'
                    : 'text-secondary hover:text-on-surface'
                }`}
              >
                Human Voice
              </button>
              <button
                onClick={() => setSimulationMode('AI_ATTACK')}
                className={`px-3 py-1 rounded-pill font-semibold transition-all ${
                  simulationMode === 'AI_ATTACK'
                    ? 'bg-rose-600 text-white shadow-sm'
                    : 'text-secondary hover:text-rose-600'
                }`}
              >
                Simulate AI Attack
              </button>
            </div>
          </div>
        </div>

        {/* Real-time Frequency Spectrum Visualizer */}
        <div className="bg-[#0B1C30] p-5 rounded-card space-y-3 text-white">
          <div className="flex items-center justify-between text-xs font-code text-white/70">
            <span className="flex items-center gap-2">
              <Activity className="w-3.5 h-3.5 text-primary-container" />
              Live FFT Frequency Matrix
            </span>
            <div className="flex items-center gap-4">
              <span>Input Level: <strong className="text-primary-container">{isListening ? `${decibels} dBFS` : 'Muted'}</strong></span>
              <span>Latency: <strong className="text-emerald-400">{analysisResult.latencyMs} ms</strong></span>
            </div>
          </div>

          {/* Dynamic Audio Bars driven by real mic or idle */}
          <div className="h-16 flex items-end gap-1.5 pt-2">
            {frequencyData.map((val, idx) => (
              <div
                key={idx}
                className="flex-1 rounded-t-full transition-all duration-75"
                style={{
                  height: `${isListening ? val : 10}%`,
                  backgroundColor:
                    idx % 3 === 0
                      ? '#F59E0B'
                      : idx % 5 === 0
                      ? '#38BDF8'
                      : '#94A3B8',
                }}
              />
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-xs font-berthold text-secondary flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>Continuous Rolling Analysis: 1.5s sliding window ({analysisResult.analyzedChunks} chunks inspected)</span>
          </div>

          <Button
            variant={isListening ? 'dark' : 'primary'}
            size="lg"
            onClick={isListening ? stopListening : startListening}
            icon={isListening ? <MicOff className="w-4 h-4 text-rose-400" /> : <Mic className="w-4 h-4" />}
          >
            {isListening ? 'Stop Real-Time Listening' : 'Start Real-Time Listening'}
          </Button>
        </div>
      </Card>

      {/* 3. Real-Time Detection Verdict Banner */}
      <div className="max-w-4xl mx-auto">
        <div
          className={`p-6 sm:p-8 rounded-card-lg border transition-all duration-300 ${
            isHuman
              ? 'bg-emerald-50/80 border-emerald-300 shadow-md'
              : 'bg-rose-50/90 border-rose-300 shadow-lg'
          }`}
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={`w-14 h-14 rounded-full flex items-center justify-center shrink-0 ${
                  isHuman ? 'bg-emerald-600 text-white shadow-md' : 'bg-rose-600 text-white shadow-lg animate-pulse'
                }`}
              >
                {isHuman ? <ShieldCheck className="w-8 h-8" /> : <ShieldAlert className="w-8 h-8" />}
              </div>
              <div className="space-y-1">
                <span className="text-[11px] font-berthold uppercase tracking-widest font-bold text-secondary">
                  Live Biometric Verdict
                </span>
                <h2
                  className={`font-recoletta text-2xl sm:text-3xl font-bold tracking-tight ${
                    isHuman ? 'text-emerald-950' : 'text-rose-950'
                  }`}
                >
                  {isHuman ? 'AUTHENTIC HUMAN VOICE DETECTED' : 'SYNTHETIC / AI GENERATED VOICE DETECTED'}
                </h2>
                <p className="font-lora italic text-xs text-secondary">
                  {isHuman
                    ? 'All 6 acoustic defense layers confirmed biological vocal tract mechanics and natural phonetic entropy.'
                    : 'High-confidence synthetic audio detected. Multiple defense layers breached by neural vocoder signatures.'}
                </p>
              </div>
            </div>

            {/* Confidence Gauge */}
            <div className="text-left sm:text-right shrink-0 bg-white/70 px-5 py-3 rounded-card border border-outline-subtle">
              <span className="text-[11px] font-berthold uppercase tracking-wider text-secondary block">
                {isHuman ? 'Human Authenticity' : 'Synthetic Probability'}
              </span>
              <span
                className={`font-recoletta text-3xl font-bold ${
                  isHuman ? 'text-emerald-700' : 'text-rose-700'
                }`}
              >
                {isHuman ? `${analysisResult.confidence.toFixed(1)}%` : `${analysisResult.isSyntheticProb.toFixed(1)}%`}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Per-Layer Breakdown Grid (All 6 Layers) */}
      <div className="max-w-4xl mx-auto space-y-5">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              6-Layer Defense Score Breakdown
            </h3>
            <p className="font-lora italic text-xs text-secondary">
              Granular telemetry across all 6 biometric and mathematical security vectors
            </p>
          </div>
          <Badge variant="neutral" size="sm">
            6 Layers Active
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {analysisResult.layers.map((layer) => {
            const isPass = layer.status === 'PASS';
            const isAnomaly = layer.status === 'ANOMALY';

            return (
              <Card
                key={layer.id}
                elevation="elevated"
                padding="md"
                className={`space-y-3 transition-colors ${
                  !isPass && !isAnomaly
                    ? 'border-rose-300 bg-rose-50/30'
                    : isAnomaly
                    ? 'border-amber-300 bg-amber-50/20'
                    : 'hover:border-primary-container/40'
                }`}
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-0.5">
                    <span className="text-[11px] font-code font-bold text-primary-container uppercase">
                      {layer.badge}
                    </span>
                    <h4 className="font-recoletta text-base font-bold text-on-surface leading-snug">
                      {layer.name}
                    </h4>
                  </div>
                  <Badge
                    variant={isPass ? 'success' : isAnomaly ? 'amber' : 'dark'}
                    size="sm"
                    icon={isPass ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3 text-rose-400" />}
                  >
                    {layer.status}
                  </Badge>
                </div>

                {/* Score Bar */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs font-berthold font-semibold">
                    <span className="text-secondary">{layer.metric}</span>
                    <span
                      className={`font-code ${
                        isPass ? 'text-emerald-700' : isAnomaly ? 'text-amber-700' : 'text-rose-700 font-bold'
                      }`}
                    >
                      {layer.score.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-surface-container h-2 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        isPass ? 'bg-emerald-600' : isAnomaly ? 'bg-amber-500' : 'bg-rose-600'
                      }`}
                      style={{ width: `${layer.score}%` }}
                    />
                  </div>
                </div>

                {/* Description & Diagnostic */}
                <p className="text-xs font-berthold text-secondary leading-relaxed">
                  {layer.description}
                </p>

                <div className="p-2.5 rounded-lg bg-surface-container/80 text-[11px] font-code text-on-surface border border-outline-subtle">
                  <strong className="text-primary-container">Telemetry: </strong>
                  {layer.diagnostic}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* 5. Developer Callout: Backend Integration Blueprint */}
      <div className="max-w-4xl mx-auto p-6 rounded-card bg-[#0B1C30] text-white space-y-4 shadow-xl">
        <div className="flex items-center gap-2.5">
          <Code2 className="w-5 h-5 text-primary-container" />
          <h3 className="font-recoletta text-lg font-bold text-white">
            Backend Inference Endpoint Blueprint
          </h3>
        </div>
        <p className="text-xs font-berthold text-secondary-fixed-dim leading-relaxed">
          When you connect your Python, PyTorch, or Go model, point <code className="font-code text-primary-container">VITE_API_BASE_URL</code> in <code className="font-code text-primary-container">.env.development</code> to your server. The frontend is wired to stream PCM chunks to your verification handler:
        </p>
        <div className="p-3 bg-black/40 rounded-lg font-code text-xs text-primary-fixed border border-white/10 overflow-x-auto whitespace-pre">
{`POST /api/v1/verify-voice
Content-Type: multipart/form-data (audio/wav chunk)
Response: {
  verdict: "HUMAN" | "AI_GENERATED",
  confidence: 99.2,
  layers: [
    { id: 1, name: "Ultrasonic Steganography", score: 98.4, status: "PASS", diagnostic: "..." },
    { id: 2, name: "Glottal Pulse Mechanics", score: 96.8, status: "PASS", diagnostic: "..." },
    ...
  ]
}`}
        </div>
      </div>
    </div>
  );
};
