import React, { useEffect, useState } from 'react';
import clsx from 'clsx';

export interface WaveformVisualizerProps {
  isPlaying?: boolean;
  barCount?: number;
  height?: number;
  accentColor?: string;
  className?: string;
  interactive?: boolean;
  onBarClick?: (index: number) => void;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  isPlaying = true,
  barCount = 36,
  height = 54,
  className,
  interactive = false,
  onBarClick,
}) => {
  // Generate pseudo-random or organic heights
  const [bars, setBars] = useState<number[]>(() =>
    Array.from({ length: barCount }, (_, i) => {
      // Natural speech envelope wave
      const progress = i / barCount;
      const envelope = Math.sin(progress * Math.PI);
      const noise = 0.3 + Math.sin(i * 0.8) * 0.2 + (i % 3 === 0 ? 0.3 : 0.1);
      return Math.min(100, Math.max(15, Math.floor(envelope * noise * 100)));
    })
  );

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      setBars((prev) =>
        prev.map((val, idx) => {
          const delta = (Math.random() - 0.48) * 20;
          const envelope = Math.sin((idx / barCount) * Math.PI);
          return Math.min(95, Math.max(12, Math.floor(val + delta * envelope)));
        })
      );
    }, 120);

    return () => clearInterval(interval);
  }, [isPlaying, barCount]);

  return (
    <div
      className={clsx('flex items-center gap-[3px] select-none py-2 px-1', className)}
      style={{ height: `${height}px` }}
    >
      {bars.map((barHeight, idx) => {
        // Color distribution following Stitch spec: predominantly amber peaks + slate ink
        const isPeak = barHeight > 65;
        const isAmber = isPeak || idx % 4 === 0 || idx % 7 === 0;
        const colorClass = isAmber
          ? 'bg-primary-container shadow-[0_0_8px_rgba(245,158,11,0.4)]'
          : 'bg-on-surface/80 hover:bg-on-surface';

        return (
          <div
            key={idx}
            onClick={() => interactive && onBarClick?.(idx)}
            className={clsx(
              'flex-1 rounded-full transition-all duration-150',
              colorClass,
              interactive && 'cursor-pointer hover:scale-y-110'
            )}
            style={{
              height: `${barHeight}%`,
              minHeight: '4px',
            }}
          />
        );
      })}
    </div>
  );
};

