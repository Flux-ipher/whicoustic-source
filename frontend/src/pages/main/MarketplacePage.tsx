import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { licenseService, MarketplaceLicenseItem } from '../../services/licenseService';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptySearchIllustration, EmptyVaultIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { Search, Play, Pause, ShieldCheck, SlidersHorizontal, RotateCcw, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export const MarketplacePage: React.FC = () => {
  const [voices, setVoices] = useState<MarketplaceLicenseItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [playingId, setPlayingId] = useState<string | null>(null);

  const categories = ['All', 'commercial', 'personal', 'enterprise', 'educational', 'non_profit', 'custom'];

  const fetchMarketplace = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await licenseService.browseMarketplace({
        license_type: selectedCategory === 'All' ? undefined : selectedCategory,
      });
      setVoices(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to Whicoustic Marketplace API.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedCategory]);

  useEffect(() => {
    fetchMarketplace();
  }, [fetchMarketplace]);

  const filteredVoices = voices.filter((v) => {
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      v.name.toLowerCase().includes(q) ||
      (v.description && v.description.toLowerCase().includes(q)) ||
      v.license_type.toLowerCase().includes(q) ||
      (v.territory && v.territory.some((t) => t.toLowerCase().includes(q))) ||
      (v.allowed_use_cases && v.allowed_use_cases.some((u) => u.toLowerCase().includes(q)));

    const matchesCategory =
      selectedCategory === 'All' || v.license_type.toLowerCase() === selectedCategory.toLowerCase();

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
          <h1 className="font-recoleta text-4xl sm:text-5xl font-bold text-on-surface">
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
            placeholder="Search voice, territory, or use case..."
            className="w-full h-11 pl-11 pr-4 text-sm font-berthold bg-white rounded-pill border border-outline-border focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20 shadow-sm transition-all"
          />
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        <span className="text-xs font-berthold font-semibold text-secondary uppercase tracking-wider flex items-center gap-1.5 mr-2 shrink-0">
          <SlidersHorizontal className="w-3.5 h-3.5" />
          License Type:
        </span>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-1.5 rounded-pill text-xs font-berthold font-semibold capitalize transition-all shrink-0 ${
              selectedCategory === cat
                ? 'bg-[#0B1C30] text-white shadow-sm'
                : 'bg-white text-secondary hover:text-on-surface hover:bg-surface-container border border-outline-subtle'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Loading Skeleton */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center space-y-4">
          <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
          <p className="text-sm font-berthold text-slate-600">Connecting to real-time marketplace registry...</p>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Marketplace Stream Unreachable"
          description={error}
          solutionSteps={[
            'Ensure the Whicoustic backend API server is running on http://localhost:8000.',
            'Verify that network firewall or CORS settings permit /api/v1/licenses requests.',
            'Click the retry button below to re-attempt establishing connection.',
          ]}
          retryLabel="Retry Registry Connection"
          onRetry={fetchMarketplace}
          isRetrying={isLoading}
          secondaryLabel="Contact Support Desk"
          secondaryHref="/contact"
          technicalError={error}
        />
      )}

      {/* Voice Talent Grid or Empty State */}
      {!isLoading && !error && (
        <>
          {filteredVoices.length === 0 ? (
            voices.length === 0 ? (
              <EmptyState
                illustration={<EmptyVaultIllustration size={180} />}
                title="Voice IP Marketplace Catalog is Empty"
                description="There are currently no active public voice licenses registered in the database. Voice actors and talent can publish verified personas via the Voice Studio to appear in the marketplace."
                actionLabel="Explore Voice Studio"
                actionHref="/studio"
                secondaryLabel="Submit Bespoke Casting Request"
                secondaryHref="/contact"
              />
            ) : (
              <EmptyState
                illustration={<EmptySearchIllustration size={180} />}
                title="No voice personas match criteria"
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
            )
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
                      {/* Header: Name & Verification */}
                      <div>
                        <div className="flex items-start justify-between gap-4 mb-3">
                          <div>
                            <div className="flex items-center gap-1.5">
                              <h3 className="font-recoleta text-lg font-bold text-on-surface">
                                {voice.name}
                              </h3>
                              <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                            </div>
                            <p className="font-code text-xs text-slate-500">
                              {voice.id}
                            </p>
                          </div>
                          <span className="text-xs font-berthold font-semibold uppercase px-2 py-0.5 rounded-pill bg-surface-container text-[#0B1C30] border border-outline-subtle">
                            {voice.license_type}
                          </span>
                        </div>

                        <p className="text-xs font-berthold text-secondary leading-relaxed line-clamp-2 mb-4">
                          {voice.description || 'Verified biometric model anchored with 21.4 kHz ultrasonic watermark.'}
                        </p>

                        {/* Territories / Use Cases */}
                        <div className="flex flex-wrap gap-1.5 mb-4">
                          {(voice.territory || ['Worldwide']).map((t) => (
                            <span
                              key={t}
                              className="px-2 py-0.5 rounded-pill bg-surface-container text-[11px] font-berthold text-secondary"
                            >
                              {t}
                            </span>
                          ))}
                          {(voice.allowed_use_cases || []).map((u) => (
                            <span
                              key={u}
                              className="px-2 py-0.5 rounded-pill bg-amber-50 text-[11px] font-berthold text-amber-800 border border-amber-200"
                            >
                              {u}
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
                            {voice.duration_days ? `${voice.duration_days} Days Term` : 'Perpetual'}
                          </span>
                        </div>
                        <WaveformVisualizer isPlaying={isPlaying} height={36} barCount={28} />
                      </div>

                      {/* Pricing & CTA */}
                      <div className="pt-3 border-t border-outline-subtle flex items-center justify-between">
                        <div>
                          <span className="text-[11px] font-berthold uppercase tracking-wider text-secondary block">
                            License Fee
                          </span>
                          <div className="flex items-baseline gap-1">
                            <span className="font-recoleta text-2xl font-bold text-on-surface">
                              ${voice.price.toLocaleString()}
                            </span>
                            <span className="text-xs font-berthold text-secondary">
                              {voice.currency}
                            </span>
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
        </>
      )}
    </PageTransition>
  );
};
