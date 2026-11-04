import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Search, ChevronDown, ChevronUp, ShieldAlert, Cpu, DollarSign, RotateCcw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { EmptySearchIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';

interface FAQ {
  q: string;
  a: string;
  category: string;
}

const faqs: FAQ[] = [
  {
    category: 'Watermarking & Security',
    q: 'How does ultrasonic cryptographic watermarking prevent unauthorized deepfakes?',
    a: 'Whicoustic embeds an imperceptible, lossless cryptographic payload (SHA-256 hash) directly into the acoustic frequency matrix of synthesized audio. If an unauthorized entity broadcasts audio claiming to be you, automated web sniffers and forensic scanners analyze the stream for your unique acoustic key.',
  },
  {
    category: 'Watermarking & Security',
    q: 'Can third-party compression (MP3, YouTube, TikTok) erase the watermark?',
    a: 'No. The Whicoustic steganographic algorithm is trained against heavy psychoacoustic compression, bandpass filtering, and ambient background noise. The watermark survives standard broadcast codecs and downsampling.',
  },
  {
    category: 'Licensing & Royalties',
    q: 'How are royalty disbursements calculated and paid out?',
    a: 'Every time an enterprise studio or game developer synthesizes audio using your voice persona, the consumption is metered by the second. Royalties are accrued in an automated escrow contract and disbursed monthly via direct Fedwire bank transfer or USDC crypto vault.',
  },
  {
    category: 'Licensing & Royalties',
    q: 'Can I decline a studio license request?',
    a: 'Yes. As the verified voice rights holder, you retain total sovereign veto authority over any inbound request. You can also establish pre-approved commercial tiers and strict exclusion categories (e.g. gambling, political campaigning).',
  },
  {
    category: 'Voice Cloning Studio',
    q: 'How much audio do I need to create a high-fidelity clone?',
    a: 'A minimum of 5 minutes of clean studio speech (24-bit/48kHz or higher) is sufficient to calibrate your acoustic anchor. For AAA game dialogue with extreme emotional inflection, we recommend 20 to 30 minutes of varied training reads.',
  },
  {
    category: 'Platform Architecture',
    q: 'Why does the platform console live on the app.whicoustic.ai sub-domain?',
    a: 'For enterprise-grade security isolation. The public marketing website (whicoustic.ai) and the authenticated platform console (app.whicoustic.ai) operate with isolated cookie scopes and strict CORS policies to protect your biometric vault keys.',
  },
];

export const HelpPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const filteredFaqs = faqs.filter(
    (f) =>
      f.q.toLowerCase().includes(search.toLowerCase()) ||
      f.a.toLowerCase().includes(search.toLowerCase()) ||
      f.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <PageTransition className="max-w-container mx-auto px-6 py-12 space-y-12">
      {/* Header */}
      <div className="max-w-3xl mx-auto text-center space-y-4">
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Frequently Asked Questions
        </h1>
        <p className="font-berthold text-slate-700 text-base">
          Everything you need to know about biometric voice cloning, cryptographic provenance, and automated royalty licensing.
        </p>

        {/* Search Input */}
        <div className="relative max-w-lg mx-auto pt-4">
          <Search className="w-4 h-4 text-secondary absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search questions by keyword..."
            className="w-full h-12 pl-11 pr-4 text-sm font-berthold bg-white rounded-pill border border-outline-border focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20 shadow-sm"
          />
        </div>
      </div>

      {/* Category Tiles */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
        <Card elevation="elevated" padding="md" className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface">Security & Proof</h4>
            <p className="text-xs font-berthold text-secondary">Ultrasonic watermarks & keys</p>
          </div>
        </Card>
        <Card elevation="elevated" padding="md" className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface">Royalties & Escrow</h4>
            <p className="text-xs font-berthold text-secondary">Disbursements & contracts</p>
          </div>
        </Card>
        <Card elevation="elevated" padding="md" className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface">Synthesis Studio</h4>
            <p className="text-xs font-berthold text-secondary">Audio formats & latency</p>
          </div>
        </Card>
      </div>

      {/* Accordion FAQ List or Empty State */}
      {filteredFaqs.length === 0 ? (
        <EmptyState
          illustration={<EmptySearchIllustration size={180} />}
          title="No documentation matches your inquiry"
          description={`We couldn't find any questions matching "${search}". Our engineering and rights counsel can answer your specific questions.`}
          actionLabel="Reset Search Query"
          onAction={() => setSearch('')}
          actionIcon={<RotateCcw className="w-4 h-4" />}
          secondaryLabel="Speak with an Engineer"
          secondaryHref="/contact"
        />
      ) : (
        <div className="max-w-3xl mx-auto space-y-4">
          {filteredFaqs.map((faq, idx) => {
            const isOpen = openIndex === idx;

            return (
              <Card
                key={idx}
                elevation="flat"
                padding="md"
                role="button"
                tabIndex={0}
                aria-expanded={isOpen}
                className="cursor-pointer transition-colors hover:border-primary-container/40 focus:outline-none focus:ring-2 focus:ring-primary-container/30"
                onClick={() => setOpenIndex(isOpen ? null : idx)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenIndex(isOpen ? null : idx);
                  }
                }}
              >
                <div className="flex items-center justify-between gap-4">
                  <span className="font-recoletta text-base sm:text-lg font-bold text-on-surface">
                    {faq.q}
                  </span>
                  <span className="text-secondary shrink-0">
                    {isOpen ? <ChevronUp className="w-4 h-4 text-primary-container" /> : <ChevronDown className="w-4 h-4" />}
                  </span>
                </div>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      transition={{ duration: 0.25, ease: 'easeOut' }}
                      className="overflow-hidden"
                    >
                      <div className="pt-3 mt-3 border-t border-outline-subtle">
                        <p className="font-berthold text-sm text-slate-700 leading-relaxed">
                          {faq.a}
                        </p>
                        <span className="inline-block mt-3 text-[11px] font-code text-primary-container">
                          Category: {faq.category}
                        </span>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            );
          })}
        </div>
      )}

      {/* Escalation CTA */}
      <div className="max-w-xl mx-auto text-center p-8 rounded-card bg-surface-container border border-outline-subtle space-y-3">
        <h3 className="font-recoletta text-xl font-bold text-on-surface">
          Have an enterprise security question?
        </h3>
        <p className="font-berthold text-xs text-slate-600">
          Our acoustic engineers and IP licensing counsel are available for technical consultations.
        </p>
        <div className="pt-2">
          <Link to="/contact">
            <Button variant="primary" size="sm">
              Contact Infrastructure Team
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
};

