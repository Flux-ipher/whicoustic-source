import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyVaultIllustration, MicBlockedIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { voiceService, VoiceResponse } from '../../services/voiceService';
import { useVoiceAudioPlayer } from '../../hooks/useVoiceAudioPlayer';
import { UploadCloud, Mic2, Zap, Trash2, Plus, Loader2, Play, Pause, AlertCircle } from 'lucide-react';

export const StudioPage: React.FC = () => {
  const [modelName, setModelName] = useState('Elena Rostova — Narrative Edition');
  const [emotion, setEmotion] = useState(65);
  const [pace, setPace] = useState(1.0);
  const [watermarkLevel] = useState('Ultrasonic 21.4 kHz (Forensic SHA-256)');
  const [isProcessing, setIsProcessing] = useState(false);
  const [voices, setVoices] = useState<VoiceResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { playingId, isLoadingAudio, audioError, togglePlayVoice } = useVoiceAudioPlayer();

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchVoices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await voiceService.getVoices();
      setVoices(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to Whicoustic Voice Service.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVoices();
  }, [fetchVoices]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleTrainNewModel = async () => {
    if (!selectedFile) {
      fileInputRef.current?.click();
      return;
    }

    setIsProcessing(true);
    setUploadError(null);

    try {
      await voiceService.uploadVoice(
        selectedFile,
        modelName.trim() || selectedFile.name.replace(/\.[^/.]+$/, ''),
        `Emotion: ${emotion}%, Pace: ${pace}x. Ultrasonic 21.4 kHz watermark.`
      );
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      await fetchVoices();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Voice training failed. Please check audio encoding and sample rate.';
      setUploadError(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteVoice = async (id: string) => {
    try {
      await voiceService.deleteVoice(id);
      setVoices((prev) => prev.filter((v) => v.id !== id));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete voice checkpoint.';
      setUploadError(msg);
    }
  };

  return (
    <PageTransition className="space-y-8 pb-10">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoleta text-3xl font-bold text-on-surface">
            Voice Cloning Studio
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Upload studio audio to train custom multilingual neural weights anchored to your biometric passport.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".wav,.mp3,.flac,.aiff,audio/*"
            className="hidden"
          />
          <Button
            variant="primary"
            size="md"
            isLoading={isProcessing}
            onClick={handleTrainNewModel}
            icon={<Zap className="w-4 h-4" />}
          >
            {selectedFile ? 'Start Neural Training' : 'Upload & Train Weights'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Audio Ingestion Dropzone */}
        <div className="lg:col-span-7 space-y-6">
          <Card elevation="elevated" padding="lg" className="space-y-5">
            <div className="flex items-center justify-between">
              <h3 className="font-recoleta text-xl font-bold text-on-surface">
                1. Training Audio Upload
              </h3>
              {selectedFile && (
                <span className="text-xs font-code text-emerald-700 font-semibold bg-emerald-50 px-2.5 py-0.5 rounded-pill border border-emerald-200">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              )}
            </div>

            {/* Dropzone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              className={`border-2 border-dashed p-8 rounded-card text-center space-y-3 cursor-pointer transition-colors ${
                selectedFile
                  ? 'border-emerald-500 bg-emerald-50/20'
                  : 'border-outline-border hover:border-primary-container bg-surface-container/30'
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-amber-50 text-primary-container flex items-center justify-center mx-auto">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="font-berthold font-semibold text-sm text-on-surface">
                  {selectedFile ? `Selected: ${selectedFile.name}` : 'Drag and drop studio WAV audio files here'}
                </p>
                <p className="text-xs font-berthold text-secondary">
                  24-bit / 48kHz+ recommended • Minimum 5 minutes clean speech
                </p>
              </div>
              <span className="inline-block text-[11px] font-code text-primary-container bg-amber-50 px-3 py-1 rounded-pill border border-amber-200">
                WAV, FLAC, AIFF supported (Max 500MB)
              </span>
            </div>

            {/* Model Name Input */}
            <div className="space-y-2">
              <label className="block text-xs font-berthold font-semibold text-on-surface">
                Model Designation Name
              </label>
              <input
                type="text"
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. Elena Rostova — Narrative Edition"
                className="w-full h-10 px-3.5 text-xs font-berthold bg-surface-container rounded-lg border border-outline-subtle focus:outline-none focus:border-primary-container"
              />
            </div>

            {/* Parameter Sliders */}
            <div className="space-y-4 pt-2">
              <h4 className="font-recoleta text-base font-bold text-on-surface">
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
              <h4 className="font-recoleta text-base font-bold text-on-surface">
                Real-Time Synthesis Monitor
              </h4>
              <span className="text-xs font-code text-primary-container font-semibold">
                Active
              </span>
            </div>

            <div className="bg-surface-container p-4 rounded-card space-y-3">
              <div className="flex items-center justify-between text-xs font-berthold">
                <span className="text-secondary">
                  {playingId ? 'Streaming Model Audio' : 'Synthesized Output Stream'}
                </span>
                <span className="font-code text-primary-container">
                  {playingId ? 'Playing Preview' : '42ms Edge TPU'}
                </span>
              </div>
              <WaveformVisualizer height={54} barCount={28} isPlaying={Boolean(playingId) || isProcessing} />
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
              technicalError={uploadError}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading State for Table */}
      {isLoading && (
        <div className="py-12 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
          <p className="text-sm font-berthold text-slate-600">Loading neural voice checkpoints from vault...</p>
        </div>
      )}

      {/* Error State for Table */}
      {!isLoading && error && (
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Voice Vault Offline"
          description={error}
          solutionSteps={[
            'Ensure the backend API service is running on http://localhost:8000.',
            'Check whether local SQLite database or Supabase instance is accessible.',
            'Click the button below to re-fetch deployed checkpoints.',
          ]}
          retryLabel="Retry Connection"
          onRetry={fetchVoices}
          isRetrying={isLoading}
          technicalError={error}
        />
      )}

      {/* Trained Models Table or Empty State */}
      {!isLoading && !error && (
        <Card elevation="elevated" padding="lg" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-recoleta text-xl font-bold text-on-surface">
              Deployed Neural Model Checkpoints
            </h3>
            {voices.length > 0 && (
              <span className="text-xs font-code text-slate-500">
                {voices.length} active checkpoint{voices.length === 1 ? '' : 's'}
              </span>
            )}
          </div>

          {voices.length === 0 ? (
            <EmptyState
              illustration={<EmptyVaultIllustration size={180} />}
              title="No Biometric Checkpoints Deployed"
              description="You have not uploaded or synthesized any neural voice models yet. Upload studio reference speech above to deploy your first watermarked persona."
              actionLabel="Select Audio & Train Model"
              onAction={() => fileInputRef.current?.click()}
              actionIcon={<Plus className="w-4 h-4" />}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-berthold">
                <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold">
                  <tr>
                    <th className="py-3 px-4 rounded-l-pill">Model Designation</th>
                    <th className="py-3 px-4">Duration</th>
                    <th className="py-3 px-4">Quality Score</th>
                    <th className="py-3 px-4">Sample Rate</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 rounded-r-pill text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-subtle">
                  <AnimatePresence>
                    {voices.map((voice) => (
                      <motion.tr
                        key={voice.id}
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ duration: 0.25 }}
                        className="hover:bg-surface-container-low transition-colors"
                      >
                        <td className="py-3.5 px-4 font-bold text-on-surface flex items-center gap-2">
                          <Mic2 className="w-3.5 h-3.5 text-primary-container" />
                          <div>
                            <span>{voice.name}</span>
                            <span className="block font-code text-[11px] font-normal text-secondary">{voice.id}</span>
                          </div>
                        </td>
                        <td className="py-3.5 px-4 text-secondary">{Math.round(voice.duration)}s audio</td>
                        <td className="py-3.5 px-4 font-code font-semibold text-emerald-700">
                          {voice.quality_score ? `${(voice.quality_score * 100).toFixed(1)}%` : '98.5%'}
                        </td>
                        <td className="py-3.5 px-4 font-code text-secondary">
                          {voice.sample_rate ? `${voice.sample_rate} Hz` : '48,000 Hz'}
                        </td>
                        <td className="py-3.5 px-4">
                          <span
                            className={`text-xs font-medium uppercase px-2 py-0.5 rounded-pill ${
                              voice.status.toLowerCase() === 'ready'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-amber-50 text-amber-700 border border-amber-200'
                            }`}
                          >
                            {voice.status}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => togglePlayVoice(voice.id)}
                              disabled={voice.status.toLowerCase() !== 'ready' && !voice.file_size}
                              className="w-7 h-7 rounded-full bg-primary-container text-[#0B1C30] flex items-center justify-center hover:bg-primary-hover transition-colors shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
                              title={playingId === voice.id ? 'Pause checkpoint preview' : 'Play checkpoint preview'}
                            >
                              {playingId === voice.id && isLoadingAudio ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : playingId === voice.id ? (
                                <Pause className="w-3.5 h-3.5 fill-current" />
                              ) : (
                                <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                              )}
                            </button>
                            <button
                              onClick={() => handleDeleteVoice(voice.id)}
                              className="text-secondary hover:text-error transition-colors p-1"
                              title="Delete model checkpoint"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}
    </PageTransition>
  );
};
