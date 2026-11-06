import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import { RefreshCw, ArrowRight, ChevronDown, ChevronUp } from 'lucide-react';
import { Link } from 'react-router-dom';

export interface ErrorStateProps {
  illustration: React.ReactNode;
  title: string;
  description: string;
  solutionSteps?: string[];
  retryLabel?: string;
  onRetry?: () => void;
  isRetrying?: boolean;
  secondaryLabel?: string;
  onSecondaryAction?: () => void;
  secondaryHref?: string;
  technicalError?: string;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  illustration,
  title,
  description,
  retryLabel = 'Try Again',
  onRetry,
  isRetrying = false,
  secondaryLabel,
  onSecondaryAction,
  secondaryHref,
  technicalError,
  className = '',
}) => {
  const [showTechnical, setShowTechnical] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className={`text-center py-10 px-6 max-w-xl mx-auto flex flex-col items-center justify-center space-y-6 ${className}`}
    >
      {/* Illustration */}
      <div className="shrink-0">{illustration}</div>

      {/* Title & Human-readable Explanation */}
      <div className="space-y-2">
        <h3 className="font-recoleta text-2xl sm:text-3xl font-bold text-on-surface tracking-tight">
          {title}
        </h3>
        <p className="font-berthold text-sm sm:text-base text-slate-600 leading-relaxed max-w-md mx-auto">
          {description}
        </p>
      </div>

      {/* Primary & Secondary Action CTAs */}
      <div className="pt-1 flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <Button
            variant="primary"
            size="md"
            onClick={onRetry}
            isLoading={isRetrying}
            icon={<RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />}
          >
            {retryLabel}
          </Button>
        )}

        {secondaryLabel && (
          secondaryHref ? (
            <Link to={secondaryHref}>
              <Button variant="secondary" size="md" icon={<ArrowRight className="w-4 h-4" />} iconPosition="right">
                {secondaryLabel}
              </Button>
            </Link>
          ) : (
            <Button variant="secondary" size="md" onClick={onSecondaryAction}>
              {secondaryLabel}
            </Button>
          )
        )}
      </div>

      {/* Optional Technical Details Toggle */}
      {technicalError && (
        <div className="w-full pt-2">
          <button
            onClick={() => setShowTechnical(!showTechnical)}
            className="inline-flex items-center gap-1.5 text-xs font-code text-slate-500 hover:text-slate-800 transition-colors"
          >
            <span>{showTechnical ? 'Hide technical diagnostics' : 'View technical diagnostics'}</span>
            {showTechnical ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          <AnimatePresence>
            {showTechnical && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden mt-2 text-left"
              >
                <div className="p-3 bg-slate-900 text-emerald-400 font-code text-xs rounded-lg border border-slate-800 overflow-x-auto">
                  <span className="text-slate-400 block mb-1"># Error Payload Diagnostic:</span>
                  <pre className="whitespace-pre-wrap">{technicalError}</pre>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </motion.div>
  );
};

