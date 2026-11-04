import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { mockMarketplaceVoices, VoiceTalent } from '../../data/mock/marketplace';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { EmptyState } from '../../components/ui/EmptyState';
import { EmptySearchIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { Search, Play, Pause, ShieldCheck, SlidersHorizontal, RotateCcw } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MarketplacePage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [playingId, setPlayingId] = useState<string | null>(null);

  const categories = ['All', 'Cinematic', 'Commercial', 'Video Game', 'Audiobook', 'Corporate', 'Character'];

  const filteredVoices = mockMarketplaceVoices.filter((v) => {
    const matchesSearch =
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.stageName.toLowerCase().includes(search.toLowerCase()) ||
      v.accent.toLowerCase().includes(search.toLowerCase()) ||
      v.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));

    const matchesCategory = selectedCategory === 'All' || v.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  const togglePlay = (id: string) => {
    setPlayingId((prev) => (prev === id ? null : id));
  };

  return (
    <PageTransition className="max-w-container mx-auto px-6 py-12 space-y-10">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b border-outline-subtle">
        <div className="space-y-2">
          <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
            Voice IP Marketplace
          </h1>
          <p className="font-berthold text-slate-700 text-base max-w-xl">
            Browse legally verified, SHA-256 watermarked neural voice personas available for instant license across games, streaming, and global advertising.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-secondary absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search voice, accent, or style..."
            className="w-full h-11 pl-11 pr-4 text-sm font-berthold bg-white rounded-pill border border-outline-border focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20 shadow-sm transition-all"
          />
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        <span className="text-xs font-berthold font-semibold text-secondary uppercase tracking-wider flex items-center gap-1.5 mr-2 shrink-0">
          <SlidersHorizontal className="w-3.5 h-3.5" />
          Category:
        </span>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-1.5 rounded-pill text-xs font-berthold font-semibold transition-all shrink-0 ${
              selectedCategory === cat
                ? 'bg-[#0B1C30] text-white shadow-sm'
                : 'bg-white text-secondary hover:text-on-surface hover:bg-surface-container border border-outline-subtle'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Voice Talent Grid or Empty State */}
      {filteredVoices.length === 0 ? (
        <EmptyState
          illustration={<EmptySearchIllustration size={180} />}
          title="No voice personas found"
          description={`We couldn't locate any verified models matching "${search || selectedCategory}". Try testing alternate search terms, or reset your filters.`}
          actionLabel="Reset Search & Filters"
          onAction={() => {
            setSearch('');
            setSelectedCategory('All');
          }}
          actionIcon={<RotateCcw className="w-4 h-4" />}
          secondaryLabel="Submit Bespoke Casting Request"
          secondaryHref="/contact"
        />
      ) : (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: { staggerChildren: 0.08 },
            },
          }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {filteredVoices.map((voice) => {
            const isPlaying = playingId === voice.id;

            return (
              <motion.div
                key={voice.id}
                variants={{
                  hidden: { opacity: 0, y: 16 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                <Card
                  elevation="elevated"
                  padding="lg"
                  hoverEffect
                  className="flex flex-col justify-between space-y-5 h-full"
                >
                  {/* Header: Avatar, Name & Verification */}
                  <div>
                    <div className="flex items-start justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3">
                        <img
                          src={voice.avatar}
                          alt={voice.name}
                          className="w-14 h-14 rounded-full object-cover border-2 border-primary-container/30 shadow-sm"
                        />
                        <div>
                          <div className="flex items-center gap-1.5">
                            <h3 className="font-recoletta text-lg font-bold text-on-surface">
                              {voice.name}
                            </h3>
                            {voice.verified && (
                              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                            )}
                          </div>
                          <p className="font-berthold text-xs text-slate-600">
                            "{voice.stageName}"
                          </p>
                        </div>
                      </div>
                      <span className="text-xs font-berthold font-medium text-secondary">
                        {voice.category}
                      </span>
                    </div>

                    <p className="text-xs font-berthold text-secondary leading-relaxed line-clamp-2 mb-4">
                      {voice.description}
                    </p>

                    {/* Accent & Language */}
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {voice.tags.map((t) => (
                        <span
                          key={t}
                          className="px-2 py-0.5 rounded-pill bg-surface-container text-[11px] font-berthold text-secondary"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Audio Preview & Waveform */}
                  <div className="bg-surface-container/70 p-3.5 rounded-card border border-outline-subtle space-y-2">
                    <div className="flex items-center justify-between text-xs font-berthold">
                      <button
                        onClick={() => togglePlay(voice.id)}
                        className="flex items-center gap-2 font-semibold text-primary-container hover:text-primary-hover transition-colors"
                      >
                        {isPlaying ? (
                          <Pause className="w-4 h-4 fill-current" />
                        ) : (
                          <Play className="w-4 h-4 fill-current" />
                        )}
                        <span>{isPlaying ? 'Pause Sample' : 'Listen Sample'}</span>
                      </button>
                      <span className="font-code text-[11px] text-secondary">
                        {voice.accent}
                      </span>
                    </div>
                    <WaveformVisualizer isPlaying={isPlaying} height={36} barCount={28} />
                  </div>

                  {/* Pricing & CTA */}
                  <div className="pt-3 border-t border-outline-subtle flex items-center justify-between">
                    <div>
                      <span className="text-[11px] font-berthold uppercase tracking-wider text-secondary block">
                        Starting At
                      </span>
                      <div className="flex items-baseline gap-1">
                        <span className="font-recoletta text-2xl font-bold text-on-surface">
                          ${voice.hourlyRate}
                        </span>
                        <span className="text-xs font-berthold text-secondary">/hr</span>
                      </div>
                    </div>

                    <Link to="/contact">
                      <Button variant="primary" size="sm">
                        Request License
                      </Button>
                    </Link>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </motion.div>
      )}
    </PageTransition>
  );
};

