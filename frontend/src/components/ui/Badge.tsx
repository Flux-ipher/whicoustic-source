import React from 'react';
import clsx from 'clsx';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'amber' | 'neutral' | 'success' | 'outline' | 'dark';
  size?: 'sm' | 'md';
  pulse?: boolean;
  className?: string;
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'amber',
  size = 'md',
  pulse = false,
  className,
  icon,
}) => {
  const base =
    'inline-flex items-center rounded-pill font-berthold tracking-wide uppercase font-semibold select-none';

  const variants = {
    amber: 'bg-[#FEF3C7] text-[#92400E] border border-[#FDE68A]',
    neutral: 'bg-surface-container text-secondary border border-outline-subtle',
    success: 'bg-[#DCFCE7] text-[#166534] border border-[#BBF7D0]',
    outline: 'bg-white text-on-surface border border-outline-subtle',
    dark: 'bg-on-surface text-white border border-on-surface',
  };

  const sizes = {
    sm: 'text-[10px] px-2.5 py-0.5 gap-1.5 leading-none',
    md: 'text-xs px-3 py-1 gap-2',
  };

  return (
    <span className={clsx(base, variants[variant], sizes[size], className)}>
      {pulse && (
        <span className="relative flex h-2 w-2 shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-container opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-container" />
        </span>
      )}
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

