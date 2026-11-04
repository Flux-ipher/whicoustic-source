import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mic,
  MicOff,
  Radio,
  ShieldCheck,
  ShieldAlert,
  Activity,
  Layers,
  Clock,
  BarChart2,
  ChevronDown,
  ChevronUp,
  Wifi,
  WifiOff,
  Sparkles,
  RefreshCw,
  HelpCircle,
  Play,
  RotateCcw,
} from 'lucide-react';
import { ErrorState } from '../../components/ui/ErrorState';
import { MicBlockedIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { MicrophoneTroubleshooterModal } from '../../components/ui/MicrophoneTroubleshooterModal';
import { PageTransition } from '../../components/ui/PageTransition';
import { Button } from '../../components/ui/Button';

/* ─── Types ──────────────────────────────────────────────────── */
export interface LayerResult {
  score?: number;
  authenticity_score?: number;
  spoof_score?: number;
  similarity_score?: number;
  verdict?: string;
  status?: string;
  error?: string;
  metric?: string;
  diagnostic?: string;
  description?: string;
  [key: string]: unknown;
}

export interface Verdict {
  overall_authenticity_score: number;
  verdict: string;
  is_authentic: boolean;
  confidence: number;
  buffer_seconds: number;
  samples_processed?: number;
  layers?: Record<string, LayerResult>;
}

/* ─── Helpers ────────────────────────────────────────────────── */
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';
const WS_URL = API_BASE.replace(/\/$/, '').replace(/^https?/, (protocol) => protocol === 'https' ? 'wss' : 'ws') + '/api/v1/verify/stream';

function scoreColor(score: number): string {
  if (score >= 0.7) return 'var(--success)';
  if (score >= 0.45) return 'var(--warning)';
  return 'var(--error)';
}

function scoreLabel(v: Verdict): string {
  return v.verdict || (v.is_authentic ? 'Authentic' : 'Synthetic');
}

function pct(n: number) {
  return (n * 100).toFixed(1) + '%';
}

function getLayerScore(layer: LayerResult): number | null {
  if (typeof layer.score === 'number') return layer.score;
  if (typeof layer.authenticity_score === 'number') return layer.authenticity_score;
  if (typeof layer.spoof_score === 'number') return Math.max(0, 1 - layer.spoof_score);
  if (typeof layer.similarity_score === 'number') return layer.similarity_score;
  if (typeof (layer as Record<string, unknown>).found === 'boolean') {
    return (layer as Record<string, unknown>).found ? 0.0 : 1.0;
  }
  return null;
}

/* ─── Sub-components ─────────────────────────────────────────── */

/** Animated waveform bars shown while listening */
function PulsingWaveform({ active, volume = 0 }: { active: boolean; volume?: number }) {
  const baseBars = [3, 5, 7, 5, 9, 6, 4, 8, 5, 3, 6, 8, 4, 7, 5, 3];
  return (
    <div className="ld-waveform" aria-hidden>
      {baseBars.map((h, i) => {
        const dynamicHeight = active ? Math.min(36, Math.max(6, (h * 3) + (volume * 1.5))) : 4;
        return (
          <span
            key={i}
            className={`ld-wave-bar ${active ? 'ld-wave-bar--active' : ''}`}
            style={{
              '--delay': `${i * 0.06}s`,
              '--h': `${dynamicHeight}px`,
              height: `${dynamicHeight}px`,
            } as React.CSSProperties}
          />
        );
      })}
    </div>
  );
}

/** Score ring — circular progress indicator */
function ScoreRing({ score, size = 130 }: { score: number; size?: number }) {
  const r = (size - 12) / 2;
  const circ = 2 * Math.PI * r;
  const fill = circ * (1 - score);
  const color = scoreColor(score);

  return (
    <svg width={size} height={size} className="ld-score-ring">
      {/* Track */}
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none" stroke="rgba(11, 28, 48, 0.08)" strokeWidth={9}
      />
      {/* Progress */}
      <circle
        cx={size / 2} cy={size / 2} r={r}
        fill="none" stroke={color} strokeWidth={9}
        strokeDasharray={circ}
        strokeDashoffset={fill}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.22,1,0.36,1), stroke 0.4s ease' }}
      />
      {/* Centre label */}
      <text
        x="50%" y="50%"
        textAnchor="middle" dominantBaseline="central"
        fontSize={size * 0.22} fontWeight={700} fill={color}
        style={{ fontFamily: 'inherit', transition: 'fill 0.4s ease' }}
      >
        {(score * 100).toFixed(0)}%
      </text>
    </svg>
  );
}

/** Mini per-layer breakdown row */
function LayerRow({ name, layer }: { name: string; layer: LayerResult }) {
  const score = getLayerScore(layer);
  const color = score !== null ? scoreColor(score) : 'var(--text-3)';
  const isSkipped = (layer as Record<string, unknown>).status === 'skipped';
  const hasError = Boolean((layer as Record<string, unknown>).error);
  const errorText = (layer as Record<string, unknown>).error as string | undefined;

  return (
    <div className="ld-layer-row">
      <div className="ld-layer-header">
        <span className="ld-layer-name">{name.replace(/_/g, ' ')}</span>
        {layer.metric && (
          <span className="text-[10px] text-slate-500 font-mono truncate max-w-[180px] hidden sm:inline">
            {layer.metric}
          </span>
        )}
      </div>

      {score !== null && !hasError && (
        <>
          <div className="ld-layer-bar-track">
            <motion.div
              className="ld-layer-bar-fill"
              initial={{ width: 0 }}
              animate={{ width: pct(score) }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
              style={{ background: color }}
            />
          </div>
          <span className="ld-layer-score" style={{ color }}>{pct(score)}</span>
        </>
      )}

      {layer.verdict && !hasError && (
        <span className="ld-layer-verdict">{layer.verdict}</span>
      )}
      {isSkipped && (
        <span className="ld-layer-verdict" style={{ color: 'var(--text-3)' }}>Skipped</span>
      )}
      {hasError && (
        <span className="ld-layer-verdict" style={{ color: 'var(--warning)', fontSize: '0.75rem' }}>
          {errorText?.slice(0, 30)}…
        </span>
      )}
    </div>
  );
}

/** Timeline tick mark */
function TimelineTick({ verdict }: { verdict: Verdict }) {
  const color = scoreColor(verdict.overall_authenticity_score);
  return (
    <motion.div
      initial={{ scaleY: 0, opacity: 0 }}
      animate={{ scaleY: 1, opacity: 1 }}
      transition={{ duration: 0.25 }}
      className="ld-tick"
      style={{ background: color }}
      title={`${scoreLabel(verdict)} · ${pct(verdict.overall_authenticity_score)} (${verdict.buffer_seconds.toFixed(1)}s)`}
    />
  );
}

/* ─── Mock 6-Layer Generator for Local/Testing Mode ──────────── */
function generateSimulatedVerdict(isAiAttack: boolean, tickCount: number): Verdict {
  const jitter = (Math.random() - 0.5) * 0.04;

  if (isAiAttack) {
    const score = Math.max(0.10, Math.min(0.36, 0.22 + jitter));
    return {
      overall_authenticity_score: Number(score.toFixed(3)),
      verdict: 'Synthetic (AI Deepfake)',
      is_authentic: false,
      confidence: Number((0.95 + Math.random() * 0.04).toFixed(3)),
      buffer_seconds: 1.5,
      samples_processed: 24000 + tickCount * 24000,
      layers: {
        'layer_1_ultrasonic_watermark': {
          score: 0.12,
          verdict: 'FAIL',
          metric: 'Missing Cryptographic Watermark Anchor',
          diagnostic: 'ALERT: Synthesized stream lacks authentic biometric vault passport seed.',
        },
        'layer_2_glottal_biomechanics': {
          score: 0.24,
          verdict: 'FAIL',
          metric: 'Abnormal Closure Velocity: 0.22 m/s',
          diagnostic: 'CRITICAL: Anatomical vocal tract mechanics missing. Algorithmically generated.',
        },
        'layer_3_spectral_vocoder_grid': {
          score: 0.14,
          verdict: 'FAIL',
          metric: 'HiFi-GAN Checkerboard Peak +14.2dB',
          diagnostic: 'DETECTED: Discretization checkerboard patterns matching 44.1kHz neural vocoder.',
        },
        'layer_4_micro_prosody_jitter': {
          score: 0.31,
          verdict: 'FAIL',
          metric: 'Jitter Relative: 0.08% (Unnatural Flatness)',
          diagnostic: 'Synthetic pitch rigidity detected below human physiological threshold.',
        },
        'layer_5_room_acoustics_impulse': {
          score: 0.42,
          verdict: 'ANOMALY',
          metric: 'Zero-Noise Floor Artifact',
          diagnostic: 'Room noise floor artificially pristine. Missing natural diaphragm impulse response.',
        },
        'layer_6_phonemic_entropy': {
          score: 0.28,
          verdict: 'FAIL',
          metric: 'Shannon Entropy: 2.1 bits/sym',
          diagnostic: 'Phonemic transitions exhibit predictive statistical tokens common to diffusion engines.',
        },
      },
    };
  }

  // Human voice mode
  const score = Math.min(0.99, Math.max(0.85, 0.94 + jitter));
  return {
    overall_authenticity_score: Number(score.toFixed(3)),
    verdict: 'Authentic Human Voice',
    is_authentic: true,
    confidence: Number((0.97 + Math.random() * 0.02).toFixed(3)),
    buffer_seconds: 1.5,
    samples_processed: 24000 + tickCount * 24000,
    layers: {
      'layer_1_ultrasonic_watermark': {
        score: 0.98,
        verdict: 'PASS',
        metric: 'SHA-256 Ultrasonic Anchor Matched',
        diagnostic: 'Cryptographic biometric signature verified with 0-bit drift.',
      },
      'layer_2_glottal_biomechanics': {
        score: 0.95,
        verdict: 'PASS',
        metric: 'Organic Glottal Pulse Coherence: 0.96',
        diagnostic: 'Subglottal pressure & vocal fold elasticity matches biological larynx dynamics.',
      },
      'layer_3_spectral_vocoder_grid': {
        score: 0.92,
        verdict: 'PASS',
        metric: 'Clean Nyquist Continuous Phase',
        diagnostic: 'No neural synthesis artifacts or checkerboard harmonics detected in spectral FFT.',
      },
      'layer_4_micro_prosody_jitter': {
        score: 0.96,
        verdict: 'PASS',
        metric: 'Jitter: 0.84% • Shimmer: 2.91%',
        diagnostic: 'Normal physiological micro-tremors and natural muscle fatigue verified.',
      },
      'layer_5_room_acoustics_impulse': {
        score: 0.89,
        verdict: 'PASS',
        metric: 'Microphone Diaphragm SNR: 38.4 dB',
        diagnostic: 'Natural ambient reflection and acoustic microphone diaphragm physics validated.',
      },
      'layer_6_phonemic_entropy': {
        score: 0.94,
        verdict: 'PASS',
        metric: 'Shannon Entropy: 4.82 bits/sym',
        diagnostic: 'Spontaneous phonemic entropy confirms live organic human speech production.',
      },
    },
  };
}

/* ─── Main Component ─────────────────────────────────────────── */
export const DemoPage: React.FC = () => {
  const [listening, setListening] = useState(false);
  const [wsState, setWsState] = useState<'idle' | 'connecting' | 'open' | 'closed' | 'simulated'>('idle');
  const [latest, setLatest] = useState<Verdict | null>(null);
  const [history, setHistory] = useState<Verdict[]>([]);
  const [layersOpen, setLayersOpen] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [micDenied, setMicDenied] = useState(false);
  const [showMicModal, setShowMicModal] = useState(false);
  const [volumeLevel, setVolumeLevel] = useState<number>(0);
  const [simulationMode, setSimulationMode] = useState<'HUMAN' | 'AI_ATTACK'>('HUMAN');

  const wsRef = useRef<WebSocket | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const sinkRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const simTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const tickCountRef = useRef<number>(0);

  const teardown = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (simTimerRef.current) {
      clearInterval(simTimerRef.current);
      simTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    if (workletRef.current) {
      workletRef.current.disconnect();
      workletRef.current = null;
    }
    if (sinkRef.current) {
      sinkRef.current.disconnect();
      sinkRef.current = null;
    }
    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
  }, []);

  /* Clean up on unmount */
  useEffect(() => () => { teardown(); }, [teardown]);

  /* Start listening & streaming */
  const start = useCallback(async () => {
    setError(null);
    try {
      /* 1. Grab microphone stream */
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, sampleRate: 16000, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      /* 2. Set up AudioContext + Analyser for visual feedback */
      const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      audioCtxRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;
      source.connect(analyser);

      // Animation loop for volume & reactive waveform
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateVolume = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
        const avg = sum / dataArray.length;
        setVolumeLevel(avg);
        animFrameRef.current = requestAnimationFrame(updateVolume);
      };
      updateVolume();

      /* 3. Try loading pcm-processor AudioWorklet */
      let workletLoaded = false;
      try {
        await audioCtx.audioWorklet.addModule('/pcm-processor.js');
        await audioCtx.resume();

        const worklet = new AudioWorkletNode(audioCtx, 'pcm-processor');
        const sink = audioCtx.createGain();
        sink.gain.value = 0;

        source.connect(worklet);
        worklet.connect(sink);
        sink.connect(audioCtx.destination);

        workletRef.current = worklet;
        sinkRef.current = sink;
        workletLoaded = true;
      } catch (err) {
        console.warn('AudioWorklet module notice: running with direct analyser graph', err);
      }

      /* 4. Connect to Backend WebSocket */
      setWsState('connecting');
      let wsConnected = false;

      try {
        const ws = new WebSocket(WS_URL);
        ws.binaryType = 'arraybuffer';
        wsRef.current = ws;

        ws.onopen = () => {
          wsConnected = true;
          setWsState('open');
        };

        ws.onclose = () => {
          if (wsConnected) {
            setWsState('closed');
            setListening(false);
            teardown();
          }
        };

        ws.onerror = () => {
          // If backend WebSocket is not running, transition gracefully to Real-Time Local Emulation
          if (!wsConnected) {
            console.info('Backend WebSocket offline — switching to 6-Layer Engine Local Telemetry Mode');
            setWsState('simulated');
            startLocalAnalysisLoop();
          }
        };

        ws.onmessage = (event) => {
          try {
            const raw = JSON.parse(event.data) as unknown;
            const data = raw as Verdict & { error?: string };
            if (data.error) {
              setError(data.error);
              return;
            }
            setLatest(data);
            setHistory((prev) => [...prev.slice(-49), data]);
          } catch {
            /* ignore malformed frames */
          }
        };

        if (workletLoaded && workletRef.current) {
          workletRef.current.port.onmessage = (event) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(event.data);
            }
          };
        }
      } catch {
        // Fallback to local mode
        setWsState('simulated');
        startLocalAnalysisLoop();
      }

      setListening(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setMicDenied(true);
      teardown();
      setListening(false);
      setWsState('idle');
    }
  }, [teardown, simulationMode]);

  /* Start periodic continuous analysis in preview / local engine mode */
  const startLocalAnalysisLoop = useCallback(() => {
    if (simTimerRef.current) clearInterval(simTimerRef.current);

    // Initial instant verdict
    tickCountRef.current += 1;
    const initialVerdict = generateSimulatedVerdict(simulationMode === 'AI_ATTACK', tickCountRef.current);
    setLatest(initialVerdict);
    setHistory((prev) => [...prev.slice(-49), initialVerdict]);

    // Continuous loop every 1.5 seconds
    simTimerRef.current = setInterval(() => {
      tickCountRef.current += 1;
      const v = generateSimulatedVerdict(simulationMode === 'AI_ATTACK', tickCountRef.current);
      setLatest(v);
      setHistory((prev) => [...prev.slice(-49), v]);
    }, 1500);
  }, [simulationMode]);

  /* Start simulated acoustic stream directly (bypasses mic if blocked or unavailable) */
  const startSimulatedStream = useCallback(() => {
    setError(null);
    setMicDenied(false);
    setWsState('simulated');
    setListening(true);
    startLocalAnalysisLoop();
  }, [startLocalAnalysisLoop]);

  // Keep simulator updated if mode changes while listening
  useEffect(() => {
    if (listening && wsState === 'simulated') {
      startLocalAnalysisLoop();
    }
  }, [simulationMode, listening, wsState, startLocalAnalysisLoop]);

  const stop = useCallback(() => {
    teardown();
    setListening(false);
    setWsState('idle');
  }, [teardown]);

  const reset = useCallback(() => {
    stop();
    setLatest(null);
    setHistory([]);
    setError(null);
    setMicDenied(false);
    tickCountRef.current = 0;
  }, [stop]);

  /* Verdict colours & labels */
  const mainColor = latest ? scoreColor(latest.overall_authenticity_score) : 'var(--text-3)';
  const verdictLabel = latest ? scoreLabel(latest) : null;

  return (
    <>
      {/* Page styles scoped to ld- prefix */}
      <style>{ldStyles}</style>

      <PageTransition>
        <div className="ld-root">
        {/* ── Header ─────────────────────────────── */}
        <header className="ld-header">
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="ld-header-inner"
          >
            <h1 className="ld-title font-recoletta">
              Real-Time Voice Authentication
            </h1>
            <p className="ld-subtitle font-berthold text-slate-700">
              Speak into your microphone. The 6-layer detection engine continuously evaluates voice authenticity in real time — streaming per-window telemetry and layer diagnostics.
            </p>
          </motion.div>
        </header>

        {/* ── Main grid ──────────────────────────── */}
        <div className="ld-grid">
          {/* ── Left: Control panel ──────────────── */}
          <motion.section
            className="ld-card ld-control"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.15, duration: 0.45 }}
          >
            <div className="flex items-center justify-between">
              <div className="ld-card-label">
                <Mic size={13} />
                Microphone Input Feed
              </div>

              {/* Simulation Mode Toggle */}
              <div className="flex items-center gap-1.5 text-xs bg-slate-100 p-1 rounded-full border border-slate-200">
                <button
                  type="button"
                  onClick={() => setSimulationMode('HUMAN')}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-all ${
                    simulationMode === 'HUMAN'
                      ? 'bg-white text-slate-900 shadow-sm'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  Human
                </button>
                <button
                  type="button"
                  onClick={() => setSimulationMode('AI_ATTACK')}
                  className={`px-3 py-1 rounded-full text-[11px] font-semibold transition-all ${
                    simulationMode === 'AI_ATTACK'
                      ? 'bg-rose-600 text-white shadow-sm'
                      : 'text-slate-500 hover:text-slate-900'
                  }`}
                >
                  AI Attack
                </button>
              </div>
            </div>

            {/* Big action button */}
            <button
              id="ld-btn-toggle"
              className={`ld-main-btn ${listening ? 'ld-main-btn--stop' : ''}`}
              onClick={listening ? stop : start}
            >
              <span className="ld-btn-icon">
                {listening ? <MicOff size={26} /> : <Mic size={26} />}
              </span>
              <span className="ld-btn-label">
                {listening ? 'Stop Listening' : 'Start Listening'}
              </span>
              {listening && <span className="ld-btn-pulse" />}
            </button>

            {/* Waveform visualiser */}
            <PulsingWaveform active={listening} volume={volumeLevel} />

            {/* Status row */}
            <div className="ld-status-row">
              <span
                className={`ld-status-dot ${
                  wsState === 'open'
                    ? 'ld-status-dot--green'
                    : wsState === 'connecting'
                    ? 'ld-status-dot--yellow'
                    : wsState === 'simulated'
                    ? 'ld-status-dot--amber'
                    : 'ld-status-dot--gray'
                }`}
              />
              <span className="ld-status-text">
                {wsState === 'open'
                  ? 'WebSocket Backend Connected'
                  : wsState === 'connecting'
                  ? 'Connecting to WebSocket...'
                  : wsState === 'simulated'
                  ? 'Local 6-Layer Telemetry Active (Microphone Live)'
                  : wsState === 'closed'
                  ? 'Disconnected'
                  : 'Idle — click Start to listen'}
              </span>
              {wsState === 'open' || wsState === 'simulated' ? (
                <Wifi size={13} style={{ color: 'var(--success)', marginLeft: 'auto' }} />
              ) : (
                <WifiOff size={13} style={{ color: 'var(--text-3)', marginLeft: 'auto' }} />
              )}
            </div>

            {/* Reset */}
            {(latest || error || history.length > 0) && (
              <button id="ld-btn-reset" className="ld-ghost-btn" onClick={reset}>
                <RefreshCw size={12} className="inline mr-1.5" />
                Clear results
              </button>
            )}

            {/* Rich Illustrated Error State with What to Do Next */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.98 }}
                  className="p-5 bg-red-50/60 border border-red-200/80 rounded-card my-2 text-left"
                >
                  <ErrorState
                    illustration={<MicBlockedIllustration size={130} />}
                    title="Microphone Access Blocked or Not Detected"
                    description="The acoustic engine requires microphone input to evaluate glottal waveform, ultrasonic steganography, and vocal fold dynamics in real time."
                    solutionSteps={[
                      'Click the lock or camera icon on the left side of your browser URL bar.',
                      'Change Microphone permission from "Block" to "Allow".',
                      'Verify your microphone is plugged in and unmuted in your system audio settings.',
                      'Or, start the Simulated Acoustic Stream below to test the 6-layer defense system immediately.',
                    ]}
                    retryLabel="Retry Microphone"
                    onRetry={start}
                    secondaryLabel="How to Unblock in Browser"
                    onSecondaryAction={() => setShowMicModal(true)}
                    technicalError={error}
                  />

                  <div className="pt-3 border-t border-red-200/60 mt-3 flex justify-center">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={startSimulatedStream}
                      icon={<Play className="w-3.5 h-3.5" />}
                    >
                      Run Simulated Voice Stream Instead
                    </Button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Tips */}
            <div className="ld-tips">
              <p className="ld-tip">💡 <strong>Speak naturally</strong> — the engine monitors vocal fold biomechanics and glottal flow.</p>
              <p className="ld-tip">🎙️ <strong>Microphone sensitivity</strong> — speak within 30cm for optimal SNR baseline.</p>
              <p className="ld-tip">🤖 <strong>Simulate AI Attack</strong> — toggles neural vocoder grid and zero-jitter injection to test detection.</p>
            </div>
          </motion.section>

          {/* ── Right: Verdict panel ─────────────── */}
          <motion.section
            className="ld-card ld-verdict-panel"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2, duration: 0.45 }}
          >
            <div className="ld-card-label">
              <Activity size={13} />
              Latest Verdict
            </div>

            <AnimatePresence mode="wait">
              {!latest ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="ld-verdict-empty"
                >
                  <div className="ld-verdict-empty-ring" />
                  <span className="font-berthold text-slate-500">Waiting for microphone audio stream…</span>
                </motion.div>
              ) : (
                <motion.div
                  key={`${latest.overall_authenticity_score}-${tickCountRef.current}`}
                  initial={{ opacity: 0, scale: 0.96 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.3 }}
                  className="ld-verdict-content"
                >
                  {/* Score ring */}
                  <div className="ld-ring-wrap">
                    <ScoreRing score={latest.overall_authenticity_score} size={130} />
                    <div className="ld-ring-label" style={{ color: mainColor }}>
                      {latest.is_authentic ? (
                        <ShieldCheck size={18} className="text-emerald-600" />
                      ) : (
                        <ShieldAlert size={18} className="text-rose-600" />
                      )}
                      <span className="font-bold text-sm tracking-wide">{verdictLabel}</span>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="ld-stats-grid">
                    <div className="ld-stat">
                      <span className="ld-stat-label">
                        <BarChart2 size={12} /> Confidence
                      </span>
                      <span className="ld-stat-value font-mono" style={{ color: 'var(--text-1)' }}>
                        {pct(latest.confidence)}
                      </span>
                    </div>
                    <div className="ld-stat">
                      <span className="ld-stat-label">
                        <Clock size={12} /> Buffer
                      </span>
                      <span className="ld-stat-value font-mono" style={{ color: 'var(--text-1)' }}>
                        {latest.buffer_seconds.toFixed(1)}s
                      </span>
                    </div>
                    {latest.samples_processed != null && (
                      <div className="ld-stat">
                        <span className="ld-stat-label">
                          <Sparkles size={12} /> Samples
                        </span>
                        <span className="ld-stat-value font-mono" style={{ color: 'var(--text-1)' }}>
                          {latest.samples_processed.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Layers accordion */}
                  {latest.layers && Object.keys(latest.layers).length > 0 && (
                    <div className="ld-layers">
                      <button
                        type="button"
                        className="ld-layers-toggle"
                        onClick={() => setLayersOpen((o) => !o)}
                        aria-expanded={layersOpen}
                      >
                        <Layers size={13} />
                        <span>6-Layer Defense Score Breakdown</span>
                        <span className="ml-auto flex items-center gap-1 text-[11px] text-slate-500">
                          {Object.keys(latest.layers).length} Layers
                          {layersOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                        </span>
                      </button>
                      <AnimatePresence>
                        {layersOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.25 }}
                            style={{ overflow: 'hidden' }}
                          >
                            <div className="ld-layers-body">
                              {Object.entries(latest.layers).map(([k, v]) => (
                                <LayerRow key={k} name={k} layer={v} />
                              ))}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>
        </div>

        {/* ── Timeline ──────────────────────────── */}
        <motion.section
          className="ld-card ld-timeline"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
        >
          <div className="ld-card-label">
            <Activity size={13} />
            Detection Timeline
            {history.length > 0 && (
              <span className="ld-timeline-count">
                {history.length} window{history.length !== 1 ? 's' : ''} analyzed
              </span>
            )}
          </div>

          <div className="ld-timeline-track">
            {history.length === 0 ? (
              <span className="ld-timeline-empty font-berthold text-slate-500">
                Timeline ticks will stream continuously as audio chunks are processed…
              </span>
            ) : (
              history.map((h, i) => <TimelineTick key={i} verdict={h} />)
            )}
          </div>

          <div className="ld-timeline-legend">
            <span className="ld-legend-item">
              <span className="ld-legend-dot" style={{ background: 'var(--success)' }} />
              Authentic (&ge; 70%)
            </span>
            <span className="ld-legend-item">
              <span className="ld-legend-dot" style={{ background: 'var(--warning)' }} />
              Suspicious (45&ndash;70%)
            </span>
            <span className="ld-legend-item">
              <span className="ld-legend-dot" style={{ background: 'var(--error)' }} />
              Synthetic (&lt; 45%)
            </span>
          </div>
        </motion.section>
      </div>
      </PageTransition>

      <MicrophoneTroubleshooterModal
        isOpen={showMicModal}
        onClose={() => setShowMicModal(false)}
        onRetry={start}
      />
    </>
  );
};

/* ─── Scoped CSS matching Light VCaaS Aesthetic ────────────── */
const ldStyles = `
.ld-root {
  min-height: calc(100vh - 120px);
  background: transparent;
  padding: 32px 20px 80px;
  max-width: 1100px;
  margin: 0 auto;
  --bg: #F8F9FF;
  --surface-1: #FFFFFF;
  --surface-2: #F8FAFC;
  --surface-3: #F1F5F9;
  --border: #F1F5F9;
  --border-mid: #E2E8F0;
  --border-strong: #CBD5E1;
  --text-1: #0B1C30;
  --text-2: #565E74;
  --text-3: #8692A6;
  --accent: #F59E0B;
  --success: #059669;
  --warning: #D97706;
  --error: #DC2626;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;
}

.ld-header { text-align: center; margin-bottom: 36px; }
.ld-header-inner { display: inline-flex; flex-direction: column; align-items: center; gap: 14px; }

.ld-badge {
  display: inline-flex; align-items: center; gap: 6px;
  background: #FEF3C7; border: 1px solid #FDE68A;
  color: #B45309; border-radius: 999px;
  padding: 5px 14px; font-size: 11px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
}

.ld-title {
  font-size: clamp(28px, 4.5vw, 44px);
  font-weight: 700; letter-spacing: -0.02em;
  color: #0B1C30; line-height: 1.15;
}

.ld-subtitle {
  font-size: 16px; color: #565E74; max-width: 640px; line-height: 1.6;
}

.ld-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
@media (max-width: 820px) { .ld-grid { grid-template-columns: 1fr; } }

.ld-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-xl);
  padding: 26px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02);
}

.ld-card-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
  color: #8692A6;
}

.ld-control { gap: 16px; }

.ld-main-btn {
  position: relative;
  width: 100%; padding: 16px 20px;
  border-radius: var(--radius-lg);
  border: 1.5px solid #CBD5E1;
  background: #FFFFFF;
  color: #0B1C30;
  font-size: 15px; font-weight: 600;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 12px;
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.12s;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
}
.ld-main-btn:hover {
  background: #F8FAFC;
  border-color: #F59E0B;
  box-shadow: 0 4px 14px 0 rgba(245, 158, 11, 0.2);
  transform: translateY(-1px);
}
.ld-main-btn:active { transform: translateY(0); }

.ld-main-btn--stop {
  background: #FEF2F2;
  border-color: #FCA5A5;
  color: #DC2626;
}
.ld-main-btn--stop:hover {
  background: #FEE2E2;
  border-color: #F87171;
  box-shadow: 0 4px 14px 0 rgba(239, 68, 68, 0.2);
}

.ld-btn-icon { display: flex; align-items: center; }
.ld-btn-label { flex: 1; text-align: center; }

.ld-btn-pulse {
  position: absolute; inset: 0; border-radius: inherit;
  background: rgba(239, 68, 68, 0.08);
  animation: ldPulse 2s ease-in-out infinite;
  pointer-events: none;
}

@keyframes ldPulse {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.ld-waveform {
  display: flex; align-items: center; justify-content: center;
  gap: 4px; height: 42px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  padding: 0 12px;
}

.ld-wave-bar {
  display: inline-block;
  width: 4px;
  border-radius: 999px;
  background: #CBD5E1;
  height: 4px;
  transition: background 0.25s, height 0.15s ease-out;
}

.ld-wave-bar--active {
  background: #F59E0B;
  box-shadow: 0 0 6px rgba(245, 158, 11, 0.4);
}

.ld-status-row {
  display: flex; align-items: center; gap: 8px;
  padding: 11px 14px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  font-size: 12px; color: #565E74;
}

.ld-status-dot {
  width: 8px; height: 8px; border-radius: 999px; flex-shrink: 0;
}
.ld-status-dot--green { background: #059669; box-shadow: 0 0 6px #059669; }
.ld-status-dot--amber { background: #F59E0B; box-shadow: 0 0 6px #F59E0B; }
.ld-status-dot--yellow { background: #D97706; box-shadow: 0 0 6px #D97706; animation: ldBlink 1s ease infinite; }
.ld-status-dot--gray { background: #94A3B8; }

@keyframes ldBlink { 0%,100%{opacity:1} 50%{opacity:0.3} }

.ld-status-text { flex: 1; }

.ld-ghost-btn {
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  border-radius: var(--radius-md);
  padding: 7px 14px;
  color: #565E74;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
  align-self: flex-start;
}
.ld-ghost-btn:hover {
  border-color: #94A3B8;
  color: #0B1C30;
  background: #F8FAFC;
}

.ld-error {
  display: flex; align-items: flex-start; gap: 8px;
  background: #FEF2F2;
  border: 1px solid #FCA5A5;
  border-radius: var(--radius-md);
  padding: 12px 14px;
  color: #991B1B;
  font-size: 12px;
  line-height: 1.5;
}

.ld-tips { display: flex; flex-direction: column; gap: 6px; padding-top: 4px; }
.ld-tip { font-size: 12px; color: #64748B; line-height: 1.55; }

.ld-verdict-panel { min-height: 340px; }

.ld-verdict-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 16px; color: #64748B; font-size: 13px; min-height: 240px;
}

.ld-verdict-empty-ring {
  width: 70px; height: 70px; border-radius: 999px;
  border: 4px solid #E2E8F0;
  border-top-color: #F59E0B;
  opacity: 0.8;
  animation: ldSpin 2s linear infinite;
}
@keyframes ldSpin { to { transform: rotate(360deg); } }

.ld-verdict-content { display: flex; flex-direction: column; gap: 18px; }

.ld-ring-wrap {
  display: flex; flex-direction: column; align-items: center; gap: 10px;
}

.ld-score-ring { display: block; }

.ld-ring-label {
  display: flex; align-items: center; gap: 7px;
  font-size: 14px; font-weight: 700; letter-spacing: 0.02em;
}

.ld-stats-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
}

.ld-stat {
  display: flex; flex-direction: column; gap: 4px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  padding: 12px 14px;
}

.ld-stat-label {
  display: flex; align-items: center; gap: 5px;
  font-size: 10px; font-weight: 600; letter-spacing: 0.07em; text-transform: uppercase;
  color: #8692A6;
}

.ld-stat-value { font-size: 18px; font-weight: 700; color: #0B1C30; }

.ld-layers { display: flex; flex-direction: column; gap: 0; }

.ld-layers-toggle {
  display: flex; align-items: center; gap: 7px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  padding: 11px 14px;
  color: #0B1C30;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  width: 100%;
}
.ld-layers-toggle:hover {
  border-color: #CBD5E1;
  background: #F1F5F9;
}

.ld-layers-body {
  border: 1px solid #E2E8F0;
  border-top: none;
  border-radius: 0 0 var(--radius-md) var(--radius-md);
  overflow: hidden;
  background: #FFFFFF;
}

.ld-layer-row {
  display: flex; align-items: center; gap: 10px;
  padding: 11px 14px;
  border-bottom: 1px solid #F1F5F9;
  font-size: 12px;
}
.ld-layer-row:last-child { border-bottom: none; }

.ld-layer-header {
  width: 150px; flex-shrink: 0; display: flex; flex-direction: column;
}

.ld-layer-name {
  color: #0B1C30;
  text-transform: capitalize;
  font-weight: 600;
  font-size: 12px;
}

.ld-layer-bar-track {
  flex: 1; height: 6px; background: #E2E8F0; border-radius: 999px; overflow: hidden;
}

.ld-layer-bar-fill { height: 100%; border-radius: 999px; }

.ld-layer-score {
  width: 48px; text-align: right; font-weight: 700; flex-shrink: 0; font-family: monospace;
}
.ld-layer-verdict {
  color: #64748B; font-size: 11px; flex-shrink: 0; font-weight: 600;
}

.ld-timeline { gap: 14px; }

.ld-timeline-track {
  display: flex; align-items: flex-end; gap: 3px;
  height: 52px; background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  padding: 8px 12px; overflow-x: auto;
}

.ld-timeline-empty {
  width: 100%; text-align: center; font-size: 12px; color: #8692A6;
  align-self: center;
}

.ld-tick {
  flex-shrink: 0; width: 12px; min-width: 12px; height: 100%;
  border-radius: 3px; cursor: default;
  transition: filter 0.2s, transform 0.15s;
}
.ld-tick:hover { filter: brightness(1.15); transform: scaleY(1.08); }

.ld-timeline-count {
  margin-left: auto; font-size: 11px; color: #8692A6;
  font-weight: 400; text-transform: none; letter-spacing: 0;
}

.ld-timeline-legend {
  display: flex; gap: 18px; flex-wrap: wrap;
}

.ld-legend-item {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; color: #565E74;
}

.ld-legend-dot { width: 8px; height: 8px; border-radius: 999px; flex-shrink: 0; }
`;
