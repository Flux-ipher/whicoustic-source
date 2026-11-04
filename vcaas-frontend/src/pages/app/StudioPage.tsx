import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyVaultIllustration, MicBlockedIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { mockCloneJobs, CloneJob } from '../../data/mock/studio';
import { UploadCloud, Mic2, Play, Sliders, CheckCircle2, Zap, Trash2, AlertTriangle, Plus, RotateCcw } from 'lucide-react';

export const StudioPage: React.FC = () => {
  const [modelName, setModelName] = useState('Elena Rostova — Narrative Edition');
  const [emotion, setEmotion] = useState(65);
  const [pace, setPace] = useState(1.0);
  const [watermarkLevel, setWatermarkLevel] = useState('Ultrasonic L3 (Forensic)');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobs, setJobs] = useState<CloneJob[]>(mockCloneJobs);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleTrainNewModel = () => {
    setIsProcessing(true);
    setUploadError(null);
    setTimeout(() => {
      setIsProcessing(false);
      const newJob: CloneJob = {
        id: `clone_${Date.now()}`,
        name: modelName || 'Untitled Biometric Model',
        sourceAudioDurationSec: 300,
        qualityScore: 99.1,
        status: 'READY',
        createdDate: '2026-11-04',
        watermarkSha256: '4080c0aea1ea4cc3a63a13901af1baaa',
        latencyMs: 36,
      };
      setJobs([newJob, ...jobs]);
    }, 1500);
  };

  const handleDeleteJob = (id: string) => {
    setJobs(jobs.filter((j) => j.id !== id));
  };

  return (
    <PageTransition className="space-y-8 pb-10">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoletta text-3xl font-bold text-on-surface">
            Voice Cloning Studio
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Upload studio audio to train custom multilingual neural weights anchored to your biometric passport.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          isLoading={isProcessing}
          onClick={handleTrainNewModel}
          icon={<Zap className="w-4 h-4" />}
        >
          Train New Neural Weights
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Audio Ingestion Dropzone */}
        <div className="lg:col-span-7 space-y-6">
          <Card elevation="elevated" padding="lg" className="space-y-5">
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              1. Training Audio Upload
            </h3>

            {/* Dropzone */}
            <div className="border-2 border-dashed border-outline-border hover:border-primary-container p-8 rounded-card text-center space-y-3 cursor-pointer bg-surface-container/30 transition-colors">
              <div className="w-12 h-12 rounded-full bg-amber-50 text-primary-container flex items-center justify-center mx-auto">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="font-berthold font-semibold text-sm text-on-surface">
                  Drag and drop studio WAV audio files here
                </p>
                <p className="text-xs font-berthold text-secondary">
                  24-bit / 48kHz+ recommended • Minimum 5 minutes clean speech
                </p>
              </div>
              <span className="inline-block text-[11px] font-code text-primary-container bg-amber-50 px-3 py-1 rounded-pill border border-amber-200">
                WAV, FLAC, AIFF supported (Max 500MB)
              </span>
            </div>

            {/* Parameter Sliders */}
            <div className="space-y-4 pt-2">
              <h4 className="font-recoletta text-base font-bold text-on-surface">
                2. Synthesis Parameters & Conditioning
              </h4>

              <div className="space-y-2">
                <div className="flex justify-between text-xs font-berthold font-semibold">
                  <span>Emotional Inflection Matrix</span>
                  <span className="font-code text-primary-container">{emotion}% Saturated</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={emotion}
                  onChange={(e) => setEmotion(parseInt(e.target.value))}
                  className="w-full h-2 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary-container"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs font-berthold font-semibold">
                  <span>Pacing & Breath Cadence</span>
                  <span className="font-code text-primary-container">{pace}x Natural</span>
                </div>
                <input
                  type="range"
                  min="0.75"
                  max="1.5"
                  step="0.05"
                  value={pace}
                  onChange={(e) => setPace(parseFloat(e.target.value))}
                  className="w-full h-2 bg-surface-container rounded-lg appearance-none cursor-pointer accent-primary-container"
                />
              </div>
            </div>
          </Card>
        </div>

        {/* Right: Live Waveform Preview */}
        <div className="lg:col-span-5 space-y-6">
          <Card elevation="amber-border" padding="lg" className="space-y-5">
            <div className="flex items-center justify-between pb-2 border-b border-outline-subtle">
              <h4 className="font-recoletta text-base font-bold text-on-surface">
                Real-Time Synthesis Monitor
              </h4>
              <span className="text-xs font-code text-primary-container font-semibold">
                Active
              </span>
            </div>

            <div className="bg-surface-container p-4 rounded-card space-y-3">
              <div className="flex items-center justify-between text-xs font-berthold">
                <span className="text-secondary">Synthesized Output Stream</span>
                <span className="font-code text-primary-container">42ms Edge TPU</span>
              </div>
              <WaveformVisualizer height={54} barCount={28} isPlaying={true} />
            </div>

            <div className="space-y-2 text-xs font-berthold">
              <div className="flex justify-between py-1 border-b border-outline-subtle">
                <span className="text-secondary">Model Precision</span>
                <span className="font-code font-bold text-emerald-700">99.4% F1 Score</span>
              </div>
              <div className="flex justify-between py-1 border-b border-outline-subtle">
                <span className="text-secondary">Watermark Mode</span>
                <span className="font-code text-on-surface font-semibold">{watermarkLevel}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-outline-subtle">
                <span className="text-secondary">Cross-Lingual Ready</span>
                <span className="text-on-surface font-semibold">14 Global Locales</span>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Optional Upload Error Box with Solution Steps */}
      <AnimatePresence>
        {uploadError && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="p-6 bg-red-50/70 border border-red-200 rounded-card"
          >
            <ErrorState
              illustration={<MicBlockedIllustration size={130} />}
              title="Acoustic Quality Baseline Failure"
              description={uploadError}
              solutionSteps={[
                'Ensure audio was recorded with an external cardioid microphone (avoid built-in laptop mics).',
                'Verify sampling rate is at least 44.1 kHz, 16-bit or 24-bit lossless PCM WAV.',
                'Ensure background noise level is under -45 dBFS without acoustic reverberation.',
              ]}
              retryLabel="Dismiss & Re-select Audio"
              onRetry={() => setUploadError(null)}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Trained Models Table or Empty State */}
      <Card elevation="elevated" padding="lg" className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-recoletta text-xl font-bold text-on-surface">
            Deployed Neural Model Checkpoints
          </h3>
          {jobs.length > 0 && (
            <span className="text-xs font-code text-slate-500">
              {jobs.length} active checkpoint{jobs.length === 1 ? '' : 's'}
            </span>
          )}
        </div>

        {jobs.length === 0 ? (
          <EmptyState
            illustration={<EmptyVaultIllustration size={180} />}
            title="No Biometric Checkpoints Deployed"
            description="You have not synthesized any neural voice models yet. Upload 5 minutes of reference studio speech to train your first watermarked persona."
            actionLabel="Train Initial Voice Model"
            onAction={handleTrainNewModel}
            actionIcon={<Plus className="w-4 h-4" />}
            secondaryLabel="Reset Mock Checkpoints"
            onSecondaryAction={() => setJobs(mockCloneJobs)}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-berthold">
              <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4 rounded-l-pill">Model Designation</th>
                  <th className="py-3 px-4">Training Audio</th>
                  <th className="py-3 px-4">Quality Score</th>
                  <th className="py-3 px-4">Watermark SHA-256</th>
                  <th className="py-3 px-4">Inference Latency</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 rounded-r-pill text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-subtle">
                <AnimatePresence>
                  {jobs.map((job) => (
                    <motion.tr
                      key={job.id}
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.25 }}
                      className="hover:bg-surface-container-low transition-colors"
                    >
                      <td className="py-3.5 px-4 font-bold text-on-surface flex items-center gap-2">
                        <Mic2 className="w-3.5 h-3.5 text-primary-container" />
                        <span>{job.name}</span>
                      </td>
                      <td className="py-3.5 px-4 text-secondary">{job.sourceAudioDurationSec} secs WAV</td>
                      <td className="py-3.5 px-4 font-code font-semibold text-emerald-700">
                        {job.qualityScore}%
                      </td>
                      <td className="py-3.5 px-4 font-code text-secondary">
                        {job.watermarkSha256.substring(0, 12)}...
                      </td>
                      <td className="py-3.5 px-4 font-code text-secondary">{job.latencyMs} ms</td>
                      <td className="py-3.5 px-4">
                        <span className={`text-xs font-medium ${job.status === 'READY' ? 'text-emerald-700' : 'text-amber-700'}`}>
                          {job.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          className="text-secondary hover:text-error transition-colors p-1"
                          title="Delete model checkpoint"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </PageTransition>
  );
};

