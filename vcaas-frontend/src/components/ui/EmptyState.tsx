import React from 'react';
import { motion } from 'framer-motion';
import { Button } from './Button';
import { Link } from 'react-router-dom';

export interface EmptyStateProps {
  illustration: React.ReactNode;
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  actionHref?: string;
  actionIcon?: React.ReactNode;
  secondaryLabel?: string;
  onSecondaryAction?: () => void;
  secondaryHref?: string;
  className?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  illustration,
  title,
  description,
  actionLabel,
  onAction,
  actionHref,
  actionIcon,
  secondaryLabel,
  onSecondaryAction,
  secondaryHref,
  className = '',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className={`text-center py-12 px-6 max-w-lg mx-auto flex flex-col items-center justify-center space-y-5 ${className}`}
    >
      <div className="mb-2 shrink-0">{illustration}</div>

      <div className="space-y-2">
        <h3 className="font-recoletta text-2xl sm:text-3xl font-bold text-on-surface tracking-tight">
          {title}
        </h3>
        <p className="font-berthold text-sm sm:text-base text-slate-600 leading-relaxed max-w-md mx-auto">
          {description}
        </p>
      </div>

      {(actionLabel || secondaryLabel) && (
        <div className="pt-2 flex flex-wrap items-center justify-center gap-3">
          {actionLabel && (
            actionHref ? (
              <Link to={actionHref}>
                <Button variant="primary" size="md" icon={actionIcon}>
                  {actionLabel}
                </Button>
              </Link>
            ) : (
              <Button variant="primary" size="md" onClick={onAction} icon={actionIcon}>
                {actionLabel}
              </Button>
            )
          )}

          {secondaryLabel && (
            secondaryHref ? (
              <Link to={secondaryHref}>
                <Button variant="secondary" size="md">
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
      )}
    </motion.div>
  );
};
