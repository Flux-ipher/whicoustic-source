import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { PageTransition } from '../../components/ui/PageTransition';
import { TalentVoiceIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { useAuth } from '../../context/AuthContext';
import { voiceService, VoiceResponse } from '../../services/voiceService';
import { ShieldCheck, Play, Pause, Edit3, Plus, Loader2 } from 'lucide-react';

export const TalentPage: React.FC = () => {
  const { user } = useAuth();
  const [voices, setVoices] = useState<VoiceResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchVoices = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await voiceService.getVoices();
      setVoices(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to Voice Service.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVoices();
  }, [fetchVoices]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setIsUploading(true);
      try {
        await voiceService.uploadVoice(
          file,
          file.name.replace(/\.[^/.]+$/, ''),
          'Studio showcase demo reel with 21.4 kHz ultrasonic watermark'
        );
        await fetchVoices();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to upload reel';
        setError(msg);
      } finally {
        setIsUploading(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
      }
    }
  };

  return (
    <PageTransition className="space-y-8 pb-10">
      {/* Profile Overview Card */}
      <Card elevation="elevated" padding="lg">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="flex items-center gap-5">
            <img
              src={user?.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80'}
              alt={user?.name || 'Talent'}
              className="w-20 h-20 rounded-full object-cover border-2 border-primary-container shadow-md"
            />
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h2 className="font-recoleta text-2xl font-bold text-on-surface">
                  {user?.name || 'Elena Rostova'}
                </h2>
                <span className="text-xs font-medium text-emerald-700 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Verified
                </span>
              </div>
              <p className="font-berthold text-xs text-slate-600">
                "Siren of the North" • Slavic-British Mid-Atlantic Resonant Tone
              </p>
              <div className="flex items-center gap-3 text-xs font-berthold text-secondary pt-1">
                <span>{voices.length} Registered Model{voices.length === 1 ? '' : 's'}</span>
                <span>•</span>
                <span className="font-code text-primary-container font-semibold">
                  Vault Key: {user?.vaultKey || 'SHA256:4080c0aea...'}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <TalentVoiceIllustration size={110} className="shrink-0 hidden md:inline-flex" />
            <Button variant="secondary" size="sm" icon={<Edit3 className="w-3.5 h-3.5" />}>
              Edit Public Profile
            </Button>
          </div>
        </div>
      </Card>

      {/* Voice Samples Showcase */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-recoleta text-xl font-bold text-on-surface">
              Featured Voice Demo Reels
            </h3>
            <p className="font-berthold text-xs text-slate-600">
              Published on the main domain Voice IP Marketplace (whicoustic.ai/marketplace)
            </p>
          </div>
          <div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".wav,.mp3,.flac,.aiff,audio/*"
              className="hidden"
            />
            <Button
              variant="primary"
              size="sm"
              isLoading={isUploading}
              onClick={() => fileInputRef.current?.click()}
              icon={<Plus className="w-3.5 h-3.5" />}
            >
              Upload New Audio Reel
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="py-12 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
            <p className="text-sm font-berthold text-slate-600">Loading verified demo reels from vault...</p>
          </div>
        )}

        {/* Error State */}
        {!isLoading && error && (
          <ErrorState
            illustration={<ConnectionLostIllustration size={180} />}
            title="Unable to Load Voice Reels"
            description={error}
            solutionSteps={[
              'Check backend service health on http://localhost:8000.',
              'Ensure database connection to SQLite or Supabase is active.',
              'Click retry below to re-fetch your demo reels.',
            ]}
            retryLabel="Retry Connection"
            onRetry={fetchVoices}
            isRetrying={isLoading}
            technicalError={error}
          />
        )}

        {/* Reels List or Empty State */}
        {!isLoading && !error && (
          <>
            {voices.length === 0 ? (
              <Card elevation="elevated" padding="lg">
                <EmptyState
                  illustration={<TalentVoiceIllustration size={180} />}
                  title="No Voice Demo Reels Uploaded"
                  description="You have not uploaded any voice demo reels yet. Upload reference speech samples to showcase your biometric persona on the Whicoustic Marketplace."
                  actionLabel="Upload First Audio Reel"
                  onAction={() => fileInputRef.current?.click()}
                  actionIcon={<Plus className="w-4 h-4" />}
                />
              </Card>
            ) : (
              <div className="space-y-3">
                {voices.map((voice) => {
                  const isPlaying = playingId === voice.id;

                  return (
                    <Card
                      key={voice.id}
                      elevation="flat"
                      padding="md"
                      className="flex flex-col sm:flex-row items-center justify-between gap-4 hover:border-primary-container/40 transition-colors"
                    >
                      <div className="flex items-center gap-4 w-full sm:w-1/3">
                        <button
                          onClick={() => setPlayingId(isPlaying ? null : voice.id)}
                          aria-label={isPlaying ? 'Pause sample' : 'Play sample'}
                          className="w-10 h-10 rounded-full bg-primary-container text-[#0B1C30] flex items-center justify-center shadow-amber-glow hover:bg-primary-hover shrink-0"
                        >
                          {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
                        </button>
                        <div className="min-w-0">
                          <p className="font-recoleta text-sm font-bold text-on-surface truncate">
                            {voice.name}
                          </p>
                          <p className="font-berthold text-xs text-secondary">
                            {voice.description || 'Biometric Voice Reel'} • {Math.round(voice.duration)}s
                          </p>
                        </div>
                      </div>

                      <div className="w-full sm:w-1/3">
                        <WaveformVisualizer isPlaying={isPlaying} height={36} barCount={24} />
                      </div>

                      <div className="flex items-center gap-4 text-xs font-berthold shrink-0">
                        <span className="text-secondary font-code">
                          {voice.sample_rate ? `${voice.sample_rate} Hz` : '48,000 Hz'}
                        </span>
                        <span className="text-xs font-code text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-pill border border-emerald-200">
                          Watermarked
                        </span>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>
    </PageTransition>
  );
};
