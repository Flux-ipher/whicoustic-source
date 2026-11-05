import React from 'react';
import clsx from 'clsx';
import { Card } from './Card';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface StatCardProps {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  caption?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  change,
  trend = 'neutral',
  caption,
  icon,
  className,
}) => {
  return (
    <Card elevation="elevated" padding="md" className={clsx('flex flex-col justify-between', className)}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-berthold font-semibold uppercase tracking-wider text-secondary">
          {label}
        </span>
        {icon && (
          <div className="w-8 h-8 rounded-full bg-surface-container flex items-center justify-center text-primary-container">
            {icon}
          </div>
        )}
      </div>

      <div className="mb-2">
        <h3 className="text-3xl font-recoleta text-on-surface font-bold tracking-tight">
          {value}
        </h3>
      </div>

      <div className="flex items-center gap-2 text-xs font-berthold">
        {change && (
          <span
            className={clsx(
              'inline-flex items-center gap-0.5 font-semibold px-2 py-0.5 rounded-pill',
              trend === 'up' && 'bg-emerald-50 text-emerald-700',
              trend === 'down' && 'bg-rose-50 text-rose-700',
              trend === 'neutral' && 'bg-surface-container text-secondary'
            )}
          >
            {trend === 'up' && <TrendingUp className="w-3 h-3" />}
            {trend === 'down' && <TrendingDown className="w-3 h-3" />}
            {trend === 'neutral' && <Minus className="w-3 h-3" />}
            {change}
          </span>
        )}
        {caption && <span className="text-secondary/80 font-normal">{caption}</span>}
      </div>
    </Card>
  );
};

