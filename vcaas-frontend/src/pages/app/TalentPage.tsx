import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { useAuth } from '../../context/AuthContext';
import { ShieldCheck, Play, Pause, Edit3, Plus, Globe, Sparkles } from 'lucide-react';

export const TalentPage: React.FC = () => {
  const { user } = useAuth();
  const [playingId, setPlayingId] = useState<string | null>(null);

  const samples = [
    {
      id: 'samp_01',
      title: 'Cinematic Noir Narration — The Last Rain',
      category: 'Audio Drama',
      duration: '0:48',
      licenseCount: 14,
    },
    {
      id: 'samp_02',
      title: 'Automotive Intelligence Keynote Speech',
      category: 'Commercial',
      duration: '1:12',
      licenseCount: 22,
    },
    {
      id: 'samp_03',
      title: 'Sci-Fi War Commander Tactical Dialogue',
      category: 'Video Game',
      duration: '0:35',
      licenseCount: 31,
    },
  ];

  return (
    <div className="space-y-8 pb-10">
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
                <h2 className="font-recoletta text-2xl font-bold text-on-surface">
                  {user?.name || 'Elena Rostova'}
                </h2>
                <Badge variant="amber" size="sm" icon={<ShieldCheck className="w-3.5 h-3.5" />}>
                  Verified Biometric Persona
                </Badge>
              </div>
              <p className="font-lora italic text-xs text-secondary">
                "Siren of the North" • Slavic-British Mid-Atlantic Resonant Tone
              </p>
              <div className="flex items-center gap-3 text-xs font-berthold text-secondary pt-1">
                <span>42 Active Licenses</span>
                <span>•</span>
                <span className="font-code text-primary-container font-semibold">
                  Vault SHA256: 4080c0aea...
                </span>
              </div>
            </div>
          </div>

          <Button variant="secondary" size="sm" icon={<Edit3 className="w-3.5 h-3.5" />}>
            Edit Public Profile
          </Button>
        </div>
      </Card>

      {/* Voice Samples Showcase */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              Featured Voice Demo Reels
            </h3>
            <p className="font-lora italic text-xs text-secondary">
              Published on the main domain Voice IP Marketplace (vcaas.com/marketplace)
            </p>
          </div>
          <Button variant="primary" size="sm" icon={<Plus className="w-3.5 h-3.5" />}>
            Upload New Audio Reel
          </Button>
        </div>

        <div className="space-y-3">
          {samples.map((sample) => {
            const isPlaying = playingId === sample.id;

            return (
              <Card
                key={sample.id}
                elevation="flat"
                padding="md"
                className="flex flex-col sm:flex-row items-center justify-between gap-4 hover:border-primary-container/40 transition-colors"
              >
                <div className="flex items-center gap-4 w-full sm:w-1/3">
                  <button
                    onClick={() => setPlayingId(isPlaying ? null : sample.id)}
                    className="w-10 h-10 rounded-full bg-primary-container text-white flex items-center justify-center shadow-amber-glow hover:bg-primary-hover shrink-0"
                  >
                    {isPlaying ? <Pause className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
                  </button>
                  <div className="min-w-0">
                    <p className="font-recoletta text-sm font-bold text-on-surface truncate">
                      {sample.title}
                    </p>
                    <p className="font-berthold text-xs text-secondary">
                      {sample.category} • {sample.duration}
                    </p>
                  </div>
                </div>

                <div className="w-full sm:w-1/3">
                  <WaveformVisualizer isPlaying={isPlaying} height={36} barCount={24} />
                </div>

                <div className="flex items-center gap-4 text-xs font-berthold shrink-0">
                  <span className="text-secondary font-code">{sample.licenseCount} Studios Licensed</span>
                  <Badge variant="neutral" size="sm">
                    Watermarked
                  </Badge>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};
