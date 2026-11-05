import React from 'react';
import clsx from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, helperText, error, leftIcon, rightIcon, className, id, ...props }, ref) => {
    const generatedId = React.useId();
    const inputId = id || (label ? `${label.toLowerCase().replace(/\s+/g, '-')}-${generatedId}` : generatedId);
    const helperId = `${inputId}-helper`;
    const errorId = `${inputId}-error`;

    return (
      <div className="w-full text-left">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-1.5"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          {leftIcon && (
            <div className="absolute left-3.5 flex items-center pointer-events-none text-secondary">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            aria-invalid={!!error}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            className={clsx(
              'w-full h-11 px-3.5 bg-white font-berthold text-sm text-on-surface rounded-input border transition-all duration-150',
              'placeholder:text-secondary/60 placeholder:font-normal',
              'focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20',
              error
                ? 'border-error focus:border-error focus:ring-error/20'
                : 'border-outline-border hover:border-secondary',
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3.5 flex items-center text-secondary">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <p id={errorId} className="mt-1 text-xs text-error font-berthold">{error}</p>
        ) : helperText ? (
          <p id={helperId} className="mt-1 text-xs text-secondary font-berthold">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';

