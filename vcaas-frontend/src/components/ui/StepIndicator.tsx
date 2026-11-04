import React from 'react';
import clsx from 'clsx';
import { Check } from 'lucide-react';

export interface Step {
  id: number;
  title: string;
  subtitle?: string;
}

export interface StepIndicatorProps {
  steps: Step[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
  className?: string;
}

export const StepIndicator: React.FC<StepIndicatorProps> = ({
  steps,
  currentStep,
  onStepClick,
  className,
}) => {
  return (
    <div className={clsx('w-full max-w-2xl mx-auto', className)}>
      <div className="relative flex items-center justify-between">
        {/* Continuous connector background */}
        <div className="absolute top-1/2 left-0 right-0 -translate-y-1/2 h-0.5 bg-outline-subtle -z-0" />

        {/* Active progress bar */}
        <div
          className="absolute top-1/2 left-0 -translate-y-1/2 h-0.5 bg-primary-container transition-all duration-300 -z-0"
          style={{
            width: `${((currentStep - 1) / (steps.length - 1)) * 100}%`,
          }}
        />

        {steps.map((step) => {
          const isCompleted = step.id < currentStep;
          const isCurrent = step.id === currentStep;

          return (
            <div
              key={step.id}
              onClick={() => isCompleted && onStepClick?.(step.id)}
              className={clsx(
                'relative z-10 flex flex-col items-center group',
                isCompleted && onStepClick && 'cursor-pointer'
              )}
            >
              <div
                className={clsx(
                  'w-9 h-9 rounded-full flex items-center justify-center font-berthold font-semibold text-xs transition-all duration-200 border-2',
                  isCompleted
                    ? 'bg-primary-container text-white border-primary-container shadow-amber-glow'
                    : isCurrent
                    ? 'bg-white text-primary-container border-primary-container ring-4 ring-primary-container/20 shadow-md scale-105'
                    : 'bg-white text-secondary border-outline-subtle'
                )}
              >
                {isCompleted ? <Check className="w-4 h-4 stroke-[3]" /> : step.id}
              </div>

              <div className="absolute -bottom-7 w-36 text-center">
                <p
                  className={clsx(
                    'text-xs font-berthold transition-colors',
                    isCurrent
                      ? 'font-bold text-on-surface'
                      : isCompleted
                      ? 'text-on-surface'
                      : 'text-secondary/70'
                  )}
                >
                  {step.title}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

