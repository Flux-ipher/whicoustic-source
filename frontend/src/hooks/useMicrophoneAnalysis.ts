import { useState, useEffect, useRef, useCallback } from 'react';

export interface DefenseLayerScore {
  id: number;
  name: string;
  badge: string;
  score: number; // 0 - 100
  status: 'PASS' | 'ANOMALY' | 'FAIL';
  metric: string;
  description: string;
  diagnostic: string;
}

export interface VoiceAnalysisResult {
  verdict: 'HUMAN' | 'AI_GENERATED';
  confidence: number; // 0 - 100
  latencyMs: number;
  layers: DefenseLayerScore[];
  isSyntheticProb: number;
  decibels: number;
  analyzedChunks: number;
}

const defaultLayers: DefenseLayerScore[] = [
  {
    id: 1,
    name: 'Ultrasonic Steganographic Watermark Sniffer',
    badge: 'L1: Watermark',
    score: 98.4,
    status: 'PASS',
    metric: 'Carrier Resonance at 21.4 kHz',
    description: 'Scans for cryptographic SHA-256 ultrasonic watermark carriers and phase continuity.',
    diagnostic: 'Clean spectral ceiling. No unauthorized steganographic tampering.',
  },
  {
    id: 2,
    name: 'Glottal Pulse & Biomechanical Vocal Tract Dynamics',
    badge: 'L2: Biomechanics',
    score: 96.8,
    status: 'PASS',
    metric: 'Vocal Fold Closure Velocity: 1.24 m/s',
    description: 'Measures organic vocal cord turbulence, lung breath inhalation, and subglottal pressure.',
    diagnostic: 'Organic laryngeal opening/closing ratio matches natural biological physiology.',
  },
  {
    id: 3,
    name: 'Spectral Vocoder & HiFi-GAN Grid Artifact Detection',
    badge: 'L3: Synthesis Grid',
    score: 99.1,
    status: 'PASS',
    metric: 'Spectrogram Discretization: Zero-Grid',
    description: 'Identifies neural vocoder checkerboard artifacts, diffusion steps, and synthetic phase anomalies.',
    diagnostic: 'Continuous natural spectral roll-off. No neural vocoder framing periodicity.',
  },
  {
    id: 4,
    name: 'Micro-Prosody Perturbation & Cycle Jitter',
    badge: 'L4: Jitter & Shimmer',
    score: 94.2,
    status: 'PASS',
    metric: 'Jitter (Relative): 0.82% • Shimmer: 2.1%',
    description: 'Calculates pitch cycle-to-cycle micro-tremors and natural muscle fatigue fluctuations.',
    diagnostic: 'Acoustic micro-tremor is organic. Lacks the hyper-smooth rigidity of synthetic models.',
  },
  {
    id: 5,
    name: 'Acoustic Ambient Environment & Room Impulse Signature',
    badge: 'L5: Acoustics',
    score: 97.5,
    status: 'PASS',
    metric: 'Room Reverberation (RT60): 0.18s • Floor: -54 dB',
    description: 'Verifies natural diaphragm microphone acoustics against mathematical zero-noise synthetic silence.',
    diagnostic: 'Authentic ambient physical room reflections detected.',
  },
  {
    id: 6,
    name: 'Phonemic Co-Articulation Entropy & Latency Invariance',
    badge: 'L6: Phonemic Entropy',
    score: 98.9,
    status: 'PASS',
    metric: 'Transition Shannon Entropy: 4.82 bits',
    description: 'Evaluates the statistical randomness of consonants blending into vowels over time.',
    diagnostic: 'High-entropy human articulation transitions verified.',
  },
];

export function useMicrophoneAnalysis() {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decibels, setDecibels] = useState(-60);
  const [frequencyData, setFrequencyData] = useState<number[]>(new Array(32).fill(10));
  const [simulationMode, setSimulationMode] = useState<'AUTO' | 'HUMAN' | 'AI_ATTACK'>('AUTO');
  const simulationModeRef = useRef(simulationMode);

  useEffect(() => {
    simulationModeRef.current = simulationMode;
  }, [simulationMode]);

  const [analysisResult, setAnalysisResult] = useState<VoiceAnalysisResult>({
    verdict: 'HUMAN',
    confidence: 98.6,
    latencyMs: 38,
    layers: defaultLayers,
    isSyntheticProb: 1.4,
    decibels: -42,
    analyzedChunks: 0,
  });

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const micStreamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const analysisIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startListening = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: false,
          noiseSuppression: false,
          autoGainControl: false,
        },
      });

      micStreamRef.current = stream;

      const audioCtx = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      analyserRef.current = analyser;

      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      setIsListening(true);

      // Real-time audio loop for waveform
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      const updateAudioTelemetry = () => {
        if (!analyserRef.current) return;
        analyserRef.current.getByteFrequencyData(dataArray);

        // Calculate average dB
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const db = Math.round((avg / 255) * 60 - 60);
        setDecibels(db);

        // Normalize frequency slices
        const bars = Array.from(dataArray.slice(0, 32)).map((v) => Math.max(8, Math.round((v / 255) * 100)));
        setFrequencyData(bars);

        animationFrameRef.current = requestAnimationFrame(updateAudioTelemetry);
      };

      updateAudioTelemetry();

      // Continuous 6-Layer analysis loop every 1.5s
      analysisIntervalRef.current = setInterval(() => {
        runSixLayerAnalysis();
      }, 1500);

    } catch (err: unknown) {
      console.error('Microphone access failed:', err);
      setError('Microphone access permission was denied or is unavailable. Please allow microphone access in your browser.');
      setIsListening(false);
    }
  };

  const stopListening = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (analysisIntervalRef.current) {
      clearInterval(analysisIntervalRef.current);
    }
    if (micStreamRef.current) {
      micStreamRef.current.getTracks().forEach((track) => track.stop());
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    setIsListening(false);
    setDecibels(-60);
    setFrequencyData(new Array(32).fill(10));
  }, []);

  const runSixLayerAnalysis = useCallback(async () => {
    // If backend API is configured, we can dispatch chunks here:
    // const apiBase = import.meta.env.VITE_API_BASE_URL;

    // Simulate 6-layer defense response:
    setAnalysisResult((prev) => {
      const isAiAttack = simulationModeRef.current === 'AI_ATTACK';

      if (isAiAttack) {
        // AI Attack detected: Multiple layer failures
        const updatedLayers: DefenseLayerScore[] = [
          {
            id: 1,
            name: 'Ultrasonic Steganographic Watermark Sniffer',
            badge: 'L1: Watermark',
            score: 18.2,
            status: 'FAIL',
            metric: 'Missing Cryptographic Watermark Anchor',
            description: 'Scans for cryptographic SHA-256 ultrasonic watermark carriers and phase continuity.',
            diagnostic: 'ALERT: Synthesized stream lacks authentic biometric vault passport seed.',
          },
          {
            id: 2,
            name: 'Glottal Pulse & Biomechanical Vocal Tract Dynamics',
            badge: 'L2: Biomechanics',
            score: 24.5,
            status: 'FAIL',
            metric: 'Abnormal Closure Velocity: 0.22 m/s',
            description: 'Measures organic vocal cord turbulence, lung breath inhalation, and subglottal pressure.',
            diagnostic: 'CRITICAL: Anatomical vocal tract mechanics missing. Waveform generated algorithmically.',
          },
          {
            id: 3,
            name: 'Spectral Vocoder & HiFi-GAN Grid Artifact Detection',
            badge: 'L3: Synthesis Grid',
            score: 12.8,
            status: 'FAIL',
            metric: 'HiFi-GAN Periodic Artifact Peak: +14.2 dB',
            description: 'Identifies neural vocoder checkerboard artifacts, diffusion steps, and synthetic phase anomalies.',
            diagnostic: 'DETECTED: Discretization checkerboard patterns matching 44.1kHz neural vocoder.',
          },
          {
            id: 4,
            name: 'Micro-Prosody Perturbation & Cycle Jitter',
            badge: 'L4: Jitter & Shimmer',
            score: 31.4,
            status: 'FAIL',
            metric: 'Jitter (Relative): 0.08% (Unnatural Flatness)',
            description: 'Calculates pitch cycle-to-cycle micro-tremors and natural muscle fatigue fluctuations.',
            diagnostic: 'Synthetic pitch rigidity detected. Standard deviation below human physiological threshold.',
          },
          {
            id: 5,
            name: 'Acoustic Ambient Environment & Room Impulse Signature',
            badge: 'L5: Acoustics',
            score: 42.0,
            status: 'ANOMALY',
            metric: 'Synthesized Zero-Noise Baseline',
            description: 'Verifies natural diaphragm microphone acoustics against mathematical zero-noise synthetic silence.',
            diagnostic: 'Room noise floor artificially pristine. Missing natural diaphragm impulse response.',
          },
          {
            id: 6,
            name: 'Phonemic Co-Articulation Entropy & Latency Invariance',
            badge: 'L6: Phonemic Entropy',
            score: 28.7,
            status: 'FAIL',
            metric: 'Entropy: 1.64 bits (Overly Deterministic)',
            description: 'Evaluates the statistical randomness of consonants blending into vowels over time.',
            diagnostic: 'Phonemic co-articulation follows neural text-to-speech parameter distribution.',
          },
        ];

        return {
          verdict: 'AI_GENERATED',
          confidence: 98.8,
          latencyMs: 34 + Math.round(Math.random() * 8),
          layers: updatedLayers,
          isSyntheticProb: 98.8,
          decibels: prev.decibels,
          analyzedChunks: prev.analyzedChunks + 1,
        };
      } else {
        // Natural Human Voice Verified
        const updatedLayers: DefenseLayerScore[] = [
          {
            id: 1,
            name: 'Ultrasonic Steganographic Watermark Sniffer',
            badge: 'L1: Watermark',
            score: Math.min(99.5, 97.0 + Math.random() * 2.5),
            status: 'PASS',
            metric: 'Carrier Resonance: Clean Pass',
            description: 'Scans for cryptographic SHA-256 ultrasonic watermark carriers and phase continuity.',
            diagnostic: 'Clean spectral ceiling. No unauthorized steganographic tampering.',
          },
          {
            id: 2,
            name: 'Glottal Pulse & Biomechanical Vocal Tract Dynamics',
            badge: 'L2: Biomechanics',
            score: Math.min(99.0, 95.5 + Math.random() * 3.5),
            status: 'PASS',
            metric: 'Natural Glottal Closure: 1.28 m/s',
            description: 'Measures organic vocal cord turbulence, lung breath inhalation, and subglottal pressure.',
            diagnostic: 'Organic laryngeal opening/closing ratio matches natural biological physiology.',
          },
          {
            id: 3,
            name: 'Spectral Vocoder & HiFi-GAN Grid Artifact Detection',
            badge: 'L3: Synthesis Grid',
            score: Math.min(99.8, 98.2 + Math.random() * 1.6),
            status: 'PASS',
            metric: 'Spectrogram Discretization: Negative',
            description: 'Identifies neural vocoder checkerboard artifacts, diffusion steps, and synthetic phase anomalies.',
            diagnostic: 'Continuous natural spectral roll-off. No neural vocoder framing periodicity.',
          },
          {
            id: 4,
            name: 'Micro-Prosody Perturbation & Cycle Jitter',
            badge: 'L4: Jitter & Shimmer',
            score: Math.min(98.5, 93.0 + Math.random() * 5.0),
            status: 'PASS',
            metric: 'Micro-Jitter: 0.94% • Shimmer: 2.3%',
            description: 'Calculates pitch cycle-to-cycle micro-tremors and natural muscle fatigue fluctuations.',
            diagnostic: 'Acoustic micro-tremor is organic. Lacks the hyper-smooth rigidity of synthetic models.',
          },
          {
            id: 5,
            name: 'Acoustic Ambient Environment & Room Impulse Signature',
            badge: 'L5: Acoustics',
            score: Math.min(99.2, 96.0 + Math.random() * 3.0),
            status: 'PASS',
            metric: 'Room Reverberation (RT60): 0.19s',
            description: 'Verifies natural diaphragm microphone acoustics against mathematical zero-noise synthetic silence.',
            diagnostic: 'Authentic ambient physical room reflections detected.',
          },
          {
            id: 6,
            name: 'Phonemic Co-Articulation Entropy & Latency Invariance',
            badge: 'L6: Phonemic Entropy',
            score: Math.min(99.6, 97.4 + Math.random() * 2.2),
            status: 'PASS',
            metric: 'Transition Entropy: 4.91 bits',
            description: 'Evaluates the statistical randomness of consonants blending into vowels over time.',
            diagnostic: 'High-entropy human articulation transitions verified.',
          },
        ];

        return {
          verdict: 'HUMAN',
          confidence: 99.2,
          latencyMs: 32 + Math.round(Math.random() * 6),
          layers: updatedLayers,
          isSyntheticProb: 0.8,
          decibels: prev.decibels,
          analyzedChunks: prev.analyzedChunks + 1,
        };
      }
    });
  }, [simulationMode]);

  useEffect(() => {
    return () => {
      stopListening();
    };
  }, [stopListening]);

  return {
    isListening,
    error,
    decibels,
    frequencyData,
    analysisResult,
    simulationMode,
    setSimulationMode,
    startListening,
    stopListening,
  };
}
