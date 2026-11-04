import React from 'react';
import clsx from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevation?: 'flat' | 'elevated' | 'amber-border';
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hoverEffect?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  elevation = 'flat',
  padding = 'md',
  hoverEffect = false,
  className,
  ...props
}) => {
  const base = 'bg-white rounded-card transition-all duration-200 border';

  const elevations = {
    // Level 1: Flat with subtle hairline border
    flat: 'border-outline-subtle shadow-none',
    // Level 2: Elevated soft ambient shadow
    elevated: 'border-outline-subtle shadow-card',
    // Level 3: Amber highlight border with soft aura
    'amber-border': 'border-[#FDE68A] bg-gradient-to-b from-[#FFFDF7] to-white shadow-card',
  };

  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
    xl: 'p-10',
  };

  const hover = hoverEffect
    ? 'hover:border-primary-container/40 hover:shadow-elevated hover:-translate-y-0.5 cursor-pointer'
    : '';

  return (
    <div
      className={clsx(base, elevations[elevation], paddings[padding], hover, className)}
      {...props}
    >
      {children}
    </div>
  );
};

